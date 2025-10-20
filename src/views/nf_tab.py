"""
Noise Figure test tab
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from src.views.compliance_table import ComplianceTable
from src.views.plot_window import PlotWindow
from src.controllers.file_parser import FileParser
from src.utils.csv_reader import CSVReader
from src.controllers.nf_processor import NoiseFigureProcessor
from src.constants import TEST_STAGES, DEFAULT_TEST_STAGE, TEST_STAGE_DISPLAY_NAMES
from typing import List, Dict, Any, Optional

class NFTab(QWidget):
    """Noise Figure test tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.file_parser = FileParser()
        self.csv_reader = CSVReader()
        self.nf_processor = NoiseFigureProcessor()
        
        self.loaded_files = []
        self.file_metadata = []
        self.nf_data = None
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
        plot_layout = QHBoxLayout(plot_group)
        
        self.nf_plot_btn = QPushButton("Noise Figure Plot")
        self.nf_plot_btn.clicked.connect(self.open_nf_plot)
        plot_layout.addWidget(self.nf_plot_btn)
        
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
            self.nf_plot_btn.setEnabled(dut_config.test_enables.get('noise_figure', False))
        else:
            self.nf_plot_btn.setEnabled(False)
    
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
            self.nf_data = self.csv_reader.read_noise_figure_csv(files[0])
            if not self.nf_data:
                QMessageBox.warning(self, "File Read Error", 
                                  f"Could not read CSV file: {files[0]}")
                self.progress_bar.setVisible(False)
                return
            
            self.progress_bar.setValue(50)
            
            # Process noise figure data
            test_stage = self.main_window.current_test_stage if self.main_window else DEFAULT_TEST_STAGE
            self.processed_results = self.nf_processor.process_noise_figure(
                self.nf_data, dut_config, test_stage)
            
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
        
        # Add noise figure requirements
        compliance_data.append({
            'requirement': "Noise Figure Max",
            'limit': f"<= {requirements.nf_max_db:.1f} dB",
            'pri': f"{self.processed_results['nf_max']:.1f} dB",
            'pri_status': "Pass" if self.processed_results['pass'] else "Fail",
            'red': "N/A",  # Would need RED data
            'red_status': "N/A"
        })
        
        compliance_data.append({
            'requirement': "Noise Figure Frequency",
            'limit': "Worst-case frequency",
            'pri': f"{self.processed_results['frequency_at_max']:.1f} GHz",
            'pri_status': "N/A",
            'red': "N/A",
            'red_status': "N/A"
        })
        
        # Set compliance table data
        self.compliance_table.set_data(compliance_data, 
                                     ["Requirement", "Limit", "PRI", "PRI Status", "RED", "RED Status"],
                                     dut_config.hg_lg_enabled)
    
    def open_nf_plot(self):
        """Open noise figure plot window."""
        if not self.processed_results:
            QMessageBox.warning(self, "No Data", "Please load files first.")
            return
        
        # Create plot window
        plot_window = PlotWindow(self)
        
        # Get plot data
        plot_data = self.nf_processor.get_plot_data(self.processed_results)
        
        # Prepare metadata
        metadata = self.prepare_metadata()
        
        # Plot the data
        plot_window.plot_data(plot_data, metadata)
        
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
        self.nf_data = None
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
