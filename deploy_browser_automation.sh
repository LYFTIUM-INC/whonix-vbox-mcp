#!/bin/bash

# Browser Automation Infrastructure Deployment Script
# This script sets up and manages the complete containerized browser automation system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="browser-automation"
POD_NAME="${PROJECT_NAME}-pod"
COMPOSE_FILE="podman-compose.yaml"
POD_YAML="browser-automation-pod.yaml"
DATA_DIR="$HOME/browser-automation"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    local deps_missing=false
    
    # Check for Podman
    if command -v podman &> /dev/null; then
        print_success "Podman installed: $(podman --version)"
    else
        print_error "Podman is not installed"
        deps_missing=true
    fi
    
    # Check for Podman Compose
    if command -v podman-compose &> /dev/null; then
        print_success "Podman Compose installed: $(podman-compose --version)"
    else
        print_warning "Podman Compose not found, checking for docker-compose compatibility"
        if command -v docker-compose &> /dev/null; then
            print_success "Docker Compose found, will use with podman"
        else
            print_error "Neither podman-compose nor docker-compose found"
            deps_missing=true
        fi
    fi
    
    # Check for Python
    if command -v python3 &> /dev/null; then
        print_success "Python3 installed: $(python3 --version)"
    else
        print_error "Python3 is not installed"
        deps_missing=true
    fi
    
    # Check for Node.js
    if command -v node &> /dev/null; then
        print_success "Node.js installed: $(node --version)"
    else
        print_warning "Node.js not installed (will be installed in container)"
    fi
    
    if [ "$deps_missing" = true ]; then
        print_error "Missing required dependencies. Please install them first."
        exit 1
    fi
}

setup_directories() {
    print_header "Setting Up Directory Structure"
    
    # Create main directories
    mkdir -p "$DATA_DIR"/{data,screenshots,exports,logs,scripts,containers}
    mkdir -p "$DATA_DIR"/logs/{tor,browser,processor,screenshots}
    
    print_success "Created directory structure at $DATA_DIR"
    
    # Set permissions
    chmod -R 755 "$DATA_DIR"
    print_success "Set directory permissions"
}

