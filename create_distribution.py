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
import sysconfig

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

            # Create bundled virtual environment
            self._create_virtual_environment(resources_dir)

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
import logging


def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    # Ensure bundled resources are importable
    sys.path.insert(0, app_dir)

    log_dir = Path.home() / "Library" / "Logs" / "WordGlobalReplace"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "application.log"

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicate logging if run multiple times
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if sys.stdout is not None:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    root_logger.info("Launcher started; log file: %s", log_file)

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
APP_DIR=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"
RESOURCE_DIR=\"$APP_DIR/Resources\"
LOG_DIR=\"${HOME}/Library/Logs/WordGlobalReplace\"
LOG_FILE=\"$LOG_DIR/launcher.log\"
VENV_PY=\"$RESOURCE_DIR/venv/bin/python3\"
FALLBACK_PY=\"$RESOURCE_DIR/venv/bin/python\"

mkdir -p \"$LOG_DIR\"

if [ ! -t 1 ]; then
    exec >>\"$LOG_FILE\" 2>&1
fi

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

echo \"[$(timestamp)] Starting WordGlobalReplace launcher\"

export PYTHONUNBUFFERED=1
export PYTHONPATH=\"$RESOURCE_DIR:${PYTHONPATH:-}\"
export DYLD_FRAMEWORK_PATH=\"$RESOURCE_DIR:${DYLD_FRAMEWORK_PATH:-}\"

cd \"$RESOURCE_DIR\"

