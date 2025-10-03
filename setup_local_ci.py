#!/usr/bin/env python3
"""
Setup script for local CI system
Configures git hooks and GitHub CLI for automated builds and releases
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository")
        return False
    print("✅ Git repository found")
    
    # Check if GitHub CLI is installed
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI found")
            github_cli_available = True
        else:
            print("⚠️  GitHub CLI not found")
            github_cli_available = False
    except:
        print("⚠️  GitHub CLI not found")
        github_cli_available = False
    
    return github_cli_available

def setup_git_hooks():
    """Setup git hooks for automated builds"""
    print("\n🔧 Setting up git hooks...")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository")
        return False
    
    git_hooks_dir = '.git/hooks'
    scripts_dir = 'scripts'
    
    # Copy post-commit hook
    post_commit_script = os.path.join(scripts_dir, 'post-commit')
    post_commit_hook = os.path.join(git_hooks_dir, 'post-commit')
    
    if os.path.exists(post_commit_script):
        shutil.copy2(post_commit_script, post_commit_hook)
        os.chmod(post_commit_hook, 0o755)
        print(f"✅ Installed post-commit hook: {post_commit_hook}")
    else:
        print(f"❌ Post-commit script not found: {post_commit_script}")
        return False
    
    return True

def setup_github_cli():
    """Setup GitHub CLI authentication"""
    print("\n🔐 Setting up GitHub CLI...")
    
    try:
        # Check if already authenticated
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI already authenticated")
            return True
        
        print("🔑 GitHub CLI authentication required")
        print("Please run: gh auth login")
        print("Then run this setup script again")
        return False
        
    except Exception as e:
        print(f"❌ Error checking GitHub CLI: {e}")
        return False

def create_ci_script():
    """Create a convenient CI script"""
    print("\n📝 Creating CI script...")
    
    ci_script_content = '''#!/bin/bash
# WordGlobalReplace Local CI Script
# Run this script to execute the full CI process

echo "🚀 WordGlobalReplace Local CI"
echo "=============================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Run the CI process
python3 ci_local.py --repo-url "https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\\([^/]*\\/[^/]*\\)\\.git.*/\\1/')" --publish

if [ $? -eq 0 ]; then
    echo "✅ CI completed successfully!"
else
    echo "❌ CI failed!"
    exit 1
fi
'''
    
    ci_script_path = 'run_ci.sh'
    with open(ci_script_path, 'w') as f:
        f.write(ci_script_content)
    
    os.chmod(ci_script_path, 0o755)
    print(f"✅ Created CI script: {ci_script_path}")
    
    return True

def main():
    """Main setup function"""
    print("🚀 WordGlobalReplace Local CI Setup")
    print("===================================")
    
    # Check requirements
    github_cli_available = check_requirements()
    
    # Setup git hooks
    if not setup_git_hooks():
        print("❌ Failed to setup git hooks")
        return 1
    
    # Setup GitHub CLI
    if github_cli_available:
        if not setup_github_cli():
            print("⚠️  GitHub CLI setup incomplete")
    else:
        print("⚠️  GitHub CLI not available - install with: brew install gh")
    
    # Create CI script
    if not create_ci_script():
        print("❌ Failed to create CI script")
        return 1
    
    print("\n🎉 Local CI setup completed!")
    print("\nNext steps:")
    print("1. Install GitHub CLI: brew install gh")
    print("2. Authenticate: gh auth login")
    print("3. Run CI: ./run_ci.sh")
    print("4. Or run manually: python3 ci_local.py --publish")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
