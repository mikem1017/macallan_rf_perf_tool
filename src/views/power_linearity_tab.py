"""
Power/Linearity test tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from src.views.compliance_table import ComplianceTable
from src.views.plot_window_simple import PlotWindow
from src.controllers.file_parser import FileParser
from src.utils.csv_reader import CSVReader
from src.controllers.power_processor import PowerProcessor
from src.constants import TEST_STAGES, DEFAULT_TEST_STAGE, TEST_STAGE_DISPLAY_NAMES
from typing import List, Dict, Any, Optional

class PowerLinearityTab(QWidget):
    """Power/Linearity test tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.file_parser = FileParser()
        self.csv_reader = CSVReader()
        self.power_processor = PowerProcessor()
        
        self.loaded_files = []
        self.file_metadata = []
        self.power_data = None
        self.temperature_data = []
        self.processed_results = {}
        self.plot_windows = []
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # File loading section
        file_group = QGroupBox("File Loading")
        file_layout = QVBoxLayout(file_group)
        
        # File selection
        file_select_layout = QHBoxLayout()
        self.load_files_btn = QPushButton("Load CSV Files")
        self.load_files_btn.clicked.connect(self.load_files)
        file_select_layout.addWidget(self.load_files_btn)
        
        self.clear_files_btn = QPushButton("Clear Files")
        self.clear_files_btn.clicked.connect(self.clear_files)
        file_select_layout.addWidget(self.clear_files_btn)
        
        file_select_layout.addStretch()
        file_layout.addLayout(file_select_layout)
        
        # File info display
        self.file_info_text = QTextEdit()
        self.file_info_text.setMaximumHeight(100)
        self.file_info_text.setReadOnly(True)
        self.file_info_text.setPlaceholderText("No files loaded")
        file_layout.addWidget(self.file_info_text)
        
        # Notes field
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes for this test...")
        notes_layout.addWidget(self.notes_edit)
        file_layout.addLayout(notes_layout)
        
        layout.addWidget(file_group)
        
        # Plot buttons section
        plot_group = QGroupBox("Plots")
        plot_layout = QGridLayout(plot_group)
        
        self.full_power_sweep_btn = QPushButton("Full Power Sweep")
        self.full_power_sweep_btn.clicked.connect(lambda: self.open_plots("full_power_sweep"))
        plot_layout.addWidget(self.full_power_sweep_btn, 0, 0)
        
        self.operational_range_btn = QPushButton("Operational Power")
        self.operational_range_btn.clicked.connect(lambda: self.open_plots("operational_range"))
        plot_layout.addWidget(self.operational_range_btn, 0, 1)
        
        self.linearity_btn = QPushButton("Full Linearity Sweep")
        self.linearity_btn.clicked.connect(lambda: self.open_plots("linearity"))
        plot_layout.addWidget(self.linearity_btn, 1, 0)
        
        self.im3_operational_btn = QPushButton("Operational Linearity")
        self.im3_operational_btn.clicked.connect(lambda: self.open_plots("im3_operational_range"))
        plot_layout.addWidget(self.im3_operational_btn, 1, 1)
        
        layout.addWidget(plot_group)
        
        # Compliance table
        compliance_group = QGroupBox("Compliance Table")
        compliance_layout = QVBoxLayout(compliance_group)
        
        self.compliance_table = ComplianceTable()
        compliance_layout.addWidget(self.compliance_table)
        
        layout.addWidget(compliance_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect to main window signals
        if self.main_window:
            self.main_window.dut_changed.connect(self.on_dut_changed)
            self.main_window.test_stage_changed.connect(self.on_test_stage_changed)
    
    def on_dut_changed(self, dut_name: str):
        """Handle DUT selection change."""
        self.update_file_loading_capability()
        self.update_plot_buttons()
    
    def on_test_stage_changed(self, test_stage: str):
        """Handle test stage change."""
        print(f"DEBUG: Power/Linearity tab received test stage change: {test_stage}")
        print(f"DEBUG: processed_results available: {bool(self.processed_results)}")
        # Update plot buttons for new test stage
        self.update_plot_buttons()
        # Re-process data with new test stage if we have processed results
        if self.processed_results:
            print("DEBUG: Re-processing power/linearity data with new test stage")
            self.reprocess_data_with_new_test_stage(test_stage)
    
    def reprocess_data_with_new_test_stage(self, test_stage: str):
        """Re-process all loaded data with the new test stage."""
        if not self.processed_results or not self.main_window:
            return
        
        dut_config = self.main_window.get_current_dut_config()
        if not dut_config:
            return
        
        print(f"DEBUG: Re-processing {len(self.processed_results)} files with test stage: {test_stage}")
        
        # Re-process each file with the new test stage
        for file_type, file_results in self.processed_results.items():
            # Get the original power data (we need to store this during initial processing)
            if hasattr(self, 'original_power_data') and file_type in self.original_power_data:
                power_data = self.original_power_data[file_type]
                # Re-process with new test stage
                new_results = self.power_processor.process_power_linearity(
                    power_data, dut_config, test_stage)
                self.processed_results[file_type] = new_results
                print(f"DEBUG: Re-processed {file_type} with test stage {test_stage}")
        
        # Update the compliance table with the new results
        self.update_compliance_table()
    
    def update_file_loading_capability(self):
        """Update file loading capability based on selected DUT."""
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        
        if dut_config:
            if dut_config.hg_lg_enabled:
                self.load_files_btn.setText("Load CSV Files (4 files)")
                self.load_files_btn.setToolTip("Load 4 files: PRI HG, PRI LG, RED HG, RED LG")
            else:
                self.load_files_btn.setText("Load CSV Files (2 files)")
                self.load_files_btn.setToolTip("Load 2 files: PRI, RED")
        else:
            self.load_files_btn.setText("Load CSV Files")
            self.load_files_btn.setToolTip("Select a DUT first")
            self.load_files_btn.setEnabled(True)  # Always enabled
    
    def update_plot_buttons(self):
        """Update plot button states based on DUT configuration."""
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        
        if dut_config:
            # Enable compression/linearity buttons based on test enables
            compression_enabled = dut_config.test_enables.get('compression', False)
            linearity_enabled = dut_config.test_enables.get('linearity', False)
            
            self.full_power_sweep_btn.setEnabled(compression_enabled)
            self.linearity_btn.setEnabled(linearity_enabled)
            
            # Check if operational range button should be enabled
            # It's enabled if compression is enabled AND there are power/linearity requirements
            test_stage = self.main_window.current_test_stage if self.main_window else "board_bringup"
            if test_stage == "board_bringup":
                requirements = dut_config.board_bringup
            elif test_stage == "sit":
                requirements = dut_config.sit
            elif test_stage == "test_campaign":
                requirements = dut_config.test_campaign
            else:
                requirements = dut_config.board_bringup
            
            has_power_requirements = len(requirements.pin_pout_im3_requirements) > 0
            self.operational_range_btn.setEnabled(compression_enabled and has_power_requirements)
            self.im3_operational_btn.setEnabled(linearity_enabled and has_power_requirements)
        else:
            self.full_power_sweep_btn.setEnabled(False)
            self.operational_range_btn.setEnabled(False)
            self.linearity_btn.setEnabled(False)
            self.im3_operational_btn.setEnabled(False)
    
    def load_files(self):
        """Load CSV files."""
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        if not dut_config:
            QMessageBox.warning(self, "No DUT Selected", "Please select a DUT type first.")
            return
        
        # Determine number of files needed
        num_files = 4 if dut_config.hg_lg_enabled else 2
        
        # Open file dialog - start from user's home directory to avoid cross-platform path issues
        import os
        start_dir = os.path.expanduser("~")
        files, _ = QFileDialog.getOpenFileNames(
            self, f"Select {num_files} Power/Linearity Files", start_dir, 
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Supported Files (*.xlsx *.xls *.csv)")
        
        if not files:
            return
        
        # Validate file count
        if len(files) != num_files:
            QMessageBox.warning(self, "Wrong Number of Files", 
                              f"Please select exactly {num_files} files.")
            return
        
        # Validate that all files exist (cross-platform compatibility)
        for file_path in files:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Not Found", 
                                  f"File does not exist: {file_path}")
                return
        
        # Validate and parse files
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            # Parse filenames (placeholder - need CSV filename convention)
            # For now, assume files are valid
            metadata_list = []
            for file_path in files:
                # Extract metadata from CSV file
                metadata = self.csv_reader.extract_csv_metadata(file_path)
                metadata_list.append(metadata)
            
            self.progress_bar.setValue(25)
            
            # Process all power/linearity files (PRI, RED, etc.)
            self.processed_results = {}
            self.temperature_data = {}
            self.original_power_data = {}  # Store original power data for re-processing
            
            for i, file_path in enumerate(files):
                # Read power/linearity file
                power_data = self.csv_reader.read_power_linearity_csv(file_path)
                if not power_data:
                    QMessageBox.warning(self, "File Read Error", 
                                      f"Could not read power/linearity file: {file_path}")
                    self.progress_bar.setVisible(False)
                    return
                
                # Extract temperature data
                temp_data = self.extract_temperature_data(file_path)
                
                # Process power/linearity data
                test_stage = self.main_window.current_test_stage if self.main_window else DEFAULT_TEST_STAGE
                file_results = self.power_processor.process_power_linearity(
                    power_data, dut_config, test_stage)
                
                # Determine file type (PRI, RED, etc.) from metadata
                file_metadata = self.csv_reader.extract_csv_metadata(file_path)
                file_type = file_metadata.get('pri_red', f'FILE_{i+1}')
                
                # Store results with file type as key
                self.processed_results[file_type] = file_results
                self.temperature_data[file_type] = temp_data
                self.original_power_data[file_type] = power_data  # Store original data
            
            self.progress_bar.setValue(50)
            
            self.progress_bar.setValue(75)
            
            # Update UI
            self.loaded_files = files
            self.file_metadata = metadata_list
            self.update_file_info()
            self.update_compliance_table()
            
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", "Files loaded and processed successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing files: {e}")
        finally:
            self.progress_bar.setVisible(False)
    
    def extract_temperature_data(self, file_path: str) -> List[float]:
        """Extract temperature data from CSV or Excel file."""
        try:
            import pandas as pd
            # Read file based on extension
            if file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Get temperature data for each frequency
            temperature = df['Thermister Calc (C)'].tolist()
            
            # Group by frequency (assuming 3 frequencies)
            freq_groups = []
            for i in range(3):  # 3 frequencies
                freq_indices = list(range(i, len(temperature), 3))
                freq_temp = [temperature[j] for j in freq_indices]
                freq_groups.append(freq_temp)
            
            return freq_groups
            
        except Exception as e:
            print(f"Error extracting temperature data: {e}")
            return []
    
    def update_file_info(self):
        """Update file information display."""
        if not self.file_metadata:
            self.file_info_text.setPlainText("No files loaded")
            return
        
        info_lines = []
        for metadata in self.file_metadata:
            line_parts = []
            
            # Format serial number (handle SN/EM prefixes correctly)
            if 'serial' in metadata:
                serial = str(metadata['serial'])
                # Handle SNEM case (e.g., SNEM-0003 -> EM0003)
                if serial.startswith('SNEM'):
                    serial = 'EM' + serial[4:]  # Remove "SN" from "SNEM-0003"
                # Handle SNSN case (e.g., SNSN0003 -> SN0003)
                elif serial.startswith('SNSN'):
                    serial = 'SN' + serial[4:]  # Remove first "SN" from "SNSN0003"
                # Handle SN case (e.g., SN0003 -> SN0003, keep as is)
                elif serial.startswith('SN'):
                    serial = serial  # Keep SN prefix
                # Handle EM case (e.g., EM0003 -> EM0003, keep as is)
                elif serial.startswith('EM'):
                    serial = serial  # Keep EM prefix
                line_parts.append(f"Serial: {serial}")
            
            # Format part number (remove redundant "L" prefix)
            if 'part_number' in metadata:
                part_num = str(metadata['part_number'])
                if part_num.startswith('L'):
                    part_num = part_num[1:]  # Remove "L" prefix
                line_parts.append(f"Part Number: L{part_num}")
            
            # Format date
            if 'date' in metadata:
                line_parts.append(f"Date: {metadata['date']}")
            
            # Format PRI/RED status
            if 'pri_red' in metadata:
                line_parts.append(f"Type: {metadata['pri_red']}")
            
            # Format temperature
            if 'temperature' in metadata:
                line_parts.append(f"Temperature: {metadata['temperature']}")
            
            info_lines.append(" | ".join(line_parts))
        
        self.file_info_text.setPlainText("\n".join(info_lines))
    
    def update_compliance_table(self):
        """Update the compliance table with processed results."""
        if not self.processed_results:
            self.compliance_table.clear_data()
            return
        
        # Prepare compliance data
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        test_stage = self.main_window.current_test_stage if self.main_window else "board_bringup"
        
        if not dut_config:
            return
        
        # Get requirements for current test stage
        if test_stage == TEST_STAGES["board_bringup"]:
            requirements = dut_config.board_bringup
        elif test_stage == TEST_STAGES["sit"]:
            requirements = dut_config.sit
        elif test_stage == TEST_STAGES["test_campaign"]:
            requirements = dut_config.test_campaign
        else:
            return
        
        compliance_data = []
        
        # Get PRI and RED data
        pri_data = self.processed_results.get('PRI', {})
        red_data = self.processed_results.get('RED', {})
        
        # Add P1dB requirements
        for freq, result_data in pri_data.items():
            red_result_data = red_data.get(freq, {}) if red_data else {}
            
            # PRI data
            pri_p1db = result_data.get('p1db', 0.0)
            pri_p1db_pass = result_data.get('p1db_pass', False)
            
            # RED data
            red_p1db = red_result_data.get('p1db', 0.0) if red_result_data else 0.0
            red_p1db_pass = red_result_data.get('p1db_pass', False) if red_result_data else False
            
            compliance_data.append({
                'requirement': f"P1dB @ {float(freq):.2f} GHz",
                'limit': f">= {requirements.p1db_min_dbm:.2f} dBm",
                'pri': f"{pri_p1db:.2f} dBm",
                'pri_status': "Pass" if pri_p1db_pass else "Fail",
                'red': f"{red_p1db:.2f} dBm" if red_result_data else "N/A",
                'red_status': "Pass" if red_p1db_pass else ("Fail" if red_result_data else "N/A")
            })
        
        # Add Pin-Pout-IM3 requirements
        for freq, result_data in pri_data.items():
            red_result_data = red_data.get(freq, {}) if red_data else {}
            
            for i, req_result in enumerate(result_data.get('pin_pout_im3_results', [])):
                red_req_result = red_result_data.get('pin_pout_im3_results', [])[i] if red_result_data and i < len(red_result_data.get('pin_pout_im3_results', [])) else None
                
                # Pout requirement
                compliance_data.append({
                    'requirement': f"Pout @ Pin={req_result['pin_dbm']:.2f}dBm, {float(freq):.2f}GHz",
                    'limit': f">= {req_result['pout_required']:.2f} dBm",
                    'pri': f"{req_result['pout_measured']:.2f} dBm",
                    'pri_status': "Pass" if req_result['pout_pass'] else "Fail",
                    'red': f"{red_req_result['pout_measured']:.2f} dBm" if red_req_result else "N/A",
                    'red_status': "Pass" if red_req_result and red_req_result['pout_pass'] else ("Fail" if red_req_result else "N/A")
                })
                
                # IM3 requirement
                compliance_data.append({
                    'requirement': f"IM3 @ Pin={req_result['pin_dbm']:.2f}dBm, {float(freq):.2f}GHz",
                    'limit': f"< {req_result['im3_required']:.2f} dBc",
                    'pri': f"{req_result['im3_measured']:.2f} dBc",
                    'pri_status': "Pass" if req_result['im3_pass'] else "Fail",
                    'red': f"{red_req_result['im3_measured']:.2f} dBc" if red_req_result else "N/A",
                    'red_status': "Pass" if red_req_result and red_req_result['im3_pass'] else ("Fail" if red_req_result else "N/A")
                })
        
        # Set compliance table data
        self.compliance_table.set_data(compliance_data, 
                                     ["Requirement", "Limit", "PRI", "PRI Status", "RED", "RED Status"],
                                     dut_config.hg_lg_enabled)
    
    def open_plots(self, plot_type: str):
        """Open plot windows for the specified plot type."""
        if not self.processed_results:
            QMessageBox.warning(self, "No Data", "Please load files first.")
            return
        
        # Get DUT config
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        if not dut_config:
            QMessageBox.warning(self, "No DUT Config", "Please select a DUT configuration.")
            return
        
        # Create a single plot window with all frequencies and file types
        plot_window = PlotWindow(self)
        
        # Get all frequencies from PRI data (assuming all files have same frequencies)
        pri_data = self.processed_results.get('PRI', {})
        red_data = self.processed_results.get('RED', {})
        
        # Collect all plot data for all frequencies and file types
        all_plot_data = {}
        
        # Prepare data in the format expected by power processor: {file_key: {freq: result_data}}
        all_file_data = {}
        if pri_data:
            all_file_data['PRI'] = pri_data
        if red_data:
            all_file_data['RED'] = red_data
        
        # Get plot data for all files and frequencies
        test_stage = self.main_window.current_test_stage if self.main_window else "board_bringup"
        plot_data_dict = self.power_processor.get_plot_data(
            all_file_data, plot_type, dut_config,
            self.temperature_data.get('PRI', []) if self.temperature_data else None, test_stage)
        
        # The plot_data_dict now contains keys like "2.2_PRI", "2.2_RED", etc.
        all_plot_data = plot_data_dict
        
        # Prepare metadata
        metadata = self.prepare_metadata()
        
        # Plot all data on single window
        if all_plot_data:
            plot_window.plot_multiple_data(all_plot_data, metadata)
            plot_window.show()
            self.plot_windows.append(plot_window)
        else:
            print("DEBUG: No plot data available")
    
    def prepare_metadata(self) -> Dict[str, str]:
        """Prepare metadata for plots."""
        metadata = {}
        
        if self.file_metadata:
            first_metadata = self.file_metadata[0]
            if 'serial' in first_metadata:
                serial = str(first_metadata['serial'])
                # Handle SNEM case (e.g., SNEM-0003 -> EM0003)
                if serial.startswith('SNEM'):
                    serial = 'EM' + serial[4:]  # Remove "SN" from "SNEM-0003"
                # Handle SNSN case (e.g., SNSN0003 -> SN0003)
                elif serial.startswith('SNSN'):
                    serial = 'SN' + serial[4:]  # Remove first "SN" from "SNSN0003"
                # Handle SN case (e.g., SN0003 -> SN0003, keep as is)
                elif serial.startswith('SN'):
                    serial = serial  # Keep SN prefix
                # Handle EM case (e.g., EM0003 -> EM0003, keep as is)
                elif serial.startswith('EM'):
                    serial = serial  # Keep EM prefix
                metadata['serial'] = serial
            if 'part_number' in first_metadata:
                metadata['part_number'] = f"L{first_metadata['part_number']}"
            if 'date' in first_metadata:
                metadata['date'] = first_metadata['date']
            if 'pri_red' in first_metadata:
                metadata['pri_red'] = first_metadata['pri_red']
            if 'temperature' in first_metadata:
                metadata['temperature'] = first_metadata['temperature']
        
        # Add test stage
        if self.main_window:
            stage_mapping = TEST_STAGE_DISPLAY_NAMES
            metadata['test_stage'] = stage_mapping.get(self.main_window.current_test_stage, "Unknown")
        
        # Add notes
        if self.notes_edit.text():
            metadata['notes'] = self.notes_edit.text()
        
        return metadata
    
    def clear_files(self):
        """Clear loaded files and reset UI."""
        self.loaded_files = []
        self.file_metadata = []
        self.power_data = None
        self.temperature_data = []
        self.processed_results = {}
        self.notes_edit.clear()
        
        # Close plot windows
        for window in self.plot_windows:
            window.close()
        self.plot_windows = []
        
        # Reset UI
        self.file_info_text.setPlainText("No files loaded")
        self.compliance_table.clear_data()
    
    def clear_data(self):
        """Clear all data (called from main window)."""
        self.clear_files()