copy_files() {
    print_header "Copying Required Files"
    
    # Copy automation scripts
    if [ -d "./automation" ]; then
        cp -r ./automation/* "$DATA_DIR/scripts/" 2>/dev/null || true
        print_success "Copied automation scripts"
    fi
    
    # Copy browser server files
    for file in secure_tor_browser_server.js browser_server_dual_mode.js enhanced_browser_automation.py enhanced_url_collector.py; do
        if [ -f "$file" ]; then
            cp "$file" "$DATA_DIR/scripts/"
            print_success "Copied $file"
        fi
    done
    
    # Copy Dockerfiles
    if [ -d "./containers" ]; then
        cp -r ./containers/* "$DATA_DIR/containers/" 2>/dev/null || true
        print_success "Copied container definitions"
    fi
}

create_env_file() {
    print_header "Creating Environment Configuration"
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Browser Automation Environment Configuration
LOG_LEVEL=INFO
API_KEY=b3bf6d72f07e50c78493bf780ca140501f3077534ac812c487798ab4a7db9688
TOR_CONTROL_PASSWORD=changeme
DASHBOARD_AUTH=false
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=changeme
WHONIX_VM_PASSWORD=${WHONIX_VM_PASSWORD:-}
EOF
        print_success "Created .env file"
    else
        print_success ".env file already exists"
    fi
}

build_containers() {
    print_header "Building Container Images"
    
    # Build using podman-compose
    if command -v podman-compose &> /dev/null; then
        podman-compose build
    else
        # Fallback to individual builds
        print_warning "Building containers individually"
        
        # Build Tor container
        if [ -f "containers/Dockerfile.tor" ]; then
            podman build -t darkweb-tor:latest -f containers/Dockerfile.tor .
            print_success "Built Tor proxy container"
        fi
        
        # Build Browser container
        if [ -f "containers/Dockerfile.browser" ]; then
            podman build -t browser-automation:latest -f containers/Dockerfile.browser .
            print_success "Built browser automation container"
        fi
        
        # Build Processor container
        if [ -f "containers/Dockerfile.processor" ]; then
            podman build -t data-processor:latest -f containers/Dockerfile.processor .
            print_success "Built data processor container"
        fi
        
        # Build Screenshot container
        if [ -f "containers/Dockerfile.screenshots" ]; then
            podman build -t screenshot-processor:latest -f containers/Dockerfile.screenshots .
            print_success "Built screenshot processor container"
        fi
        
        # Build Dashboard container
        if [ -f "containers/Dockerfile.dashboard" ]; then
            podman build -t browser-dashboard:latest -f containers/Dockerfile.dashboard .
            print_success "Built dashboard container"
        fi
    fi
}

start_pod() {
    print_header "Starting Browser Automation Pod"
    
    # Choose deployment method
    echo "Select deployment method:"
    echo "1) Podman Compose (recommended)"
    echo "2) Kubernetes-style Pod YAML"
    echo "3) Individual containers"
    read -p "Choice [1-3]: " choice
    
    case $choice in
        1)
            if command -v podman-compose &> /dev/null; then
                podman-compose up -d
            else
                docker-compose --podman-local up -d
            fi
            print_success "Started pod using Podman Compose"
            ;;
        2)
            podman play kube "$POD_YAML"
            print_success "Started pod using Kubernetes YAML"
            ;;
        3)
            # Start individual containers
            print_warning "Starting containers individually"
            
            # Create pod first
            podman pod create --name "$POD_NAME" \
                -p 3000:3000 \
                -p 8080:8080 \
                -p 9050:9050 \
                -p 6379:6379
            
            # Start Tor
            podman run -d --pod "$POD_NAME" \
                --name browser-tor \
                -v "$DATA_DIR/logs/tor:/var/log/tor" \
                darkweb-tor:latest
            
            # Start Redis
            podman run -d --pod "$POD_NAME" \
                --name browser-redis \
                redis:7-alpine
            
            # Start Browser Automation
            podman run -d --pod "$POD_NAME" \
                --name browser-engine \
                -v "$DATA_DIR/data:/data" \
                -v "$DATA_DIR/screenshots:/screenshots" \
                -v "$DATA_DIR/logs/browser:/logs" \
                -v "$DATA_DIR/scripts:/app/scripts:ro" \
                browser-automation:latest
            
            # Start Data Processor
            podman run -d --pod "$POD_NAME" \
                --name browser-processor \
                -v "$DATA_DIR/data:/data" \
                -v "$DATA_DIR/exports:/exports" \
                -v "$DATA_DIR/logs/processor:/logs" \
                data-processor:latest
            
            # Start Screenshot Processor
            podman run -d --pod "$POD_NAME" \
                --name browser-screenshots \
                -v "$DATA_DIR/screenshots:/screenshots" \
                -v "$DATA_DIR/logs/screenshots:/logs" \
                screenshot-processor:latest
            
            # Start Dashboard
            podman run -d --pod "$POD_NAME" \
                --name browser-dashboard \
                -v "$DATA_DIR/data:/data:ro" \
                -v "$DATA_DIR/screenshots:/screenshots:ro" \
                -v "$DATA_DIR/exports:/exports:ro" \
                browser-dashboard:latest
            
            print_success "Started all containers in pod"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

check_status() {
    print_header "Checking Pod Status"
    
    # Check pod status
    if podman pod exists "$POD_NAME" 2>/dev/null; then
        podman pod ps
        echo ""
        podman ps -a --pod
    else
        # Check compose status
        if command -v podman-compose &> /dev/null; then
            podman-compose ps
        else
            podman ps -a
        fi
    fi
    
    # Test endpoints
    echo ""
    print_header "Testing Endpoints"
    
    # Test Browser API
    if curl -s -f http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Browser API is running at http://localhost:3000"
    else
        print_warning "Browser API is not responding"
    fi
    
    # Test Dashboard
    if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Dashboard is running at http://localhost:8080"
    else
        print_warning "Dashboard is not responding"
    fi
    
    # Test Tor
    if nc -z localhost 9050 2>/dev/null; then
        print_success "Tor proxy is running on port 9050"
    else
        print_warning "Tor proxy is not responding"
    fi
    
    # Test Redis
    if nc -z localhost 6379 2>/dev/null; then
        print_success "Redis cache is running on port 6379"
    else
        print_warning "Redis cache is not responding"
    fi
}

stop_pod() {
    print_header "Stopping Browser Automation Pod"
    
    if podman pod exists "$POD_NAME" 2>/dev/null; then
        podman pod stop "$POD_NAME"
        print_success "Stopped pod $POD_NAME"
    else
        if command -v podman-compose &> /dev/null; then
            podman-compose down
        else
            docker-compose --podman-local down
        fi
        print_success "Stopped containers"
    fi
}

clean_up() {
    print_header "Cleaning Up"
    
    read -p "This will remove all containers and images. Are you sure? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        # Stop and remove pod
        if podman pod exists "$POD_NAME" 2>/dev/null; then
            podman pod rm -f "$POD_NAME"
        fi
        
        # Remove compose containers
        if command -v podman-compose &> /dev/null; then
            podman-compose down -v --rmi all
        fi
        
        # Remove images
        podman rmi -f darkweb-tor:latest 2>/dev/null || true
        podman rmi -f browser-automation:latest 2>/dev/null || true
        podman rmi -f data-processor:latest 2>/dev/null || true
        podman rmi -f screenshot-processor:latest 2>/dev/null || true
        podman rmi -f browser-dashboard:latest 2>/dev/null || true
        
        print_success "Cleaned up containers and images"
    else
        print_warning "Cleanup cancelled"
    fi
}

show_logs() {
    print_header "Container Logs"
    
    echo "Select container to view logs:"
    echo "1) Browser Automation"
    echo "2) Tor Proxy"
    echo "3) Data Processor"
    echo "4) Screenshot Processor"
    echo "5) Redis Cache"
    echo "6) Dashboard"
    echo "7) All containers"
    read -p "Choice [1-7]: " choice
    
    case $choice in
        1) podman logs -f browser-engine ;;
        2) podman logs -f browser-tor ;;
        3) podman logs -f browser-processor ;;
        4) podman logs -f browser-screenshots ;;
        5) podman logs -f browser-redis ;;
        6) podman logs -f browser-dashboard ;;
        7) 
            if command -v podman-compose &> /dev/null; then
                podman-compose logs -f
            else
                podman pod logs -f "$POD_NAME"
            fi
            ;;
        *) print_error "Invalid choice" ;;
    esac
}

# Main menu
main_menu() {
    clear
    print_header "Browser Automation Infrastructure Manager"
    echo ""
    echo "Select an option:"
    echo "1) Full Setup and Deploy"
    echo "2) Build Containers Only"
    echo "3) Start Pod"
    echo "4) Stop Pod"
    echo "5) Check Status"
    echo "6) View Logs"
    echo "7) Clean Up"
    echo "8) Exit"
    echo ""
    read -p "Choice [1-8]: " choice
    
    case $choice in
        1)
            check_dependencies
            setup_directories
            copy_files
            create_env_file
            build_containers
            start_pod
            check_status
            ;;
        2)
            build_containers
            ;;
        3)
            start_pod
            check_status
            ;;
        4)
            stop_pod
            ;;
        5)
            check_status
            ;;
        6)
            show_logs
            ;;
        7)
            clean_up
            ;;
        8)
            echo "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            sleep 2
            main_menu
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    main_menu
}

# Run main menu if no arguments
if [ $# -eq 0 ]; then
    main_menu
else
    # Handle command-line arguments
    case "$1" in
        setup)
            check_dependencies
            setup_directories
            copy_files
            create_env_file
            ;;
        build)
            build_containers
            ;;
        start)
            start_pod
            check_status
            ;;
        stop)
            stop_pod
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs
            ;;
        clean)
            clean_up
            ;;
        *)
            echo "Usage: $0 [setup|build|start|stop|status|logs|clean]"
            echo "Or run without arguments for interactive menu"
            exit 1
            ;;
    esac
fi