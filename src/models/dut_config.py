"""
DUT Configuration data models
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import os

@dataclass
class FrequencyRange:
    """Frequency range specification."""
    min_freq: float  # GHz
    max_freq: float  # GHz

@dataclass
class OutOfBandRequirement:
    """Out-of-band gain requirement."""
    freq_min: float  # GHz
    freq_max: float  # GHz
    rejection_db: float  # dBc

@dataclass
class PinPoutIM3Requirement:
    """Pin-Pout-IM3 requirement triplet."""
    pin_dbm: float
    pout_min_dbm: float
    im3_max_dbc: float

@dataclass
class TestStageRequirements:
    """Requirements for a specific test stage."""
    # S-Parameters
    gain_min_db: float
    gain_max_db: float
    gain_flatness_db: float
    vswr_max: float
    out_of_band_requirements: List[OutOfBandRequirement] = field(default_factory=list)
    
    # Power/Linearity
    p1db_min_dbm: float = 0.0
    pin_pout_im3_requirements: List[PinPoutIM3Requirement] = field(default_factory=list)
    
    # Noise Figure
    nf_max_db: float = 0.0

@dataclass
class DUTConfiguration:
    """Complete DUT configuration."""
    name: str
    part_number: str
    
    # Frequency ranges
    operational_range: FrequencyRange
    wideband_range: FrequencyRange
    
    # Port configuration
    num_ports: int
    input_ports: List[int]  # List of port numbers that are inputs
    output_ports: List[int]  # List of port numbers that are outputs
    
    # Test configuration
    hg_lg_enabled: bool = False
    test_enables: Dict[str, bool] = field(default_factory=lambda: {
        's_parameters': True,
        'compression': True,
        'linearity': True,
        'noise_figure': True,
        'spurious': False,
        'psd': False
    })
    
    # Requirements for each test stage
    board_bringup: TestStageRequirements = field(default_factory=TestStageRequirements)
    sit: TestStageRequirements = field(default_factory=TestStageRequirements)
    test_campaign: TestStageRequirements = field(default_factory=TestStageRequirements)

class DUTConfigManager:
    """Manager for DUT configurations."""
    
    def __init__(self, config_file: str = "config/dut_configs.json"):
        self.config_file = config_file
        self.dut_configs: Dict[str, DUTConfiguration] = {}
        self.load_configs()
    
    def load_configs(self):
        """Load DUT configurations from JSON file."""
        if not os.path.exists(self.config_file):
            self.dut_configs = {}
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            self.dut_configs = {}
            for name, config_data in data.items():
                self.dut_configs[name] = self._dict_to_dut_config(config_data)
        except Exception as e:
            print(f"Error loading DUT configs: {e}")
            self.dut_configs = {}
    
    def save_configs(self):
        """Save DUT configurations to JSON file."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        data = {}
        for name, config in self.dut_configs.items():
            data[name] = self._dut_config_to_dict(config)
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_dut(self, dut_config: DUTConfiguration):
        """Add a new DUT configuration."""
        self.dut_configs[dut_config.name] = dut_config
        self.save_configs()
    
    def update_dut(self, name: str, dut_config: DUTConfiguration):
        """Update an existing DUT configuration."""
        if name in self.dut_configs:
            self.dut_configs[name] = dut_config
            self.save_configs()
    
    def delete_dut(self, name: str):
        """Delete a DUT configuration."""
        if name in self.dut_configs:
            del self.dut_configs[name]
            self.save_configs()
    
    def get_dut(self, name: str) -> Optional[DUTConfiguration]:
        """Get a DUT configuration by name."""
        return self.dut_configs.get(name)
    
    def list_duts(self) -> List[str]:
        """List all DUT configuration names."""
        return list(self.dut_configs.keys())
    
    def _dut_config_to_dict(self, config: DUTConfiguration) -> Dict[str, Any]:
        """Convert DUTConfiguration to dictionary for JSON serialization."""
        return {
            'name': config.name,
            'part_number': config.part_number,
            'operational_range': {
                'min_freq': config.operational_range.min_freq,
                'max_freq': config.operational_range.max_freq
            },
            'wideband_range': {
                'min_freq': config.wideband_range.min_freq,
                'max_freq': config.wideband_range.max_freq
            },
            'num_ports': config.num_ports,
            'input_ports': config.input_ports,
            'output_ports': config.output_ports,
            'hg_lg_enabled': config.hg_lg_enabled,
            'test_enables': config.test_enables,
            'board_bringup': self._test_stage_to_dict(config.board_bringup),
            'sit': self._test_stage_to_dict(config.sit),
            'test_campaign': self._test_stage_to_dict(config.test_campaign)
        }
    
    def _test_stage_to_dict(self, stage: TestStageRequirements) -> Dict[str, Any]:
        """Convert TestStageRequirements to dictionary."""
        return {
            'gain_min_db': stage.gain_min_db,
            'gain_max_db': stage.gain_max_db,
            'gain_flatness_db': stage.gain_flatness_db,
            'vswr_max': stage.vswr_max,
            'out_of_band_requirements': [
                {
                    'freq_min': req.freq_min,
                    'freq_max': req.freq_max,
                    'rejection_db': req.rejection_db
                }
                for req in stage.out_of_band_requirements
            ],
            'p1db_min_dbm': stage.p1db_min_dbm,
            'pin_pout_im3_requirements': [
                {
                    'pin_dbm': req.pin_dbm,
                    'pout_min_dbm': req.pout_min_dbm,
                    'im3_max_dbc': req.im3_max_dbc
                }
                for req in stage.pin_pout_im3_requirements
            ],
            'nf_max_db': stage.nf_max_db
        }
    
    def _dict_to_dut_config(self, data: Dict[str, Any]) -> DUTConfiguration:
        """Convert dictionary to DUTConfiguration."""
        return DUTConfiguration(
            name=data['name'],
            part_number=data['part_number'],
            operational_range=FrequencyRange(
                min_freq=data['operational_range']['min_freq'],
                max_freq=data['operational_range']['max_freq']
            ),
            wideband_range=FrequencyRange(
                min_freq=data['wideband_range']['min_freq'],
                max_freq=data['wideband_range']['max_freq']
            ),
            num_ports=data['num_ports'],
            input_ports=data['input_ports'],
            output_ports=data['output_ports'],
            hg_lg_enabled=data.get('hg_lg_enabled', False),
            test_enables=data.get('test_enables', {
                's_parameters': True,
                'compression': True,
                'linearity': True,
                'noise_figure': True,
                'spurious': False,
                'psd': False
            }),
            board_bringup=self._dict_to_test_stage(data.get('board_bringup', {})),
            sit=self._dict_to_test_stage(data.get('sit', {})),
            test_campaign=self._dict_to_test_stage(data.get('test_campaign', {}))
        )
    
    def _dict_to_test_stage(self, data: Dict[str, Any]) -> TestStageRequirements:
        """Convert dictionary to TestStageRequirements."""
        return TestStageRequirements(
            gain_min_db=data.get('gain_min_db', 0.0),
            gain_max_db=data.get('gain_max_db', 0.0),
            gain_flatness_db=data.get('gain_flatness_db', 0.0),
            vswr_max=data.get('vswr_max', 0.0),
            out_of_band_requirements=[
                OutOfBandRequirement(
                    freq_min=req['freq_min'],
                    freq_max=req['freq_max'],
                    rejection_db=req['rejection_db']
                )
                for req in data.get('out_of_band_requirements', [])
            ],
            p1db_min_dbm=data.get('p1db_min_dbm', 0.0),
            pin_pout_im3_requirements=[
                PinPoutIM3Requirement(
                    pin_dbm=req['pin_dbm'],
                    pout_min_dbm=req['pout_min_dbm'],
                    im3_max_dbc=req['im3_max_dbc']
                )
                for req in data.get('pin_pout_im3_requirements', [])
            ],
            nf_max_db=data.get('nf_max_db', 0.0)
        )



