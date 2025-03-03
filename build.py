#!/usr/bin/env python3
"""
Build script for creating a standalone executable of the Repo Opener application
using PyInstaller.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Application name
APP_NAME = "repo-opener"

# Script to build
SCRIPT_PATH = "repo_opener.py"

# Output directory
DIST_DIR = "dist"

def main():
    """Main build function"""
    print(f"Building {APP_NAME} executable...")
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",  # Create a single executable file
        "--clean",    # Clean PyInstaller cache
        "--noconfirm",  # Replace output directory without asking
    ]
    
    # Add windowed mode for GUI application
    cmd.append("--windowed")
    
    # Check for icon file
    icon_path = Path("icon.png")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Add Linux-specific options
    if platform.system() == "Linux":
        # Add hidden imports for Linux
        cmd.extend(["--hidden-import", "PyQt6.QtSvg"])
        cmd.extend(["--hidden-import", "PyQt6.QtCore"])
        cmd.extend(["--hidden-import", "PyQt6.QtGui"])
        cmd.extend(["--hidden-import", "PyQt6.QtWidgets"])
    
    # Add the script to build
    cmd.append(SCRIPT_PATH)
    
    # Execute PyInstaller
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print(f"Error: PyInstaller failed with exit code {result.returncode}")
        return result.returncode
    
    print(f"Build completed successfully!")
    print(f"Executable created at: {os.path.join(DIST_DIR, APP_NAME)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())