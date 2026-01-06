#!/bin/bash
# One-Command GitLeaks Control Panel Setup
# Usage: curl -sSL https://your-domain.com/setup.sh | bash

set -e

echo "🔒 GitLeaks Control Panel - One-Command Setup"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directory
INSTALL_DIR="$HOME/gitleaks-panel"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "📁 Installing to: $INSTALL_DIR"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3 first."
    exit 1
fi

echo "✓ Python 3 found"

# Install Python dependencies
echo "📦 Installing dependencies..."
pip3 install flask flask-cors requests --quiet || pip install flask flask-cors requests --quiet

# Download files (in production, these would be actual URLs)
echo "⬇️  Downloading control panel files..."

# In production, replace these with actual download URLs
# For now, we'll create the files inline

# Create API server
cat > api-server.py << 'EOFAPI'
#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import zipfile
import io

app = Flask(__name__)
CORS(app)

GITHUB_WORKFLOW = """name: Security
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
"""

PRECOMMIT_CONFIG = """repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.20.1
    hooks:
      - id: gitleaks
"""

GITLEAKS_CONFIG = """[extend]
useDefault = true
[allowlist]
paths = ['''\.env\.example$''', '''tests/.*''']
"""

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/download-config')
def download_config():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('.github/workflows/security.yml', GITHUB_WORKFLOW)
        zip_file.writestr('.pre-commit-config.yaml', PRECOMMIT_CONFIG)
        zip_file.writestr('.gitleaks.toml', GITLEAKS_CONFIG)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='gitleaks-config.zip')

@app.route('/api/deploy-single', methods=['POST'])
def deploy_single():
    data = request.json
    project_path = os.path.expanduser(data.get('path', ''))
    
    try:
        workflows_dir = os.path.join(project_path, '.github', 'workflows')
        os.makedirs(workflows_dir, exist_ok=True)
        
        with open(os.path.join(workflows_dir, 'security.yml'), 'w') as f:
            f.write(GITHUB_WORKFLOW)
        with open(os.path.join(project_path, '.pre-commit-config.yaml'), 'w') as f:
            f.write(PRECOMMIT_CONFIG)
        with open(os.path.join(project_path, '.gitleaks.toml'), 'w') as f:
            f.write(GITLEAKS_CONFIG)
        
        return jsonify({'success': True, 'message': 'Deployed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚀 API Server running at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)
EOFAPI

chmod +x api-server.py

# Create HTML interface (simplified version)
cat > index.html << 'EOFHTML'
<!DOCTYPE html>
<html>
<head>
    <title>GitLeaks Control Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { text-align: center; color: #667eea; margin-bottom: 30px; }
        .option { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 4px solid #667eea; }
        .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin: 10px 5px; }
        .btn:hover { background: #5568d3; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 2px solid #e0e0e0; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 GitLeaks Control Panel</h1>
        
        <div class="option">
            <h3>Option 1: Download Configuration Files</h3>
            <p>Get a zip file with all GitLeaks configuration files</p>
            <button class="btn" onclick="window.location.href='http://localhost:5000/api/download-config'">Download Files</button>
        </div>
        
        <div class="option">
            <h3>Option 2: Deploy to Single Project</h3>
            <p>Enter your project path:</p>
            <input type="text" id="project-path" placeholder="~/projects/my-project">
            <button class="btn" onclick="deploySingle()">Deploy Now</button>
            <div id="result"></div>
        </div>
        
        <div class="option">
            <h3>Option 3: Deploy to Multiple Projects</h3>
            <p>Enter project paths (one per line):</p>
            <textarea id="bulk-paths" rows="5" placeholder="~/projects/project1
~/projects/project2"></textarea>
            <button class="btn" onclick="deployBulk()">Deploy to All</button>
        </div>
    </div>
    
    <script>
        function deploySingle() {
            const path = document.getElementById('project-path').value;
            fetch('http://localhost:5000/api/deploy-single', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: path})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('result').innerHTML = 
                    data.success ? '✅ Deployed successfully!' : '❌ Error: ' + data.message;
            });
        }
        
        function deployBulk() {
            const paths = document.getElementById('bulk-paths').value.split('\n');
            alert('Deploying to ' + paths.length + ' projects...');
            // Implement bulk deployment
        }
    </script>
</body>
</html>
EOFHTML

echo ""
echo "✅ Installation complete!"
echo ""
echo -e "${GREEN}🚀 Quick Start:${NC}"
echo ""
echo "1. Start the API server:"
echo -e "   ${BLUE}python3 api-server.py${NC}"
echo ""
echo "2. Open the control panel:"
echo -e "   ${BLUE}open index.html${NC}"
echo "   Or go to: http://localhost:5000"
echo ""
echo "📖 Full documentation:"
echo "   https://github.com/your-org/gitleaks-panel"
echo ""
echo -e "${GREEN}That's it! Your GitLeaks Control Panel is ready!${NC}"
