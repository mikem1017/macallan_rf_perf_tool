"""
File readers for power/linearity and noise figure data (CSV and Excel formats)
"""

import csv
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.models.test_data import PowerLinearityData, NoiseFigureData

class CSVReader:
    """Reader for CSV and Excel files containing power/linearity and noise figure data."""
    
    def __init__(self):
        pass
    
    def read_power_linearity_csv(self, file_path: str) -> Optional[PowerLinearityData]:
        """Read power/linearity CSV or Excel file."""
        try:
            # Read file based on extension
            if file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Simple approach: Column C = Frequency, Column F = Pin, Column H = Pout, Column G = Mode
            # Get the basic data
            frequency_mhz = df['Frequency'].tolist()  # Column C
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
            
            # Convert numeric columns to float to handle Excel string data
            def safe_float_convert(value):
                """Safely convert value to float, handling 'OFF' and other non-numeric strings."""
                if pd.isna(value):
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    # Handle common non-numeric values
                    if value.upper() in ['OFF', 'N/A', 'NA', '', ' ']:
                        return None
                    try:
                        return float(value)
                    except ValueError:
                        return None
                return None
            
            # Convert frequency data (should already be numeric)
            frequency_mhz = [float(f) for f in frequency_mhz if f is not None and not pd.isna(f)]
            print(f"DEBUG: frequency_mhz after conversion: {frequency_mhz}")
            
            # Convert all data but keep alignment - don't filter out None values yet
            pin = [safe_float_convert(p) for p in pin]
            pout = [safe_float_convert(p) for p in pout]
            temperature = [safe_float_convert(t) for t in temperature]
            marker1 = [safe_float_convert(m) for m in marker1]
            marker2 = [safe_float_convert(m) for m in marker2]
            marker3 = [safe_float_convert(m) for m in marker3]
            marker4 = [safe_float_convert(m) for m in marker4]
            marker5 = [safe_float_convert(m) for m in marker5]
            marker6 = [safe_float_convert(m) for m in marker6]
            
            # Convert frequency from MHz to GHz
            frequency_ghz = [freq / 1000.0 for freq in frequency_mhz]
            print(f"DEBUG: frequency_ghz after conversion: {frequency_ghz}")
            
            # Ensure all lists have the same length
            min_length = min(len(pin), len(pout), len(mode), len(temperature), 
                           len(marker1), len(marker2), len(marker3), len(marker4), len(marker5), len(marker6))
            
            # Truncate all lists to the same length
            pin = pin[:min_length]
            pout = pout[:min_length]
            mode = mode[:min_length]
            temperature = temperature[:min_length]
            marker1 = marker1[:min_length]
            marker2 = marker2[:min_length]
            marker3 = marker3[:min_length]
            marker4 = marker4[:min_length]
            marker5 = marker5[:min_length]
            marker6 = marker6[:min_length]
            
            # Create 6 arrays: PRI-2200, PRI-2240, PRI-2280, RED-2200, RED-2240, RED-2280
            # First, get unique frequencies
            unique_frequencies = list(set(frequency_mhz))
            unique_frequencies.sort()  # Sort to ensure consistent order
            
            # Create dictionaries to store data for each frequency
            freq_data = {}
            for freq in unique_frequencies:
                freq_data[freq] = {
                    'single_tone_pin': [],
                    'single_tone_pout': [],
                    'two_tone_pin': [],
                    'two_tone_im3_lower': [],
                    'two_tone_im3_upper': [],
                    'two_tone_im5_lower': [],
                    'two_tone_im5_upper': [],
                    'two_tone_im3': [],  # Combined for backward compatibility
                    'two_tone_im5': []   # Combined for backward compatibility
                }
            
            # Process each row and group by frequency
            for i in range(len(pin)):
                if pin[i] is not None:  # Skip "OFF" values
                    freq = frequency_mhz[i]
                    if freq in freq_data:
                        if mode[i] == "Single Tone":
                            freq_data[freq]['single_tone_pin'].append(pin[i])
                            freq_data[freq]['single_tone_pout'].append(pout[i])
                        elif mode[i] == "Two Tone":
                            freq_data[freq]['two_tone_pin'].append(pin[i])
                            # Store separate upper and lower sidebands
                            freq_data[freq]['two_tone_im3_lower'].append(marker3[i] if marker3[i] is not None else 0.0)
                            freq_data[freq]['two_tone_im3_upper'].append(marker4[i] if marker4[i] is not None else 0.0)
                            freq_data[freq]['two_tone_im5_lower'].append(marker5[i] if marker5[i] is not None else 0.0)
                            freq_data[freq]['two_tone_im5_upper'].append(marker6[i] if marker6[i] is not None else 0.0)
                            # Also store combined for backward compatibility
                            freq_data[freq]['two_tone_im3'].append(max(marker3[i], marker4[i]) if marker3[i] is not None and marker4[i] is not None else 0.0)
                            freq_data[freq]['two_tone_im5'].append(max(marker5[i], marker6[i]) if marker5[i] is not None and marker6[i] is not None else 0.0)
            
            # For backward compatibility, create combined lists
            single_tone_pin = []
            single_tone_pout = []
            two_tone_pin = []
            two_tone_im3 = []
            two_tone_im5 = []
            
            for freq in unique_frequencies:
                single_tone_pin.extend(freq_data[freq]['single_tone_pin'])
                single_tone_pout.extend(freq_data[freq]['single_tone_pout'])
                two_tone_pin.extend(freq_data[freq]['two_tone_pin'])
                two_tone_im3.extend(freq_data[freq]['two_tone_im3'])
                two_tone_im5.extend(freq_data[freq]['two_tone_im5'])
            
            pout_single_tone = single_tone_pout.copy()
            im3_data = [0.0] * len(single_tone_pin) + two_tone_im3  # No IM3 for single-tone
            im5_data = [0.0] * len(single_tone_pin) + two_tone_im5  # No IM5 for single-tone
            test_type = ["single-tone"] * len(single_tone_pin) + ["two-tone"] * len(two_tone_pin)
            
            return PowerLinearityData(
                frequency=frequency_ghz,
                pin=pin,
                pout_single_tone=pout_single_tone,
                im3=im3_data,
                im5=im5_data,
                test_type=test_type,
                single_tone_pin=single_tone_pin,
                single_tone_pout=single_tone_pout,
                two_tone_pin=two_tone_pin,
                two_tone_im3=two_tone_im3,
                two_tone_im5=two_tone_im5,
                freq_data=freq_data  # Store the frequency-specific data
            )
            
        except Exception as e:
            print(f"Error reading power/linearity file {file_path}: {e}")
            return None
    
    def read_noise_figure_csv(self, file_path: str) -> Optional[NoiseFigureData]:
        """Read noise figure CSV or Excel file."""
        try:
            # Read file based on extension
            if file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Extract frequency and noise figure data
            # Note: This is a placeholder - we need the actual column structure
            frequency = df['Frequency'].tolist()  # Assuming frequency column exists
            nf = df['Noise Figure'].tolist()  # Assuming NF column exists
            
            # Convert numeric columns to float to handle Excel string data
            try:
                frequency = [float(f) for f in frequency if pd.notna(f)]
                nf = [float(n) for n in nf if pd.notna(n)]
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not convert some numeric data to float: {e}")
                # Continue with original data - let the processor handle any remaining issues
            
            # Convert frequency to GHz if needed
            frequency_ghz = [freq / 1000.0 if freq > 100 else freq for freq in frequency]
            
            return NoiseFigureData(
                frequency=frequency_ghz,
                nf=nf
            )
            
        except Exception as e:
            print(f"Error reading noise figure file {file_path}: {e}")
            return None
    
    def extract_csv_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from CSV or Excel file."""
        try:
            # Read first few rows to get metadata
            if file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, nrows=1)
            else:
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
            print(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def validate_csv_structure(self, file_path: str, file_type: str) -> Tuple[bool, str]:
        """Validate CSV or Excel file structure."""
        try:
            # Read first 5 rows for validation
            if file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, nrows=5)
            else:
                df = pd.read_csv(file_path, nrows=5)
            
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
            return False, f"Error validating file: {e}"

