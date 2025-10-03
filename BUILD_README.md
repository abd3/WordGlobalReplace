# WordGlobalReplace - Build System

This document describes the comprehensive build system for WordGlobalReplace, including automated testing, distribution building, and GitHub release publishing.

## 🏗️ Build System Overview

The build system provides:
- **Automated Testing**: Runs unit tests on every commit
- **Distribution Building**: Creates lightweight, distributable packages
- **GitHub Integration**: Publishes releases automatically
- **Local Development**: Local build scripts for development
- **CI/CD**: GitHub Actions workflows for automated builds

## 📁 Build System Structure

```
WordGlobalReplace/
├── build.py                    # Main build script
├── local_build.py             # Local build script
├── create_distribution.py     # Distribution creator
├── setup_git_hooks.py         # Git hooks setup
├── scripts/
│   └── post-commit            # Git post-commit hook
├── tests/                     # Unit tests
│   ├── test_word_processor.py
│   ├── test_advanced_word_processor.py
│   ├── test_auto_updater.py
│   └── test_app.py
├── .github/workflows/
│   └── build.yml              # GitHub Actions workflow
├── build/                     # Build artifacts (ignored by git)
├── dist/                      # Distribution packages (ignored by git)
└── .gitignore                 # Updated to ignore build artifacts
```

## 🚀 Quick Start

### 1. Setup Git Hooks (Recommended)

```bash
# Install git hooks for automated builds
python3 setup_git_hooks.py

# This will:
# - Install post-commit hook
# - Run tests and build on every commit
# - Only run full build on main branch
```

### 2. Manual Build

```bash
# Run full build process
python3 build.py --repo-url "https://github.com/yourusername/WordGlobalReplace.git"

# Build with GitHub release publishing
python3 build.py --repo-url "https://github.com/yourusername/WordGlobalReplace.git" --publish
```

### 3. Local Development Build

```bash
# Run local build (faster, for development)
python3 local_build.py

# Skip tests (for quick builds)
python3 local_build.py --skip-tests
```

## 🔧 Build Process Details

### Step 1: Clean Build Directories
- Removes old build artifacts
- Creates fresh build and dist directories

### Step 2: Install Dependencies
- Installs requirements from `requirements.txt`
- Installs test dependencies (pytest, coverage, flake8)
- Handles missing dependencies gracefully

### Step 3: Code Linting
- Runs flake8 for code quality checks
- Warns about issues but doesn't fail build
- Ensures consistent code style

### Step 4: Unit Tests
- Runs comprehensive test suite
- Tests all major components:
  - Word processor functionality
  - Advanced word processor features
  - Auto-updater system
  - Flask application
- Generates coverage reports
- **Build fails if tests fail**

### Step 5: Distribution Building
- Creates lightweight distribution package
- Includes all necessary files
- Configures auto-updater with repository URL
- Creates installer scripts
- Generates user documentation

### Step 6: Release Package Creation
- Creates versioned release directory
- Adds version metadata
- Creates zip package for distribution
- Includes build information

### Step 7: GitHub Publishing (Optional)
- Publishes to GitHub releases
- Requires GitHub CLI (gh) and authentication
- Creates release with version tag
- Uploads distribution package

## 🧪 Testing

### Running Tests Manually

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run tests with coverage
python3 -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
python3 -m pytest tests/test_word_processor.py -v
```

### Test Coverage

The build system includes comprehensive tests for:
- **Word Processing**: Document scanning and text replacement
- **Advanced Features**: Context extraction, batch operations
- **Auto-Updater**: Update checking and installation
- **Flask App**: API endpoints and error handling
- **Build System**: Distribution creation and publishing

## 📦 Distribution

### What Gets Built

The build process creates:
```
dist/
├── WordGlobalReplace.app/          # Application directory
│   ├── app.py                      # Main Flask application
│   ├── word_processor.py           # Word processing logic
│   ├── advanced_word_processor.py  # Advanced features
│   ├── auto_updater.py            # Auto-update functionality
│   ├── launcher.py                # Main launcher
│   ├── run.py                     # Simple startup script
│   ├── requirements.txt           # Dependencies
│   ├── install.sh                 # Installation script
│   ├── README.md                  # User documentation
│   ├── templates/                 # Web interface
│   ├── static/                    # CSS and JavaScript
│   └── Samples/                   # Sample documents
└── WordGlobalReplace-v1.0.0.zip   # Release package
```

### Distribution Features

- **Self-Contained**: Everything needed in one package
- **Auto-Updating**: Checks GitHub for updates automatically
- **Easy Installation**: One-click installer script
- **Cross-Platform**: Works on macOS (primary target)
- **Lightweight**: Minimal dependencies and footprint

## 🔄 Automated Builds

### Git Hooks

The post-commit hook automatically:
1. **Runs on every commit**
2. **Executes tests** (fails if tests fail)
3. **Builds distribution** (if tests pass)
4. **Creates release package**
5. **Only runs full build on main branch**

### GitHub Actions

The CI/CD pipeline:
1. **Triggers on**: Push to main/develop, pull requests, releases
2. **Runs tests**: Full test suite with coverage
3. **Builds distribution**: On main branch
4. **Publishes releases**: On release events
5. **Uploads artifacts**: Build artifacts and release packages

## 🛠️ Configuration

### Build Script Options

```bash
# Basic build
python3 build.py

