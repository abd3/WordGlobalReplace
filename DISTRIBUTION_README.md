# WordGlobalReplace - Distribution Guide

This guide explains how to create and distribute a lightweight, auto-updating version of WordGlobalReplace for macOS.

## Overview

The distribution system includes:
- **Auto-updater**: Checks GitHub for new commits and updates automatically
- **Lightweight launcher**: Handles updates and launches the application
- **Easy distribution**: Simple zip package that users can extract and run
- **macOS optimized**: Designed specifically for macOS users

## Creating a Distribution

### 1. Basic Distribution (No Auto-Updates)

```bash
# Create a basic distribution
python3 create_distribution.py

# This creates a dist/WordGlobalReplace.zip file
```

### 2. Distribution with Auto-Updates

```bash
# Create distribution with auto-updates from GitHub
python3 create_distribution.py --repo-url "https://github.com/abd3/WordGlobalReplace.git"

# This creates a dist/WordGlobalReplace.zip file with auto-update capability
```

## Distribution Contents

The created distribution includes:

```
WordGlobalReplace.app/
├── app.py                          # Main Flask application
├── word_processor.py              # Word processing logic
├── advanced_word_processor.py     # Advanced processing features
├── auto_updater.py                # Auto-update functionality
├── launcher.py                    # Main launcher with update handling
├── run.py                         # Simple startup script
├── requirements.txt               # Python dependencies
├── install.sh                     # Installation script
├── README.md                      # User documentation
├── templates/                     # Web interface templates
├── static/                        # CSS and JavaScript files
└── Samples/                       # Sample documents
```

## User Installation Process

### For End Users:

1. **Download** the `WordGlobalReplace.zip` file
2. **Extract** the zip file to a desired location
3. **Run** the installer: `./install.sh`
4. **Launch** the application: `python3 run.py`

### What the Installer Does:

- Checks for Python 3.7+ installation
- Installs required dependencies
- Sets up proper permissions
- Creates necessary directories

## Auto-Update Configuration

### For Developers:

1. **Set up GitHub repository** with your code
2. **Create distribution** with your repo URL:
   ```bash
   python3 create_distribution.py --repo-url "https://github.com/abd3/WordGlobalReplace.git"
   ```

### How Auto-Updates Work:

1. **On startup**, the application checks GitHub for new commits
2. **If updates are available**, it automatically downloads and installs them
3. **Dependencies are updated** automatically
4. **Backups are created** before updates
5. **Application restarts** with the new version

## Testing the Distribution

### Test Auto-Updater:

```bash
# Run the manual auto-updater check
python3 tests/manual/auto_updater_check.py
```

### Test Manual Update:

```bash
# Check for updates only
python3 launcher.py --update-only --repo-url "https://github.com/abd3/WordGlobalReplace.git"
```

## Distribution Features

### Security:
- ✅ Automatic backup creation before updates
- ✅ Rollback capability if updates fail
- ✅ Safe dependency installation
- ✅ Permission validation

### User Experience:
- ✅ One-click installation
- ✅ Automatic browser opening
- ✅ Clear error messages
- ✅ Progress indicators

### Developer Experience:
- ✅ Simple distribution creation
- ✅ Configurable auto-updates
- ✅ Comprehensive logging
- ✅ Easy testing

## Customization

### Disable Auto-Updates:

Edit `start.py` and set:
```python
repo_url = None  # Disables auto-updates
```

### Custom Repository:

Edit `start.py` and set:
```python
repo_url = "https://github.com/abd3/your-repo.git"
```

### Manual Update Control:

Users can run with different options:
```bash
# Disable auto-updates
python3 run.py --no-auto-update

# Skip update check entirely
python3 run.py --skip-update-check

# Check for updates only
python3 run.py --update-only
```

## Troubleshooting

### Common Issues:

1. **Python not found**: Ensure Python 3.7+ is installed
2. **Permission denied**: Run `chmod +x install.sh` and `chmod +x run.py`
3. **App doesn't launch**: Try opening via `open -a Terminal WordGlobalReplace.app` to view logs
4. **Update fails**: Check repository URL and internet connection

### Log Files:
Every session writes to:
`~/Library/Logs/WordGlobalReplace/application.log`
The shell stub redirects stdout/stderr to launcher.log when there’s no terminal attached

### Debug Mode:

Enable detailed logging by editing `launcher.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Bundled Python:
The virtual-environment builder copies the full Python.framework into Contents/Resources, enabling the app to run on machines without a preinstalled Python, and adjusts the README/install helper to reflect the bundled runtime. macOS launches pick up that framework via `DYLD_FRAMEWORK_PATH`.

## File Structure

```
WordGlobalReplace/
├── auto_updater.py          # Auto-update functionality
├── launcher.py              # Main launcher with update handling
├── create_distribution.py   # Distribution creator
├── test_auto_updater.py     # Test suite
├── start.py                 # Simple startup script
├── app.py                   # Main Flask application
├── word_processor.py        # Word processing logic
├── advanced_word_processor.py # Advanced features
├── requirements.txt         # Dependencies
├── templates/               # Web interface
├── static/                  # CSS/JS files
├── Samples/                 # Sample documents
└── dist/                    # Generated distribution (created by script)
```

## Best Practices

### For Distribution:
1. **Test thoroughly** before distributing
2. **Use version tags** in your GitHub repository
3. **Document changes** in commit messages
4. **Test on clean systems** to ensure dependencies work

### For Users:
1. **Keep backups** of important documents
2. **Test with sample files** first
3. **Report issues** to the developer
4. **Update regularly** for latest features

## Support

For issues with the distribution system:
1. Check the console output for error messages
2. Verify all files are present in the distribution
3. Test with the provided test suite
4. Contact the developer with specific error details

---

**Note**: This distribution system is designed for macOS. For other platforms, additional configuration may be required.
