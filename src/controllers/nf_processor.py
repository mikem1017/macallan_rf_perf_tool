"""
Noise figure processing and calculations
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from src.models.test_data import NoiseFigureData
from src.models.dut_config import DUTConfiguration, TestStageRequirements
from src.constants import TEST_STAGES

class NoiseFigureProcessor:
    """Processor for noise figure calculations and analysis."""
    
    def __init__(self):
        pass
    
    def find_worst_case_nf(self, frequencies: List[float], nf_values: List[float]) -> Dict[str, float]:
        """Find worst-case (maximum) noise figure."""
        if not frequencies or not nf_values:
            return {'nf_max': 0.0, 'frequency_at_max': 0.0, 'index_at_max': 0}
        
        # Find index of maximum NF
        max_idx = np.argmax(nf_values)
        
        return {
            'nf_max': nf_values[max_idx],
            'frequency_at_max': frequencies[max_idx],
            'index_at_max': max_idx
        }
    
    def process_noise_figure(self, nf_data: NoiseFigureData,
                           dut_config: DUTConfiguration,
                           test_stage: str) -> Dict[str, any]:
        """Process noise figure data and calculate requirements."""
        # Get requirements for the test stage
        if test_stage == TEST_STAGES["board_bringup"]:
            requirements = dut_config.board_bringup
        elif test_stage == TEST_STAGES["sit"]:
            requirements = dut_config.sit
        elif test_stage == TEST_STAGES["test_campaign"]:
            requirements = dut_config.test_campaign
        else:
            raise ValueError(f"Unknown test stage: {test_stage}")
        
        # Find worst-case NF
        worst_case = self.find_worst_case_nf(nf_data.frequency, nf_data.nf)
        
        # Check requirement
        nf_pass = worst_case['nf_max'] <= requirements.nf_max_db
        
        return {
            'frequency': nf_data.frequency,
            'nf': nf_data.nf,
            'nf_max': worst_case['nf_max'],
            'frequency_at_max': worst_case['frequency_at_max'],
            'requirement': requirements.nf_max_db,
            'pass': nf_pass,
            'margin': requirements.nf_max_db - worst_case['nf_max']
        }
    
    def get_plot_data(self, results: Dict[str, any]) -> Dict[str, any]:
        """Get data for plotting."""
        return {
            'frequency': results['frequency'],
            'nf': results['nf'],
            'nf_max': results['nf_max'],
            'frequency_at_max': results['frequency_at_max'],
            'requirement': results['requirement'],
            'title': "Noise Figure vs Frequency",
            'x_label': "Frequency (GHz)",
            'y_label': "Noise Figure (dB)"
        }