# Build with auto-update repository
python3 build.py --repo-url "https://github.com/user/repo.git"

# Build and publish to GitHub
python3 build.py --repo-url "https://github.com/user/repo.git" --publish

# Skip tests (not recommended)
python3 build.py --skip-tests

# Skip linting
python3 build.py --skip-linting
```

### Environment Variables

```bash
# GitHub token for publishing
export GITHUB_TOKEN="your_github_token"

# GitHub repository
export GITHUB_REPO="owner/repository"
```

## 📋 Prerequisites

### Required Tools

- **Python 3.7+**: For running the application
- **Git**: For version control and hooks
- **GitHub CLI**: For publishing releases (optional)

### Python Dependencies

- **Flask**: Web framework
- **python-docx**: Word document processing
- **pytest**: Testing framework
- **flake8**: Code linting
- **coverage**: Test coverage

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 coverage
```

## 🚨 Troubleshooting

### Common Issues

1. **Tests Fail**
   - Check test output for specific errors
   - Ensure all dependencies are installed
   - Verify test files are present

2. **Build Fails**
   - Check error messages in build output
   - Ensure all required files exist
   - Verify permissions on build directories

3. **GitHub Publishing Fails**
   - Ensure GitHub CLI is installed: `gh --version`
   - Check authentication: `gh auth status`
   - Verify repository permissions

4. **Git Hooks Not Working**
   - Check hook permissions: `ls -la .git/hooks/`
   - Reinstall hooks: `python3 setup_git_hooks.py`
   - Test manually: `./.git/hooks/post-commit`

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH=.
python3 -c "import logging; logging.basicConfig(level=logging.DEBUG)"

# Run build with debug output
python3 build.py --repo-url "your-repo-url"
```

## 📊 Build Artifacts

### Generated Files

- **`build/`**: Temporary build files (ignored by git)
- **`dist/`**: Distribution packages (ignored by git)
- **`.coverage`**: Test coverage data (ignored by git)
- **`htmlcov/`**: HTML coverage reports (ignored by git)

### Git Ignore Updates

The build system automatically ignores:
```
# Build artifacts
build/
dist/
*.egg-info/
.coverage
.pytest_cache/
htmlcov/
```

## 🔄 Workflow Examples

### Development Workflow

```bash
# 1. Make changes to code
git add .
git commit -m "Add new feature"

# 2. Git hook automatically runs tests and builds
# (if on main branch)

# 3. Check build results
ls -la dist/

# 4. Test distribution
cd dist/WordGlobalReplace.app
./install.sh
python3 run.py
```

### Release Workflow

```bash
# 1. Create release tag
git tag v1.0.0
git push origin v1.0.0

# 2. GitHub Actions automatically:
#    - Runs tests
#    - Builds distribution
#    - Publishes release
#    - Uploads artifacts

# 3. Check GitHub releases page
# 4. Download and test release package
```

## 📈 Monitoring

### Build Status

- **Local**: Check console output for build status
- **GitHub**: Check Actions tab for CI/CD status
- **Tests**: Coverage reports in `htmlcov/` directory

### Performance

- **Build Time**: Typically 30-60 seconds
- **Test Time**: 10-20 seconds
- **Distribution Size**: ~5-10 MB (compressed)

## 🎯 Best Practices

### For Developers

1. **Run tests locally** before committing
2. **Use meaningful commit messages** for better release notes
3. **Test distribution** before publishing
4. **Keep dependencies updated** in requirements.txt
5. **Monitor build logs** for issues

### For Releases

1. **Tag releases** with semantic versioning
2. **Test release packages** before distribution
3. **Update documentation** with new features
4. **Monitor user feedback** on releases

---

**Note**: This build system is designed for macOS. For other platforms, additional configuration may be required.
