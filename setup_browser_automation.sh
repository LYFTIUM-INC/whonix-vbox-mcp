#!/bin/bash

# Browser Automation VM Setup Script
# This script sets up Claude Code and Playwright MCP in a Whonix VM

set -e

echo "🚀 Setting up Browser Automation Environment in Whonix VM..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update

# Install prerequisites
echo "🔧 Installing prerequisites..."
sudo apt-get install -y curl wget gnupg2 software-properties-common git

# Install Node.js 18.x
echo "📦 Installing Node.js 18.x..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node.js installation
echo "✅ Node.js version: $(node --version)"
echo "✅ NPM version: $(npm --version)"

# Install Claude Code
echo "🤖 Installing Claude Code..."
curl -fsSL https://claude.ai/install.sh | sh

# Add Claude Code to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Install Playwright MCP server
echo "🎭 Installing Playwright MCP server..."
npm install -g @playwright/mcp

# Install Playwright browsers (Chromium for headless)
echo "🌐 Installing Playwright browsers..."
npx playwright install chromium
npx playwright install-deps chromium

# Create MCP configuration directory
echo "⚙️ Creating MCP configuration..."
mkdir -p ~/.config/claude

# Create .mcp.json configuration
cat > ~/.config/claude/mcp.json << 'EOF'
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"],
      "env": {
        "PLAYWRIGHT_HEADLESS": "true",
        "PLAYWRIGHT_BROWSER": "chromium"
      },
      "metadata": {
        "name": "Playwright Browser Automation",
        "version": "1.0.0",
        "description": "Headless browser automation through Tor via Whonix"
      }
    }
  }
}
EOF

# Create launch script for Claude Code
cat > ~/launch_claude_browser.sh << 'EOF'
#!/bin/bash

# Launch Claude Code with MCP configuration for browser automation
export PATH="$HOME/.local/bin:$PATH"

echo "🚀 Launching Claude Code with Browser Automation MCP..."
echo "📍 MCP Config: ~/.config/claude/mcp.json"
echo "🔒 Tor Network: Active through Whonix"

# Check if Tor is working
echo "🔍 Checking Tor connectivity..."
if curl -s --socks5 127.0.0.1:9050 https://check.torproject.org/ | grep -q "Congratulations"; then
    echo "✅ Tor connection verified"
else
    echo "⚠️ Tor connection may not be working properly"
fi

# Launch Claude Code with MCP configuration
claude-code --mcp-config ~/.config/claude/mcp.json
EOF

# Make launch script executable
chmod +x ~/launch_claude_browser.sh

# Create alias in bashrc
echo "🔗 Creating alias 'browser-claude'..."
echo "alias browser-claude='~/launch_claude_browser.sh'" >> ~/.bashrc

# Test installations
echo "🧪 Testing installations..."
echo "Node.js: $(node --version)"
echo "NPM: $(npm --version)"
echo "Playwright: $(npx playwright --version)"

# Final setup message
echo ""
echo "🎉 Browser Automation Setup Complete!"
echo ""
echo "📋 What was installed:"
echo "  ✅ Node.js 18.x and NPM"
echo "  ✅ Claude Code CLI" 
echo "  ✅ Playwright MCP server"
echo "  ✅ Chromium browser (headless)"
echo "  ✅ MCP configuration file"
echo "  ✅ Launch script and alias"
echo ""
echo "🚀 To start browser automation:"
echo "  1. Run: source ~/.bashrc"
echo "  2. Run: browser-claude"
echo "  3. Or run: ~/launch_claude_browser.sh"
echo ""
echo "🔒 All browser traffic will be routed through Tor via Whonix!"
echo ""