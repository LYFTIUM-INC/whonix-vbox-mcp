@echo off
REM Quick start script for Whonix VirtualBox MCP on Windows

echo Starting Whonix VirtualBox MCP...

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing dependencies...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if VirtualBox is accessible
echo Checking VirtualBox installation...
VBoxManage --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo WARNING: VBoxManage not found in PATH
    echo Please ensure VirtualBox is installed and added to your PATH
)

REM Start the MCP server
echo Starting MCP server...
python consolidated_mcp_whonix.py

pause
