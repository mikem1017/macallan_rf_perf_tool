"""
Power/Linearity test tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from src.views.compliance_table import ComplianceTable
from src.views.plot_window import PlotWindow
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
        
        self.compression_btn = QPushButton("Compression Plots")
        self.compression_btn.clicked.connect(lambda: self.open_plots("compression"))
        plot_layout.addWidget(self.compression_btn, 0, 0)
        
        self.linearity_btn = QPushButton("Linearity Plots")
        self.linearity_btn.clicked.connect(lambda: self.open_plots("linearity"))
        plot_layout.addWidget(self.linearity_btn, 0, 1)
        
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
    
    def on_dut_changed(self, dut_name: str):
        """Handle DUT selection change."""
        self.update_file_loading_capability()
        self.update_plot_buttons()
    
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
            self.compression_btn.setEnabled(dut_config.test_enables.get('compression', False))
            self.linearity_btn.setEnabled(dut_config.test_enables.get('linearity', False))
        else:
            self.compression_btn.setEnabled(False)
            self.linearity_btn.setEnabled(False)
    
    def load_files(self):
        """Load CSV files."""
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        if not dut_config:
            QMessageBox.warning(self, "No DUT Selected", "Please select a DUT type first.")
            return
        
        # Determine number of files needed
        num_files = 4 if dut_config.hg_lg_enabled else 2
        
        # Open file dialog
        files, _ = QFileDialog.getOpenFileNames(
            self, f"Select {num_files} CSV Files", "", 
            "CSV Files (*.csv)")
        
        if not files:
            return
        
        # Validate file count
        if len(files) != num_files:
            QMessageBox.warning(self, "Wrong Number of Files", 
                              f"Please select exactly {num_files} files.")
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
            
            # Read CSV files
            self.power_data = self.csv_reader.read_power_linearity_csv(files[0])
            if not self.power_data:
                QMessageBox.warning(self, "File Read Error", 
                                  f"Could not read CSV file: {files[0]}")
                self.progress_bar.setVisible(False)
                return
            
            # Extract temperature data
            self.temperature_data = self.extract_temperature_data(files[0])
            
            self.progress_bar.setValue(50)
            
            # Process power/linearity data
            test_stage = self.main_window.current_test_stage if self.main_window else DEFAULT_TEST_STAGE
            self.processed_results = self.power_processor.process_power_linearity(
                self.power_data, dut_config, test_stage)
            
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
        """Extract temperature data from CSV file."""
        try:
            import pandas as pd
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
            
            if 'serial' in metadata:
                line_parts.append(f"SN{metadata['serial']}")
            if 'part_number' in metadata:
                line_parts.append(f"PN{metadata['part_number']}")
            if 'date' in metadata:
                line_parts.append(metadata['date'])
            if 'pri_red' in metadata:
                line_parts.append(metadata['pri_red'])
            if 'temperature' in metadata:
                line_parts.append(f"Temp: {metadata['temperature']}")
            
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
        
        # Add P1dB requirements
        for freq, result_data in self.processed_results.items():
            compliance_data.append({
                'requirement': f"P1dB @ {freq:.1f} GHz",
                'limit': f">= {requirements.p1db_min_dbm:.1f} dBm",
                'pri': f"{result_data['p1db']:.1f} dBm",
                'pri_status': "Pass" if result_data['p1db_pass'] else "Fail",
                'red': "N/A",  # Would need RED data
                'red_status': "N/A"
            })
        
        # Add Pin-Pout-IM3 requirements
        for freq, result_data in self.processed_results.items():
            for req_result in result_data['pin_pout_im3_results']:
                compliance_data.append({
                    'requirement': f"Pout @ Pin={req_result['pin_dbm']:.1f}dBm, {freq:.1f}GHz",
                    'limit': f">= {req_result['pout_required']:.1f} dBm",
                    'pri': f"{req_result['pout_measured']:.1f} dBm",
                    'pri_status': "Pass" if req_result['pout_pass'] else "Fail",
                    'red': "N/A",
                    'red_status': "N/A"
                })
                
                compliance_data.append({
                    'requirement': f"IM3 @ Pin={req_result['pin_dbm']:.1f}dBm, {freq:.1f}GHz",
                    'limit': f"< {req_result['im3_required']:.1f} dBc",
                    'pri': f"{req_result['im3_measured']:.1f} dBc",
                    'pri_status': "Pass" if req_result['im3_pass'] else "Fail",
                    'red': "N/A",
                    'red_status': "N/A"
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
        
        # Create plot windows for each frequency
        for freq, result_data in self.processed_results.items():
            plot_window = PlotWindow(self)
            
            # Get plot data
            plot_data = self.power_processor.get_plot_data(
                {freq: result_data}, plot_type, 
                self.temperature_data[list(self.processed_results.keys()).index(freq)] if self.temperature_data else None)
            
            # Prepare metadata
            metadata = self.prepare_metadata()
            
            # Plot the data
            if freq in plot_data:
                plot_window.plot_data(plot_data[freq], metadata)
            
            plot_window.show()
            self.plot_windows.append(plot_window)
    
    def prepare_metadata(self) -> Dict[str, str]:
        """Prepare metadata for plots."""
        metadata = {}
        
        if self.file_metadata:
            first_metadata = self.file_metadata[0]
            if 'serial' in first_metadata:
                metadata['serial'] = f"SN{first_metadata['serial']}"
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
