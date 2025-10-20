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
        
        # Process each frequency (3 frequencies per file)
        for i, freq in enumerate(power_data.frequency):
            # Get data for this frequency - data is interleaved by frequency
            freq_indices = list(range(i, len(power_data.pin), len(power_data.frequency)))
            
            pin_freq = [power_data.pin[j] for j in freq_indices]
            pout_freq = [power_data.pout_single_tone[j] for j in freq_indices]
            im3_freq = [power_data.im3[j] for j in freq_indices]
            im5_freq = [power_data.im5[j] for j in freq_indices]
            test_type_freq = [power_data.test_type[j] for j in freq_indices]
            
            # Separate single-tone and two-tone data
            single_tone_indices = [j for j, t in enumerate(test_type_freq) if t == "single-tone"]
            two_tone_indices = [j for j, t in enumerate(test_type_freq) if t == "two-tone"]
            
            single_tone_pin = [pin_freq[j] for j in single_tone_indices]
            single_tone_pout = [pout_freq[j] for j in single_tone_indices]
            
            two_tone_pin = [pin_freq[j] for j in two_tone_indices]
            two_tone_im3 = [im3_freq[j] for j in two_tone_indices]
            two_tone_im5 = [im5_freq[j] for j in two_tone_indices]
            
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
                'p1db': p1db,
                'p1db_pass': p1db_pass,
                'pin_pout_im3_results': pin_pout_im3_results,
                'pin_pout_im3_pass': pin_pout_im3_pass,
                'overall_pass': overall_pass
            }
        
        return results
    
    def get_plot_data(self, results: Dict[str, Dict[str, any]], 
                     plot_type: str, temperature_data: List[float] = None) -> Dict[str, any]:
        """Get data for plotting."""
        plot_data = {}
        
        for freq, result_data in results.items():
            if plot_type == "compression":
                plot_data[freq] = {
                    'x': result_data['single_tone_pin'],
                    'y': result_data['single_tone_pout'],
                    'p1db': result_data['p1db'],
                    'title': f"Compression @ {freq:.1f} GHz",
                    'x_label': "Pin (dBm)",
                    'y_label': "Pout (dBm)",
                    'curves': [{
                        'x': result_data['single_tone_pin'],
                        'y': result_data['single_tone_pout'],
                        'label': 'Pout',
                        'linestyle': '-',
                        'color': 'blue'
                    }]
                }
                
                # Add temperature on secondary Y-axis
                if temperature_data:
                    plot_data[freq]['y2'] = temperature_data
                    plot_data[freq]['y2_label'] = "Temperature (°C)"
                    plot_data[freq]['curves'].append({
                        'x': result_data['single_tone_pin'],
                        'y': temperature_data,
                        'label': 'Temperature',
                        'linestyle': '--',
                        'color': 'red'
                    })
                    
            elif plot_type == "linearity":
                # Create 4 curves for IM3/IM5 lower and upper
                curves = []
                
                # IM3 lower and upper (assuming we have separate data)
                # For now, using the same data - this would need to be updated with actual lower/upper data
                curves.append({
                    'x': result_data['two_tone_pin'],
                    'y': result_data['two_tone_im3'],
                    'label': 'IM3 Lower',
                    'linestyle': '-',
                    'color': 'green'
                })
                curves.append({
                    'x': result_data['two_tone_pin'],
                    'y': result_data['two_tone_im3'],  # Would be upper IM3
                    'label': 'IM3 Upper',
                    'linestyle': '--',
                    'color': 'green'
                })
                curves.append({
                    'x': result_data['two_tone_pin'],
                    'y': result_data['two_tone_im5'],
                    'label': 'IM5 Lower',
                    'linestyle': '-',
                    'color': 'orange'
                })
                curves.append({
                    'x': result_data['two_tone_pin'],
                    'y': result_data['two_tone_im5'],  # Would be upper IM5
                    'label': 'IM5 Upper',
                    'linestyle': '--',
                    'color': 'orange'
                })
                
                plot_data[freq] = {
                    'title': f"Linearity @ {freq:.1f} GHz",
                    'x_label': "Pin (dBm)",
                    'y_label': "IM3/IM5 (dBc)",
                    'curves': curves
                }
                
                # Add temperature on secondary Y-axis
                if temperature_data:
                    plot_data[freq]['y2'] = temperature_data
                    plot_data[freq]['y2_label'] = "Temperature (°C)"
                    plot_data[freq]['curves'].append({
                        'x': result_data['two_tone_pin'],
                        'y': temperature_data,
                        'label': 'Temperature',
                        'linestyle': ':',
                        'color': 'red'
                    })
        
        return plot_data
