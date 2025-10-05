#!/usr/bin/env python3
"""
Lightweight launcher for WordGlobalReplace application
Handles auto-updates and launches the main application
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path
import logging

from config import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_LOCAL_URL, DEFAULT_REPO_URL

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WordGlobalReplaceLauncher:
    def __init__(self):
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.auto_updater = None
        self.update_available = False
        
    def initialize_updater(self, repo_url=None):
        """Initialize the auto-updater"""
        try:
            from auto_updater import AutoUpdater
            self.auto_updater = AutoUpdater(repo_url, self.app_dir)
            return True
        except ImportError as e:
            logger.warning(f"Auto-updater not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Error initializing updater: {e}")
            return False
    
    def check_and_update(self, auto_update=True):
        """Check for updates and optionally update automatically"""
        if not self.auto_updater:
            logger.info("Auto-updater not available, skipping update check")
            return True
        
        try:
            logger.info("Checking for updates...")
            # has_update, current, latest = self.auto_updater.check_for_updates()
            has_update=False
            
            if has_update:
                logger.info(f"Update available: {current} -> {latest}")
                self.update_available = True
                
                if auto_update:
                    logger.info("Auto-updating application...")
                    if self.auto_updater.update_application():
                        logger.info("Update completed successfully!")
                        # Install/update dependencies
                        self.auto_updater.install_dependencies()
                        return True
                    else:
                        logger.error("Update failed!")
                        return False
                else:
                    logger.info("Update available but auto-update is disabled")
                    return True
            else:
                logger.info("Application is up to date")
                return True
                
        except Exception as e:
            logger.error(f"Error during update check: {e}")
            return True  # Continue even if update check fails
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            import flask
            from docx import Document
            return True
        except ImportError as e:
            logger.warning(f"Missing dependencies: {e}")
            return False
    
    def install_dependencies(self):
        """Install required dependencies"""
        try:
            import subprocess
            requirements_file = os.path.join(self.app_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                logger.info("Installing dependencies...")
                cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]

                in_virtual_env = (
                    hasattr(sys, 'real_prefix') or
                    sys.prefix != getattr(sys, 'base_prefix', sys.prefix) or
                    os.environ.get('VIRTUAL_ENV')
                )

                if not in_virtual_env:
                    cmd.insert(-1, '--user')

                result = subprocess.run(cmd, cwd=self.app_dir, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Dependencies installed successfully")
                    return True
                else:
                    logger.error(f"Failed to install dependencies: {result.stderr}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def launch_application(self):
        """Launch the main application"""
        try:
            # Change to application directory
            os.chdir(self.app_dir)
            
            # Import and run the Flask app
            from app import app
            
            logger.info("Starting WordGlobalReplace application...")
            logger.info(f"Open your browser and go to: {DEFAULT_LOCAL_URL}")
            logger.info("Press Ctrl+C to stop the server")
            
            # Open browser automatically
            def open_browser():
                time.sleep(2)  # Wait for server to start
                webbrowser.open(DEFAULT_LOCAL_URL)
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Run the Flask app
            app.run(debug=False, host=DEFAULT_HOST, port=DEFAULT_PORT)
            
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        except Exception as e:
            logger.error(f"Error launching application: {e}")
            return False
        return True
    
    def run(self, repo_url=None, auto_update=True, skip_update_check=False):
        """Main run method"""
        print("=" * 60)
        print("WordGlobalReplace - Global Word Document Find & Replace")
        print("=" * 60)
        
        if repo_url is None:
            repo_url = DEFAULT_REPO_URL
        
        # Initialize auto-updater if repo URL is provided
        if repo_url and not skip_update_check:
            if not self.initialize_updater(repo_url):
                logger.warning("Auto-updater initialization failed, continuing without updates")
        
        # Check and update if needed
        if not skip_update_check:
            if not self.check_and_update(auto_update):
                logger.error("Update process failed")
                return False
        
        # Check dependencies
        if not self.check_dependencies():
            logger.info("Installing missing dependencies...")
            if not self.install_dependencies():
                logger.error("Failed to install dependencies")
                return False
        
        # Create necessary directories
        os.makedirs(os.path.join(self.app_dir, 'templates'), exist_ok=True)
        os.makedirs(os.path.join(self.app_dir, 'static'), exist_ok=True)
        os.makedirs(os.path.join(self.app_dir, 'backups'), exist_ok=True)
        
        # Launch the application
        return self.launch_application()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WordGlobalReplace Launcher')
    parser.add_argument('--repo-url', help='GitHub repository URL for auto-updates')
    parser.add_argument('--no-auto-update', action='store_true', 
                       help='Disable automatic updates')
    parser.add_argument('--skip-update-check', action='store_true',
                       help='Skip update check entirely')
    parser.add_argument('--update-only', action='store_true',
                       help='Only check for updates, don\'t launch app')
    
    args = parser.parse_args()
    
    launcher = WordGlobalReplaceLauncher()
    
    if args.update_only:
        if not args.repo_url:
            print("Repository URL required for update check")
            return 1
        
        if launcher.initialize_updater(args.repo_url):
            has_update, current, latest = launcher.auto_updater.check_for_updates()
            if has_update:
                print(f"Update available: {current} -> {latest}")
                response = input("Do you want to update? (y/n): ")
                if response.lower() == 'y':
                    if launcher.auto_updater.update_application():
                        print("Update completed successfully!")
                        launcher.auto_updater.install_dependencies()
                    else:
                        print("Update failed!")
                else:
                    print("Update cancelled.")
            else:
                print("Application is up to date.")
        return 0
    
    # Run the application
    success = launcher.run(
        repo_url=args.repo_url,
        auto_update=not args.no_auto_update,
        skip_update_check=args.skip_update_check
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
