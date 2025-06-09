#!/usr/bin/env python3

"""
Script to integrate file transfer tools into the main MCP server
"""

import re

# Read the original file
with open('consolidated_mcp_whonix.py', 'r') as f:
    content = f.read()

# Add import after other imports
import_line = "from file_transfer_service import FileTransferService"
import_pattern = r"(from safe_context import SafeContext\n)"
content = re.sub(import_pattern, r"\1" + import_line + "\n", content)

# Add initialization after vbox_service initialization
init_line = "\n# Initialize the file transfer service\nfile_transfer_service = FileTransferService(vbox_service)\n"
init_pattern = r"(vbox_service = VirtualBoxService\(CONFIG\[\"virtualbox\"\]\[\"vboxmanage_path\"\]\)\n)"
content = re.sub(init_pattern, r"\1" + init_line, content)

# Read the tool functions from add_file_transfer_tools.py
with open('add_file_transfer_tools.py', 'r') as f:
    tools_content = f.read()
    
# Extract the tools code
start_marker = "FILE_TRANSFER_TOOLS = '''"
end_marker = "'''"
start_idx = tools_content.find(start_marker) + len(start_marker)
end_idx = tools_content.rfind(end_marker)
tools_code = tools_content[start_idx:end_idx]

# Clean up the tools code
tools_code = tools_code.strip()
# Remove the import and init lines since we already added them
tools_code = re.sub(r'# Import the file transfer service\n.*?\n\n', '', tools_code)
tools_code = re.sub(r'# Initialize the file transfer service\n.*?\n\n', '', tools_code)

# Add the tools before the main function
main_pattern = r'(# Main function to run the server\n)'
content = re.sub(main_pattern, tools_code + "\n\n" + r"\1", content)

# Write the modified content
with open('consolidated_mcp_whonix_with_file_transfer.py', 'w') as f:
    f.write(content)

print("Successfully created consolidated_mcp_whonix_with_file_transfer.py")
print("The new file includes secure file transfer capabilities.")
