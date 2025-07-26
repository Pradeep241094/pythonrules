# GitHub Actions Setup Guide

This guide explains how to set up automated publishing and CI/CD for the lightweight-test-runner package using GitHub Actions.

## Workflow Files Created

1. **`.github/workflows/publish-to-pypi.yml`** - Automated publishing to PyPI
2. **`.github/workflows/ci.yml`** - Continuous Integration testing
3. **`.github/workflows/release.yml`** - Automated releases on git tags

## Setup Instructions

### 1. Repository Setup

1. **Create GitHub Repository**:
   ```bash
   # Initialize git repository
   git init
   git add .
   git commit -m "Initial commit: Lightweight Test Runner"
   
   # Add remote repository
   git remote add origin https://github.com/pradeepprakash1024/lightweight-test-runner.git
   git push -u origin main
   ```

### 2. Configure PyPI API Tokens

#### For TestPyPI (Testing)

1. Go to [TestPyPI Account Settings](https://test.pypi.org/manage/account/token/)
2. Create a new API token with scope "Entire account"
3. Copy the token (starts with `pypi-`)

#### For PyPI (Production)

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/token/)
2. Create a new API token with scope "Entire account"
3. Copy the token (starts with `pypi-`)

### 3. Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets:

   - **`TEST_PYPI_API_TOKEN`**: Your TestPyPI API token
   - **`PYPI_API_TOKEN`**: Your PyPI API token

### 4. Set Up Environments (Optional but Recommended)

1. Go to **Settings** → **Environments**
2. Create two environments:
   - **`testpypi`**: For testing releases
   - **`pypi`**: For production releases
3. Add protection rules as needed (e.g., required reviewers)

## Workflow Triggers

### Continuous Integration (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Actions:**
- Tests on multiple Python versions (3.7-3.11)
- Tests on multiple OS (Ubuntu, Windows, macOS)
- Linting with flake8
- Package building and installation testing

### Publishing (`publish-to-pypi.yml`)

**Triggers:**
- **Automatic**: When a GitHub release is published
- **Manual**: Via workflow dispatch with environment selection

**Actions:**
- Builds the package
- Tests installation on multiple Python versions
- Publishes to TestPyPI or PyPI based on trigger

### Release (`release.yml`)

**Triggers:**
- When a git tag starting with `v` is pushed (e.g., `v1.0.0`)

**Actions:**
- Creates a GitHub release
- Builds and publishes to PyPI
- Uploads release assets

## Usage Examples

### 1. Manual Publishing to TestPyPI

1. Go to **Actions** tab in your GitHub repository
2. Select **"Publish to PyPI"** workflow
3. Click **"Run workflow"**
4. Select `testpypi` environment
5. Click **"Run workflow"**

### 2. Manual Publishing to PyPI

1. Go to **Actions** tab in your GitHub repository
2. Select **"Publish to PyPI"** workflow
3. Click **"Run workflow"**
4. Select `pypi` environment
5. Click **"Run workflow"**

### 3. Automated Release

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

This will automatically:
- Create a GitHub release
- Build the package
- Publish to PyPI

### 4. Testing Changes

Simply push to `main` or create a pull request:

```bash
git add .
git commit -m "Add new feature"
git push origin main
```

This will trigger the CI workflow to test your changes.

## Monitoring Workflows

### View Workflow Status

1. Go to the **Actions** tab in your repository
2. Click on any workflow run to see details
3. Check logs for each job and step

### Common Issues and Solutions

#### 1. Authentication Errors

**Problem**: `403 Forbidden` or authentication errors

**Solution**:
- Verify API tokens are correct
- Check token permissions
- Ensure secrets are properly set in repository settings

#### 2. Package Name Conflicts

**Problem**: Package name already exists on PyPI

**Solution**:
- Choose a different package name
- Update `setup.py` and `pyproject.toml`
- Update workflow files if needed

#### 3. Build Failures

**Problem**: Package build fails

**Solution**:
- Check Python syntax in all files
- Verify all dependencies are specified
- Test build locally first: `python -m build`

#### 4. Test Failures

**Problem**: Tests fail in CI

**Solution**:
- Run tests locally: `testrules comprehensive`
- Check Python version compatibility
- Review test logs in GitHub Actions

## Workflow Customization

### Adding New Test Types

Edit `.github/workflows/ci.yml`:

```yaml
- name: Run custom tests
  run: |
    testrules my_custom_test_type
```

### Changing Python Versions

Edit the matrix in workflow files:

```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
```

### Adding Code Coverage

The CI workflow includes coverage reporting. To enable:

1. Sign up for [Codecov](https://codecov.io/)
2. Add `CODECOV_TOKEN` to repository secrets
3. Coverage reports will be uploaded automatically

## Security Best Practices

1. **Use API Tokens**: Never use username/password
2. **Scope Tokens**: Use project-scoped tokens when possible
3. **Environment Protection**: Use GitHub environments for production
4. **Review Process**: Require reviews for production deployments
5. **Secret Rotation**: Regularly rotate API tokens

## Troubleshooting

### Debug Mode

Add this step to any workflow for debugging:

```yaml
- name: Debug Information
  run: |
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
    echo "Working directory: $(pwd)"
    echo "Files: $(ls -la)"
    echo "Environment: ${{ github.event_name }}"
```

### Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow locally
act push

# Run specific job
act -j test
```

## Next Steps

1. **Set up the repository** with the workflow files
2. **Configure secrets** for PyPI tokens
3. **Test the workflows** with a test release
4. **Monitor and iterate** based on results

The workflows are now ready to automate your package publishing and testing process!