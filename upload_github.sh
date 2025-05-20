#!/bin/bash

# GitHub Repository Upload and Verification Script for Whonix VBox MCP
# Created: May 19, 2025
# Description: Uploads remaining files from /home/dell/coding/mcp/vbox-whonix to GitHub

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

# Files to be uploaded (these should already exist in your project directory)
CORE_FILES=(
    "consolidated_mcp_whonix.py"
    "virtualbox_service.py"
    "safe_context.py"
    "config_loader.py"
)

SETUP_FILES=(
    "start.sh"
    "start.bat"
    "config.ini.example"
    ".gitignore"
)

DOCS_FILES=(
    "SETUP.md"
    "SECURITY_ANALYSIS.md"
    "DEPLOYMENT_SUMMARY.md"
)

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
    
    local all_files=("${CORE_FILES[@]}" "${SETUP_FILES[@]}" "${DOCS_FILES[@]}")
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
    git config credential.helper store
    
    log "${GREEN}Git repository setup complete.${NC}"
}

# Function to perform git pull to get latest changes
pull_latest_changes() {
    log "${BLUE}Pulling latest changes from remote repository...${NC}"
    
    # Fetch and check if branch exists
    git fetch origin
    if git show-ref --verify --quiet "refs/remotes/origin/${BRANCH}"; then
        # Branch exists, pull changes
        git pull origin "${BRANCH}" || { 
            log "${RED}Failed to pull latest changes. Resolving conflicts may be required.${NC}"
            log "${YELLOW}Please resolve any conflicts manually, then continue.${NC}"
            read -p "Press Enter once conflicts are resolved or to continue anyway..."
        }
    else
        log "${YELLOW}Branch ${BRANCH} doesn't exist on remote yet. Will create on push.${NC}"
    fi
    
    log "${GREEN}Pull operation completed.${NC}"
}

# Function to stage files - FIXED version
stage_files() {
    log "${BLUE}Staging files for commit...${NC}"
    
    # Use git add with specific files directly (replaced loop)
    cd "${PROJECT_DIR}" || { log "${RED}Failed to navigate to project directory${NC}"; exit 1; }
    
    # Stage all files at once
    git add "${CORE_FILES[@]}" "${SETUP_FILES[@]}" "${DOCS_FILES[@]}" 2>/dev/null
    
    # Check if any files were staged
    STAGED_COUNT=$(git diff --cached --name-only | wc -l)
    
    if [ "$STAGED_COUNT" -eq 0 ]; then
        log "${YELLOW}No files staged. Trying alternative approach...${NC}"
        # Alternative approach: stage files individually with full path
        for file in "${CORE_FILES[@]}" "${SETUP_FILES[@]}" "${DOCS_FILES[@]}"; do
            if [ -f "$file" ]; then
                git add "$file"
                log "${GREEN}Tried to stage: $file${NC}"
            fi
        done
        
        # Check again
        STAGED_COUNT=$(git diff --cached --name-only | wc -l)
    fi
    
    # Show what was staged
    log "${BLUE}Files staged for commit:${NC}"
    git diff --cached --name-only | while read -r line; do
        log "${GREEN}Staged: $line${NC}"
    done
    
    log "${GREEN}Staged $STAGED_COUNT files for commit.${NC}"
    
    if [ "$STAGED_COUNT" -eq 0 ]; then
        log "${RED}Warning: No files were staged. Trying more aggressive approach...${NC}"
        # Most aggressive approach: add everything
        git add .
        log "${YELLOW}Added all files in directory.${NC}"
        
        # Show what was staged after aggressive approach
        log "${BLUE}Files staged for commit (aggressive approach):${NC}"
        git diff --cached --name-only | while read -r line; do
            log "${GREEN}Staged: $line${NC}"
        done
        
        STAGED_COUNT=$(git diff --cached --name-only | wc -l)
        log "${GREEN}Staged $STAGED_COUNT files for commit.${NC}"
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
            commit_msg="Upload remaining project files for Whonix VBox MCP"
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
    
    # Set upstream and push
    git push -u origin "$BRANCH" || {
        log "${RED}Push failed. Please check your credentials and try again.${NC}"
        log "${YELLOW}You may need to create a personal access token on GitHub.${NC}"
        log "${YELLOW}Store your GitHub token using this command:${NC}"
        log "${BLUE}git config --global credential.helper store${NC}"
        log "${BLUE}git push -u origin ${BRANCH}${NC}"
        log "${YELLOW}(Enter your username and token when prompted)${NC}"
        log "${YELLOW}See: https://github.com/settings/tokens${NC}"
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
    
    local all_files=("${CORE_FILES[@]}" "${SETUP_FILES[@]}" "${DOCS_FILES[@]}")
    local success=0
    local total=${#all_files[@]}
    
    # Use GitHub API to check for files
    log "${BLUE}Checking files on GitHub repository...${NC}"
    for file in "${all_files[@]}"; do
        # Use curl to check if file exists
        local check=$(curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.github.v3+json" \
                       "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${file}")
        
        if [ "$check" -eq 200 ]; then
            log "${GREEN}Verified: $file exists on GitHub${NC}"
            success=$((success + 1))
        else
            log "${RED}Failed: $file was not found on GitHub${NC}"
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

# Function to run the entire workflow
run_workflow() {
    log "${BLUE}Starting GitHub upload workflow...${NC}"
    
    # Run each step and stop on failure
    check_requirements || exit 1
    check_files_exist || exit 1
    setup_git_repo || exit 1
    pull_latest_changes
    stage_files || exit 1
    commit_changes || exit 1
    push_changes || exit 1
    verify_upload
    
    log "${GREEN}Upload workflow completed successfully!${NC}"
    log "${GREEN}Repository URL: ${REPO_URL}${NC}"
}

# Print usage instructions
log "${GREEN}========================${NC}"
log "${GREEN}UPLOAD SCRIPT READY${NC}"
log "${GREEN}========================${NC}"
log "${YELLOW}This script will upload the following files to GitHub:${NC}"

# List core files
log "${BLUE}Core Files:${NC}"
for file in "${CORE_FILES[@]}"; do
    log "  - $file"
done

# List setup files
log "${BLUE}Setup Files:${NC}"
for file in "${SETUP_FILES[@]}"; do
    log "  - $file"
done

# List documentation files
log "${BLUE}Documentation Files:${NC}"
for file in "${DOCS_FILES[@]}"; do
    log "  - $file"
done

log "${GREEN}========================${NC}"
log "${YELLOW}Authentication Troubleshooting:${NC}"
log "${BLUE}1. If authentication fails, create a Personal Access Token (PAT) on GitHub${NC}"
log "${BLUE}   Visit: https://github.com/settings/tokens${NC}"
log "${BLUE}2. Use these tokens for HTTPS authentication${NC}"
log "${BLUE}3. Store your credentials with: git config --global credential.helper store${NC}"
log "${GREEN}========================${NC}"
log "${YELLOW}Instructions:${NC}"
log "${BLUE}1. Ensure you have git access to GitHub repository${NC}"
log "${BLUE}2. Run this script with the --run flag to execute the upload workflow${NC}"
log "${BLUE}   ./upload_github.sh --run${NC}"
log "${GREEN}========================${NC}"

# Check if --run flag is provided
if [[ "$1" == "--run" ]]; then
    run_workflow
fi
