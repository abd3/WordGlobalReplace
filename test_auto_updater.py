#!/usr/bin/env python3
"""
Test script for the auto-updater functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_auto_updater():
    """Test the auto-updater functionality"""
    print("Testing Auto-Updater...")
    print("=" * 40)
    
    try:
        from auto_updater import AutoUpdater
        
        # Test with a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Testing in temporary directory: {temp_dir}")
            
            # Create a test updater
            updater = AutoUpdater(
                repo_url="https://github.com/yourusername/WordGlobalReplace.git",  # Replace with actual repo
                current_dir=temp_dir,
                branch="main"
            )
            
            # Test version checking
            print("\\n1. Testing version checking...")
            current_version = updater.get_current_version()
            print(f"Current version: {current_version}")
            
            # Test update check (this will likely fail without a real repo, but that's expected)
            print("\\n2. Testing update check...")
            has_update, current, latest = updater.check_for_updates()
            print(f"Has update: {has_update}")
            print(f"Current: {current}")
            print(f"Latest: {latest}")
            
            # Test dependency installation
            print("\\n3. Testing dependency installation...")
            # Create a test requirements file
            test_req_file = os.path.join(temp_dir, "requirements.txt")
            with open(test_req_file, 'w') as f:
                f.write("requests==2.31.0\\n")
            
            result = updater.install_dependencies()
            print(f"Dependency installation result: {result}")
            
            print("\\n✓ Auto-updater tests completed")
            return True
            
    except ImportError as e:
        print(f"Error importing auto_updater: {e}")
        return False
    except Exception as e:
        print(f"Error during testing: {e}")
        return False

def test_launcher():
    """Test the launcher functionality"""
    print("\\nTesting Launcher...")
    print("=" * 40)
    
    try:
        from launcher import WordGlobalReplaceLauncher
        
        launcher = WordGlobalReplaceLauncher()
        
        # Test dependency checking
        print("1. Testing dependency check...")
        deps_ok = launcher.check_dependencies()
        print(f"Dependencies OK: {deps_ok}")
        
        # Test updater initialization
        print("\\n2. Testing updater initialization...")
        updater_ok = launcher.initialize_updater()
        print(f"Updater initialized: {updater_ok}")
        
        print("\\n✓ Launcher tests completed")
        return True
        
    except ImportError as e:
        print(f"Error importing launcher: {e}")
        return False
    except Exception as e:
        print(f"Error during launcher testing: {e}")
        return False

def main():
    """Main test function"""
    print("WordGlobalReplace - Auto-Updater Test Suite")
    print("=" * 50)
    
    # Test auto-updater
    updater_success = test_auto_updater()
    
    # Test launcher
    launcher_success = test_launcher()
    
    print("\\n" + "=" * 50)
    print("Test Results:")
    print(f"Auto-updater: {'✓ PASS' if updater_success else '✗ FAIL'}")
    print(f"Launcher: {'✓ PASS' if launcher_success else '✗ FAIL'}")
    
    if updater_success and launcher_success:
        print("\\n🎉 All tests passed!")
        return 0
    else:
        print("\\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
