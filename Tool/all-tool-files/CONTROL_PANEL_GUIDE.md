# 🔒 GitLeaks Control Panel - Complete Setup Guide

## 🎯 What Is This?

A **web-based control panel** that makes deploying GitLeaks security scanning to your projects as easy as clicking a button. No more complex command-line operations!

### ✨ Features

- ✅ **Single Project Deployment** - Add GitLeaks to one project in 30 seconds
- ✅ **Bulk Deployment** - Deploy to 10, 20, 50+ projects at once
- ✅ **GitHub Organization** - Automatically deploy to all repos in your org
- ✅ **Visual Dashboard** - Track deployment status and progress
- ✅ **Download Configs** - Get pre-configured files ready to use
- ✅ **One-Click Setup** - No manual file editing required

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Requirements

```bash
# Install Python dependencies
pip install flask flask-cors requests

# Or use requirements.txt
pip install -r requirements.txt
```

### Step 2: Start the Control Panel

```bash
# Start the backend API
python3 api-server.py

# Open the control panel in your browser
open gitleaks-control-panel.html
```

### Step 3: Choose Your Deployment Method

1. **Single Project** - For testing or individual repos
2. **Bulk Deploy** - For multiple projects on your machine
3. **GitHub Org** - For deploying to all repos in your organization

**That's it!** 🎉

---

## 📋 Detailed Setup Instructions

### Option 1: Local Web Server (Recommended)

```bash
# 1. Clone or download the control panel files
git clone <your-repo>
cd gitleaks-control-panel

# 2. Install dependencies
pip install flask flask-cors requests

# 3. Start the API server
python3 api-server.py
# ✓ API running at http://localhost:5000

# 4. Open the control panel
# In another terminal:
python3 -m http.server 8000
# ✓ Panel at http://localhost:8000/gitleaks-control-panel.html
```

### Option 2: Direct File Opening

```bash
# Just open the HTML file in your browser
open gitleaks-control-panel.html

# Note: Some features (like file download) work better with a web server
```

### Option 3: Docker (Simplest)

```bash
# Build the Docker image
docker build -t gitleaks-panel .

# Run the container
docker run -p 5000:5000 -p 8000:8000 gitleaks-panel

# Access at http://localhost:8000
```

---

## 📖 Usage Guide

### 🎯 Single Project Deployment

**Use Case:** You want to add GitLeaks to one specific project.

**Steps:**
1. Click "Single Project" tab
2. Click "Download Files"
3. Extract to your project root
4. Commit and push

**Time:** 30 seconds

---

### ⚡ Bulk Deployment

**Use Case:** You have 5-50 projects on your local machine.

**Steps:**
1. Click "Bulk Deploy" tab
2. Enter project paths (one per line):
   ```
   ~/projects/project1
   ~/projects/project2
   ~/projects/project3
   ```
3. Click "Scan Projects"
4. Review found projects
5. Click "Deploy to All Projects"

**Time:** 2-5 minutes for all projects

---

### 🏢 GitHub Organization Deployment

**Use Case:** You want to deploy to all repos in your GitHub org.

**Steps:**
1. Click "GitHub Org" tab
2. Create a GitHub Personal Access Token:
   - Go to: https://github.com/settings/tokens/new
   - Scopes needed: `repo`, `workflow`
   - Copy the token
3. Enter token and organization name
4. Click "Fetch Repositories"
5. Select repos to deploy (or select all)
6. **Important:** Check "Dry Run" first to preview
7. Click "Deploy to Selected"

**Time:** 5-10 minutes for 100+ repos

---

## 🛠️ API Endpoints

The backend API provides these endpoints:

### Health Check
```bash
GET http://localhost:5000/api/health
```

### Download Configuration Files
```bash
GET http://localhost:5000/api/download-config
```
Returns a zip file with all GitLeaks configuration files.

### Scan Local Projects
```bash
POST http://localhost:5000/api/scan-projects
Content-Type: application/json

{
  "paths": [
    "~/projects/project1",
    "~/projects/project2"
  ]
}
```

### Deploy to Single Project
```bash
POST http://localhost:5000/api/deploy-single
Content-Type: application/json

{
  "path": "~/projects/my-project"
}
```

### Deploy to Multiple Projects
```bash
POST http://localhost:5000/api/deploy-bulk
Content-Type: application/json

{
  "paths": [
    "~/projects/project1",
    "~/projects/project2"
  ]
}
```

### Get GitHub Org Repositories
```bash
POST http://localhost:5000/api/github-org/repos
Content-Type: application/json

{
  "token": "ghp_xxxxxxxxxxxxx",
  "organization": "my-org"
}
```

