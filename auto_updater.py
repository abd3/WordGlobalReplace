#!/usr/bin/env python3
"""
Auto-updater for WordGlobalReplace application
Checks GitHub for new commits and updates the application automatically
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import logging

from config import DEFAULT_REPO_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        """Get the current version/commit hash"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    return f.read().strip()
            else:
                # Try to get current commit hash
                result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                     cwd=self.current_dir, 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                return "unknown"
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return "unknown"
    
    def get_latest_version(self):
        """Get the latest version/commit hash from GitHub"""
        try:
            # Use GitHub API to get latest commit
            import urllib.request
            import urllib.parse
            
            # Extract owner and repo from URL
            if "github.com" in self.repo_url:
                parts = self.repo_url.replace("https://github.com/", "").replace(".git", "")
                owner, repo = parts.split("/")
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{self.branch}"
                
                try:
                    with urllib.request.urlopen(api_url) as response:
                        data = json.loads(response.read().decode())
                        return data['sha']
                except Exception as e:
                    logger.warning(f"GitHub API failed: {e}, trying git fetch")
                    return self._get_latest_via_git()
            else:
                return self._get_latest_via_git()
                
        except Exception as e:
            logger.error(f"Error getting latest version: {e}")
            return None
    
    def _get_latest_via_git(self):
        """Fallback method to get latest version via git"""
        try:
            # Create a temporary directory to fetch latest
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                result = subprocess.run(['git', 'clone', '--depth', '1', 
                                       '--branch', self.branch, 
                                       self.repo_url, temp_dir], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # Get the commit hash
                    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                          cwd=temp_dir, capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error in git fallback: {e}")
        return None
    
    def check_for_updates(self):
        """Check if there are updates available"""
        try:
            current_version = self.get_current_version()
            latest_version = self.get_latest_version()
            
            if not latest_version:
                logger.warning("Could not determine latest version")
                return False, None, None
            
            if current_version == latest_version:
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
                exclude_files = {'.version', '.update_log'}
                
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
                result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                                      cwd=self.current_dir, capture_output=True, text=True)
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
    has_update, current, latest = updater.check_for_updates()
    
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
