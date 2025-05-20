#!/bin/bash

# GitHub Repository Upload and Verification Script for Whonix VBox MCP
# Created: May 19, 2025
# Description: Uploads essential project files from /home/dell/coding/mcp/vbox-whonix to GitHub

# Color codes for output formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository information
REPO_OWNER="PreistlyPython"
REPO_NAME="whonix-vbox-mcp"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
BRANCH="main"
PROJECT_DIR="/home/dell/coding/mcp/vbox-whonix"

# Essential files to be uploaded - core functionality
ESSENTIAL_FILES=(
    "consolidated_mcp_whonix.py"
    "virtualbox_service.py"
    "safe_context.py"
    "config_loader.py"
    "configure_claude.py"
    "README.md"
    "requirements.txt"
    "LICENSE"
)

# Configuration and start scripts
CONFIG_FILES=(
    "start.sh"
    "start.bat"
    "start_mcp.sh"
    "run_consolidated.sh"
    "config.ini.example"
    "cleanup.sh"
)

# Documentation files (excluding SECURITY_ANALYSIS.md)
DOC_FILES=(
    "SETUP.md"
    "CONSOLIDATED_README.md"
    "GITHUB_MCP_FIX.md"
    "MCP_INSPECTOR_SETUP.md"
    "MCP_INSPECTOR_QUICK_SETUP.md"
)

# Flags
FORCE_PUSH=false

# Log function with timestamp
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check for required commands
check_requirements() {
    log "${BLUE}Checking requirements...${NC}"
    
    local requirements=("git" "curl")
    local missing=0
    
    for cmd in "${requirements[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log "${RED}Error: $cmd is not installed or not in PATH${NC}"
            missing=1
        fi
    done
    
    if [ "$missing" -eq 1 ]; then
        log "${RED}Missing required tools. Please install them and retry.${NC}"
        exit 1
    fi
    
    log "${GREEN}All required tools are available.${NC}"
}

# Function to check if files exist in local directory
check_files_exist() {
    log "${BLUE}Verifying files exist in local directory...${NC}"
    
    local all_files=("${ESSENTIAL_FILES[@]}" "${CONFIG_FILES[@]}" "${DOC_FILES[@]}")
    local missing=0
    
    for file in "${all_files[@]}"; do
        if [ ! -f "${PROJECT_DIR}/$file" ]; then
            log "${YELLOW}Warning: $file not found locally${NC}"
            missing=1
        else
            log "${GREEN}Found: $file${NC}"
        fi
    done
    
    if [ "$missing" -eq 1 ]; then
        log "${YELLOW}Some files are missing. Continue anyway? (y/n)${NC}"
        read -r response
        if [[ "$response" != "y" && "$response" != "Y" ]]; then
            log "${RED}Upload aborted by user.${NC}"
            exit 1
        fi
    else
        log "${GREEN}All expected files found locally.${NC}"
    fi
}

# Function to setup git repository
setup_git_repo() {
    log "${BLUE}Setting up Git repository...${NC}"
    
    # Navigate to project directory
    cd "${PROJECT_DIR}" || { log "${RED}Failed to navigate to project directory${NC}"; exit 1; }
    
    # Check if git is already initialized
    if [ -d ".git" ]; then
        log "${YELLOW}Git repository already initialized. Checking remote...${NC}"
        
        # Check if remote is correct
        CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "none")
        if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
            log "${YELLOW}Remote URL mismatch. Setting correct remote...${NC}"
            git remote remove origin
            git remote add origin "$REPO_URL"
        else
            log "${GREEN}Remote URL is correctly set.${NC}"
        fi
    else
        log "${BLUE}Initializing git repository...${NC}"
        git init
        git remote add origin "$REPO_URL"
    fi
    
    # Set git configuration if needed
    if [ -z "$(git config user.name)" ]; then
        log "${YELLOW}Git user.name not set. Please enter your name:${NC}"
        read -r username
        git config user.name "$username"
    fi
    
    if [ -z "$(git config user.email)" ]; then
        log "${YELLOW}Git user.email not set. Please enter your email:${NC}"
        read -r email
        git config user.email "$email"
    fi
    
    # Configure git to store credentials
    git config credential.https://github.com.helper store
    
    log "${GREEN}Git repository setup complete.${NC}"
}

