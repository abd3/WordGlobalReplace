#!/usr/bin/env python3
"""
Test script to verify the Global Word Document Find & Replace setup
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so imports work when run from tests/manual
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DEFAULT_LOCAL_URL

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        from docx import Document
        print("✓ python-docx imported successfully")
    except ImportError as e:
        print(f"✗ python-docx import failed: {e}")
        return False
    
    try:
        from advanced_word_processor import AdvancedWordProcessor
        print("✓ AdvancedWordProcessor imported successfully")
    except ImportError as e:
        print(f"✗ AdvancedWordProcessor import failed: {e}")
        return False
    
    return True

def test_directories():
    """Test if required directories exist or can be created"""
    print("\nTesting directories...")
    
    required_dirs = ['templates', 'static', 'backups']
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✓ {dir_name}/ directory exists")
        else:
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✓ {dir_name}/ directory created")
            except Exception as e:
                print(f"✗ Failed to create {dir_name}/ directory: {e}")
                return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\nTesting files...")
    
    required_files = [
        'app.py',
        'advanced_word_processor.py',
        'word_processor.py',
        'templates/index.html',
        'static/style.css',
        'static/script.js',
        'requirements.txt',
        'README.md'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            return False
    
    return True

def test_word_processor():
    """Test basic Word processor functionality"""
    print("\nTesting Word processor...")
    
    try:
        from advanced_word_processor import AdvancedWordProcessor
        processor = AdvancedWordProcessor()
        
        # Test if processor can be instantiated
        print("✓ AdvancedWordProcessor instantiated successfully")
        
        # Test file type detection
        test_files = [
            'test.docx',
            'test.doc',
            'test.txt',
            'test.pdf'
        ]
        
        for test_file in test_files:
            is_word = processor.is_word_file(test_file)
            expected = test_file.endswith(('.docx', '.doc'))
            if is_word == expected:
                print(f"✓ File type detection works for {test_file}")
            else:
                print(f"✗ File type detection failed for {test_file}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Word processor test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Global Word Document Find & Replace - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_directories,
        test_files,
        test_word_processor
    ]
    
    all_passed = True
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! The application should work correctly.")
        print("\nTo run the application:")
        print("  python app.py")
        print(f"Then open: {DEFAULT_LOCAL_URL}")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTo install missing dependencies:")
        print("  python3 -m pip install --user -r requirements.txt")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
