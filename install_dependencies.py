#!/usr/bin/env python3
"""
Install Missing Dependencies
Fix all dependency issues for MCP system
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install all required dependencies."""
    print("🔧 INSTALLING MISSING DEPENDENCIES")
    print("=" * 50)
    
    # Required packages
    packages = [
        "rapidfuzz",
        "pymongo",
        "requests",
        "python-dotenv",
        "fastapi",
        "uvicorn",
        "langchain",
        "langchain-community",
        "langchain-core",
        "pytesseract",
        "Pillow",
        "opencv-python",
        "PyPDF2",
        "python-multipart"
    ]
    
    installed = 0
    failed = 0
    
    for package in packages:
        print(f"📦 Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
            installed += 1
        else:
            print(f"❌ {package} installation failed")
            failed += 1
    
    print(f"\n📊 Installation Results:")
    print(f"✅ Installed: {installed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All dependencies installed successfully!")
    else:
        print(f"\n⚠️ {failed} packages failed to install")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    if success:
        print("🚀 Ready to connect all agents!")
    else:
        print("🔧 Some dependencies need manual installation")
