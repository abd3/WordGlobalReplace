#!/usr/bin/env python3
"""
Local CI script for WordGlobalReplace
Runs tests, builds distribution, and publishes to GitHub releases
"""

import os
import sys
import subprocess
import shutil
import tempfile
import json
import zipfile
from pathlib import Path
import logging
from datetime import datetime
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalCI:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.build_dir = os.path.join(self.project_root, "build")
        self.dist_dir = os.path.join(self.project_root, "dist")
        self.version = self.get_version()
        
    def get_version(self):
        """Get current version from git or version file"""
        try:
            # Try to get version from git
            result = subprocess.run(['git', 'describe', '--tags', '--always'], 
                                 cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Fallback to version file or timestamp
        version_file = os.path.join(self.project_root, 'VERSION')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def clean_build_dirs(self):
        """Clean build and distribution directories"""
        logger.info("🧹 Cleaning build directories...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                logger.info(f"   Cleaned {dir_path}")
        
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)
    
    def install_dependencies(self):
        """Install build dependencies"""
        logger.info("📦 Installing dependencies...")
        
        try:
            # Install requirements
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                 cwd=self.project_root, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
            
            # Install test dependencies
            test_deps = ["pytest", "pytest-cov", "coverage", "flake8"]
            for dep in test_deps:
                result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to install {dep}: {result.stderr}")
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def run_tests(self):
        """Run unit tests"""
        logger.info("🧪 Running unit tests...")
        
        try:
            # Run tests with pytest
            test_cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--cov=.", "--cov-report=html"]
            result = subprocess.run(test_cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("❌ Tests failed!")
                logger.error(f"Test output: {result.stdout}")
                logger.error(f"Test errors: {result.stderr}")
                return False
            
            logger.info("✅ All tests passed!")
            logger.info(f"Test output: {result.stdout}")
            return True
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
    
    def run_linting(self):
        """Run code linting"""
        logger.info("🔍 Running code linting...")
        
        try:
            # Run flake8 if available
            result = subprocess.run([sys.executable, "-m", "flake8", "."], 
                                 cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"⚠️  Linting issues found: {result.stdout}")
                # Don't fail build for linting issues, just warn
            else:
                logger.info("✅ Linting passed!")
            
            return True
            
        except Exception as e:
            logger.warning(f"Linting not available: {e}")
            return True  # Don't fail build if linting is not available
    
    def build_distribution(self, repo_url=None):
        """Build the distribution package"""
        logger.info("📦 Building distribution...")
        
        try:
            # Import and run the distribution creator
            sys.path.insert(0, self.project_root)
            from create_distribution import DistributionCreator
            
            creator = DistributionCreator(
                source_dir=self.project_root,
                output_dir=self.dist_dir
            )
            
            success = creator.create_distribution(repo_url=repo_url)
            
            if success:
                logger.info(f"✅ Distribution built successfully in {self.dist_dir}")
                return True
            else:
                logger.error("❌ Distribution build failed")
                return False
                
        except Exception as e:
            logger.error(f"Error building distribution: {e}")
            return False
    
    def create_release_package(self):
        """Create a release package with version info"""
        logger.info("📋 Creating release package...")
        
        try:
            # Create versioned release directory
            release_dir = os.path.join(self.dist_dir, f"WordGlobalReplace-{self.version}")
            if os.path.exists(release_dir):
                shutil.rmtree(release_dir)
            
            # Copy distribution files
            dist_app_dir = os.path.join(self.dist_dir, "WordGlobalReplace.app")
            if os.path.exists(dist_app_dir):
                shutil.copytree(dist_app_dir, release_dir)
            else:
                logger.error("Distribution not found. Run build_distribution first.")
                return False
            
            # Create version info file
            version_info = {
                "version": self.version,
                "build_date": datetime.now().isoformat(),
                "git_commit": self.get_git_commit(),
                "python_version": sys.version,
                "build_type": "local_ci"
            }
            
            version_file = os.path.join(release_dir, "version.json")
            with open(version_file, 'w') as f:
                json.dump(version_info, f, indent=2)
            
            # Create zip package
            zip_path = os.path.join(self.dist_dir, f"WordGlobalReplace-{self.version}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(release_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, release_dir)
                        zipf.write(file_path, arc_path)
            
            logger.info(f"✅ Release package created: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating release package: {e}")
            return None
    
    def get_git_commit(self):
        """Get current git commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                 cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "unknown"
    
    def publish_to_github(self, zip_path, github_token=None, repo=None):
        """Publish release to GitHub"""
        logger.info("🚀 Publishing to GitHub...")
        
        try:
            # Check if GitHub CLI is available
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ GitHub CLI (gh) not found. Please install it first.")
                logger.info("Install with: brew install gh")
                return False
            
            # Check authentication
            auth_result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
            if auth_result.returncode != 0:
                logger.error("❌ Not authenticated with GitHub CLI")
                logger.info("Authenticate with: gh auth login")
                return False
            
            # Create release
            release_cmd = [
                'gh', 'release', 'create', f'v{self.version}',
                zip_path,
                '--title', f'WordGlobalReplace v{self.version}',
                '--notes', f'Automated release of WordGlobalReplace v{self.version}\n\nBuilt with local CI system.'
            ]
            
            if repo:
                release_cmd.extend(['--repo', repo])
            
            result = subprocess.run(release_cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully published release v{self.version}")
                logger.info(f"Release URL: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ Failed to create release: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to GitHub: {e}")
            return False
    
    def run_ci(self, repo_url=None, publish=False, github_token=None, github_repo=None):
        """Main CI process"""
        logger.info("🚀 Starting Local CI Process")
        logger.info(f"Version: {self.version}")
        logger.info(f"Project root: {self.project_root}")
        logger.info("=" * 50)
        
        # Step 1: Clean build directories
        self.clean_build_dirs()
        
        # Step 2: Install dependencies
        if not self.install_dependencies():
            logger.error("❌ Failed to install dependencies")
            return False
        
        # Step 3: Run linting
        self.run_linting()
        
        # Step 4: Run tests
        if not self.run_tests():
            logger.error("❌ Tests failed. CI aborted.")
            return False
        
        # Step 5: Build distribution
        if not self.build_distribution(repo_url):
            logger.error("❌ Failed to build distribution")
            return False
        
        # Step 6: Create release package
        zip_path = self.create_release_package()
        if not zip_path:
            logger.error("❌ Failed to create release package")
            return False
        
        # Step 7: Publish to GitHub (if requested)
        if publish:
            if not self.publish_to_github(zip_path, github_token, github_repo):
                logger.error("❌ Failed to publish to GitHub")
                return False
        
        logger.info("=" * 50)
        logger.info("🎉 Local CI completed successfully!")
        logger.info(f"📦 Distribution: {self.dist_dir}")
        logger.info(f"📋 Release package: {zip_path}")
        
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Local CI for WordGlobalReplace')
    parser.add_argument('--repo-url', help='GitHub repository URL for auto-updates')
    parser.add_argument('--publish', action='store_true', help='Publish to GitHub releases')
    parser.add_argument('--github-token', help='GitHub token for publishing')
    parser.add_argument('--github-repo', help='GitHub repository (owner/repo)')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--skip-linting', action='store_true', help='Skip linting')
    
    args = parser.parse_args()
    
    ci = LocalCI()
    
    # Override test and linting if requested
    if args.skip_tests:
        ci.run_tests = lambda: True
    if args.skip_linting:
        ci.run_linting = lambda: True
    
    success = ci.run_ci(
        repo_url=args.repo_url,
        publish=args.publish,
        github_token=args.github_token,
        github_repo=args.github_repo
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
