#!/usr/bin/env python3
"""
Simple startup script for WordGlobalReplace
This is the main entry point for users
"""

import sys
import os
from pathlib import Path

def main():
    """Main startup function"""
    print("WordGlobalReplace - Starting...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        # Import and run the launcher
        from launcher import WordGlobalReplaceLauncher
        
        launcher = WordGlobalReplaceLauncher()
        
        # You can configure the repository URL here for auto-updates
        # Replace with your actual GitHub repository URL
        repo_url = None  # Set to your GitHub repo URL, e.g., "https://github.com/abd3/WordGlobalReplace.git"
        
        launcher.run(repo_url=repo_url, auto_update=True)
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Please ensure all required files are present.")
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
