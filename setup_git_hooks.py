#!/usr/bin/env python3
"""
Setup script for git hooks
Installs post-commit hook to trigger builds on every commit
"""

import os
import sys
import shutil
from pathlib import Path

def setup_git_hooks():
    """Setup git hooks for automated builds"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    git_hooks_dir = os.path.join(project_root, '.git', 'hooks')
    scripts_dir = os.path.join(project_root, 'scripts')
    
    # Check if we're in a git repository
    if not os.path.exists(git_hooks_dir):
        print("Error: Not in a git repository")
        return False
    
    # Check if scripts directory exists
    if not os.path.exists(scripts_dir):
        print("Error: Scripts directory not found")
        return False
    
    # Copy post-commit hook
    post_commit_script = os.path.join(scripts_dir, 'post-commit')
    post_commit_hook = os.path.join(git_hooks_dir, 'post-commit')
    
    if os.path.exists(post_commit_script):
        shutil.copy2(post_commit_script, post_commit_hook)
        os.chmod(post_commit_hook, 0o755)
        print(f"✅ Installed post-commit hook: {post_commit_hook}")
    else:
        print(f"Error: Post-commit script not found: {post_commit_script}")
        return False
    
    print("Git hooks setup completed!")
    print("\nThe post-commit hook will now:")
    print("1. Run tests on every commit")
    print("2. Build distribution if tests pass")
    print("3. Create release package")
    print("4. Only run full build on main branch (use --force to override)")
    
    return True

def remove_git_hooks():
    """Remove git hooks"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    git_hooks_dir = os.path.join(project_root, '.git', 'hooks')
    post_commit_hook = os.path.join(git_hooks_dir, 'post-commit')
    
    if os.path.exists(post_commit_hook):
        os.remove(post_commit_hook)
        print(f"✅ Removed post-commit hook: {post_commit_hook}")
    else:
        print("No post-commit hook found to remove")
    
    return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup git hooks for WordGlobalReplace')
    parser.add_argument('--remove', action='store_true', help='Remove git hooks')
    
    args = parser.parse_args()
    
    if args.remove:
        success = remove_git_hooks()
    else:
        success = setup_git_hooks()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
