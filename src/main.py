"""
Main entry point for Macallan RF Performance Tool
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.views.main_window import MainWindow
from src.version import get_version

def main():
    """Main application entry point."""
    # Enable high DPI scaling (PyQt6 compatibility)
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # PyQt6 doesn't have these attributes, skip them
        pass
    
    app = QApplication(sys.argv)
    app.setApplicationName("Macallan RF Performance Tool")
    app.setApplicationVersion(get_version())
    app.setOrganizationName("Macallan")
    
    # Create main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
