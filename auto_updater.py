#!/usr/bin/env python3
"""
Auto-updater for WordGlobalReplace application
Checks GitHub for new commits and updates the application automatically
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import logging
import urllib.request
import urllib.parse
import re
from typing import List, Optional, Tuple, Union

from config import DEFAULT_REPO_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEMVER_RE = re.compile(
    r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$'
)


PrereleasePart = Tuple[bool, Union[int, str]]


def _split_prerelease(value: Optional[str]) -> List[PrereleasePart]:
    if not value:
        return []
    parts = value.split('.')
    result: List[PrereleasePart] = []
    for part in parts:
        if part.isdigit():
            result.append((True, int(part)))
        else:
            result.append((False, part))
    return result


def _parse_semver(value: str) -> Optional[Tuple[int, int, int, List[PrereleasePart]]]:
    match = SEMVER_RE.fullmatch(value.strip())
    if not match:
        return None
    major, minor, patch, prerelease, _build = match.groups()
    return (
        int(major),
        int(minor),
        int(patch),
        _split_prerelease(prerelease),
    )


def _compare_semver(a: str, b: str) -> int:
    parsed_a = _parse_semver(a)
    parsed_b = _parse_semver(b)
    if not parsed_a or not parsed_b:
        return (a > b) - (a < b)

    for idx in range(3):
        if parsed_a[idx] != parsed_b[idx]:
            return (parsed_a[idx] > parsed_b[idx]) - (parsed_a[idx] < parsed_b[idx])

    pre_a = parsed_a[3]
    pre_b = parsed_b[3]
    if not pre_a and not pre_b:
        return 0
    if not pre_a:
        return 1
    if not pre_b:
        return -1

    for part_a, part_b in zip(pre_a, pre_b):
        is_digit_a, value_a = part_a
        is_digit_b, value_b = part_b
        if is_digit_a and is_digit_b:
            if value_a != value_b:
                return (value_a > value_b) - (value_a < value_b)
        elif is_digit_a != is_digit_b:
            return -1 if is_digit_a else 1
        else:
            if value_a != value_b:
                return (value_a > value_b) - (value_a < value_b)
    return (len(pre_a) > len(pre_b)) - (len(pre_a) < len(pre_b))


class AutoUpdater:
    def __init__(self, repo_url=DEFAULT_REPO_URL, 
                 current_dir=None, branch="main"):
        """
        Initialize the auto-updater
        
        Args:
            repo_url: GitHub repository URL
            current_dir: Current application directory
            branch: Git branch to track (default: main)
        """
        self.repo_url = repo_url
        self.current_dir = current_dir or os.getcwd()
        self.branch = branch
        self.version_file = os.path.join(self.current_dir, ".version")
        self.update_log = os.path.join(self.current_dir, ".update_log")
        
    def get_current_version(self):
        """Return the installed semantic version string."""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return f.read().strip() or "0.0.0"
            return "0.0.0"
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return "0.0.0"
    
    def _get_remote_version_url(self) -> Optional[str]:
        try:
            if "github.com" not in self.repo_url:
                return None
            parts = self.repo_url.replace("https://github.com/", "").replace(".git", "")
            owner, repo = parts.split("/")
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{self.branch}/.version"
            with urllib.request.urlopen(raw_url) as response:
                return response.read().decode("utf-8").strip()
        except Exception as exc:
            logger.warning(f"Failed to fetch .version via raw URL: {exc}")
            return None

    def _get_latest_via_git(self) -> Optional[str]:
        """Fallback method to get latest version via git clone"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                result = subprocess.run(['git', 'clone', '--depth', '1', 
                                       '--branch', self.branch, 
                                       self.repo_url, temp_dir], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version_path = Path(temp_dir) / ".version"
                    if version_path.exists():
                        return version_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error(f"Error in git fallback: {e}")
        return None
    
    def get_latest_version(self):
        """Fetch the most recent available semantic version."""
        version = self._get_remote_version_url()
        if version:
            return version
        return self._get_latest_via_git()
    
    def check_for_updates(self):
        """Check if there are updates available"""
        try:
            current_version = self.get_current_version()
            latest_version = self.get_latest_version()
            
            if not latest_version:
                logger.warning("Could not determine latest version")
                return False, None, None
            
            if _compare_semver(latest_version, current_version) <= 0:
                logger.info("Application is up to date")
                return False, current_version, latest_version
            
            logger.info(f"Update available: {current_version} -> {latest_version}")
            return True, current_version, latest_version
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, None, None
    
    def update_application(self):
        """Update the application to the latest version"""
        try:
            logger.info("Starting application update...")
            
            # Create backup of current version
            backup_dir = os.path.join(self.current_dir, "backups", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup important files
            important_files = ['app.py', 'run.py', 'word_processor.py', 'advanced_word_processor.py', 
                             'templates', 'static', 'requirements.txt']
            
            for item in important_files:
                src = os.path.join(self.current_dir, item)
                if os.path.exists(src):
                    dst = os.path.join(backup_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # Create temporary directory for update
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the latest version
                result = subprocess.run(['git', 'clone', '--depth', '1', 
                                       '--branch', self.branch, 
                                       self.repo_url, temp_dir], 
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Failed to clone repository: {result.stderr}")
                    return False
                
                # Copy new files (excluding .git, backups, and other non-essential directories)
                exclude_dirs = {'.git', 'backups', '__pycache__', '.DS_Store'}
                exclude_files = {'.update_log'}
                
                for root, dirs, files in os.walk(temp_dir):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    
                    for file in files:
                        if file in exclude_files:
                            continue
                            
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, temp_dir)
                        dst_path = os.path.join(self.current_dir, rel_path)
                        
                        # Create destination directory if needed
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(src_path, dst_path)
            
            # Update version file
            latest_version = self.get_latest_version()
            if latest_version:
                with open(self.version_file, 'w') as f:
                    f.write(latest_version)
            
            # Log the update
            with open(self.update_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()}: Updated to {latest_version}\n")
            
            logger.info("Application updated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error updating application: {e}")
            return False
    
    def install_dependencies(self):
        """Install or update Python dependencies"""
        try:
            requirements_file = os.path.join(self.current_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                logger.info("Installing/updating dependencies...")
                cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]

                in_virtual_env = (
                    hasattr(sys, 'real_prefix') or
                    sys.prefix != getattr(sys, 'base_prefix', sys.prefix) or
                    os.environ.get('VIRTUAL_ENV')
                )

                if not in_virtual_env:
                    cmd.insert(-1, '--user')

                result = subprocess.run(cmd, cwd=self.current_dir, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Dependencies updated successfully")
                    return True
                else:
                    logger.error(f"Failed to install dependencies: {result.stderr}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False

def main():
    """Main function for testing the auto-updater"""
    updater = AutoUpdater()
    
    print("Checking for updates...")
    # has_update, current, latest = updater.check_for_updates()
    has_update = False
    if has_update:
        print(f"Update available: {current} -> {latest}")
        response = input("Do you want to update? (y/n): ")
        if response.lower() == 'y':
            if updater.update_application():
                print("Update completed successfully!")
                updater.install_dependencies()
            else:
                print("Update failed!")
        else:
            print("Update cancelled.")
    else:
        print("Application is up to date.")

if __name__ == "__main__":
    main()
