"""
S-parameter processing and calculations
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from src.models.test_data import SParameterData
from src.models.dut_config import DUTConfiguration, TestStageRequirements, OutOfBandRequirement
from src.constants import TEST_STAGES, DEFAULT_TEST_STAGE, PLOT_EXPANSION_FACTOR, VSWR_Y_AXIS_EXPANSION_FACTOR

class SParameterProcessor:
    """Processor for S-parameter calculations and analysis."""
    
    def __init__(self):
        pass
    
    def calculate_gain(self, s_param: List[complex]) -> List[float]:
        """Calculate gain in dB from S-parameter magnitude."""
        return [20 * np.log10(abs(s)) for s in s_param]
    
    def calculate_vswr(self, s11: List[complex]) -> List[float]:
        """Calculate VSWR from S11 reflection coefficient."""
        vswr = []
        for s in s11:
            magnitude = abs(s)
            if magnitude >= 1.0:
                # Cap at reasonable maximum instead of infinity
                vswr.append(1000.0)  # Very high VSWR but finite
            else:
                vswr.append((1 + magnitude) / (1 - magnitude))
        return vswr
    
    def find_frequency_range_indices(self, frequencies: List[float], 
                                   freq_min: float, freq_max: float) -> Tuple[int, int]:
        """Find indices for a frequency range."""
        freq_array = np.array(frequencies)
        min_idx = np.argmin(np.abs(freq_array - freq_min))
        max_idx = np.argmin(np.abs(freq_array - freq_max))
        
        # Ensure min_idx <= max_idx
        if min_idx > max_idx:
            min_idx, max_idx = max_idx, min_idx
        
        return min_idx, max_idx
    
    def calculate_in_band_gain(self, frequencies: List[float], gain: List[float],
                             freq_min: float, freq_max: float) -> Dict[str, float]:
        """Calculate in-band gain statistics."""
        min_idx, max_idx = self.find_frequency_range_indices(frequencies, freq_min, freq_max)
        
        gain_in_band = gain[min_idx:max_idx+1]
        
        return {
            'min_gain': min(gain_in_band),
            'max_gain': max(gain_in_band),
            'flatness': max(gain_in_band) - min(gain_in_band)
        }
    
    def calculate_vswr_max(self, frequencies: List[float], vswr: List[float],
                          freq_min: float, freq_max: float) -> float:
        """Calculate maximum VSWR in frequency range."""
        min_idx, max_idx = self.find_frequency_range_indices(frequencies, freq_min, freq_max)
        
        vswr_in_band = vswr[min_idx:max_idx+1]
        # Filter out infinite values
        vswr_finite = [v for v in vswr_in_band if v != float('inf')]
        
        return max(vswr_finite) if vswr_finite else 0.0
    
    def calculate_out_of_band_rejection(self, frequencies: List[float], gain: List[float],
                                      oob_requirement: OutOfBandRequirement,
                                      operational_min: float, operational_max: float) -> Dict[str, float]:
        """Calculate out-of-band rejection."""
        # Find worst-case (lowest) gain in operational band
        op_min_idx, op_max_idx = self.find_frequency_range_indices(
            frequencies, operational_min, operational_max)
        gain_operational = gain[op_min_idx:op_max_idx+1]
        worst_case_operational = min(gain_operational)
        
        # Find worst-case (highest) gain in OoB range
        oob_min_idx, oob_max_idx = self.find_frequency_range_indices(
            frequencies, oob_requirement.freq_min, oob_requirement.freq_max)
        gain_oob = gain[oob_min_idx:oob_max_idx+1]
        worst_case_oob = max(gain_oob)
        
        # Calculate rejection
        rejection = worst_case_operational - worst_case_oob
        
        print(f"DEBUG OoB Calculation:")
        print(f"  Operational range: {operational_min:.3f} to {operational_max:.3f} GHz")
        print(f"  OoB range: {oob_requirement.freq_min:.3f} to {oob_requirement.freq_max:.3f} GHz")
        print(f"  Worst-case operational gain: {worst_case_operational:.2f} dB")
        print(f"  Worst-case OoB gain: {worst_case_oob:.2f} dB")
        print(f"  Calculated rejection: {rejection:.2f} dB")
        print(f"  Required rejection: {oob_requirement.rejection_db:.2f} dB")
        print(f"  Pass: {rejection > oob_requirement.rejection_db}")
        
        return {
            'rejection_db': rejection,
            'worst_case_operational': worst_case_operational,
            'worst_case_oob': worst_case_oob,
            'requirement': oob_requirement.rejection_db,
            'pass': rejection > oob_requirement.rejection_db
        }
    
    def process_s_parameters(self, s_param_data: SParameterData, 
                           dut_config: DUTConfiguration,
                           test_stage: str) -> Dict[str, Dict[str, any]]:
        """Process S-parameter data and calculate all requirements."""
        # Get requirements for the test stage
        if test_stage == TEST_STAGES["board_bringup"]:
            requirements = dut_config.board_bringup
        elif test_stage == TEST_STAGES["sit"]:
            requirements = dut_config.sit
        elif test_stage == TEST_STAGES["test_campaign"]:
            requirements = dut_config.test_campaign
        else:
            raise ValueError(f"Unknown test stage: {test_stage}")
        
        results = {}
        
        # Determine which S-parameters to analyze based on port configuration
        s_params_to_analyze = []
        print(f"DEBUG: Available S-parameters in file: {list(s_param_data.s_parameters.keys())}")
        
        # Add transmission S-parameters (output ports from input ports)
        for output_port in dut_config.output_ports:
            for input_port in dut_config.input_ports:
                s_param_name = f"S{output_port}{input_port}"
                if s_param_name in s_param_data.s_parameters:
                    s_params_to_analyze.append(s_param_name)
        
        # Add reflection S-parameters (S11, S22, S33, S44) for VSWR calculation
        for port in range(1, dut_config.num_ports + 1):
            reflection_param = f"S{port}{port}"
            if reflection_param in s_param_data.s_parameters and reflection_param not in s_params_to_analyze:
                s_params_to_analyze.append(reflection_param)
        
        print(f"DEBUG: S-parameters to analyze: {s_params_to_analyze}")
        
        for s_param_name in s_params_to_analyze:
            s_param = s_param_data.s_parameters[s_param_name]
            gain = self.calculate_gain(s_param)
            
            # Calculate in-band gain
            in_band_stats = self.calculate_in_band_gain(
                s_param_data.frequency, gain,
                dut_config.operational_range.min_freq,
                dut_config.operational_range.max_freq
            )
            
            # Calculate VSWR (only for reflection S-parameters)
            vswr_max = 0.0
            if s_param_name.startswith('S') and s_param_name[1] == s_param_name[2]:  # S11, S22, etc.
                s11 = s_param_data.s_parameters[s_param_name]
                vswr = self.calculate_vswr(s11)
                vswr_max = self.calculate_vswr_max(
                    s_param_data.frequency, vswr,
                    dut_config.operational_range.min_freq,
                    dut_config.operational_range.max_freq
                )
                print(f"DEBUG: VSWR calculated for {s_param_name}: {vswr_max}")
            else:
                print(f"DEBUG: Skipping VSWR for {s_param_name} (not reflection)")
            
            # Calculate out-of-band rejections
            oob_results = []
            print(f"DEBUG: Processing {len(requirements.out_of_band_requirements)} OoB requirements")
            for i, oob_req in enumerate(requirements.out_of_band_requirements):
                oob_result = self.calculate_out_of_band_rejection(
                    s_param_data.frequency, gain, oob_req,
                    dut_config.operational_range.min_freq,
                    dut_config.operational_range.max_freq
                )
                oob_results.append(oob_result)
                print(f"DEBUG: OoB {i+1} result: {oob_result}")
            
            # Determine pass/fail
            pass_fail = self._determine_pass_fail(in_band_stats, vswr_max, oob_results, requirements)
            
            results[s_param_name] = {
                'frequency': s_param_data.frequency,
                'gain': gain,
                's11_data': s_param if s_param_name.startswith('S') and s_param_name[1] == s_param_name[2] else [],
                'in_band_gain_min': in_band_stats['min_gain'],
                'in_band_gain_max': in_band_stats['max_gain'],
                'flatness': in_band_stats['flatness'],
                'vswr_max': vswr_max,
                'out_of_band_rejections': oob_results,
                'pass_fail': pass_fail
            }
        
        return results
    
    def _determine_pass_fail(self, in_band_stats: Dict[str, float], vswr_max: float,
                           oob_results: List[Dict[str, float]], 
                           requirements: TestStageRequirements) -> str:
        """Determine overall pass/fail status."""
        # Check gain requirements
        if (in_band_stats['min_gain'] < requirements.gain_min_db or
            in_band_stats['max_gain'] > requirements.gain_max_db):
            return "Fail"
        
        # Check flatness requirement
        if in_band_stats['flatness'] > requirements.gain_flatness_db:
            return "Fail"
        
        # Check VSWR requirement
        if vswr_max > requirements.vswr_max:
            return "Fail"
        
        # Check out-of-band requirements
        for oob_result in oob_results:
            if not oob_result['pass']:
                return "Fail"
        
        return "Pass"
    
    def get_plot_data(self, results: Dict[str, Dict[str, any]], 
                     plot_type: str, dut_config: DUTConfiguration, test_stage: str = DEFAULT_TEST_STAGE) -> Dict[str, any]:
        """Get data for plotting."""
        plot_data = {}
        
        # Handle the case where results might be nested (multiple files)
        if not results:
            return plot_data
        
        # Get requirements for the test stage
        if test_stage == TEST_STAGES["board_bringup"]:
            requirements = dut_config.board_bringup
        elif test_stage == TEST_STAGES["sit"]:
            requirements = dut_config.sit
        elif test_stage == TEST_STAGES["test_campaign"]:
            requirements = dut_config.test_campaign
        else:
            requirements = dut_config.board_bringup
        
        # Define colors for different S-parameters
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        # Process all files (PRI, RED, etc.)
        for file_key, file_results in results.items():
            if not isinstance(file_results, dict):
                continue
                
            for i, (s_param_name, result_data) in enumerate(file_results.items()):
                color = colors[i % len(colors)]
                
                # Create unique key for each S-parameter and file combination
                plot_key = f"{s_param_name}_{file_key}"
                
                if plot_type == "wideband_gain":
                    if s_param_name not in plot_data:
                        plot_data[s_param_name] = {
                            'title': f"{dut_config.name} Wideband Gain",
                            'x_label': "Frequency (GHz)",
                            'y_label': "Gain (dB)",
                            'curves': []
                        }
                    
                    plot_data[s_param_name]['curves'].append({
                        'x': result_data['frequency'],
                        'y': result_data['gain'],
                        'label': f'{s_param_name} {file_key}',
                        'linestyle': '-',
                        'color': color
                    })
                elif plot_type == "operational_gain":
                        if s_param_name not in plot_data:
                            # Expand the acceptance region slightly for better visibility
                            freq_expansion = (dut_config.operational_range.max_freq - dut_config.operational_range.min_freq) * PLOT_EXPANSION_FACTOR
                            gain_expansion = (requirements.gain_max_db - requirements.gain_min_db) * PLOT_EXPANSION_FACTOR
                            
                            plot_data[s_param_name] = {
                                'title': f"{dut_config.name} Operational Gain",
                                'x_label': "Frequency (GHz)",
                                'y_label': "Gain (dB)",
                                'curves': [],
                                'acceptance_region': {
                                    'freq_min': dut_config.operational_range.min_freq - freq_expansion,
                                    'freq_max': dut_config.operational_range.max_freq + freq_expansion,
                                    'gain_min': requirements.gain_min_db - gain_expansion,
                                    'gain_max': requirements.gain_max_db + gain_expansion
                                }
                            }
                        
                        plot_data[s_param_name]['curves'].append({
                            'x': result_data['frequency'],
                            'y': result_data['gain'],
                            'label': f'{s_param_name} {file_key}',
                            'linestyle': '-',
                            'color': color
                        })
                elif plot_type == "wideband_vswr":
                    print(f"DEBUG VSWR: Processing {s_param_name}, vswr_max = {result_data['vswr_max']}")
                    if result_data['vswr_max'] > 0:  # Only for reflection S-parameters
                        # Calculate VSWR for all frequencies
                        vswr_values = self.calculate_vswr(result_data['s11_data'])
                        print(f"DEBUG VSWR: Calculated {len(vswr_values)} VSWR values")
                        
                        if s_param_name not in plot_data:
                            plot_data[s_param_name] = {
                                'title': f"{dut_config.name} Wideband VSWR",
                                'x_label': "Frequency (GHz)",
                                'y_label': "VSWR",
                                'curves': []
                            }
                        
                        plot_data[s_param_name]['curves'].append({
                            'x': result_data['frequency'],
                            'y': vswr_values,
                            'label': f'{s_param_name} {file_key}',
                            'linestyle': '-',
                            'color': color
                        })
                        print(f"DEBUG VSWR: Added curve for {s_param_name} {file_key}")
                    else:
                        print(f"DEBUG VSWR: Skipping {s_param_name} (vswr_max = 0)")
                elif plot_type == "operational_vswr":
                    print(f"DEBUG VSWR: Processing {s_param_name}, vswr_max = {result_data['vswr_max']}")
                    if result_data['vswr_max'] > 0:  # Only for reflection S-parameters
                        # Calculate VSWR for all frequencies
                        vswr_values = self.calculate_vswr(result_data['s11_data'])
                        print(f"DEBUG VSWR: Calculated {len(vswr_values)} VSWR values")
                        
                        # Validate VSWR data
                        if not vswr_values or len(vswr_values) == 0:
                            print(f"DEBUG VSWR: Skipping {s_param_name} - no VSWR data")
                            continue
                        
                        # Check for invalid values
                        valid_vswr = [v for v in vswr_values if np.isfinite(v) and v > 0]
                        if len(valid_vswr) == 0:
                            print(f"DEBUG VSWR: Skipping {s_param_name} - no valid VSWR values")
                            continue
                        
                        # Filter to operational frequency range only
                        freq_mask = ((result_data['frequency'] >= dut_config.operational_range.min_freq) & 
                                   (result_data['frequency'] <= dut_config.operational_range.max_freq))
                        operational_freq = result_data['frequency'][freq_mask].tolist()
                        operational_vswr = np.array(vswr_values)[freq_mask].tolist()
                        
                        print(f"DEBUG VSWR: Operational range: {dut_config.operational_range.min_freq:.3f} to {dut_config.operational_range.max_freq:.3f} GHz")
                        print(f"DEBUG VSWR: Filtered to {len(operational_freq)} points in operational range")
                        
                        # Skip if no data in operational range
                        if len(operational_freq) == 0:
                            print(f"DEBUG VSWR: Skipping {s_param_name} - no data in operational range")
                            continue
                        
                        if s_param_name not in plot_data:
                            # Expand the acceptance region slightly for better visibility
                            freq_expansion = (dut_config.operational_range.max_freq - dut_config.operational_range.min_freq) * PLOT_EXPANSION_FACTOR
                            
                            plot_data[s_param_name] = {
                                'title': f"{dut_config.name} Operational VSWR",
                                'x_label': "Frequency (GHz)",
                                'y_label': "VSWR",
                                'curves': [],
                                'acceptance_region': {
                                    'freq_min': dut_config.operational_range.min_freq - freq_expansion,
                                    'freq_max': dut_config.operational_range.max_freq + freq_expansion,
                                    'vswr_max': requirements.vswr_max
                                }
                            }
                        
                        # Final validation before adding to plot
                        if len(operational_freq) > 0 and len(operational_vswr) > 0:
                            plot_data[s_param_name]['curves'].append({
                                'x': operational_freq,
                                'y': operational_vswr,
                                'label': f'{s_param_name} {file_key}',
                                'linestyle': '-',
                                'color': color
                            })
                            print(f"DEBUG VSWR: Added curve for {s_param_name} {file_key}")
                        else:
                            print(f"DEBUG VSWR: Skipping {s_param_name} {file_key} - no valid operational data")
                    else:
                        print(f"DEBUG VSWR: Skipping {s_param_name} (vswr_max = 0)")
        
        # Check if we have any data to plot
        if not plot_data:
            print("DEBUG VSWR: No VSWR data to plot - all S-parameters skipped")
            return {}
        
        return plot_data
