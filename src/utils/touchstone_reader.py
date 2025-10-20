"""
Touchstone file reader utilities using scikit-rf
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from src.models.test_data import SParameterData
import skrf as rf

class TouchstoneReader:
    """Reader for Touchstone (.s1p, .s2p, .s3p, .s4p) files using scikit-rf."""
    
    def __init__(self):
        pass
    
    def read_touchstone_file(self, file_path: str) -> Optional[SParameterData]:
        """Read a Touchstone file and return S-parameter data."""
        try:
            # Use scikit-rf to read the Touchstone file
            network = rf.Network(file_path)
            
            # Extract frequency data (convert to GHz)
            frequencies = network.f / 1e9  # Convert Hz to GHz
            
            # Extract S-parameters
            s_parameters = {}
            num_ports = network.nports
            
            # Create S-parameter dictionary
            for i in range(num_ports):
                for j in range(num_ports):
                    s_param_name = f"S{i+1}{j+1}"
                    s_parameters[s_param_name] = network.s[:, i, j]
            
            # Determine format from network properties
            format_type = "mag/deg"  # Default, scikit-rf handles conversion internally
            
            return SParameterData(
                frequency=frequencies.tolist(),
                s_parameters=s_parameters,
                format=format_type
            )
            
        except Exception as e:
            print(f"Error reading Touchstone file {file_path}: {e}")
            return None
    
    def validate_touchstone_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate Touchstone file using scikit-rf."""
        try:
            network = rf.Network(file_path)
            
            # Basic validation
            if network.nports < 1 or network.nports > 4:
                return False, f"Unsupported number of ports: {network.nports}"
            
            if len(network.f) == 0:
                return False, "No frequency data found"
            
            return True, f"Valid {network.nports}-port Touchstone file with {len(network.f)} frequency points"
            
        except Exception as e:
            return False, f"Invalid Touchstone file: {e}"
