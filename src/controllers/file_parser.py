"""
File parsing and metadata extraction
"""

import re
import os
from typing import List, Dict, Optional, Tuple
from src.models.test_data import FileMetadata

class FileParser:
    """Parser for extracting metadata from filenames and loading data files."""
    
    def __init__(self):
        # Regex patterns for filename parsing
        self.date_pattern = re.compile(r'(\d{8})')  # YYYYMMDD
        self.serial_pattern = re.compile(r'(SN\d+)', re.IGNORECASE)
        self.part_pattern = re.compile(r'(L\d{4,6})', re.IGNORECASE)  # Allow 4-6 digits
        self.pri_red_pattern = re.compile(r'_(PRI|RED)(?:_|\.)', re.IGNORECASE)  # Allow _PRI_ or _PRI.
        self.hg_lg_pattern = re.compile(r'_(HG|LG)(?:_|\.)', re.IGNORECASE)  # Allow _HG_ or _HG.
    
    def parse_filename(self, filename: str) -> Optional[FileMetadata]:
        """Parse filename to extract metadata."""
        basename = os.path.basename(filename)
        
        # Extract date (YYYYMMDD)
        date_match = self.date_pattern.search(basename)
        if not date_match:
            return None
        date_code = date_match.group(1)
        
        # Extract serial number (SNXXXX)
        serial_match = self.serial_pattern.search(basename)
        if not serial_match:
            return None
        serial_number = serial_match.group(1).upper()
        
        # Extract part number (LXXXXXX)
        part_match = self.part_pattern.search(basename)
        if not part_match:
            return None
        part_number = part_match.group(1).upper()
        
        # Extract PRI/RED
        pri_red_match = self.pri_red_pattern.search(basename)
        if not pri_red_match:
            return None
        pri_red = pri_red_match.group(1).upper()
        
        # Extract HG/LG (optional)
        hg_lg_match = self.hg_lg_pattern.search(basename)
        hg_lg = hg_lg_match.group(1).upper() if hg_lg_match else None
        
        return FileMetadata(
            date_code=date_code,
            serial_number=serial_number,
            part_number=part_number,
            pri_red=pri_red,
            hg_lg=hg_lg
        )
    
    def validate_file_set(self, files: List[str], hg_lg_enabled: bool) -> Tuple[bool, str, List[FileMetadata]]:
        """Validate that the file set is complete and correctly parsed."""
        if not files:
            return False, "No files selected", []
        
        # Parse all files
        metadata_list = []
        for file_path in files:
            metadata = self.parse_filename(file_path)
            if not metadata:
                return False, f"Could not parse filename: {os.path.basename(file_path)}", []
            metadata_list.append(metadata)
        
        # Check for required files
        if hg_lg_enabled:
            # Need 4 files: PRI HG, PRI LG, RED HG, RED LG
            if len(metadata_list) != 4:
                return False, "HG/LG enabled DUT requires exactly 4 files", metadata_list
            
            # Check for all required combinations
            required_combinations = [
                ("PRI", "HG"), ("PRI", "LG"), ("RED", "HG"), ("RED", "LG")
            ]
            
            found_combinations = []
            for metadata in metadata_list:
                found_combinations.append((metadata.pri_red, metadata.hg_lg))
            
            for required in required_combinations:
                if required not in found_combinations:
                    return False, f"Missing file for {required[0]} {required[1]}", metadata_list
        else:
            # Need 2 files: PRI, RED
            if len(metadata_list) != 2:
                return False, "DUT requires exactly 2 files (PRI and RED)", metadata_list
            
            # Check for PRI and RED
            pri_red_values = [m.pri_red for m in metadata_list]
            if "PRI" not in pri_red_values or "RED" not in pri_red_values:
                return False, "Missing PRI or RED file", metadata_list
        
        return True, "File set is valid", metadata_list
    
    def group_files_by_type(self, metadata_list: List[FileMetadata]) -> Dict[str, FileMetadata]:
        """Group files by their type (PRI, RED, etc.)."""
        grouped = {}
        
        for metadata in metadata_list:
            if metadata.hg_lg:
                key = f"{metadata.pri_red}_{metadata.hg_lg}"
            else:
                key = metadata.pri_red
            
            grouped[key] = metadata
        
        return grouped
    
    def get_file_for_metadata(self, files: List[str], target_metadata: FileMetadata) -> Optional[str]:
        """Get the file path for a specific metadata."""
        for file_path in files:
            metadata = self.parse_filename(file_path)
            if (metadata and 
                metadata.date_code == target_metadata.date_code and
                metadata.serial_number == target_metadata.serial_number and
                metadata.part_number == target_metadata.part_number and
                metadata.pri_red == target_metadata.pri_red and
                metadata.hg_lg == target_metadata.hg_lg):
                return file_path
        return None
