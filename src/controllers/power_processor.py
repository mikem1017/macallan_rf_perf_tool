"""
Power and linearity processing and calculations
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from src.models.test_data import PowerLinearityData
from src.models.dut_config import DUTConfiguration, TestStageRequirements, PinPoutIM3Requirement
from src.constants import TEST_STAGES, P1DB_THRESHOLD_DB

class PowerProcessor:
    """Processor for power and linearity calculations and analysis."""
    
    def __init__(self):
        pass
    
    def find_p1db(self, pin: List[float], pout: List[float]) -> float:
        """Find P1dB compression point."""
        if len(pin) < 2 or len(pout) < 2:
            return 0.0
        
        # Calculate small-signal gain (from first few points)
        small_signal_gain = (pout[1] - pout[0]) / (pin[1] - pin[0])
        
        # Find where gain drops by 1dB
        for i in range(len(pin)):
            if i == 0:
                continue
            
            current_gain = (pout[i] - pout[i-1]) / (pin[i] - pin[i-1])
            gain_drop = small_signal_gain - current_gain
            
            if gain_drop >= P1DB_THRESHOLD_DB:  # 1dB drop
                # Interpolate to find exact P1dB point
                if i < len(pin) - 1:
                    # Linear interpolation
                    p1db_pout = pout[i-1] + (pout[i] - pout[i-1]) * (1.0 / gain_drop)
                    return p1db_pout
                else:
                    return pout[i]
        
        # If no 1dB compression found, return highest output power
        return max(pout)
    
    def interpolate_at_pin(self, pin: List[float], values: List[float], target_pin: float) -> float:
        """Interpolate values at a specific Pin level."""
        if len(pin) != len(values) or len(pin) < 2:
            return 0.0
        
        # Ensure all pin values are floats
        pin = [float(p) for p in pin]
        values = [float(v) for v in values]
        target_pin = float(target_pin)
        
        # Find the two points to interpolate between
        for i in range(len(pin) - 1):
            if pin[i] <= target_pin <= pin[i + 1]:
                # Linear interpolation
                ratio = (target_pin - pin[i]) / (pin[i + 1] - pin[i])
                interpolated_value = values[i] + ratio * (values[i + 1] - values[i])
                return interpolated_value
        
        # If target_pin is outside range, extrapolate
        if target_pin < pin[0]:
            # Extrapolate backwards
            ratio = (target_pin - pin[0]) / (pin[1] - pin[0])
            return values[0] + ratio * (values[1] - values[0])
        else:
            # Extrapolate forwards
            ratio = (target_pin - pin[-2]) / (pin[-1] - pin[-2])
            return values[-2] + ratio * (values[-1] - values[-2])
    
    def process_power_linearity(self, power_data: PowerLinearityData,
                               dut_config: DUTConfiguration,
                               test_stage: str) -> Dict[str, Dict[str, any]]:
        """Process power and linearity data and calculate all requirements."""
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
        
        # Process each frequency using the frequency-specific data
        for freq in power_data.freq_data.keys():
            # Get data for this specific frequency
            freq_data = power_data.freq_data[freq]
            single_tone_pin = freq_data['single_tone_pin']
            single_tone_pout = freq_data['single_tone_pout']
            two_tone_pin = freq_data['two_tone_pin']
            two_tone_im3 = freq_data['two_tone_im3']
            two_tone_im5 = freq_data['two_tone_im5']
            
            # Get separate upper/lower sideband data if available
            two_tone_im3_lower = freq_data.get('two_tone_im3_lower', two_tone_im3)
            two_tone_im3_upper = freq_data.get('two_tone_im3_upper', two_tone_im3)
            two_tone_im5_lower = freq_data.get('two_tone_im5_lower', two_tone_im5)
            two_tone_im5_upper = freq_data.get('two_tone_im5_upper', two_tone_im5)
            
            # Calculate P1dB
            p1db = self.find_p1db(single_tone_pin, single_tone_pout)
            
            # Check Pin-Pout-IM3 requirements
            pin_pout_im3_results = []
            for req in requirements.pin_pout_im3_requirements:
                # Interpolate Pout at required Pin
                pout_at_pin = self.interpolate_at_pin(single_tone_pin, single_tone_pout, req.pin_dbm)
                
                # Interpolate IM3 at required Pin
                im3_at_pin = self.interpolate_at_pin(two_tone_pin, two_tone_im3, req.pin_dbm)
                
                # Check requirements
                pout_pass = pout_at_pin >= req.pout_min_dbm
                im3_pass = im3_at_pin < req.im3_max_dbc  # More negative is better
                
                pin_pout_im3_results.append({
                    'pin_dbm': req.pin_dbm,
                    'pout_measured': pout_at_pin,
                    'pout_required': req.pout_min_dbm,
                    'pout_pass': pout_pass,
                    'im3_measured': im3_at_pin,
                    'im3_required': req.im3_max_dbc,
                    'im3_pass': im3_pass,
                    'overall_pass': pout_pass and im3_pass
                })
            
            # Determine overall pass/fail
            p1db_pass = p1db >= requirements.p1db_min_dbm
            pin_pout_im3_pass = all(result['overall_pass'] for result in pin_pout_im3_results)
            overall_pass = p1db_pass and pin_pout_im3_pass
            
            results[freq] = {
                'frequency': freq,
                'single_tone_pin': single_tone_pin,
                'single_tone_pout': single_tone_pout,
                'two_tone_pin': two_tone_pin,
                'two_tone_im3': two_tone_im3,
                'two_tone_im5': two_tone_im5,
                'two_tone_im3_lower': two_tone_im3_lower,
                'two_tone_im3_upper': two_tone_im3_upper,
                'two_tone_im5_lower': two_tone_im5_lower,
                'two_tone_im5_upper': two_tone_im5_upper,
                'p1db': p1db,
                'p1db_pass': p1db_pass,
                'pin_pout_im3_results': pin_pout_im3_results,
                'pin_pout_im3_pass': pin_pout_im3_pass,
                'overall_pass': overall_pass
            }
        
        return results
    
    def get_plot_data(self, results: Dict[str, Dict[str, any]], 
                     plot_type: str, dut_config, temperature_data: List[float] = None, test_stage: str = "board_bringup") -> Dict[str, any]:
        """Get data for plotting."""
        plot_data = {}
        
        # Define colors for different frequencies
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        # Define line styles for different file types
        line_styles = {'PRI': '-', 'RED': '--'}
        
        # Process all files (PRI, RED, etc.)
        for file_key, file_results in results.items():
            if not isinstance(file_results, dict):
                continue
                
            for i, (freq, result_data) in enumerate(file_results.items()):
                color = colors[i % len(colors)]
                linestyle = line_styles.get(file_key, '-')  # Default to solid line
                
                # Create unique key for each frequency and file combination
                plot_key = f"{freq}_{file_key}"
                if plot_type in ["compression", "full_power_sweep"]:
                    # Sort data by Pin values to ensure proper left-to-right progression
                    pin_data = result_data['single_tone_pin']
                    pout_data = result_data['single_tone_pout']
                    
                    # Create sorted pairs and then separate back into x and y
                    sorted_pairs = sorted(zip(pin_data, pout_data), key=lambda pair: pair[0])
                    sorted_pin, sorted_pout = zip(*sorted_pairs)
                    
                    plot_data[plot_key] = {
                        'x': list(sorted_pin),
                        'y': list(sorted_pout),
                        'p1db': result_data['p1db'],
                        'title': f"Pout vs Pin - {dut_config.name}",
                        'x_label': "Pin (dBm)",
                        'y_label': "Pout (dBm)",
                        'curves': [{
                            'x': list(sorted_pin),
                            'y': list(sorted_pout),
                            'label': f"{file_key} @ {float(freq):.2f} GHz",
                            'linestyle': linestyle,
                            'color': color
                        }]
                    }
                
                elif plot_type == "operational_range":
                    # Sort data by Pin values to ensure proper left-to-right progression
                    pin_data = result_data['single_tone_pin']
                    pout_data = result_data['single_tone_pout']
                    
                    # Create sorted pairs and then separate back into x and y
                    sorted_pairs = sorted(zip(pin_data, pout_data), key=lambda pair: pair[0])
                    sorted_pin, sorted_pout = zip(*sorted_pairs)
                    
                    # Get requirements for the current test stage
                    if test_stage == "board_bringup":
                        requirements = dut_config.board_bringup
                    elif test_stage == "sit":
                        requirements = dut_config.sit
                    elif test_stage == "test_campaign":
                        requirements = dut_config.test_campaign
                    else:
                        requirements = dut_config.board_bringup
                    
                    # Calculate operational range limits
                    if requirements.pin_pout_im3_requirements:
                        import numpy as np
                        pin_values = [req.pin_dbm for req in requirements.pin_pout_im3_requirements]
                        pout_values = [req.pout_min_dbm for req in requirements.pin_pout_im3_requirements]
                        
                        # Calculate axis limits with 2dB margins
                        pin_min = min(pin_values) - 2.0
                        pin_max = max(pin_values) + 2.0
                        pout_min = min(pout_values) - 2.0
                        pout_max = max(pout_values) + 2.0
                        
                        # Round to 0.25 dB increments
                        x_min = np.floor(pin_min * 4) / 4
                        x_max = np.ceil(pin_max * 4) / 4
                        y_min = np.floor(pout_min * 4) / 4
                        y_max = np.ceil(pout_max * 4) / 4
                        
                        plot_data[plot_key] = {
                            'x': list(sorted_pin),
                            'y': list(sorted_pout),
                            'p1db': result_data['p1db'],
                            'title': f"Pout vs Pin - {dut_config.name} (Operational Range)",
                            'x_label': "Pin (dBm)",
                            'y_label': "Pout (dBm)",
                            'default_x_min': x_min,
                            'default_x_max': x_max,
                            'default_y_min': y_min,
                            'default_y_max': y_max,
                            'acceptance_region': {
                                'pin_min': min(pin_values),
                                'pin_max': max(pin_values),
                                'pout_min': min(pout_values),
                                'pout_max': max(pout_values),
                                'x_min': x_min,
                                'x_max': x_max,
                                'y_min': y_min,
                                'y_max': y_max,
                                'requirement_points': [(req.pin_dbm, req.pout_min_dbm) 
                                                      for req in requirements.pin_pout_im3_requirements]
                            },
                            'curves': [{
                                'x': list(sorted_pin),
                                'y': list(sorted_pout),
                                'label': f"{file_key} @ {float(freq):.2f} GHz",
                                'linestyle': linestyle,
                                'color': color
                            }]
                        }
                    else:
                        # No requirements, fall back to full power sweep behavior
                        plot_data[plot_key] = {
                            'x': list(sorted_pin),
                            'y': list(sorted_pout),
                    'p1db': result_data['p1db'],
                            'title': f"Pout vs Pin - {dut_config.name}",
                    'x_label': "Pin (dBm)",
                    'y_label': "Pout (dBm)",
                    'curves': [{
                                'x': list(sorted_pin),
                                'y': list(sorted_pout),
                                'label': f"{file_key} @ {float(freq):.2f} GHz",
                                'linestyle': linestyle,
                                'color': color
                            }]
                        }
                
                # Note: Temperature data is not plotted on compression plots
                # as it doesn't have a meaningful relationship with Pin/Pout
                
                if plot_type == "linearity":
                    # Sort data by Pin values to ensure proper left-to-right progression
                    pin_data = result_data['two_tone_pin']
                    
                    # Get separate upper and lower sideband data if available
                    im3_lower_data = result_data.get('two_tone_im3_lower', result_data['two_tone_im3'])
                    im3_upper_data = result_data.get('two_tone_im3_upper', result_data['two_tone_im3'])
                    im5_lower_data = result_data.get('two_tone_im5_lower', result_data['two_tone_im5'])
                    im5_upper_data = result_data.get('two_tone_im5_upper', result_data['two_tone_im5'])
                    
                    # Create sorted pairs for each sideband
                    sorted_im3_lower_pairs = sorted(zip(pin_data, im3_lower_data), key=lambda pair: pair[0])
                    sorted_im3_upper_pairs = sorted(zip(pin_data, im3_upper_data), key=lambda pair: pair[0])
                    sorted_im5_lower_pairs = sorted(zip(pin_data, im5_lower_data), key=lambda pair: pair[0])
                    sorted_im5_upper_pairs = sorted(zip(pin_data, im5_upper_data), key=lambda pair: pair[0])
                    
                    sorted_pin_im3_lower, sorted_im3_lower = zip(*sorted_im3_lower_pairs)
                    sorted_pin_im3_upper, sorted_im3_upper = zip(*sorted_im3_upper_pairs)
                    sorted_pin_im5_lower, sorted_im5_lower = zip(*sorted_im5_lower_pairs)
                    sorted_pin_im5_upper, sorted_im5_upper = zip(*sorted_im5_upper_pairs)
                    
                    # Create 4 curves for IM3/IM5 upper and lower sidebands
                    curves = []
                    
                    # IM3 Lower and Upper
                    curves.append({
                        'x': list(sorted_pin_im3_lower),
                        'y': list(sorted_im3_lower),
                        'label': f'IM3 Lower {file_key} @ {float(freq):.2f} GHz',
                        'linestyle': linestyle,
                        'color': color
                    })
                    curves.append({
                        'x': list(sorted_pin_im3_upper),
                        'y': list(sorted_im3_upper),
                        'label': f'IM3 Upper {file_key} @ {float(freq):.2f} GHz',
                        'linestyle': linestyle,
                        'color': color
                    })
                    
                    # IM5 Lower and Upper
                    curves.append({
                        'x': list(sorted_pin_im5_lower),
                        'y': list(sorted_im5_lower),
                        'label': f'IM5 Lower {file_key} @ {float(freq):.2f} GHz',
                        'linestyle': linestyle,
                        'color': color
                    })
                    curves.append({
                        'x': list(sorted_pin_im5_upper),
                        'y': list(sorted_im5_upper),
                        'label': f'IM5 Upper {file_key} @ {float(freq):.2f} GHz',
                        'linestyle': linestyle,
                        'color': color
                    })
                    
                    plot_data[plot_key] = {
                        'title': f"Linearity - {dut_config.name}",
                        'x_label': "Pin (dBm)",
                        'y_label': "IM3/IM5 (dBc)",
                        'curves': curves
                    }
                
                elif plot_type == "im3_operational_range":
                    # Sort data by Pin values to ensure proper left-to-right progression
                    pin_data = result_data['two_tone_pin']
                    
                    # Get separate upper and lower sideband data if available
                    im3_lower_data = result_data.get('two_tone_im3_lower', result_data['two_tone_im3'])
                    im3_upper_data = result_data.get('two_tone_im3_upper', result_data['two_tone_im3'])
                    
                    # Create sorted pairs for each sideband
                    sorted_im3_lower_pairs = sorted(zip(pin_data, im3_lower_data), key=lambda pair: pair[0])
                    sorted_im3_upper_pairs = sorted(zip(pin_data, im3_upper_data), key=lambda pair: pair[0])
                    
                    sorted_pin_im3_lower, sorted_im3_lower = zip(*sorted_im3_lower_pairs)
                    sorted_pin_im3_upper, sorted_im3_upper = zip(*sorted_im3_upper_pairs)
                    
                    # Create 2 curves for IM3 Lower and Upper only
                    curves = []
                    
                    # IM3 Lower and Upper
                    curves.append({
                        'x': list(sorted_pin_im3_lower),
                        'y': list(sorted_im3_lower),
                        'label': f'IM3 Lower {file_key} @ {float(freq):.2f} GHz',
                        'linestyle': linestyle,
                        'color': color
                    })
                    curves.append({
                        'x': list(sorted_pin_im3_upper),
                        'y': list(sorted_im3_upper),
                        'label': f'IM3 Upper {file_key} @ {float(freq):.2f} GHz',
                        'linestyle': linestyle,
                        'color': color
                    })
                    
                    # Get requirements for the current test stage
                    if test_stage == "board_bringup":
                        requirements = dut_config.board_bringup
                    elif test_stage == "sit":
                        requirements = dut_config.sit
                    elif test_stage == "test_campaign":
                        requirements = dut_config.test_campaign
                    else:
                        requirements = dut_config.board_bringup
                    
                    # Calculate operational range limits with 2dB margins
                    if requirements.pin_pout_im3_requirements:
                        import numpy as np
                        pin_values = [req.pin_dbm for req in requirements.pin_pout_im3_requirements]
                        im3_values = [req.im3_max_dbc for req in requirements.pin_pout_im3_requirements]
                        
                        # Calculate axis limits with 2dB margins
                        pin_min = min(pin_values) - 2.0
                        pin_max = max(pin_values) + 2.0
                        im3_min = min(im3_values) - 2.0
                        im3_max = max(im3_values) + 2.0
                        
                        # Round to 0.25 dB increments
                        x_min = np.floor(pin_min * 4) / 4
                        x_max = np.ceil(pin_max * 4) / 4
                        # For IM3 plots, y_min should be more negative (better), y_max should be less negative (worse)
                        y_min = np.floor(im3_min * 4) / 4  # More negative (better)
                        y_max = np.ceil(im3_max * 4) / 4   # Less negative (worse)
                        
                        plot_data[plot_key] = {
                            'title': f"IM3 Operational Range - {dut_config.name}",
                            'x_label': "Pin (dBm)",
                            'y_label': "IM3 (dBc)",
                            'curves': curves,
                            'default_x_min': x_min,
                            'default_x_max': x_max,
                            'default_y_min': y_min,
                            'default_y_max': y_max,
                            'acceptance_region': {
                                'pin_min': min(pin_values),
                                'pin_max': max(pin_values),
                                'im3_min': min(im3_values),
                                'im3_max': max(im3_values),
                                'x_min': x_min,
                                'x_max': x_max,
                                'y_min': y_min,
                                'y_max': y_max,
                                'requirement_points': [(req.pin_dbm, req.im3_max_dbc)
                                                      for req in requirements.pin_pout_im3_requirements]
                            }
                        }
                    else:
                        plot_data[plot_key] = {
                            'title': f"IM3 Operational Range - {dut_config.name}",
                            'x_label': "Pin (dBm)",
                            'y_label': "IM3 (dBc)",
                    'curves': curves
                }
                
                # Add temperature on secondary Y-axis
                if temperature_data:
                    plot_data[plot_key]['y2'] = temperature_data
                    plot_data[plot_key]['y2_label'] = "Temperature (°C)"
                    plot_data[plot_key]['curves'].append({
                        'x': result_data['two_tone_pin'],
                        'y': temperature_data,
                        'label': 'Temperature',
                        'linestyle': ':',
                        'color': 'red'
                    })
        
        return plot_data
