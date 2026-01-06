#!/usr/bin/env python3
"""
GitLeaks Control Panel - Backend API
Flask server that handles all GitLeaks deployment operations
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
import requests
import base64
import zipfile
import io
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration templates
GITHUB_WORKFLOW = """name: Security Scan

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

permissions:
  contents: read
  security-events: write

jobs:
  gitleaks:
    name: Scan for Secrets
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run GitLeaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_ENABLE_SUMMARY: true
"""

PRECOMMIT_CONFIG = """repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.20.1
    hooks:
      - id: gitleaks
"""

GITLEAKS_CONFIG = """# GitLeaks Configuration
# This config uses default rules and minimal allowlist
# to catch secrets effectively

title = "GitLeaks Security Scan"

[extend]
useDefault = true

[allowlist]
description = "Allowlist for known false positives only"

# Only ignore example/template files
paths = [
  '''\.env\.example$''',
  '''\.env\.template$''',
  '''\.env\.sample$''',
]

# Ignore common false positive patterns
regexes = [
  '''example\.com''',
  '''placeholder''',
  '''your-.*-here''',
  '''xxx+''',
]

# No commits ignored - scan everything
commits = []
"""

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'GitLeaks Control Panel API is running'})

@app.route('/api/download-config', methods=['GET'])
def download_config():
    """Download configuration files as a zip"""
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add files to zip
        zip_file.writestr('.github/workflows/security.yml', GITHUB_WORKFLOW)
        zip_file.writestr('.pre-commit-config.yaml', PRECOMMIT_CONFIG)
        zip_file.writestr('.gitleaks.toml', GITLEAKS_CONFIG)
        
        # Add README
        readme = """# GitLeaks Configuration Files

## Installation Instructions:

1. Extract these files to your project root
2. Commit and push:
   ```bash
   git add .github .pre-commit-config.yaml .gitleaks.toml
   git commit -m "Add GitLeaks security scanning"
   git push
   ```

3. That's it! GitLeaks is now active.
"""
        zip_file.writestr('README.md', readme)
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='gitleaks-config.zip'
    )

@app.route('/api/scan-projects', methods=['POST'])
def scan_projects():
    """Scan local projects to check if they're git repositories"""
    data = request.json
    paths = data.get('paths', [])
    
    results = []
    for path in paths:
        expanded_path = os.path.expanduser(path.strip())
        
        if not os.path.exists(expanded_path):
            results.append({
                'path': path,
                'exists': False,
                'is_git': False,
                'status': 'error',
                'message': 'Path does not exist'
            })
            continue
        
        is_git = os.path.exists(os.path.join(expanded_path, '.git'))
        has_gitleaks = os.path.exists(os.path.join(expanded_path, '.github/workflows'))
        
        results.append({
            'path': path,
            'exists': True,
            'is_git': is_git,
            'has_gitleaks': has_gitleaks,
            'status': 'ready' if is_git else 'error',
            'message': 'Ready for deployment' if is_git else 'Not a git repository'
        })
    
    return jsonify({'results': results})