### Deploy to GitHub Organization
```bash
POST http://localhost:5000/api/github-org/deploy
Content-Type: application/json

{
  "token": "ghp_xxxxxxxxxxxxx",
  "repos": ["my-org/repo1", "my-org/repo2"],
  "dry_run": false
}
```

---

## 📦 What Gets Deployed?

When you deploy GitLeaks, these files are added to your projects:

### 1. `.github/workflows/security.yml`
```yaml
name: Security
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2. `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.20.1
    hooks:
      - id: gitleaks
```

### 3. `.gitleaks.toml` (Optional customization)
```toml
[extend]
useDefault = true

[allowlist]
paths = [
  '''\.env\.example$''',
  '''tests/.*''',
]
```

---

## 🔧 Configuration

### Environment Variables

```bash
# API Server Configuration
export FLASK_PORT=5000
export FLASK_HOST=0.0.0.0
export FLASK_DEBUG=true

# GitHub Configuration (optional)
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
export GITHUB_ORG=my-organization
```

### Custom Templates

You can customize the configuration templates by editing `api-server.py`:

```python
# Edit these variables in api-server.py
GITHUB_WORKFLOW = """..."""
PRECOMMIT_CONFIG = """..."""
GITLEAKS_CONFIG = """..."""
```

---

## 🎨 Customization

### Change UI Theme

Edit `gitleaks-control-panel.html` CSS:

```css
/* Change primary color */
body {
  background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR 100%);
}

.btn {
  background: #YOUR_COLOR;
}
```

### Add Custom Deployment Options

Edit the JavaScript in `gitleaks-control-panel.html` to add more deployment methods.

---

## 🐛 Troubleshooting

### API Not Starting

```bash
# Check if Flask is installed
pip list | grep Flask

# Install dependencies
pip install flask flask-cors requests

# Check port availability
lsof -i :5000
```

### CORS Errors

Make sure the API server is running and CORS is enabled:
```python
CORS(app)  # Should be in api-server.py
```

### GitHub API Rate Limit

```bash
# Check rate limit
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit

# Wait for reset or use a different token
```

### Projects Not Found

```bash
# Verify paths exist
ls ~/projects/your-project

# Use absolute paths
/Users/yourname/projects/your-project
```

---

## 📊 Advanced Usage

### Automated Deployment with CLI

```bash
# Deploy using curl
curl -X POST http://localhost:5000/api/deploy-single \
  -H "Content-Type: application/json" \
  -d '{"path": "~/projects/my-project"}'

# Bulk deploy
curl -X POST http://localhost:5000/api/deploy-bulk \
  -H "Content-Type: application/json" \
  -d '{
    "paths": [
      "~/projects/project1",
      "~/projects/project2"
    ]
  }'
```

### Integration with CI/CD

```yaml
# GitHub Actions integration
name: Deploy GitLeaks
on:
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy GitLeaks
        run: |
          curl -X POST http://your-api/api/github-org/deploy \
            -H "Content-Type: application/json" \
            -d '{
              "token": "${{ secrets.GITHUB_TOKEN }}",
              "repos": ["org/repo1", "org/repo2"],
              "dry_run": false
            }'
```

### Scheduled Deployments

```bash
# Add to crontab for weekly checks
0 9 * * 1 curl -X POST http://localhost:5000/api/deploy-bulk \
  -H "Content-Type: application/json" \
  -d @projects.json
```

---

## 🔐 Security Best Practices

1. **Never commit GitHub tokens** to version control
2. **Use environment variables** for sensitive data
3. **Run API server locally** or on secure network
4. **Use HTTPS** if exposing publicly
5. **Rotate tokens regularly**
6. **Review dry run results** before deploying

---

## 📚 Additional Resources

- [GitLeaks Documentation](https://github.com/gitleaks/gitleaks)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pre-commit Framework](https://pre-commit.com/)

---

## 🤝 Contributing

Want to improve the control panel?

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🆘 Support

Need help?

- 📧 Email: support@yourcompany.com
- 💬 Slack: #security-tools
- 🐛 Issues: GitHub Issues

---

## ✅ Success Checklist

After deploying, verify these:

- [ ] GitLeaks workflow file exists in `.github/workflows/`
- [ ] GitHub Actions shows "Security" workflow running
- [ ] Pre-commit hooks installed locally (optional)
- [ ] No secrets detected in initial scan
- [ ] Team members notified about new security tool

---

**Made with ❤️ for easier security**
