# CI/CD Pipeline Guide

This project uses GitHub Actions for Continuous Integration and Continuous Deployment.

## 📋 What Does Our Pipeline Do?

### For Each Service (User & Orders):

#### 1️⃣ **Testing** (Runs on every push/PR)
- Installs Python dependencies
- Runs pytest with coverage reporting
- Uploads coverage to Codecov (optional)

#### 2️⃣ **Linting** (Runs on every push/PR)
- **Ruff**: Fast Python linter for code quality
- **Black**: Code formatter checker
- **Isort**: Import statement organizer

#### 3️⃣ **Docker Build** (Only on main branch)
- Builds Docker images
- Pushes to GitHub Container Registry
- Tags images with commit SHA and branch name

#### 4️⃣ **Deployment** (Currently disabled - see below)
- Can deploy to Kubernetes when configured

### Full Integration Tests
- Runs tests with real PostgreSQL and RabbitMQ
- Tests cross-service communication
- Security scanning with Safety and Bandit

---

## 🚀 Getting Started

### Step 1: Push to GitHub
```bash
git add .github/
git commit -m "Add CI/CD pipeline"
git push origin main
```

### Step 2: Enable GitHub Container Registry
1. Go to your repository on GitHub
2. Click "Settings" → "Actions" → "General"
3. Under "Workflow permissions", select "Read and write permissions"
4. Click "Save"

### Step 3: Watch Your First Build
1. Go to "Actions" tab in your GitHub repo
2. You'll see workflows running for each service
3. Click on any workflow to see detailed logs

---

## 🔧 How It Works

### Workflow Triggers

**On Push to main/develop:**
- Only runs if files in that service changed
- Runs all tests and builds Docker images

**On Pull Requests:**
- Runs tests and linting
- Does NOT build/deploy (safety measure)

### Workflow Jobs

```
┌─────────┐     ┌──────┐
│  Test   │────▶│ Lint │
└─────────┘     └──────┘
                   │
                   ▼
             ┌──────────┐
             │  Build   │
             └──────────┘
                   │
                   ▼
             ┌──────────┐
             │  Deploy  │ (optional)
             └──────────┘
```

---

## 📦 Docker Images

Your Docker images are automatically published to GitHub Container Registry:

**Image naming:**
```
ghcr.io/YOUR_USERNAME/YOUR_REPO/orders-service:latest
ghcr.io/YOUR_USERNAME/YOUR_REPO/user-service:latest
```

**To pull and run locally:**
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Pull image
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/orders-service:latest

# Run it
docker run -p 8000:8000 ghcr.io/YOUR_USERNAME/YOUR_REPO/orders-service:latest
```

---

## 🔐 Enabling Deployment (Optional)

When you're ready to deploy to Kubernetes:

### 1. Get your Kubernetes config
```bash
# Encode your kubeconfig
cat ~/.kube/config | base64 -w 0
```

### 2. Add as GitHub Secret
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `KUBE_CONFIG`
4. Value: (paste the base64 encoded config)

### 3. Uncomment deployment section
In both workflow files, uncomment the `deploy:` job section

### 4. Update deployment names
Edit the kubectl commands to match your deployment names

---

## 🎯 Customization Options

### Change Python Version
In workflow files, modify:
```yaml
python-version: '3.11'  # Change to 3.10, 3.12, etc.
```

### Add More Tests
Just add test files to `tests/` directories - they'll run automatically

### Run Only Fast Tests in CI
```yaml
- name: Run tests
  run: pytest -m "not slow"
```

### Add Environment Variables
```yaml
- name: Run tests
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: pytest
```

---

## 📊 Monitoring Your Pipeline

### View Workflow Status
- **Badge**: Add to README.md:
  ```markdown
  ![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Orders%20Service%20CI/CD/badge.svg)
  ```

### Failed Build?
1. Click on the failed workflow
2. Expand the failed step
3. Read the error message
4. Fix and push again

### Common Issues

**❌ Tests failing?**
- Run tests locally first: `pytest`
- Check for missing dependencies

**❌ Docker build failing?**
- Test Dockerfile locally: `docker build -t test ./orders-service`
- Check file paths in Dockerfile

**❌ Linting errors?**
- Run locally: `black orders-service/app`
- Run: `isort orders-service/app`
- Run: `ruff check orders-service/app`

---

## 🧪 Local Development

### Install dev dependencies
```bash
pip install pytest pytest-asyncio pytest-cov black isort ruff safety bandit
```

### Run tests like CI does
```bash
pytest orders-service/tests -v --cov=orders-service/app
pytest user-service/tests -v --cov=user-service/app
```

### Format code
```bash
black .
isort .
ruff check . --fix
```

### Security check
```bash
safety check -r requirements.txt
bandit -r orders-service/app user-service/app
```

---

## 🎓 Learning Resources

- **GitHub Actions**: https://docs.github.com/en/actions
- **Docker**: https://docs.docker.com/get-started/
- **Pytest**: https://docs.pytest.org/
- **Kubernetes**: https://kubernetes.io/docs/tutorials/

---

## 🆘 Need Help?

Check workflow run logs:
1. Go to Actions tab
2. Click on workflow run
3. Click on failed job
4. Read the logs

Still stuck? Common fixes:
- Clear cache: Re-run workflow with "Re-run all jobs"
- Check permissions: Settings → Actions → General
- Verify secrets: Settings → Secrets and variables → Actions
