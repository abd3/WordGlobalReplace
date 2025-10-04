"""Shared configuration values for WordGlobalReplace."""

import os

# Host and port can be overridden for local customization
DEFAULT_HOST = os.getenv("WORD_GLOBAL_REPLACE_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("WORD_GLOBAL_REPLACE_PORT", "5130"))
DEFAULT_REPO_URL = os.getenv("WORD_GLOBAL_REPLACE_REPO_URL", "https://github.com/abd3/WordGlobalReplace.git")

DEFAULT_LOCAL_URL = f"http://localhost:{DEFAULT_PORT}"
