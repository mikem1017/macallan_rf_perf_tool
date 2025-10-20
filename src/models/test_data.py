"""
Test data models for Macallan RF Performance Tool
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import sqlite3
import json
import os

@dataclass
class FileMetadata:
    """Metadata extracted from filename."""
    date_code: str  # YYYYMMDD
    serial_number: str  # SNXXXX
    part_number: str  # LXXXXXX
    pri_red: str  # PRI or RED
    hg_lg: Optional[str] = None  # HG, LG, or None

@dataclass
class SParameterData:
    """S-parameter measurement data."""
    frequency: List[float]  # GHz
    s_parameters: Dict[str, List[complex]]  # S11, S21, etc.
    format: str  # mag/deg, dB/deg, real/imag

@dataclass
class PowerLinearityData:
    """Power and linearity measurement data."""
    frequency: List[float]  # GHz
    pin: List[float]  # dBm
    pout_single_tone: List[float]  # dBm
    im3: List[float]  # dBc
    im5: List[float]  # dBc
    test_type: List[str]  # "single-tone" or "two-tone"

@dataclass
class NoiseFigureData:
    """Noise figure measurement data."""
    frequency: List[float]  # GHz
    nf: List[float]  # dB

@dataclass
class TestResults:
    """Complete test results for a test run."""
    timestamp: datetime
    dut_name: str
    test_stage: str  # board_bringup, sit, test_campaign
    files: List[FileMetadata]
    
    # Data
    s_param_data: Optional[SParameterData] = None
    power_data: Optional[PowerLinearityData] = None
    nf_data: Optional[NoiseFigureData] = None
    
    # Results
    s_param_results: Dict[str, Any] = field(default_factory=dict)
    power_results: Dict[str, Any] = field(default_factory=dict)
    nf_results: Dict[str, Any] = field(default_factory=dict)

class TestDatabase:
    """SQLite database for storing test results."""
    
    def __init__(self, db_file: str = "data/test_results.db"):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Test runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    dut_name TEXT NOT NULL,
                    serial_number TEXT,
                    part_number TEXT,
                    date_code TEXT,
                    test_stage TEXT NOT NULL,
                    pri_red TEXT,
                    hg_lg TEXT
                )
            ''')
            
            # S-parameter results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sparam_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_run_id INTEGER NOT NULL,
                    s_param_name TEXT NOT NULL,
                    in_band_gain_min REAL,
                    in_band_gain_max REAL,
                    flatness REAL,
                    vswr_max REAL,
                    oob_rejections TEXT,
                    pass_fail TEXT,
                    FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
                )
            ''')
            
            # Power results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS power_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_run_id INTEGER NOT NULL,
                    frequency REAL NOT NULL,
                    p1db REAL,
                    pout_at_pin TEXT,
                    im3_at_pin TEXT,
                    pass_fail TEXT,
                    FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
                )
            ''')
            
            # Noise figure results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nf_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_run_id INTEGER NOT NULL,
                    nf_max REAL,
                    frequency_at_max REAL,
                    pass_fail TEXT,
                    FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
                )
            ''')
            
            conn.commit()
    
    def save_test_results(self, results: TestResults):
        """Save test results to database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Insert test run
            cursor.execute('''
                INSERT INTO test_runs 
                (timestamp, dut_name, serial_number, part_number, date_code, test_stage, pri_red, hg_lg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                results.timestamp.isoformat(),
                results.dut_name,
                results.files[0].serial_number if results.files else None,
                results.files[0].part_number if results.files else None,
                results.files[0].date_code if results.files else None,
                results.test_stage,
                results.files[0].pri_red if results.files else None,
                results.files[0].hg_lg if results.files else None
            ))
            
            test_run_id = cursor.lastrowid
            
            # Insert S-parameter results
            if results.s_param_results:
                for s_param_name, result_data in results.s_param_results.items():
                    cursor.execute('''
                        INSERT INTO sparam_results 
                        (test_run_id, s_param_name, in_band_gain_min, in_band_gain_max, 
                         flatness, vswr_max, oob_rejections, pass_fail)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_run_id,
                        s_param_name,
                        result_data.get('in_band_gain_min'),
                        result_data.get('in_band_gain_max'),
                        result_data.get('flatness'),
                        result_data.get('vswr_max'),
                        json.dumps(result_data.get('oob_rejections', [])),
                        result_data.get('pass_fail')
                    ))
            
            # Insert power results
            if results.power_results:
                for freq, result_data in results.power_results.items():
                    cursor.execute('''
                        INSERT INTO power_results 
                        (test_run_id, frequency, p1db, pout_at_pin, im3_at_pin, pass_fail)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        test_run_id,
                        freq,
                        result_data.get('p1db'),
                        json.dumps(result_data.get('pout_at_pin', [])),
                        json.dumps(result_data.get('im3_at_pin', [])),
                        result_data.get('pass_fail')
                    ))
            
            # Insert noise figure results
            if results.nf_results:
                cursor.execute('''
                    INSERT INTO nf_results 
                    (test_run_id, nf_max, frequency_at_max, pass_fail)
                    VALUES (?, ?, ?, ?)
                ''', (
                    test_run_id,
                    results.nf_results.get('nf_max'),
                    results.nf_results.get('frequency_at_max'),
                    results.nf_results.get('pass_fail')
                ))
            
            conn.commit()
    
    def get_recent_tests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent test results."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM test_runs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_test_by_id(self, test_id: int) -> Optional[Dict[str, Any]]:
        """Get test results by ID."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM test_runs WHERE id = ?', (test_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None



