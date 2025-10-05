#!/usr/bin/env python3
"""
Distribution creator for WordGlobalReplace application
Creates a lightweight, distributable package for macOS
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
import logging

from config import DEFAULT_LOCAL_URL, DEFAULT_REPO_URL, CF_BUNDLE_IDENTIFIER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistributionCreator:
    def __init__(self, source_dir=None, output_dir="dist"):
        self.source_dir = source_dir or os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir
        self.app_name = "WordGlobalReplace"
        
    def create_distribution(self, repo_url=None):
        """Create a distributable package"""
        try:
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Create app directory
            app_dir = os.path.join(self.output_dir, f"{self.app_name}.app")
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)

            contents_dir = os.path.join(app_dir, "Contents")
            macos_dir = os.path.join(contents_dir, "MacOS")
            resources_dir = os.path.join(contents_dir, "Resources")

            os.makedirs(macos_dir, exist_ok=True)
            os.makedirs(resources_dir, exist_ok=True)

            # Copy application files
            self._copy_application_files(resources_dir)

            # Create Info.plist metadata
            self._create_info_plist(contents_dir)

            # Create launcher scripts
            self._create_launcher_script(macos_dir, resources_dir, repo_url)

            # Create requirements file
            self._create_requirements_file(resources_dir)

            # Create README for distribution
            self._create_distribution_readme(resources_dir, repo_url)

            # Create installer script
            self._create_installer_script(resources_dir)

            # Create zip package
            self._create_zip_package(app_dir)
            
            logger.info(f"Distribution created successfully in {self.output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating distribution: {e}")
            return False
    
    def _copy_application_files(self, resources_dir):
        """Copy essential application files"""
        essential_files = [
            'app.py',
            'word_processor.py', 
            'advanced_word_processor.py',
            'auto_updater.py',
            'launcher.py',
            'config.py',
            'templates/',
            'static/',
            'Samples/'
        ]
        
        for item in essential_files:
            src = os.path.join(self.source_dir, item)
            dst = os.path.join(resources_dir, item)
            
            if os.path.exists(src):
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                logger.info(f"Copied {item}")

    def _create_info_plist(self, contents_dir):
        """Create the macOS Info.plist metadata file"""
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>{CF_BUNDLE_IDENTIFIER}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>{self.app_name}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
'''

        plist_path = os.path.join(contents_dir, "Info.plist")
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        logger.info("Created Info.plist")
    
    def _create_launcher_script(self, macos_dir, resources_dir, repo_url):
        """Create the main launcher scripts for the bundle"""
        run_launcher_content = f'''#!/usr/bin/env python3
"""WordGlobalReplace - Auto-updating launcher"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    # Ensure bundled resources are importable
    sys.path.insert(0, app_dir)

    try:
        from launcher import WordGlobalReplaceLauncher
        from config import DEFAULT_REPO_URL

        launcher = WordGlobalReplaceLauncher()
        distribution_repo_url = "{repo_url or ''}"
        launcher.run(repo_url=distribution_repo_url or DEFAULT_REPO_URL, auto_update=True)

    except ImportError as exc:
        print(f"Error importing launcher: {{exc}}")
        print("Please ensure all files are present in the application directory.")
        return 1
    except Exception as exc:
        print(f"Error running application: {{exc}}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

        python_launcher_path = os.path.join(resources_dir, "run.py")
        with open(python_launcher_path, 'w') as f:
            f.write(run_launcher_content)
        os.chmod(python_launcher_path, 0o755)
        logger.info("Created Python launcher script")

        mac_launcher_content = """#!/bin/bash
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCE_DIR="$APP_DIR/Resources"
cd "$RESOURCE_DIR"
exec /usr/bin/env python3 run.py "$@"
"""

        mac_launcher_path = os.path.join(macos_dir, self.app_name)
        with open(mac_launcher_path, 'w') as f:
            f.write(mac_launcher_content)
        os.chmod(mac_launcher_path, 0o755)
        logger.info("Created macOS launcher executable")
    
    def _create_requirements_file(self, resources_dir):
        """Create a requirements file for the distribution"""
        requirements_content = '''# WordGlobalReplace - Python Dependencies
# Core web framework
Flask==2.3.3

# Word document processing
python-docx==0.8.11

# Additional utilities
pathlib2==2.3.7; python_version < "3.4"
'''
        
        req_path = os.path.join(resources_dir, "requirements.txt")
        with open(req_path, 'w') as f:
            f.write(requirements_content)
        logger.info("Created requirements file")
    
    def _create_distribution_readme(self, resources_dir, repo_url):
        """Create README for the distribution"""
        readme_content = f'''# WordGlobalReplace

A lightweight application for finding and replacing text across multiple Word documents.

## Features

- Web-based interface for easy use
- Support for multiple Word document formats (.doc, .docx)
- Advanced search with context preview
- Batch replacement capabilities
- Auto-updating from GitHub (if repository URL is configured)
- Backup creation before replacements

## Installation

1. Ensure Python 3.7+ is installed on your system
2. Run the installer script: `./install.sh`
3. Or run directly: `python3 run.py`

## Usage

1. Run the application: `python3 run.py`
2. Open your browser to: {DEFAULT_LOCAL_URL}
3. Select a directory containing Word documents
4. Enter search and replacement text
5. Review matches and apply replacements

## Auto-Updates

{f"Auto-updates are configured from: {repo_url}" if repo_url else "Auto-updates are not configured. To enable, run with --repo-url parameter."}

The application will automatically check for updates when launched and update itself if new versions are available.

## Requirements

- Python 3.7 or higher
- Internet connection (for auto-updates)
- macOS (tested on macOS 10.14+)

## Troubleshooting

If you encounter issues:

1. Ensure Python 3.7+ is installed
2. Check that all dependencies are installed: `python3 -m pip install --user -r requirements.txt`
3. Verify the application directory has write permissions
4. Check the console output for error messages

## Support

For issues and support, please check the GitHub repository or contact the developer.
'''
        
        readme_path = os.path.join(resources_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        logger.info("Created distribution README")
    
    def _create_installer_script(self, resources_dir):
        """Create an installer script for easy setup"""
        installer_content = f'''#!/bin/bash
# WordGlobalReplace Installer Script

echo "WordGlobalReplace Installer"
echo "=========================="

cd "$(dirname "$0")"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.7"

if [ "$(printf '%s\\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "Python version: $python_version ✓"

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --user -r requirements.txt

if [ $? -eq 0 ]; then
    echo "Dependencies installed successfully ✓"
else
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Make launcher executable
chmod +x run.py

echo ""
echo "Installation completed successfully!"
echo ""
echo "To run the application:"
echo "  open ../.."
echo ""
echo "The application will open in your browser at: {DEFAULT_LOCAL_URL}"
'''
        
        installer_path = os.path.join(resources_dir, "install.sh")
        with open(installer_path, 'w') as f:
            f.write(installer_content)
        
        # Make it executable
        os.chmod(installer_path, 0o755)
        logger.info("Created installer script")
    
    def _create_zip_package(self, app_dir):
        """Create a zip package for distribution"""
        zip_path = os.path.join(self.output_dir, f"{self.app_name}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, app_dir)
                    zipf.write(file_path, arc_path)
        
        logger.info(f"Created zip package: {zip_path}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create WordGlobalReplace distribution')
    parser.add_argument('--repo-url', help='GitHub repository URL for auto-updates')
    parser.add_argument('--output-dir', default='dist', help='Output directory for distribution')
    
    args = parser.parse_args()
    
    creator = DistributionCreator(output_dir=args.output_dir)
    success = creator.create_distribution(repo_url=args.repo_url)
    
    if success:
        print(f"\\nDistribution created successfully!")
        print(f"Output directory: {args.output_dir}")
        print(f"\\nTo distribute:")
        print(f"1. Share the {args.output_dir}/WordGlobalReplace.zip file")
        print("2. Recipients should extract and copy WordGlobalReplace.app to their Applications folder (or another preferred location)")
        print("3. Optional: run ./WordGlobalReplace.app/Contents/Resources/install.sh to pre-install dependencies")
        print("4. Launch the app by double-clicking WordGlobalReplace.app or running: open WordGlobalReplace.app")
    else:
        print("Failed to create distribution")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