run_with_interpreter() {
    local interpreter=\"$1\"
    shift
    if [ ! -x \"$interpreter\" ]; then
        return 127
    fi

    echo \"[$(timestamp)] Launching with interpreter: $interpreter\"
    PYTHONEXECUTABLE=\"$interpreter\" \"$interpreter\" run.py \"$@\"
}

if run_with_interpreter \"$VENV_PY\" \"$@\"; then
    exit 0
fi

if run_with_interpreter \"$FALLBACK_PY\" \"$@\"; then
    exit 0
fi

echo \"[$(timestamp)] Bundled interpreter failed; falling back to system python\" 1>&2
unset DYLD_FRAMEWORK_PATH
unset PYTHONEXECUTABLE

exec /usr/bin/env python3 run.py \"$@\"
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

    def _create_virtual_environment(self, resources_dir):
        """Create a self-contained virtual environment with dependencies"""
        venv_path = Path(resources_dir) / 'venv'
        if venv_path.exists():
            shutil.rmtree(venv_path)

        logger.info("Creating bundled virtual environment")
        python_executable = sys.executable
        created_with_copies = True
        try:
            try:
                subprocess.run(
                    [python_executable, '-m', 'venv', '--copies', str(venv_path)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except subprocess.CalledProcessError as exc:
                err_output = exc.stderr
                logger.warning(
                    "Creating venv with --copies failed; attempting standard venv. Details: %s",
                    err_output.strip() if err_output else exc
                )
                subprocess.run(
                    [python_executable, '-m', 'venv', str(venv_path)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                created_with_copies = False
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to create virtual environment: {exc}") from exc

        if os.name == 'nt':
            scripts_dir = venv_path / 'Scripts'
            python_bin = scripts_dir / 'python.exe'
            pip_bin = scripts_dir / 'pip.exe'
        else:
            scripts_dir = venv_path / 'bin'
            python_bin = scripts_dir / 'python'
            pip_bin = scripts_dir / 'pip'

        try:
            subprocess.run([str(python_bin), '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
            subprocess.run(
                [str(pip_bin), 'install', '--no-cache-dir', '-r', str(Path(resources_dir) / 'requirements.txt')],
                check=True
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to install dependencies into bundled environment: {exc}")

        if not created_with_copies:
            logger.info("Ensuring interpreter binaries are copied after symlink-based venv creation")
        self._solidify_python_binaries(venv_path)

        self._bundle_python_runtime(venv_path, resources_dir)
        logger.info("Bundled virtual environment ready")

    def _bundle_python_runtime(self, venv_path: Path, resources_dir: str):
        """Copy the Python framework into the bundle so the app runs without a system Python"""
        if sys.platform != "darwin":
            logger.debug("Non-macOS platform detected; skipping Python framework bundling")
            return

        framework_name = sysconfig.get_config_var('PYTHONFRAMEWORK') or "Python"

        candidate_paths = []

        cfg_prefix = sysconfig.get_config_var('PYTHONFRAMEWORKPREFIX')
        if cfg_prefix:
            candidate_paths.append(Path(cfg_prefix) / f"{framework_name}.framework")

        base_prefix = getattr(sys, 'base_prefix', '') or getattr(sys, 'prefix', '')
        if base_prefix:
            bp = Path(base_prefix)
            # base_prefix typically ends with .../Python.framework/Versions/X.Y
            candidate_paths.append(bp.parent.parent)

        source_framework = None
        for candidate in candidate_paths:
            if candidate.exists():
                source_framework = candidate
                break
        if source_framework is None:
            logger.warning(
                "Unable to locate Python framework (checked: %s); bundled interpreter may require system Python",
                ", ".join(str(p) for p in candidate_paths) or "none"
            )
            return

        destination = Path(resources_dir) / f"{framework_name}.framework"
        if destination.exists():
            shutil.rmtree(destination)

        logger.info(f"Copying Python framework to bundle: {source_framework} -> {destination}")
        shutil.copytree(source_framework, destination, symlinks=False)

        # Ensure site-packages directory exists so relative symlinks remain valid even if source omitted it
        version_dir = destination / "Versions" / f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = version_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        site_packages.mkdir(parents=True, exist_ok=True)

    def _solidify_python_binaries(self, venv_path: Path):
        """Replace symlinked python binaries with physical copies for relocation safety"""
        if os.name == 'nt':
            return  # Windows virtualenv already copies executables

        bin_dir = venv_path / 'bin'
        if not bin_dir.exists():
            return

        binaries = ['python', 'python3']
        for name in binaries:
            bin_path = bin_dir / name
            if not bin_path.exists() or not bin_path.is_symlink():
                continue

            target = bin_path.resolve()
            try:
                bin_path.unlink()
                shutil.copy2(target, bin_path)
                bin_path.chmod(0o755)
                logger.info(f"Replaced symlinked interpreter with copy: {bin_path}")
            except Exception as exc:
                logger.warning(f"Failed to solidify interpreter {bin_path}: {exc}")
    
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

1. Extract the archive and copy `WordGlobalReplace.app` to your Applications folder (or preferred location)
2. Double-click the app to launch it
3. Optionally run `./install.sh` for quick usage instructions

## Usage

1. Launch the application by opening `WordGlobalReplace.app`
2. Open your browser to: {DEFAULT_LOCAL_URL}
3. Select a directory containing Word documents
4. Enter search and replacement text
5. Review matches and apply replacements

## Auto-Updates

{f"Auto-updates are configured from: {repo_url}" if repo_url else "Auto-updates are not configured. To enable, run with --repo-url parameter."}

The application will automatically check for updates when launched and update itself if new versions are available.

## Requirements

- macOS (tested on macOS 10.14+)
- Internet connection (for auto-updates)

## Troubleshooting

If you encounter issues:

1. Verify the app bundle has write permissions (needed for backups/updates)
2. Check the console output for error messages (`open -a Terminal WordGlobalReplace.app`)
3. Ensure you have an active internet connection for auto-updates

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
# WordGlobalReplace Quick Launch Script

echo "WordGlobalReplace"
echo "=================="

cd "$(dirname "$0")"

echo "All dependencies are bundled with the application."
echo ""
echo "To launch the app now, run:"
echo "  open ../.."
echo ""
echo "When running, open your browser to: {DEFAULT_LOCAL_URL}"
echo ""
echo "Tip: You can place WordGlobalReplace.app in /Applications for easy access."
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
        print("3. Optional: run ./WordGlobalReplace.app/Contents/Resources/install.sh for quick launch instructions")
        print("4. Launch the app by double-clicking WordGlobalReplace.app or running: open WordGlobalReplace.app")
    else:
        print("Failed to create distribution")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