@app.route('/api/deploy-single', methods=['POST'])
def deploy_single():
    """Deploy GitLeaks to a single project"""
    data = request.json
    project_path = os.path.expanduser(data.get('path', ''))
    
    if not os.path.exists(project_path):
        return jsonify({'success': False, 'message': 'Project path does not exist'}), 400
    
    try:
        # Create .github/workflows directory
        workflows_dir = os.path.join(project_path, '.github', 'workflows')
        os.makedirs(workflows_dir, exist_ok=True)
        
        # Write configuration files
        with open(os.path.join(workflows_dir, 'security.yml'), 'w') as f:
            f.write(GITHUB_WORKFLOW)
        
        with open(os.path.join(project_path, '.pre-commit-config.yaml'), 'w') as f:
            f.write(PRECOMMIT_CONFIG)
        
        with open(os.path.join(project_path, '.gitleaks.toml'), 'w') as f:
            f.write(GITLEAKS_CONFIG)
        
        return jsonify({
            'success': True,
            'message': 'GitLeaks configuration deployed successfully',
            'files_created': [
                '.github/workflows/security.yml',
                '.pre-commit-config.yaml',
                '.gitleaks.toml'
            ]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/deploy-bulk', methods=['POST'])
def deploy_bulk():
    """Deploy GitLeaks to multiple projects"""
    data = request.json
    paths = data.get('paths', [])
    
    results = []
    
    for path in paths:
        expanded_path = os.path.expanduser(path.strip())
        
        try:
            # Deploy to project
            workflows_dir = os.path.join(expanded_path, '.github', 'workflows')
            os.makedirs(workflows_dir, exist_ok=True)
            
            with open(os.path.join(workflows_dir, 'security.yml'), 'w') as f:
                f.write(GITHUB_WORKFLOW)
            
            with open(os.path.join(expanded_path, '.pre-commit-config.yaml'), 'w') as f:
                f.write(PRECOMMIT_CONFIG)
            
            with open(os.path.join(expanded_path, '.gitleaks.toml'), 'w') as f:
                f.write(GITLEAKS_CONFIG)
            
            results.append({
                'path': path,
                'success': True,
                'message': 'Deployed successfully'
            })
        
        except Exception as e:
            results.append({
                'path': path,
                'success': False,
                'message': str(e)
            })
    
    return jsonify({'results': results})

@app.route('/api/github-org/repos', methods=['POST'])
def get_org_repos():
    """Fetch all repositories from a GitHub organization OR user account"""
    data = request.json
    token = data.get('token')
    org = data.get('organization')
    
    if not token or not org:
        return jsonify({'success': False, 'message': 'Token and organization required'}), 400
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        repos = []
        page = 1
        
        # First, try as an organization
        while True:
            url = f'https://api.github.com/orgs/{org}/repos?page={page}&per_page=100'
            response = requests.get(url, headers=headers)
            
            # If 404, try as a user account instead
            if response.status_code == 404 and page == 1:
                print(f"Not an org, trying as user: {org}")
                # Try user repos endpoint
                page = 1
                while True:
                    url = f'https://api.github.com/users/{org}/repos?page={page}&per_page=100'
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code != 200:
                        return jsonify({
                            'success': False,
                            'message': f'GitHub API error: {response.status_code}. Check if username/org is correct and token is valid.'
                        }), 400
                    
                    data_list = response.json()
                    if not data_list:
                        break
                    
                    for repo in data_list:
                        repos.append({
                            'name': repo['name'],
                            'full_name': repo['full_name'],
                            'default_branch': repo.get('default_branch', 'main'),
                            'private': repo['private'],
                            'updated_at': repo['updated_at']
                        })
                    
                    page += 1
                    if len(data_list) < 100:  # Last page
                        break
                
                return jsonify({
                    'success': True,
                    'repos': repos,
                    'count': len(repos),
                    'type': 'user'
                })
            
            if response.status_code != 200:
                return jsonify({
                    'success': False,
                    'message': f'GitHub API error: {response.status_code}. Check if org name is correct and token has proper permissions.'
                }), 400
            
            data_list = response.json()
            if not data_list:
                break
            
            for repo in data_list:
                repos.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'default_branch': repo.get('default_branch', 'main'),
                    'private': repo['private'],
                    'updated_at': repo['updated_at']
                })
            
            page += 1
            if len(data_list) < 100:  # Last page
                break
        
        return jsonify({
            'success': True,
            'repos': repos,
            'count': len(repos),
            'type': 'organization'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/github-org/deploy', methods=['POST'])
def deploy_to_org():
    """Deploy GitLeaks to GitHub organization repositories"""
    data = request.json
    token = data.get('token')
    repos = data.get('repos', [])
    dry_run = data.get('dry_run', True)
    
    if not token:
        return jsonify({'success': False, 'message': 'GitHub token required'}), 400
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    results = []
    
    for repo_name in repos:
        try:
            if dry_run:
                results.append({
                    'repo': repo_name,
                    'success': True,
                    'message': 'Would deploy (dry run)',
                    'dry_run': True
                })
                continue
            
            # Check if workflow already exists
            url = f'https://api.github.com/repos/{repo_name}/contents/.github/workflows'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                files = response.json()
                workflow_exists = any(
                    'gitleaks' in f['name'].lower() or 'security' in f['name'].lower()
                    for f in files
                )
                
                if workflow_exists:
                    results.append({
                        'repo': repo_name,
                        'success': True,
                        'message': 'Workflow already exists',
                        'skipped': True
                    })
                    continue
            
            # Create workflow file
            content_base64 = base64.b64encode(GITHUB_WORKFLOW.encode()).decode()
            
            url = f'https://api.github.com/repos/{repo_name}/contents/.github/workflows/security.yml'
            payload = {
                'message': 'Add GitLeaks security scanning',
                'content': content_base64
            }
            
            response = requests.put(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                results.append({
                    'repo': repo_name,
                    'success': True,
                    'message': 'Deployed successfully'
                })
            else:
                results.append({
                    'repo': repo_name,
                    'success': False,
                    'message': f'Failed: {response.status_code}'
                })
        
        except Exception as e:
            results.append({
                'repo': repo_name,
                'success': False,
                'message': str(e)
            })
    
    return jsonify({'results': results})

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    """Generate a standalone deployment script"""
    data = request.json
    script_type = data.get('type', 'bash')  # bash or python
    
    if script_type == 'bash':
        script = '''#!/bin/bash
# GitLeaks Auto-Deployment Script
set -e

echo "🔒 GitLeaks Deployment Script"
echo "=============================="

# Configuration files
read -r -d '' WORKFLOW <<'EOF'
''' + GITHUB_WORKFLOW + '''
EOF

read -r -d '' PRECOMMIT <<'EOF'
''' + PRECOMMIT_CONFIG + '''
EOF

read -r -d '' GITLEAKS <<'EOF'
''' + GITLEAKS_CONFIG + '''
EOF

# Deploy function
deploy_to_project() {
    local project_path=$1
    echo "Deploying to: $project_path"
    
    cd "$project_path"
    
    mkdir -p .github/workflows
    echo "$WORKFLOW" > .github/workflows/security.yml
    echo "$PRECOMMIT" > .pre-commit-config.yaml
    echo "$GITLEAKS" > .gitleaks.toml
    
    echo "✅ Deployed"
}

# Main
if [ $# -eq 0 ]; then
    echo "Usage: $0 <project-path>"
    exit 1
fi

deploy_to_project "$1"
'''
        return send_file(
            io.BytesIO(script.encode()),
            mimetype='text/x-shellscript',
            as_attachment=True,
            download_name='deploy-gitleaks.sh'
        )
    
    return jsonify({'success': False, 'message': 'Invalid script type'}), 400

if __name__ == '__main__':
    print("🚀 Starting GitLeaks Control Panel API...")
    print("📍 API available at: http://localhost:5000")
    print("📖 Documentation: http://localhost:5000/api/health")
    app.run(debug=True, host='0.0.0.0', port=5000)