# Function to handle the repository synchronization
sync_repository() {
    log "${BLUE}Synchronizing repository...${NC}"
    
    # Fetch the latest changes from remote
    git fetch origin
    
    # Check if there's a divergence between local and remote
    if git rev-parse HEAD &>/dev/null; then
        LOCAL_HASH=$(git rev-parse HEAD)
        REMOTE_HASH=$(git rev-parse origin/${BRANCH} 2>/dev/null || echo "none")
        
        if [ "$REMOTE_HASH" != "none" ] && [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
            log "${YELLOW}Local and remote repositories have diverged.${NC}"
            
            if [ "$FORCE_PUSH" = true ]; then
                log "${YELLOW}Force push is enabled. Will overwrite remote history.${NC}"
            else
                log "${YELLOW}Attempting to integrate changes...${NC}"
                
                # Try to pull with rebase
                git pull --rebase origin ${BRANCH} || {
                    log "${RED}Failed to integrate changes. Conflicts may exist.${NC}"
                    log "${YELLOW}Options:${NC}"
                    log "${BLUE}1. Use --force-push to overwrite remote changes${NC}"
                    log "${BLUE}2. Manually resolve conflicts${NC}"
                    log "${BLUE}3. Create a new branch instead${NC}"
                    
                    log "${YELLOW}What would you like to do? [1/2/3/q to quit]${NC}"
                    read -r choice
                    
                    case "$choice" in
                        1)
                            FORCE_PUSH=true
                            log "${YELLOW}Force push enabled.${NC}"
                            ;;
                        2)
                            log "${YELLOW}Please resolve conflicts manually, then continue.${NC}"
                            log "${YELLOW}After resolving conflicts, run 'git rebase --continue'${NC}"
                            log "${YELLOW}Then restart this script.${NC}"
                            exit 1
                            ;;
                        3)
                            NEW_BRANCH="${BRANCH}_$(date +%Y%m%d_%H%M%S)"
                            log "${YELLOW}Creating new branch: ${NEW_BRANCH}${NC}"
                            git checkout -b "$NEW_BRANCH"
                            BRANCH="$NEW_BRANCH"
                            ;;
                        q|Q)
                            log "${RED}Upload aborted by user.${NC}"
                            exit 1
                            ;;
                        *)
                            log "${RED}Invalid choice. Upload aborted.${NC}"
                            exit 1
                            ;;
                    esac
                }
            fi
        else
            log "${GREEN}Repository is up to date or being initialized.${NC}"
        fi
    else
        log "${YELLOW}This appears to be a new repository.${NC}"
    fi
}

# Function to stage files - direct file method
stage_files() {
    log "${BLUE}Staging files for commit...${NC}"
    
    # Navigate to project directory
    cd "${PROJECT_DIR}" || { log "${RED}Failed to navigate to project directory${NC}"; exit 1; }
    
    # Reset any previous staging
    git reset HEAD
    
    # First stage the essential files one by one with explicit paths
    for file in "${ESSENTIAL_FILES[@]}" "${CONFIG_FILES[@]}" "${DOC_FILES[@]}"; do
        if [ -f "$file" ]; then
            git add "$file"
            if [ $? -eq 0 ]; then
                log "${GREEN}Staged: $file${NC}"
            else
                log "${RED}Failed to stage: $file${NC}"
            fi
        fi
    done
    
    # Check how many files were staged
    STAGED_COUNT=$(git diff --cached --name-only | wc -l)
    
    log "${BLUE}Files staged for commit:${NC}"
    git diff --cached --name-only | while read -r line; do
        log "${GREEN}- $line${NC}"
    done
    
    log "${GREEN}Total files staged: $STAGED_COUNT${NC}"
    
    if [ "$STAGED_COUNT" -eq 0 ]; then
        log "${RED}Warning: No files were staged. Upload will fail.${NC}"
        log "${YELLOW}Do you want to try the 'git add .' approach? (y/n)${NC}"
        read -r response
        if [[ "$response" == "y" || "$response" == "Y" ]]; then
            git add .
            log "${YELLOW}Added all files in directory.${NC}"
            
            # Show what was staged after aggressive approach
            STAGED_COUNT=$(git diff --cached --name-only | wc -l)
            log "${BLUE}Files staged with 'git add .' approach:${NC}"
            git diff --cached --name-only | while read -r line; do
                log "${GREEN}- $line${NC}"
            done
            log "${GREEN}Total files staged: $STAGED_COUNT${NC}"
        fi
    fi
}

