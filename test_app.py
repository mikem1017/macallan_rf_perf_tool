"""
Test script for Macallan RF Performance Tool
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from src.main import main

def test_application():
    """Test the application startup."""
    print("Testing Macallan RF Performance Tool...")
    
    try:
        # Test imports
        print("Testing imports...")
        from src.models.dut_config import DUTConfigManager
        from src.controllers.file_parser import FileParser
        from src.utils.touchstone_reader import TouchstoneReader
        from src.utils.csv_reader import CSVReader
        from src.controllers.sparam_processor import SParameterProcessor
        from src.controllers.power_processor import PowerProcessor
        from src.controllers.nf_processor import NoiseFigureProcessor
        print("+ All imports successful")
        
        # Test DUT configuration loading
        print("Testing DUT configuration...")
        config_manager = DUTConfigManager()
        dut_list = config_manager.list_duts()
        print(f"+ Loaded {len(dut_list)} DUT configurations")
        
        # Test file parser
        print("Testing file parser...")
        file_parser = FileParser()
        print("+ File parser initialized")
        
        # Test Touchstone reader
        print("Testing Touchstone reader...")
        touchstone_reader = TouchstoneReader()
        print("+ Touchstone reader initialized")
        
        # Test CSV reader
        print("Testing CSV reader...")
        csv_reader = CSVReader()
        print("+ CSV reader initialized")
        
        # Test processors
        print("Testing processors...")
        sparam_processor = SParameterProcessor()
        power_processor = PowerProcessor()
        nf_processor = NoiseFigureProcessor()
        print("+ All processors initialized")
        
        print("\n+ All tests passed!")
        print("\nTo run the full application:")
        print("python src/main.py")
        
        return True
        
    except Exception as e:
        print(f"- Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_application()
    sys.exit(0 if success else 1)
