#!/usr/bin/env python3
"""
Local build script that can be triggered on every commit
Runs tests, builds distribution, and optionally publishes to GitHub releases
"""

import os
import sys
import subprocess
import shutil
import json
import zipfile
from pathlib import Path
import logging
from datetime import datetime
import argparse
import re
from dataclasses import dataclass
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SEMVER_PATTERN = re.compile(
    r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$'
)


@dataclass
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        if self.build:
            base += f"+{self.build}"
        return base


class VersionManager:
    """Minimal SemVer manager for local builds using .version file."""

    def __init__(self, project_root: str, filename: str = ".version"):
        self.version_path = Path(project_root) / filename

    def _parse(self, value: str) -> SemVer:
        match = SEMVER_PATTERN.fullmatch(value.strip())
        if not match:
            raise ValueError(f"Invalid semantic version: '{value}'")
        major, minor, patch, prerelease, build = match.groups()
        return SemVer(int(major), int(minor), int(patch), prerelease, build)

    def _validate_meta(self, meta: Optional[str], label: str) -> Optional[str]:
        if meta is None:
            return None
        if meta == "":
            return None
        if not re.fullmatch(r'[0-9A-Za-z.-]+', meta):
            raise ValueError(
                f"Invalid {label} metadata '{meta}'. "
                "Only alphanumerics, dots, and hyphen are permitted."
            )
        return meta

    def read(self) -> SemVer:
        if not self.version_path.exists():
            return SemVer(0, 1, 0)
        raw = self.version_path.read_text().strip()
        if not raw:
            return SemVer(0, 1, 0)
        return self._parse(raw)

    def write(self, version: SemVer) -> None:
        self.version_path.write_text(str(version) + "\n")

    def get_version(self) -> str:
        return str(self.read())

    def bump_version(
        self,
        bump_type: str = "patch",
        prerelease: Optional[str] = None,
        build: Optional[str] = None,
    ) -> str:
        bump_type = (bump_type or "patch").lower()
        version = self.read()

        if bump_type == "major":
            version = SemVer(version.major + 1, 0, 0)
        elif bump_type == "minor":
            version = SemVer(version.major, version.minor + 1, 0)
        elif bump_type == "patch":
            version = SemVer(version.major, version.minor, version.patch + 1)
        elif bump_type in {"none", "keep"}:
            version = SemVer(
                version.major,
                version.minor,
                version.patch,
                version.prerelease,
                version.build,
            )
        else:
            raise ValueError(f"Unsupported version bump type: '{bump_type}'")

        if prerelease is not None:
            version.prerelease = self._validate_meta(prerelease, "pre-release")
        elif bump_type != "none":
            version.prerelease = None

        if build is not None:
            version.build = self._validate_meta(build, "build")
        elif bump_type != "none":
            version.build = None

        self.write(version)
        return str(version)