# Function to commit changes
commit_changes() {
    log "${BLUE}Committing changes...${NC}"
    
    # Check if there are staged changes
    if ! git diff --cached --quiet; then
        # Get commit message from user or use default
        log "${YELLOW}Enter commit message (or press Enter for default message):${NC}"
        read -r commit_msg
        
        if [ -z "$commit_msg" ]; then
            commit_msg="Upload essential project files for Whonix VBox MCP"
        fi
        
        git commit -m "$commit_msg" || {
            log "${RED}Commit failed. Git error occurred.${NC}"
            git status
            return 1
        }
        
        log "${GREEN}Changes committed successfully.${NC}"
        return 0
    else
        log "${RED}No changes staged for commit.${NC}"
        git status
        return 1
    fi
}

# Function to push changes
push_changes() {
    log "${BLUE}Pushing changes to remote repository...${NC}"
    
    # Check if we're on the main branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        log "${YELLOW}Not on ${BRANCH} branch. Switching...${NC}"
        git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
    fi
    
    # Set push command with force option if requested
    PUSH_CMD="git push -u origin $BRANCH"
    if [ "$FORCE_PUSH" = true ]; then
        PUSH_CMD="git push -u --force origin $BRANCH"
        log "${YELLOW}Using force push. This will overwrite remote history!${NC}"
    fi
    
    # Execute push command
    eval $PUSH_CMD || {
        log "${RED}Push failed. Please check your credentials and try again.${NC}"
        log "${YELLOW}GitHub authentication troubleshooting:${NC}"
        log "${BLUE}1. Generate a Personal Access Token (PAT) at: https://github.com/settings/tokens${NC}"
        log "${BLUE}2. Configure Git to store credentials for GitHub:${NC}"
        log "   ${YELLOW}git config credential.https://github.com.helper store${NC}"
        log "${BLUE}3. Push again and when prompted, use your GitHub username and the PAT as password${NC}"
        log "${BLUE}4. Or try again with --force-push option:${NC}"
        log "   ${YELLOW}./upload_github.sh --run --force-push${NC}"
        return 1
    }
    
    log "${GREEN}Changes pushed successfully to ${REPO_URL}${NC}"
    return 0
}

# Function to verify upload
verify_upload() {
    log "${BLUE}Verifying uploaded files...${NC}"
    
    # Wait a moment for GitHub to process the push
    sleep 3
    
    local all_files=("${ESSENTIAL_FILES[@]}" "${CONFIG_FILES[@]}" "${DOC_FILES[@]}")
    local success=0
    local total=0
    
    # Count only files that actually exist locally
    for file in "${all_files[@]}"; do
        if [ -f "${PROJECT_DIR}/$file" ]; then
            total=$((total + 1))
        fi
    done
    
    if [ "$total" -eq 0 ]; then
        log "${RED}No files to verify. Something went wrong with staging.${NC}"
        return 1
    fi
    
    # Use GitHub API to check for files
    log "${BLUE}Checking files on GitHub repository...${NC}"
    for file in "${all_files[@]}"; do
        if [ -f "${PROJECT_DIR}/$file" ]; then
            # Use curl to check if file exists
            local check=$(curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.github.v3+json" \
                           "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${file}")
            
            if [ "$check" -eq 200 ]; then
                log "${GREEN}Verified: $file exists on GitHub${NC}"
                success=$((success + 1))
            else
                log "${RED}Failed: $file was not found on GitHub (HTTP $check)${NC}"
            fi
        fi
    done
    
    # Calculate percentage of success
    local percentage=$((success * 100 / total))
    
    log "${BLUE}Verification summary:${NC}"
    log "${GREEN}Successfully uploaded: $success/$total files ($percentage%)${NC}"
    
    if [ "$success" -eq "$total" ]; then
        log "${GREEN}All files were successfully uploaded and verified!${NC}"
        return 0
    else
        log "${YELLOW}Some files could not be verified. Manual check recommended.${NC}"
        return 1
    fi
}

# Function to parse command-line arguments
parse_args() {
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --run) RUN=true ;;
            --force-push) FORCE_PUSH=true ;;
            *) log "${RED}Unknown parameter: $1${NC}" ;;
        esac
        shift
    done
}

