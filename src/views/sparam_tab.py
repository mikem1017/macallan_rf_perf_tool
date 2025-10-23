"""
S-Parameters test tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from src.views.compliance_table import ComplianceTable
from src.views.plot_window_simple import PlotWindow
from src.controllers.file_parser import FileParser
from src.utils.touchstone_reader import TouchstoneReader
from src.controllers.sparam_processor import SParameterProcessor
from src.models.dut_config import DUTConfiguration
from src.constants import TEST_STAGES, DEFAULT_TEST_STAGE, TEST_STAGE_DISPLAY_NAMES
from typing import List, Dict, Any, Optional

class SParamTab(QWidget):
    """S-Parameters test tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.file_parser = FileParser()
        self.touchstone_reader = TouchstoneReader()
        self.sparam_processor = SParameterProcessor()
        
        self.loaded_files = []
        self.file_metadata = []
        self.s_param_data = None
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
        self.load_files_btn = QPushButton("Load Touchstone Files")
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
        
        self.wideband_gain_btn = QPushButton("Wideband Gain")
        self.wideband_gain_btn.clicked.connect(lambda: self.open_plot("wideband_gain"))
        plot_layout.addWidget(self.wideband_gain_btn, 0, 0)
        
        self.wideband_vswr_btn = QPushButton("Wideband VSWR")
        self.wideband_vswr_btn.clicked.connect(lambda: self.open_plot("wideband_vswr"))
        plot_layout.addWidget(self.wideband_vswr_btn, 0, 1)
        
        self.operational_gain_btn = QPushButton("Operational Gain")
        self.operational_gain_btn.clicked.connect(lambda: self.open_plot("operational_gain"))
        plot_layout.addWidget(self.operational_gain_btn, 1, 0)
        
        self.operational_vswr_btn = QPushButton("Operational VSWR")
        self.operational_vswr_btn.clicked.connect(lambda: self.open_plot("operational_vswr"))
        plot_layout.addWidget(self.operational_vswr_btn, 1, 1)
        
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
    
    def on_test_stage_changed(self, test_stage: str):
        """Handle test stage change."""
        # Update compliance table if we have processed results
        if self.processed_results:
            self.update_compliance_table()
    
    def update_file_loading_capability(self):
        """Update file loading capability based on selected DUT."""
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        
        if dut_config:
            if dut_config.hg_lg_enabled:
                self.load_files_btn.setText("Load Touchstone Files (4 files)")
                self.load_files_btn.setToolTip("Load 4 files: PRI HG, PRI LG, RED HG, RED LG")
            else:
                self.load_files_btn.setText("Load Touchstone Files (2 files)")
                self.load_files_btn.setToolTip("Load 2 files: PRI, RED")
        else:
            self.load_files_btn.setText("Load Touchstone Files")
            self.load_files_btn.setToolTip("Select a DUT first")
            self.load_files_btn.setEnabled(True)  # Always enabled
    
    def load_files(self):
        """Load Touchstone files."""
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        if not dut_config:
            QMessageBox.warning(self, "No DUT Selected", "Please select a DUT type first.")
            return
        
        # Determine number of files needed
        num_files = 4 if dut_config.hg_lg_enabled else 2
        
        # Open file dialog - start from user's home directory to avoid cross-platform path issues
        import os
        from PyQt6.QtCore import QSettings
        
        # Clear any stored file dialog state to prevent cross-platform path issues
        QSettings().remove("fileDialog/lastDirectory")
        QSettings().remove("fileDialog/recentFiles")
        
        start_dir = os.path.expanduser("~")
        files, _ = QFileDialog.getOpenFileNames(
            self, f"Select {num_files} Touchstone Files", start_dir, 
            "Touchstone Files (*.s1p *.s2p *.s3p *.s4p)")
        
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
            # Parse filenames
            is_valid, message, metadata_list = self.file_parser.validate_file_set(
                files, dut_config.hg_lg_enabled)
            
            if not is_valid:
                QMessageBox.warning(self, "File Validation Error", message)
                self.progress_bar.setVisible(False)
                return
            
            self.progress_bar.setValue(25)
            
            # Read all Touchstone files
            self.s_param_data_list = []
            for i, file_path in enumerate(files):
                s_param_data = self.touchstone_reader.read_touchstone_file(file_path)
                if not s_param_data:
                    QMessageBox.warning(self, "File Read Error", 
                                      f"Could not read Touchstone file: {file_path}")
                    self.progress_bar.setVisible(False)
                    return
                self.s_param_data_list.append(s_param_data)
                self.progress_bar.setValue(25 + (i + 1) * 15)
            
            # Process S-parameters for all files
            test_stage = self.main_window.current_test_stage if self.main_window else DEFAULT_TEST_STAGE
            self.processed_results = {}
            
            for i, s_param_data in enumerate(self.s_param_data_list):
                metadata = metadata_list[i] if i < len(metadata_list) else None
                results = self.sparam_processor.process_s_parameters(
                    s_param_data, dut_config, test_stage)
                
                # Store results with metadata
                file_key = f"{metadata.pri_red}_{metadata.hg_lg}" if metadata and metadata.hg_lg else metadata.pri_red if metadata else f"file_{i}"
                self.processed_results[file_key] = results
            
            self.progress_bar.setValue(75)
            
            # Update UI
            self.loaded_files = files
            self.file_metadata = metadata_list
            self.update_file_info()
            self.update_compliance_table()
            self.enable_plot_buttons()
            
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", "Files loaded and processed successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing files: {e}")
        finally:
            self.progress_bar.setVisible(False)
    
    def update_file_info(self):
        """Update file information display."""
        if not self.file_metadata:
            self.file_info_text.setPlainText("No files loaded")
            return
        
        info_lines = []
        for metadata in self.file_metadata:
            # Format date
            date_formatted = f"{metadata.date_code[:4]}-{metadata.date_code[4:6]}-{metadata.date_code[6:8]}"
            
            # Clean up serial number (remove redundant SN prefix)
            serial = metadata.serial_number
            if serial.startswith('SNSN'):
                serial = 'SN' + serial[4:]
            
            # Clean up part number (remove redundant L prefix)
            part_number = metadata.part_number
            if part_number.startswith('LL'):
                part_number = 'L' + part_number[2:]
            
            # Build professional metadata line
            line_parts = []
            line_parts.append(f"Type: {metadata.pri_red}")
            if metadata.hg_lg:
                line_parts.append(f"Grade: {metadata.hg_lg}")
            line_parts.append(f"Serial: {serial}")
            line_parts.append(f"Part Number: {part_number}")
            line_parts.append(f"Date: {date_formatted}")
            
            info_lines.append(" | ".join(line_parts))
        
        self.file_info_text.setPlainText("\n".join(info_lines))
    
    def update_compliance_table(self):
        """Update the compliance table with processed results."""
        if not self.processed_results:
            self.compliance_table.clear_data()
            return
        
        # Prepare compliance data
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        test_stage = self.main_window.current_test_stage if self.main_window else DEFAULT_TEST_STAGE
        
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
        
        # Add S-parameter requirements
        # Get PRI and RED results
        pri_results = self.processed_results.get('PRI', {})
        red_results = self.processed_results.get('RED', {})
        
        # Use PRI results to determine which S-parameters to process
        for s_param_name, pri_data in pri_results.items():
            # Get RED data if available
            red_data = red_results.get(s_param_name, None)
            
            # Determine parameter type
            parameter_type = pri_data.get('parameter_type', 'unknown')
            is_transmission = parameter_type == 'transmission'
            is_reflection = parameter_type == 'reflection'
            
            if is_transmission:
                # For transmission parameters (Sxy where x≠y), show gain-related requirements
                
                # PRI gain requirement
                pri_gain_pass = (pri_data['in_band_gain_min'] >= requirements.gain_min_db and 
                               pri_data['in_band_gain_max'] <= requirements.gain_max_db)
                
                # RED gain requirement (if available)
                if red_data:
                    red_gain_pass = (red_data['in_band_gain_min'] >= requirements.gain_min_db and 
                                   red_data['in_band_gain_max'] <= requirements.gain_max_db)
                    red_gain_text = f"{red_data['in_band_gain_min']:.1f} to {red_data['in_band_gain_max']:.1f} dB"
                    red_gain_status = "Pass" if red_gain_pass else "Fail"
                else:
                    red_gain_text = "N/A"
                    red_gain_status = "N/A"
                
                compliance_data.append({
                    'requirement': f"{s_param_name} Gain",
                    'limit': f"{requirements.gain_min_db:.1f} to {requirements.gain_max_db:.1f} dB",
                    'pri': f"{pri_data['in_band_gain_min']:.1f} to {pri_data['in_band_gain_max']:.1f} dB",
                    'pri_status': "Pass" if pri_gain_pass else "Fail",
                    'red': red_gain_text,
                    'red_status': red_gain_status
                })
                
                # Gain flatness
                pri_flatness_pass = pri_data['flatness'] <= requirements.gain_flatness_db
                if red_data:
                    red_flatness_pass = red_data['flatness'] <= requirements.gain_flatness_db
                    red_flatness_text = f"{red_data['flatness']:.1f} dB"
                    red_flatness_status = "Pass" if red_flatness_pass else "Fail"
                else:
                    red_flatness_text = "N/A"
                    red_flatness_status = "N/A"
                
                compliance_data.append({
                    'requirement': f"{s_param_name} Flatness",
                    'limit': f"<= {requirements.gain_flatness_db:.1f} dB",
                    'pri': f"{pri_data['flatness']:.1f} dB",
                    'pri_status': "Pass" if pri_flatness_pass else "Fail",
                    'red': red_flatness_text,
                    'red_status': red_flatness_status
                })
                
                # Out-of-band requirements - only show if they exist
                if pri_data.get('out_of_band_rejections'):
                    for i, pri_oob_result in enumerate(pri_data['out_of_band_rejections']):
                        red_oob_result = red_data['out_of_band_rejections'][i] if red_data and i < len(red_data['out_of_band_rejections']) else None
                        
                        if red_oob_result:
                            red_oob_text = f"{red_oob_result['rejection_db']:.1f} dBc"
                            red_oob_status = "Pass" if red_oob_result['pass'] else "Fail"
                        else:
                            red_oob_text = "N/A"
                            red_oob_status = "N/A"
                        
                        compliance_data.append({
                            'requirement': f"{s_param_name} OoB {i+1}",
                            'limit': f">= {pri_oob_result['requirement']:.1f} dBc",
                            'pri': f"{pri_oob_result['rejection_db']:.1f} dBc",
                            'pri_status': "Pass" if pri_oob_result['pass'] else "Fail",
                            'red': red_oob_text,
                            'red_status': red_oob_status
                        })
            
            elif is_reflection:
                # For reflection parameters (Sxx), only show VSWR requirements
                if pri_data['vswr_max'] > 0:
                    pri_vswr_pass = pri_data['vswr_max'] <= requirements.vswr_max
                    if red_data and red_data['vswr_max'] > 0:
                        red_vswr_pass = red_data['vswr_max'] <= requirements.vswr_max
                        red_vswr_text = f"{red_data['vswr_max']:.1f}"
                        red_vswr_status = "Pass" if red_vswr_pass else "Fail"
                    else:
                        red_vswr_text = "N/A"
                        red_vswr_status = "N/A"
                    
                    compliance_data.append({
                        'requirement': f"{s_param_name} VSWR",
                        'limit': f"<= {requirements.vswr_max:.1f}",
                        'pri': f"{pri_data['vswr_max']:.1f}",
                        'pri_status': "Pass" if pri_vswr_pass else "Fail",
                        'red': red_vswr_text,
                        'red_status': red_vswr_status
                    })
        
        # Set compliance table data
        self.compliance_table.set_data(compliance_data, 
                                     ["Requirement", "Limit", "PRI", "PRI Status", "RED", "RED Status"],
                                     dut_config.hg_lg_enabled)
    
    def enable_plot_buttons(self):
        """Enable plot buttons when data is loaded."""
        enabled = bool(self.processed_results)
        self.wideband_gain_btn.setEnabled(enabled)
        self.wideband_vswr_btn.setEnabled(enabled)
        self.operational_gain_btn.setEnabled(enabled)
        self.operational_vswr_btn.setEnabled(enabled)
    
    def open_plot(self, plot_type: str):
        """Open a plot window."""
        if not self.processed_results:
            QMessageBox.warning(self, "No Data", "Please load files first.")
            return
        
        # Create plot window
        plot_window = PlotWindow(self)
        
        # Get plot data
        dut_config = self.main_window.get_current_dut_config() if self.main_window else None
        test_stage = self.main_window.current_test_stage if self.main_window else DEFAULT_TEST_STAGE
        plot_data = self.sparam_processor.get_plot_data(
            self.processed_results, plot_type, dut_config, test_stage)
        
        # Prepare metadata
        metadata = self.prepare_metadata()
        
        # Plot the data
        if plot_data:
            # Plot all S-parameters in a single plot
            plot_window.plot_multiple_data(plot_data, metadata)
        
        plot_window.show()
        self.plot_windows.append(plot_window)
    
    def prepare_metadata(self) -> Dict[str, str]:
        """Prepare metadata for plots."""
        metadata = {}
        
        if self.file_metadata:
            first_metadata = self.file_metadata[0]
            metadata['serial'] = f"SN{first_metadata.serial_number}"
            metadata['part_number'] = f"L{first_metadata.part_number}"
            
            # Format date
            date_formatted = f"{first_metadata.date_code[:4]}-{first_metadata.date_code[4:6]}-{first_metadata.date_code[6:8]}"
            metadata['date'] = date_formatted
            
            metadata['pri_red'] = first_metadata.pri_red
            if first_metadata.hg_lg:
                metadata['pri_red'] += f" {first_metadata.hg_lg}"
        
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
        self.s_param_data = None
        self.processed_results = {}
        self.notes_edit.clear()
        
        # Close plot windows
        for window in self.plot_windows:
            window.close()
        self.plot_windows = []
        
        # Reset UI
        self.file_info_text.setPlainText("No files loaded")
        self.compliance_table.clear_data()
        self.enable_plot_buttons()
    
    def clear_data(self):
        """Clear all data (called from main window)."""
        self.clear_files()