class LocalBuildSystem:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.build_dir = os.path.join(self.project_root, "build")
        self.dist_dir = os.path.join(self.project_root, "dist")
        self.version_manager = VersionManager(self.project_root)
        self.version = self.get_version()
        self.venv_dir = Path(self.project_root) / ".venv"
        if os.name == 'nt':
            self.venv_python = self.venv_dir / "Scripts" / "python.exe"
        else:
            self.venv_python = self.venv_dir / "bin" / "python"
        
    def get_version(self):
        """Return current semantic version string."""
        return self.version_manager.get_version()
    
    def clean_build_dirs(self):
        """Clean build and distribution directories"""
        logger.info("Cleaning build directories...")
        
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
            logger.info(f"Cleaned {self.build_dir}")

        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)

    def ensure_virtualenv(self):
        """Create a project-local virtual environment if it does not exist"""
        if self.venv_dir.exists():
            return True

        logger.info("Creating virtual environment at %s", self.venv_dir)
        try:
            subprocess.run([sys.executable, "-m", "venv", "--upgrade-deps", str(self.venv_dir)],
                           check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to create virtual environment: {exc.stderr or exc}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error creating virtualenv: {exc}")
            return False
    
    def install_dependencies(self):
        """Install build dependencies"""
        logger.info("Installing dependencies...")
        
        try:
            if not self.ensure_virtualenv():
                return False
            python = str(self.venv_python)

            subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"],
                           check=True, capture_output=True, text=True)

            # Install requirements
            result = subprocess.run([python, "-m", "pip", "install", "-r", "requirements.txt"], 
                                 cwd=self.project_root, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
            
            # Install test dependencies
            test_deps = ["pytest", "pytest-cov", "coverage"]
            for dep in test_deps:
                result = subprocess.run([python, "-m", "pip", "install", dep], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to install {dep}: {result.stderr}")
            
            logger.info("Dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def run_tests(self):
        """Run unit tests"""
        logger.info("Running unit tests...")
        
        try:
            if not self.ensure_virtualenv():
                return False
            python = str(self.venv_python)
            # Run tests with pytest
            test_cmd = [python, "-m", "pytest", "tests/", "-v", "--tb=short"]
            result = subprocess.run(test_cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("Tests failed!")
                logger.error(f"Test output: {result.stdout}")
                logger.error(f"Test errors: {result.stderr}")
                return False
            
            logger.info("All tests passed!")
            logger.info(f"Test output: {result.stdout}")
            return True
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
    
    def run_linting(self):
        """Run code linting"""
        logger.info("Running code linting...")
        
        try:
            if not self.ensure_virtualenv():
                return False
            python = str(self.venv_python)
            # Run flake8 if available
            result = subprocess.run([python, "-m", "flake8", "."], 
                                 cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"Linting issues found: {result.stdout}")
                # Don't fail build for linting issues, just warn
            else:
                logger.info("Linting passed!")
            
            return True
            
        except Exception as e:
            logger.warning(f"Linting not available: {e}")
            return True  # Don't fail build if linting is not available
    
    def build_distribution(self, repo_url=None):
        """Build the distribution package"""
        logger.info("Building distribution...")
        
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
                logger.info(f"Distribution built successfully in {self.dist_dir}")
                return True
            else:
                logger.error("Distribution build failed")
                return False
                
        except Exception as e:
            logger.error(f"Error building distribution: {e}")
            return False
    
    def create_release_package(self):
        """Create a release package with version info"""
        logger.info("Creating release package...")
        
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
                "python_version": sys.version
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
            
            logger.info(f"Release package created: {zip_path}")
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
        logger.info("Publishing to GitHub...")
        
        try:
            # Check if GitHub CLI is available
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("GitHub CLI (gh) not found. Please install it first.")
                return False
            
            # Create release
            release_cmd = [
                'gh', 'release', 'create', f'v{self.version}',
                zip_path,
                '--title', f'WordGlobalReplace v{self.version}',
                '--notes', f'Automated release of WordGlobalReplace v{self.version}'
            ]
            
            if repo:
                release_cmd.extend(['--repo', repo])
            
            result = subprocess.run(release_cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully published release v{self.version}")
                logger.info(f"Release URL: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Failed to create release: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to GitHub: {e}")
            return False
    
    def run_application_smoke_test(self):
        """Launch the packaged app as a final smoke test."""
        app_executable = Path(self.dist_dir) / "WordGlobalReplace.app" / "Contents" / "MacOS" / "WordGlobalReplace"
        if not app_executable.exists():
            logger.error("Cannot run smoke test; app executable not found at %s", app_executable)
            return False

        logger.info("Launching packaged application for smoke test.")
        logger.info("Press Ctrl+C in this terminal to stop the app once the browser window opens.")

        try:
            process = subprocess.Popen([str(app_executable)], cwd=app_executable.parent)
            interrupted = False
            try:
                process.wait()
            except KeyboardInterrupt:
                logger.info("Ctrl+C detected; stopping the application...")
                interrupted = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Application did not terminate gracefully; forcing shutdown.")
                    process.kill()
            exit_code = process.poll()
            logger.info("Smoke test application exited with code %s", exit_code)
            return True if interrupted else exit_code == 0
        except FileNotFoundError:
            logger.error("Application executable not found: %s", app_executable)
        except Exception as exc:
            logger.error(f"Failed to launch application: {exc}")
        return False
    
    def build(
        self,
        repo_url=None,
        publish=False,
        github_token=None,
        github_repo=None,
        run_app=False,
        version_bump="patch",
        prerelease=None,
        build_metadata=None,
    ):
        """Main build process"""
        logger.info("Starting local build process...")
        logger.info(f"Project root: {self.project_root}")

        try:
            self.version = self.version_manager.bump_version(
                version_bump, prerelease=prerelease, build=build_metadata
            )
        except ValueError as exc:
            logger.error(f"Versioning error: {exc}")
            return False

        logger.info(f"Using version: {self.version}")
        
        # Step 1: Clean build directories
        self.clean_build_dirs()
        
        # Step 2: Install dependencies
        if not self.install_dependencies():
            logger.error("Failed to install dependencies")
            return False
        
        # Step 3: Run linting
        self.run_linting()
        
        # Step 4: Run tests
        if not self.run_tests():
            logger.error("Tests failed. Build aborted.")
            return False
        
        # Step 5: Build distribution
        if not self.build_distribution(repo_url):
            logger.error("Failed to build distribution")
            return False
        
        # Step 6: Create release package
        zip_path = self.create_release_package()
        if not zip_path:
            logger.error("Failed to create release package")
            return False
        
        # Step 7: Publish to GitHub (if requested)
        if publish:
            if not self.publish_to_github(zip_path, github_token, github_repo):
                logger.error("Failed to publish to GitHub")
                return False

        # Step 8: Launch the packaged app for a manual smoke test
        if run_app:
            if not self.run_application_smoke_test():
                logger.error("Smoke test failed.")
                return False
        
        logger.info("Local build completed successfully!")
        logger.info(f"Distribution: {self.dist_dir}")
        logger.info(f"Release package: {zip_path}")
        
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Local Build WordGlobalReplace')
    parser.add_argument('--repo-url', help='GitHub repository URL for auto-updates')
    parser.add_argument('--publish', action='store_true', help='Publish to GitHub releases')
    parser.add_argument('--github-token', help='GitHub token for publishing')
    parser.add_argument('--github-repo', help='GitHub repository (owner/repo)')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--skip-linting', action='store_true', help='Skip linting')
    parser.add_argument('--run-app', action='store_true', help='Skip launching the packaged app at the end of the build')
    parser.add_argument('--version-bump', choices=['major', 'minor', 'patch', 'none'], default='patch',
                        help='Semantic version component to bump (default: patch)')
    parser.add_argument('--pre-release', help='Set semantic version pre-release identifier')
    parser.add_argument('--build-metadata', help='Set semantic version build metadata')
    
    args = parser.parse_args()
    
    builder = LocalBuildSystem()
    
    # Override test and linting if requested
    if args.skip_tests:
        builder.run_tests = lambda: True
    if args.skip_linting:
        builder.run_linting = lambda: True
    
    success = builder.build(
        repo_url=args.repo_url,
        publish=args.publish,
        github_token=args.github_token,
        github_repo=args.github_repo,
        run_app=args.run_app,
        version_bump=args.version_bump,
        prerelease=args.pre_release,
        build_metadata=args.build_metadata,
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
