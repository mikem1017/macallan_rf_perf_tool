"""
PyInstaller build script for Macallan RF Performance Tool
"""

import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller."""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Don't show console window
        "--name=Macallan_RF_Tool",
        "--add-data=config;config",  # Include config directory
        "--add-data=src;src",  # Include src directory
        "--hidden-import=PyQt6",
        "--hidden-import=matplotlib",
        "--hidden-import=numpy",
        "--hidden-import=pandas",
        "--hidden-import=scipy",
        "--hidden-import=reportlab",
        "--hidden-import=skrf",
        "--collect-all=matplotlib",
        "--collect-all=numpy",
        "--collect-all=pandas",
        "--collect-all=scipy",
        "--collect-all=PyQt6",
        "--collect-all=reportlab",
        "--collect-all=skrf",
        "src/main.py"
    ]
    
    # Add version info
    version_info = f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 1, 0, 0),
    prodvers=(0, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Macallan'),
        StringStruct(u'FileDescription', u'Macallan RF Performance Visualization Tool'),
        StringStruct(u'FileVersion', u'0.1.0'),
        StringStruct(u'InternalName', u'Macallan_RF_Tool'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2025 Macallan'),
        StringStruct(u'OriginalFilename', u'Macallan_RF_Tool.exe'),
        StringStruct(u'ProductName', u'Macallan RF Performance Tool'),
        StringStruct(u'ProductVersion', u'0.1.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    # Write version info to file
    version_file = project_root / "version_info.txt"
    with open(version_file, 'w') as f:
        f.write(version_info)
    
    # Add version file to command
    cmd.extend(["--version-file=version_info.txt"])
    
    print("Building executable with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=project_root, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created in: {project_root / 'dist' / 'Macallan_RF_Tool.exe'}")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    
    except FileNotFoundError:
        print("PyInstaller not found. Please install it with: pip install pyinstaller")
        return False
    
    finally:
        # Clean up version file
        if version_file.exists():
            version_file.unlink()
    
    return True

def create_installer():
    """Create an installer using NSIS (optional)."""
    print("\nTo create an installer, you can use NSIS or Inno Setup.")
    print("The executable is located in the 'dist' directory.")

if __name__ == "__main__":
    print("Macallan RF Performance Tool - Build Script")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build the executable
    if build_executable():
        print("\nBuild completed successfully!")
        create_installer()
    else:
        print("\nBuild failed!")
        sys.exit(1)
