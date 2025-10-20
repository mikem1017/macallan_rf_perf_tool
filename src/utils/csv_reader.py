"""
CSV readers for power/linearity and noise figure data
"""

import csv
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.models.test_data import PowerLinearityData, NoiseFigureData

class CSVReader:
    """Reader for CSV files containing power/linearity and noise figure data."""
    
    def __init__(self):
        pass
    
    def read_power_linearity_csv(self, file_path: str) -> Optional[PowerLinearityData]:
        """Read power/linearity CSV file."""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Extract columns based on the structure we discussed
            frequency_mhz = df['Frequency'].unique()  # Column C
            pin = df['Power Level (dBm)'].tolist()  # Column F
            pout = df['Power Meter (dBm)'].tolist()  # Column H
            mode = df['Mode'].tolist()  # Column G
            temperature = df['Thermister Calc (C)'].tolist()  # Column J
            
            # Extract marker data (only for two-tone)
            marker1 = df['Marker 1 (dBm)'].tolist()  # Column K
            marker2 = df['Marker 2 (dBm)'].tolist()  # Column L
            marker3 = df['Marker 3 (dBm)'].tolist()  # Column M (IM3 lower)
            marker4 = df['Marker 4 (dBm)'].tolist()  # Column N (IM3 upper)
            marker5 = df['Marker 5 (dBm)'].tolist()  # Column O (IM5 lower)
            marker6 = df['Marker 6 (dBm)'].tolist()  # Column P (IM5 upper)
            
            # Convert frequency to GHz
            frequency_ghz = [freq / 1000.0 for freq in frequency_mhz]
            
            # Separate single-tone and two-tone data
            single_tone_indices = [i for i, m in enumerate(mode) if m == "Single Tone"]
            two_tone_indices = [i for i, m in enumerate(mode) if m == "Two Tone"]
            
            # For single-tone data, we need to interpolate Pout for two-tone Pin levels
            # This is a simplified approach - in practice, you might need more sophisticated interpolation
            pout_single_tone = []
            im3_data = []
            im5_data = []
            test_type = []
            
            for i in range(len(pin)):
                if i in single_tone_indices:
                    pout_single_tone.append(pout[i])
                    im3_data.append(0.0)  # No IM3 for single-tone
                    im5_data.append(0.0)  # No IM5 for single-tone
                    test_type.append("single-tone")
                else:
                    # For two-tone, use the single-tone Pout at the same Pin level
                    # This is a simplification - you might need interpolation
                    pout_single_tone.append(pout[i])
                    im3_data.append(max(marker3[i], marker4[i]))  # Worst-case IM3
                    im5_data.append(max(marker5[i], marker6[i]))  # Worst-case IM5
                    test_type.append("two-tone")
            
            return PowerLinearityData(
                frequency=frequency_ghz,
                pin=pin,
                pout_single_tone=pout_single_tone,
                im3=im3_data,
                im5=im5_data,
                test_type=test_type
            )
            
        except Exception as e:
            print(f"Error reading power/linearity CSV file {file_path}: {e}")
            return None
    
    def read_noise_figure_csv(self, file_path: str) -> Optional[NoiseFigureData]:
        """Read noise figure CSV file."""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Extract frequency and noise figure data
            # Note: This is a placeholder - we need the actual column structure
            frequency = df['Frequency'].tolist()  # Assuming frequency column exists
            nf = df['Noise Figure'].tolist()  # Assuming NF column exists
            
            # Convert frequency to GHz if needed
            frequency_ghz = [freq / 1000.0 if freq > 100 else freq for freq in frequency]
            
            return NoiseFigureData(
                frequency=frequency_ghz,
                nf=nf
            )
            
        except Exception as e:
            print(f"Error reading noise figure CSV file {file_path}: {e}")
            return None
    
    def extract_csv_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from CSV file."""
        try:
            # Read first few rows to get metadata
            df = pd.read_csv(file_path, nrows=1)
            
            metadata = {}
            
            # Extract serial number
            if 'Serial Number' in df.columns:
                metadata['serial'] = df['Serial Number'].iloc[0]
            
            # Extract temperature
            if 'Temp' in df.columns:
                metadata['temperature'] = df['Temp'].iloc[0]
            
            # Extract frequency
            if 'Frequency' in df.columns:
                metadata['frequency'] = df['Frequency'].iloc[0]
            
            # Extract chain (PRI/RED)
            if 'Chain' in df.columns:
                metadata['pri_red'] = df['Chain'].iloc[0]
            
            # Extract timestamp and convert to date
            if 'Timestamp' in df.columns:
                timestamp_str = df['Timestamp'].iloc[0]
                try:
                    # Parse timestamp and extract date
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    metadata['date'] = dt.strftime("%Y-%m-%d")
                except ValueError:
                    metadata['date'] = timestamp_str
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting CSV metadata from {file_path}: {e}")
            return {}
    
    def validate_csv_structure(self, file_path: str, file_type: str) -> Tuple[bool, str]:
        """Validate CSV file structure."""
        try:
            df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows for validation
            
            if file_type == "power_linearity":
                required_columns = [
                    'Serial Number', 'Temp', 'Frequency', 'Chain', 'Timestamp',
                    'Power Level (dBm)', 'Mode', 'Power Meter (dBm)', 'Thermister Calc (C)',
                    'Marker 1 (dBm)', 'Marker 2 (dBm)', 'Marker 3 (dBm)', 
                    'Marker 4 (dBm)', 'Marker 5 (dBm)', 'Marker 6 (dBm)'
                ]
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return False, f"Missing required columns: {', '.join(missing_columns)}"
                
                # Check for required modes
                if 'Mode' in df.columns:
                    modes = df['Mode'].unique()
                    if 'Single Tone' not in modes:
                        return False, "No 'Single Tone' data found"
                    if 'Two Tone' not in modes:
                        return False, "No 'Two Tone' data found"
                
                return True, "CSV structure is valid"
            
            elif file_type == "noise_figure":
                # Placeholder for noise figure validation
                # We need the actual column structure first
                return True, "Noise figure validation not yet implemented"
            
            return False, f"Unknown file type: {file_type}"
            
        except Exception as e:
            return False, f"Error validating CSV file: {e}"

