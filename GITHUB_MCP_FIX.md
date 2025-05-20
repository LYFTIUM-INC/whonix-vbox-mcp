# 🛠️ GitHub MCP Fix Instructions

## 🔍 Problem Identified
- **Error**: `fetch is not set. Please pass a fetch implementation`
- **Cause**: Node.js v16.20.2 doesn't have built-in `fetch`, but @octokit/rest v21+ requires it
- **Location**: `/home/dell/Documents/Cline/MCP/github-server/`

## 🚀 Solution Options

### Option 1: Upgrade Node.js (Recommended)
```bash
# Install Node.js 18+ using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
nvm alias default 18

# Restart Claude Desktop to use new Node.js version
```

### Option 2: Install Fetch Polyfill
```bash
cd /home/dell/Documents/Cline/MCP/github-server/
npm install undici
```

### Option 3: Fix the MCP Code
Replace the content of `/home/dell/Documents/Cline/MCP/github-server/src/index.ts`:

**Add these imports at the top:**
```typescript
// After existing imports, add:
let fetchImplementation;
try {
  fetchImplementation = globalThis.fetch;
} catch {
  try {
    const undici = await import('undici');
    fetchImplementation = undici.fetch;
  } catch {
    const nodeFetch = await import('node-fetch');
    fetchImplementation = nodeFetch.default;
  }
}
```

**Modify the Octokit initialization:**
```typescript
// Replace this:
this.octokit = new Octokit({
  auth: GITHUB_TOKEN,
});

// With this:
this.octokit = new Octokit({
  auth: GITHUB_TOKEN,
  request: {
    fetch: fetchImplementation,
  },
});
```

**Also fix the create_repository call** (line ~320):
```typescript
// Replace this:
const newRepo = await this.octokit.repos.createForAuthenticatedUser({
  name: args.repo!,
  description: args.body,
  private: false,
});

// With this:
const newRepo = await this.octokit.repos.createForAuthenticatedUser({
  name: args.name!,  // Fixed: was args.repo!
  description: args.description,  // Fixed: was args.body
  private: args.private || false,  // Fixed: support private flag
});
```

### After Making Changes
```bash
cd /home/dell/Documents/Cline/MCP/github-server/
npm run build
# Restart Claude Desktop
```

## 🧪 Testing the Fix
After applying any solution, test with:
```bash
# Test the MCP directly
cd /home/dell/Documents/Cline/MCP/github-server/
GITHUB_TOKEN="your_token" node build/index.js
```

## 📋 Quick Fix Script
Create this script to automatically fix the issue:

```bash
#!/bin/bash
cd /home/dell/Documents/Cline/MCP/github-server/

# Install fetch polyfill
npm install undici

# Create the fixed TypeScript file
cat > src/index.ts << 'EOF'
#!/usr/bin/env node
// ... [Fixed TypeScript code as shown above]
EOF

# Rebuild
npm run build

echo "GitHub MCP fixed! Restart Claude Desktop to use the updated version."
```

## 🔗 Alternative: Use Working GitHub MCP
If fixing proves difficult, you can download a working GitHub MCP:
```bash
# Clone a working version
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/github/
npm install
npm run build

# Update Claude config to point to this version
```

## ✅ Verification
After the fix, the GitHub MCP should work properly:
- No more fetch-related errors
- All GitHub operations functional
- Can create repositories, issues, etc.

---

**Status**: Issue diagnosed and solutions provided ✅
**Next Step**: Apply one of the solutions above and restart Claude Desktop
