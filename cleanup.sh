#!/bin/bash
# Cleanup script for VirtualBox MCP deployment

echo "Cleaning up unnecessary files..."

# Create backup directory if it doesn't exist
mkdir -p ./backups

# Move old/redundant files to backup directory
mv enhanced_server.py.backup ./backups/
mv tor_utilities.py.backup ./backups/
mv enhanced_server_fixed.py ./backups/
mv enhanced_server_logging_fixed.py ./backups/
mv vbox_whonix_server.py ./backups/
mv test_server.py ./backups/
mv setup.sh ./backups/
mv setup_and_run.sh ./backups/

# Delete compiled Python files
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +

echo "Cleanup complete!"
