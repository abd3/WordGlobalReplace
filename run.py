#!/usr/bin/env python3
"""
Startup script for Global Word Document Find & Replace Application
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from config import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_LOCAL_URL


def _setup_signal_handlers():
    """Ensure SIGTERM shuts down the server cleanly."""

    def _handle_sigterm(signum, frame):  # pragma: no cover - simple exit hook
        print("\nReceived termination signal. Shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)


def _start_parent_watchdog():
    """Exit automatically if the launcher process disappears."""
    parent_env = os.environ.get("WORD_GLOBAL_REPLACE_PARENT_PID")
    if not parent_env:
        return

    try:
        expected_ppid = int(parent_env)
    except ValueError:
        return

    def _watch_parent():  # pragma: no cover - watchdog
        while True:
            if os.getppid() != expected_ppid:
                # Parent exited (likely via Force Quit); stop immediately.
                os._exit(0)
            time.sleep(1.0)

    thread = threading.Thread(target=_watch_parent, daemon=True)
    thread.start()


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask  # noqa: F401  # pragma: no cover - import check only
        from docx import Document  # noqa: F401
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Main startup function."""
    print("Global Word Document Find & Replace")
    print("=" * 40)

    _setup_signal_handlers()
    _start_parent_watchdog()

    # Check if dependencies are installed
    if not check_dependencies():
        print("Dependencies not found. Installing...")
        if not install_dependencies():
            print("Failed to install dependencies. Please run:")
            print("  python3 -m pip install --user -r requirements.txt")
            return 1
        print("Dependencies installed successfully!")

    # Check if required files exist
    required_files = ['app.py', 'templates/index.html', 'static/style.css', 'static/script.js']
    missing_files = [f for f in required_files if not Path(f).exists()]

    if missing_files:
        print(f"Missing required files: {', '.join(missing_files)}")
        return 1

    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('backups', exist_ok=True)

    print("Starting the application...")
    print(f"Open your browser and go to: {DEFAULT_LOCAL_URL}")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)

    # Start the Flask application
    try:
        from app import app
        app.run(debug=True, host=DEFAULT_HOST, port=DEFAULT_PORT)
    except KeyboardInterrupt:
        print("\nApplication stopped.")
        return 0
    except Exception as exc:
        print(f"Error starting application: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