# Function to run the entire workflow
run_workflow() {
    log "${BLUE}Starting GitHub upload workflow...${NC}"
    
    # Run each step and stop on failure
    check_requirements || exit 1
    check_files_exist || exit 1
    setup_git_repo || exit 1
    sync_repository || exit 1
    stage_files || exit 1
    commit_changes || exit 1
    push_changes || exit 1
    verify_upload
    
    log "${GREEN}Upload workflow completed successfully!${NC}"
    log "${GREEN}Repository URL: ${REPO_URL}${NC}"
}

# Print usage instructions
log "${GREEN}========================${NC}"
log "${GREEN}WHONIX VBOX MCP UPLOAD SCRIPT${NC}"
log "${GREEN}========================${NC}"
log "${YELLOW}This script will upload essential project files to GitHub:${NC}"

# Count files in each category
CORE_COUNT=${#ESSENTIAL_FILES[@]}
CONFIG_COUNT=${#CONFIG_FILES[@]}
DOC_COUNT=${#DOC_FILES[@]}
TOTAL_COUNT=$((CORE_COUNT + CONFIG_COUNT + DOC_COUNT))

# Display file categories
log "${BLUE}Core Files (${CORE_COUNT}):${NC}"
for file in "${ESSENTIAL_FILES[@]}"; do
    log "  - $file"
done

log "${BLUE}Configuration Files (${CONFIG_COUNT}):${NC}"
for file in "${CONFIG_FILES[@]}"; do
    log "  - $file"
done

log "${BLUE}Documentation Files (${DOC_COUNT}):${NC}"
for file in "${DOC_FILES[@]}"; do
    log "  - $file"
done

log "${GREEN}Total files to upload: ${TOTAL_COUNT}${NC}"

log "${GREEN}========================${NC}"
log "${YELLOW}Usage Options:${NC}"
log "${BLUE}--run            Execute the upload workflow${NC}"
log "${BLUE}--force-push     Force push to repository (overwrites remote history)${NC}"
log "${GREEN}========================${NC}"
log "${YELLOW}Authentication Guidance:${NC}"
log "${BLUE}1. For GitHub authentication, use:${NC}"
log "   ${YELLOW}git config credential.https://github.com.helper store${NC}"
log "${BLUE}2. Create a Personal Access Token at:${NC}"
log "   ${YELLOW}https://github.com/settings/tokens${NC}"
log "${GREEN}========================${NC}"
log "${YELLOW}Instructions:${NC}"
log "${BLUE}1. Ensure you have git and curl installed${NC}"
log "${BLUE}2. Run this script with the --run flag to execute:${NC}"
log "   ${YELLOW}./upload_github.sh --run${NC}"
log "${BLUE}3. If push fails due to conflicts, use force push:${NC}"
log "   ${YELLOW}./upload_github.sh --run --force-push${NC}"
log "${GREEN}========================${NC}"

# Parse command-line arguments
parse_args "$@"

# Check if --run flag is provided
if [[ "$RUN" == true ]]; then
    run_workflow
fi
