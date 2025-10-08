#!/usr/bin/env python3
"""
Unit tests for auto_updater.py
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_updater import AutoUpdater

class TestAutoUpdater(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.updater = AutoUpdater(
            repo_url="https://github.com/test/test-repo.git",
            current_dir=self.temp_dir,
            branch="main"
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test AutoUpdater initialization"""
        self.assertEqual(self.updater.repo_url, "https://github.com/test/test-repo.git")
        self.assertEqual(self.updater.current_dir, self.temp_dir)
        self.assertEqual(self.updater.branch, "main")
        self.assertIsNotNone(self.updater.version_file)
        self.assertIsNotNone(self.updater.update_log)
    
    def test_get_current_version_from_file(self):
        """Test getting current version from version file"""
        # Create a version file
        with open(self.updater.version_file, 'w') as f:
            f.write("abc123def456")
        
        version = self.updater.get_current_version()
        self.assertEqual(version, "abc123def456")
    
    def test_get_current_version_unknown(self):
        """Test getting current version when no version file exists"""
        version = self.updater.get_current_version()
        self.assertEqual(version, "unknown")
    
    @patch('auto_updater.subprocess.run')
    def test_get_current_version_from_git(self, mock_run):
        """Test getting current version from git"""
        # Mock git command to return a commit hash
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "abc123def456"
        
        # Remove version file to force git check
        if os.path.exists(self.updater.version_file):
            os.remove(self.updater.version_file)
        
        version = self.updater.get_current_version()
        self.assertEqual(version, "abc123def456")
    
    @patch('auto_updater.urllib.request.urlopen')
    def test_get_latest_version_via_api(self, mock_urlopen):
        """Test getting latest version via GitHub API"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"sha": "def456ghi789", "parents": [{"sha": "parent123"}]}'
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        version = self.updater.get_latest_version()
        self.assertEqual(version, "parent123")
    
    @patch('auto_updater.urllib.request.urlopen')
    def test_get_latest_version_via_api_no_parents(self, mock_urlopen):
        """Ensure API fallback uses commit sha when parents missing"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"sha": "def456ghi789", "parents": []}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = self.updater.get_latest_version()
        self.assertEqual(version, "def456ghi789")
    
    @patch('auto_updater.subprocess.run')
    def test_get_latest_version_via_git(self, mock_run):
        """Test getting latest version via git clone"""
        # Mock git clone command
        clone_result = MagicMock()
        clone_result.returncode = 0
        clone_result.stdout = ""

        rev_parse_parent = MagicMock()
        rev_parse_parent.returncode = 0
        rev_parse_parent.stdout = "parent123\n"

        rev_parse_head = MagicMock()
        rev_parse_head.returncode = 0
        rev_parse_head.stdout = "def456ghi789\n"

        def side_effect(cmd, *args, **kwargs):
            if isinstance(cmd, (list, tuple)) and "rev-parse" in cmd:
                if cmd[-1] == "HEAD^":
                    return rev_parse_parent
                return rev_parse_head
            return clone_result

        mock_run.side_effect = side_effect
        
        version = self.updater.get_latest_version()
        self.assertEqual(version, "parent123")
    
    def test_check_for_updates_no_update(self):
        """Test check for updates when no update is available"""
        with patch.object(self.updater, 'get_current_version', return_value="abc123"):
            with patch.object(self.updater, 'get_latest_version', return_value="abc123"):
                has_update, current, latest = self.updater.check_for_updates()
                
                self.assertFalse(has_update)
                self.assertEqual(current, "abc123")
                self.assertEqual(latest, "abc123")
    
    def test_check_for_updates_available(self):
        """Test check for updates when update is available"""
        with patch.object(self.updater, 'get_current_version', return_value="abc123"):
            with patch.object(self.updater, 'get_latest_version', return_value="def456"):
                has_update, current, latest = self.updater.check_for_updates()
                
                self.assertTrue(has_update)
                self.assertEqual(current, "abc123")
                self.assertEqual(latest, "def456")
    
    def test_check_for_updates_error(self):
        """Test check for updates when error occurs"""
        with patch.object(self.updater, 'get_latest_version', return_value=None):
            has_update, current, latest = self.updater.check_for_updates()
            
            self.assertFalse(has_update)
            self.assertIsNone(current)
            self.assertIsNone(latest)
    
    @patch('auto_updater.subprocess.run')
    @patch('auto_updater.shutil')
    def test_update_application(self, mock_shutil, mock_run):
        """Test application update process"""
        # Mock successful git clone
        mock_run.return_value.returncode = 0
        
        # Mock get_latest_version
        with patch.object(self.updater, 'get_latest_version', return_value="def456"):
            result = self.updater.update_application()
            
            self.assertTrue(result)
            
            # Check that version file was written
            self.assertTrue(os.path.exists(self.updater.version_file))
            with open(self.updater.version_file, 'r') as f:
                self.assertEqual(f.read().strip(), "def456")
    
    @patch('auto_updater.subprocess.run')
    def test_install_dependencies(self, mock_run):
        """Test dependency installation"""
        # Create a requirements file
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, 'w') as f:
            f.write("requests==2.31.0\n")
        
        # Mock successful pip install
        mock_run.return_value.returncode = 0
        
        result = self.updater.install_dependencies()
        self.assertTrue(result)
        
        # Verify pip install was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("pip", args)
        self.assertIn("install", args)
        self.assertIn("-r", args)
    
    @patch('auto_updater.subprocess.run')
    def test_install_dependencies_failure(self, mock_run):
        """Test dependency installation failure"""
        # Create a requirements file
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, 'w') as f:
            f.write("requests==2.31.0\n")
        
        # Mock failed pip install
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Package not found"
        
        result = self.updater.install_dependencies()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
