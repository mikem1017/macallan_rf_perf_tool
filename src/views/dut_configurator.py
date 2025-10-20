"""
DUT Configurator dialog for managing DUT configurations
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
                             QCheckBox, QPushButton, QListWidget, QTabWidget,
                             QWidget, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QComboBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from src.models.dut_config import (DUTConfiguration, DUTConfigManager, 
                                 FrequencyRange, TestStageRequirements,
                                 OutOfBandRequirement, PinPoutIM3Requirement)

class DUTConfiguratorDialog(QDialog):
    """Dialog for configuring DUT types."""
    
    # Signal emitted when DUTs are updated
    duts_updated = pyqtSignal()
    
    def __init__(self, config_manager: DUTConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.current_dut = None
        
        self.setWindowTitle("DUT Configuration")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_dut_list()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # DUT list and controls
        dut_layout = QHBoxLayout()
        
        # DUT list
        dut_group = QGroupBox("DUT Types")
        dut_group_layout = QVBoxLayout(dut_group)
        
        self.dut_list = QListWidget()
        self.dut_list.currentItemChanged.connect(self.on_dut_selected)
        dut_group_layout.addWidget(self.dut_list)
        
        # DUT control buttons
        dut_buttons_layout = QHBoxLayout()
        self.add_dut_btn = QPushButton("Add DUT")
        self.add_dut_btn.clicked.connect(self.add_dut)
        self.edit_dut_btn = QPushButton("Edit DUT")
        self.edit_dut_btn.clicked.connect(self.edit_dut)
        self.delete_dut_btn = QPushButton("Delete DUT")
        self.delete_dut_btn.clicked.connect(self.delete_dut)
        
        dut_buttons_layout.addWidget(self.add_dut_btn)
        dut_buttons_layout.addWidget(self.edit_dut_btn)
        dut_buttons_layout.addWidget(self.delete_dut_btn)
        dut_group_layout.addLayout(dut_buttons_layout)
        
        dut_layout.addWidget(dut_group)
        
        # DUT configuration
        config_group = QGroupBox("DUT Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Create scroll area for configuration
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.config_layout = QVBoxLayout(scroll_widget)
        
        # Basic info
        self.create_basic_info_section()
        
        # Frequency ranges
        self.create_frequency_section()
        
        # Port configuration
        self.create_port_section()
        
        # Test enables
        self.create_test_enables_section()
        
        # Requirements tabs
        self.create_requirements_section()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        config_layout.addWidget(scroll_area)
        
        dut_layout.addWidget(config_group)
        layout.addLayout(dut_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_dut)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def create_basic_info_section(self):
        """Create basic information section."""
        group = QGroupBox("Basic Information")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit, 0, 1)
        
        layout.addWidget(QLabel("Part Number:"), 1, 0)
        self.part_number_edit = QLineEdit()
        layout.addWidget(self.part_number_edit, 1, 1)
        
        self.config_layout.addWidget(group)
    
    def create_frequency_section(self):
        """Create frequency ranges section."""
        group = QGroupBox("Frequency Ranges")
        layout = QGridLayout(group)
        
        # Operational range
        layout.addWidget(QLabel("Operational Range (GHz):"), 0, 0)
        self.op_min_edit = QDoubleSpinBox()
        self.op_min_edit.setRange(0.001, 1000.0)
        self.op_min_edit.setDecimals(3)
        layout.addWidget(self.op_min_edit, 0, 1)
        
        layout.addWidget(QLabel("to"), 0, 2)
        self.op_max_edit = QDoubleSpinBox()
        self.op_max_edit.setRange(0.001, 1000.0)
        self.op_max_edit.setDecimals(3)
        layout.addWidget(self.op_max_edit, 0, 3)
        
        # Wideband range
        layout.addWidget(QLabel("Wideband Range (GHz):"), 1, 0)
        self.wb_min_edit = QDoubleSpinBox()
        self.wb_min_edit.setRange(0.001, 1000.0)
        self.wb_min_edit.setDecimals(3)
        layout.addWidget(self.wb_min_edit, 1, 1)
        
        layout.addWidget(QLabel("to"), 1, 2)
        self.wb_max_edit = QDoubleSpinBox()
        self.wb_max_edit.setRange(0.001, 1000.0)
        self.wb_max_edit.setDecimals(3)
        layout.addWidget(self.wb_max_edit, 1, 3)
        
        self.config_layout.addWidget(group)
    
    def create_port_section(self):
        """Create port configuration section."""
        group = QGroupBox("Port Configuration")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("Number of Ports:"), 0, 0)
        self.num_ports_spin = QSpinBox()
        self.num_ports_spin.setRange(1, 10)
        self.num_ports_spin.valueChanged.connect(self.update_port_config)
        layout.addWidget(self.num_ports_spin, 0, 1)
        
        layout.addWidget(QLabel("Input Ports:"), 1, 0)
        self.input_ports_edit = QLineEdit()
        self.input_ports_edit.setPlaceholderText("e.g., 1,3")
        layout.addWidget(self.input_ports_edit, 1, 1)
        
        layout.addWidget(QLabel("Output Ports:"), 2, 0)
        self.output_ports_edit = QLineEdit()
        self.output_ports_edit.setPlaceholderText("e.g., 2,4")
        layout.addWidget(self.output_ports_edit, 2, 1)
        
        # HG/LG checkbox
        self.hg_lg_checkbox = QCheckBox("Enable HG/LG variants")
        layout.addWidget(self.hg_lg_checkbox, 3, 0, 1, 2)
        
        self.config_layout.addWidget(group)
    
    def create_test_enables_section(self):
        """Create test enables section."""
        group = QGroupBox("Test Enables")
        layout = QGridLayout(group)
        
        self.s_param_checkbox = QCheckBox("S-Parameters")
        self.compression_checkbox = QCheckBox("Compression")
        self.linearity_checkbox = QCheckBox("Linearity")
        self.nf_checkbox = QCheckBox("Noise Figure")
        self.spurious_checkbox = QCheckBox("Spurious Emissions")
        self.psd_checkbox = QCheckBox("PSD")
        
        layout.addWidget(self.s_param_checkbox, 0, 0)
        layout.addWidget(self.compression_checkbox, 0, 1)
        layout.addWidget(self.linearity_checkbox, 1, 0)
        layout.addWidget(self.nf_checkbox, 1, 1)
        layout.addWidget(self.spurious_checkbox, 2, 0)
        layout.addWidget(self.psd_checkbox, 2, 1)
        
        self.config_layout.addWidget(group)
    
    def create_requirements_section(self):
        """Create requirements section with tabs for each test stage."""
        group = QGroupBox("Requirements")
        layout = QVBoxLayout(group)
        
        # Test stage tabs
        self.requirements_tabs = QTabWidget()
        
        # Board Bring-up tab
        self.bbu_tab = self.create_test_stage_tab("Board Bring-up")
        self.requirements_tabs.addTab(self.bbu_tab, "Board Bring-up")
        
        # SIT tab
        self.sit_tab = self.create_test_stage_tab("SIT")
        self.requirements_tabs.addTab(self.sit_tab, "SIT")
        
        # Test Campaign tab
        self.tc_tab = self.create_test_stage_tab("Test Campaign")
        self.requirements_tabs.addTab(self.tc_tab, "Test Campaign")
        
        layout.addWidget(self.requirements_tabs)
        self.config_layout.addWidget(group)
    
    def create_test_stage_tab(self, stage_name: str) -> QWidget:
        """Create a tab for a test stage."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # S-Parameters requirements
        sparam_group = QGroupBox("S-Parameters")
        sparam_layout = QGridLayout(sparam_group)
        
        sparam_layout.addWidget(QLabel("Gain Min (dB):"), 0, 0)
        gain_min_spin = QDoubleSpinBox()
        gain_min_spin.setRange(-100.0, 100.0)
        gain_min_spin.setDecimals(1)
        sparam_layout.addWidget(gain_min_spin, 0, 1)
        
        sparam_layout.addWidget(QLabel("Gain Max (dB):"), 0, 2)
        gain_max_spin = QDoubleSpinBox()
        gain_max_spin.setRange(-100.0, 100.0)
        gain_max_spin.setDecimals(1)
        sparam_layout.addWidget(gain_max_spin, 0, 3)
        
        sparam_layout.addWidget(QLabel("Gain Flatness (dB):"), 1, 0)
        flatness_spin = QDoubleSpinBox()
        flatness_spin.setRange(0.0, 50.0)
        flatness_spin.setDecimals(1)
        sparam_layout.addWidget(flatness_spin, 1, 1)
        
        sparam_layout.addWidget(QLabel("VSWR Max:"), 1, 2)
        vswr_spin = QDoubleSpinBox()
        vswr_spin.setRange(1.0, 50.0)
        vswr_spin.setDecimals(1)
        sparam_layout.addWidget(vswr_spin, 1, 3)
        
        # Out-of-band requirements table
        sparam_layout.addWidget(QLabel("Out-of-Band Requirements:"), 2, 0, 1, 4)
        oob_table = QTableWidget(2, 3)  # Start with 2 rows
        oob_table.setHorizontalHeaderLabels(["Freq Min (GHz)", "Freq Max (GHz)", "Rejection (dBc)"])
        oob_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sparam_layout.addWidget(oob_table, 3, 0, 1, 4)
        
        # Initialize the 2 default rows with spin boxes
        for i in range(2):
            freq_min_spin = QDoubleSpinBox()
            freq_min_spin.setRange(0.001, 1000.0)
            freq_min_spin.setDecimals(3)
            oob_table.setCellWidget(i, 0, freq_min_spin)
            
            freq_max_spin = QDoubleSpinBox()
            freq_max_spin.setRange(0.001, 1000.0)
            freq_max_spin.setDecimals(3)
            oob_table.setCellWidget(i, 1, freq_max_spin)
            
            rejection_spin = QDoubleSpinBox()
            rejection_spin.setRange(0.0, 200.0)
            rejection_spin.setDecimals(1)
            oob_table.setCellWidget(i, 2, rejection_spin)
        
        # OoB control buttons
        oob_buttons = QHBoxLayout()
        add_oob_btn = QPushButton("Add OoB Range")
        remove_oob_btn = QPushButton("Remove Selected")
        oob_buttons.addWidget(add_oob_btn)
        oob_buttons.addWidget(remove_oob_btn)
        sparam_layout.addLayout(oob_buttons, 4, 0, 1, 4)
        
        layout.addWidget(sparam_group)
        
        # Power/Linearity requirements
        power_group = QGroupBox("Power/Linearity")
        power_layout = QGridLayout(power_group)
        
        power_layout.addWidget(QLabel("P1dB Min (dBm):"), 0, 0)
        p1db_spin = QDoubleSpinBox()
        p1db_spin.setRange(-50.0, 50.0)
        p1db_spin.setDecimals(1)
        power_layout.addWidget(p1db_spin, 0, 1)
        
        # Pin-Pout-IM3 requirements table
        power_layout.addWidget(QLabel("Pin-Pout-IM3 Requirements:"), 1, 0, 1, 4)
        pin_pout_table = QTableWidget(0, 3)
        pin_pout_table.setHorizontalHeaderLabels(["Pin (dBm)", "Pout Min (dBm)", "IM3 Max (dBc)"])
        pin_pout_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        power_layout.addWidget(pin_pout_table, 2, 0, 1, 4)
        
        # Pin-Pout control buttons
        pin_pout_buttons = QHBoxLayout()
        add_pin_pout_btn = QPushButton("Add Pin-Pout-IM3")
        remove_pin_pout_btn = QPushButton("Remove Selected")
        pin_pout_buttons.addWidget(add_pin_pout_btn)
        pin_pout_buttons.addWidget(remove_pin_pout_btn)
        power_layout.addLayout(pin_pout_buttons, 3, 0, 1, 4)
        
        layout.addWidget(power_group)
        
        # Noise Figure requirements
        nf_group = QGroupBox("Noise Figure")
        nf_layout = QGridLayout(nf_group)
        
        nf_layout.addWidget(QLabel("NF Max (dB):"), 0, 0)
        nf_spin = QDoubleSpinBox()
        nf_spin.setRange(0.0, 50.0)
        nf_spin.setDecimals(1)
        nf_layout.addWidget(nf_spin, 0, 1)
        
        layout.addWidget(nf_group)
        
        # Store references to widgets for later access
        tab.gain_min_spin = gain_min_spin
        tab.gain_max_spin = gain_max_spin
        tab.flatness_spin = flatness_spin
        tab.vswr_spin = vswr_spin
        tab.oob_table = oob_table
        tab.p1db_spin = p1db_spin
        tab.pin_pout_table = pin_pout_table
        tab.nf_spin = nf_spin
        
        # Connect signals
        add_oob_btn.clicked.connect(lambda: self.add_oob_requirement(oob_table))
        remove_oob_btn.clicked.connect(lambda: self.remove_oob_requirement(oob_table))
        add_pin_pout_btn.clicked.connect(lambda: self.add_pin_pout_requirement(pin_pout_table))
        remove_pin_pout_btn.clicked.connect(lambda: self.remove_pin_pout_requirement(pin_pout_table))
        
        return tab
    
    def add_oob_requirement(self, table: QTableWidget):
        """Add a new out-of-band requirement."""
        row = table.rowCount()
        table.insertRow(row)
        
        # Add spin boxes for frequency range and rejection
        freq_min_spin = QDoubleSpinBox()
        freq_min_spin.setRange(0.001, 1000.0)
        freq_min_spin.setDecimals(3)
        table.setCellWidget(row, 0, freq_min_spin)
        
        freq_max_spin = QDoubleSpinBox()
        freq_max_spin.setRange(0.001, 1000.0)
        freq_max_spin.setDecimals(3)
        table.setCellWidget(row, 1, freq_max_spin)
        
        rejection_spin = QDoubleSpinBox()
        rejection_spin.setRange(0.0, 200.0)
        rejection_spin.setDecimals(1)
        table.setCellWidget(row, 2, rejection_spin)
    
    def remove_oob_requirement(self, table: QTableWidget):
        """Remove selected out-of-band requirement."""
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
    
    def add_pin_pout_requirement(self, table: QTableWidget):
        """Add a new Pin-Pout-IM3 requirement."""
        row = table.rowCount()
        table.insertRow(row)
        
        # Add spin boxes for Pin, Pout, and IM3
        pin_spin = QDoubleSpinBox()
        pin_spin.setRange(-50.0, 50.0)
        pin_spin.setDecimals(1)
        table.setCellWidget(row, 0, pin_spin)
        
        pout_spin = QDoubleSpinBox()
        pout_spin.setRange(-50.0, 50.0)
        pout_spin.setDecimals(1)
        table.setCellWidget(row, 1, pout_spin)
        
        im3_spin = QDoubleSpinBox()
        im3_spin.setRange(-200.0, 0.0)
        im3_spin.setDecimals(1)
        table.setCellWidget(row, 2, im3_spin)
    
    def remove_pin_pout_requirement(self, table: QTableWidget):
        """Remove selected Pin-Pout-IM3 requirement."""
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
    
    def update_port_config(self):
        """Update port configuration when number of ports changes."""
        num_ports = self.num_ports_spin.value()
        # Could add validation here
        pass
    
    def load_dut_list(self):
        """Load the list of DUTs."""
        self.dut_list.clear()
        dut_names = self.config_manager.list_duts()
        
        for name in dut_names:
            self.dut_list.addItem(name)
    
    def on_dut_selected(self, current, previous):
        """Handle DUT selection."""
        if current:
            dut_name = current.text()
            self.load_dut_config(dut_name)
    
    def load_dut_config(self, dut_name: str):
        """Load DUT configuration into the form."""
        dut_config = self.config_manager.get_dut(dut_name)
        if not dut_config:
            return
        
        self.current_dut = dut_config
        
        # Basic info
        self.name_edit.setText(dut_config.name)
        self.part_number_edit.setText(dut_config.part_number)
        
        # Frequency ranges
        self.op_min_edit.setValue(dut_config.operational_range.min_freq)
        self.op_max_edit.setValue(dut_config.operational_range.max_freq)
        self.wb_min_edit.setValue(dut_config.wideband_range.min_freq)
        self.wb_max_edit.setValue(dut_config.wideband_range.max_freq)
        
        # Port configuration
        self.num_ports_spin.setValue(dut_config.num_ports)
        self.input_ports_edit.setText(','.join(map(str, dut_config.input_ports)))
        self.output_ports_edit.setText(','.join(map(str, dut_config.output_ports)))
        self.hg_lg_checkbox.setChecked(dut_config.hg_lg_enabled)
        
        # Test enables
        self.s_param_checkbox.setChecked(dut_config.test_enables.get('s_parameters', True))
        self.compression_checkbox.setChecked(dut_config.test_enables.get('compression', True))
        self.linearity_checkbox.setChecked(dut_config.test_enables.get('linearity', True))
        self.nf_checkbox.setChecked(dut_config.test_enables.get('noise_figure', True))
        self.spurious_checkbox.setChecked(dut_config.test_enables.get('spurious', False))
        self.psd_checkbox.setChecked(dut_config.test_enables.get('psd', False))
        
        # Load requirements for each test stage
        self.load_test_stage_requirements(dut_config.board_bringup, self.bbu_tab)
        self.load_test_stage_requirements(dut_config.sit, self.sit_tab)
        self.load_test_stage_requirements(dut_config.test_campaign, self.tc_tab)
    
    def load_test_stage_requirements(self, requirements: TestStageRequirements, tab: QWidget):
        """Load requirements for a test stage into the tab."""
        # S-Parameters
        tab.gain_min_spin.setValue(requirements.gain_min_db)
        tab.gain_max_spin.setValue(requirements.gain_max_db)
        tab.flatness_spin.setValue(requirements.gain_flatness_db)
        tab.vswr_spin.setValue(requirements.vswr_max)
        
        # Out-of-band requirements - ensure at least 2 rows
        num_oob = max(len(requirements.out_of_band_requirements), 2)
        tab.oob_table.setRowCount(num_oob)
        
        for i in range(num_oob):
            freq_min_spin = QDoubleSpinBox()
            freq_min_spin.setRange(0.001, 1000.0)
            freq_min_spin.setDecimals(3)
            freq_min_spin.setValue(requirements.out_of_band_requirements[i].freq_min if i < len(requirements.out_of_band_requirements) else 0.0)
            tab.oob_table.setCellWidget(i, 0, freq_min_spin)
            
            freq_max_spin = QDoubleSpinBox()
            freq_max_spin.setRange(0.001, 1000.0)
            freq_max_spin.setDecimals(3)
            freq_max_spin.setValue(requirements.out_of_band_requirements[i].freq_max if i < len(requirements.out_of_band_requirements) else 0.0)
            tab.oob_table.setCellWidget(i, 1, freq_max_spin)
            
            rejection_spin = QDoubleSpinBox()
            rejection_spin.setRange(0.0, 200.0)
            rejection_spin.setDecimals(1)
            rejection_spin.setValue(requirements.out_of_band_requirements[i].rejection_db if i < len(requirements.out_of_band_requirements) else 0.0)
            tab.oob_table.setCellWidget(i, 2, rejection_spin)
        
        # Power/Linearity
        tab.p1db_spin.setValue(requirements.p1db_min_dbm)
        
        # Pin-Pout-IM3 requirements
        tab.pin_pout_table.setRowCount(len(requirements.pin_pout_im3_requirements))
        for i, req in enumerate(requirements.pin_pout_im3_requirements):
            pin_spin = QDoubleSpinBox()
            pin_spin.setRange(-50.0, 50.0)
            pin_spin.setDecimals(1)
            pin_spin.setValue(req.pin_dbm)
            tab.pin_pout_table.setCellWidget(i, 0, pin_spin)
            
            pout_spin = QDoubleSpinBox()
            pout_spin.setRange(-50.0, 50.0)
            pout_spin.setDecimals(1)
            pout_spin.setValue(req.pout_min_dbm)
            tab.pin_pout_table.setCellWidget(i, 1, pout_spin)
            
            im3_spin = QDoubleSpinBox()
            im3_spin.setRange(-200.0, 0.0)
            im3_spin.setDecimals(1)
            im3_spin.setValue(req.im3_max_dbc)
            tab.pin_pout_table.setCellWidget(i, 2, im3_spin)
        
        # Noise Figure
        tab.nf_spin.setValue(requirements.nf_max_db)
    
    def add_dut(self):
        """Add a new DUT."""
        # Clear form
        self.name_edit.clear()
        self.part_number_edit.clear()
        self.op_min_edit.setValue(1.0)
        self.op_max_edit.setValue(2.0)
        self.wb_min_edit.setValue(0.1)
        self.wb_max_edit.setValue(10.0)
        self.num_ports_spin.setValue(2)
        self.input_ports_edit.setText("1")
        self.output_ports_edit.setText("2")
        self.hg_lg_checkbox.setChecked(False)
        
        # Clear test enables
        self.s_param_checkbox.setChecked(True)
        self.compression_checkbox.setChecked(True)
        self.linearity_checkbox.setChecked(True)
        self.nf_checkbox.setChecked(True)
        self.spurious_checkbox.setChecked(False)
        self.psd_checkbox.setChecked(False)
        
        # Clear requirements
        self.clear_requirements_tabs()
        
        self.current_dut = None
    
    def edit_dut(self):
        """Edit the currently selected DUT."""
        current_item = self.dut_list.currentItem()
        if current_item:
            dut_name = current_item.text()
            self.load_dut_config(dut_name)
    
    def delete_dut(self):
        """Delete the currently selected DUT."""
        current_item = self.dut_list.currentItem()
        if not current_item:
            return
        
        dut_name = current_item.text()
        reply = QMessageBox.question(self, 'Delete DUT', 
                                   f'Are you sure you want to delete DUT "{dut_name}"?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.delete_dut(dut_name)
            self.load_dut_list()
            self.current_dut = None
            
            # Emit signal to notify main window
            self.duts_updated.emit()
    
    def clear_requirements_tabs(self):
        """Clear all requirements tabs."""
        for tab in [self.bbu_tab, self.sit_tab, self.tc_tab]:
            tab.gain_min_spin.setValue(0.0)
            tab.gain_max_spin.setValue(0.0)
            tab.flatness_spin.setValue(0.0)
            tab.vswr_spin.setValue(1.0)
            # Ensure at least 2 rows in OOB table
            tab.oob_table.setRowCount(2)
            for i in range(2):
                freq_min_spin = QDoubleSpinBox()
                freq_min_spin.setRange(0.001, 1000.0)
                freq_min_spin.setDecimals(3)
                tab.oob_table.setCellWidget(i, 0, freq_min_spin)
                
                freq_max_spin = QDoubleSpinBox()
                freq_max_spin.setRange(0.001, 1000.0)
                freq_max_spin.setDecimals(3)
                tab.oob_table.setCellWidget(i, 1, freq_max_spin)
                
                rejection_spin = QDoubleSpinBox()
                rejection_spin.setRange(0.0, 200.0)
                rejection_spin.setDecimals(1)
                tab.oob_table.setCellWidget(i, 2, rejection_spin)
            tab.p1db_spin.setValue(0.0)
            tab.pin_pout_table.setRowCount(0)
            tab.nf_spin.setValue(0.0)
    
    def save_dut(self):
        """Save the current DUT configuration."""
        # Validate input
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "DUT name is required.")
            return
        
        if not self.part_number_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Part number is required.")
            return
        
        try:
            # Parse input/output ports
            input_ports = [int(x.strip()) for x in self.input_ports_edit.text().split(',') if x.strip()]
            output_ports = [int(x.strip()) for x in self.output_ports_edit.text().split(',') if x.strip()]
            
            if not input_ports or not output_ports:
                QMessageBox.warning(self, "Validation Error", "Input and output ports are required.")
                return
            
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Invalid port numbers.")
            return
        
        # Create DUT configuration
        dut_config = DUTConfiguration(
            name=self.name_edit.text().strip(),
            part_number=self.part_number_edit.text().strip(),
            operational_range=FrequencyRange(
                min_freq=self.op_min_edit.value(),
                max_freq=self.op_max_edit.value()
            ),
            wideband_range=FrequencyRange(
                min_freq=self.wb_min_edit.value(),
                max_freq=self.wb_max_edit.value()
            ),
            num_ports=self.num_ports_spin.value(),
            input_ports=input_ports,
            output_ports=output_ports,
            hg_lg_enabled=self.hg_lg_checkbox.isChecked(),
            test_enables={
                's_parameters': self.s_param_checkbox.isChecked(),
                'compression': self.compression_checkbox.isChecked(),
                'linearity': self.linearity_checkbox.isChecked(),
                'noise_figure': self.nf_checkbox.isChecked(),
                'spurious': self.spurious_checkbox.isChecked(),
                'psd': self.psd_checkbox.isChecked()
            },
            board_bringup=self.get_test_stage_requirements(self.bbu_tab),
            sit=self.get_test_stage_requirements(self.sit_tab),
            test_campaign=self.get_test_stage_requirements(self.tc_tab)
        )
        
        # Save to config manager
        if self.current_dut and self.current_dut.name == dut_config.name:
            self.config_manager.update_dut(dut_config.name, dut_config)
        else:
            self.config_manager.add_dut(dut_config)
        
        # Reload DUT list
        self.load_dut_list()
        
        # Select the saved DUT
        for i in range(self.dut_list.count()):
            if self.dut_list.item(i).text() == dut_config.name:
                self.dut_list.setCurrentRow(i)
                break
        
        QMessageBox.information(self, "Success", f"DUT '{dut_config.name}' saved successfully.")
        
        # Emit signal to notify main window
        print(f"DEBUG: Emitting duts_updated signal for DUT: {dut_config.name}")
        self.duts_updated.emit()
    
    def get_test_stage_requirements(self, tab: QWidget) -> TestStageRequirements:
        """Get requirements from a test stage tab."""
        # Get out-of-band requirements
        oob_requirements = []
        for row in range(tab.oob_table.rowCount()):
            freq_min_widget = tab.oob_table.cellWidget(row, 0)
            freq_max_widget = tab.oob_table.cellWidget(row, 1)
            rejection_widget = tab.oob_table.cellWidget(row, 2)
            
            if freq_min_widget and freq_max_widget and rejection_widget:
                oob_requirements.append(OutOfBandRequirement(
                    freq_min=freq_min_widget.value(),
                    freq_max=freq_max_widget.value(),
                    rejection_db=rejection_widget.value()
                ))
        
        # Get Pin-Pout-IM3 requirements
        pin_pout_im3_requirements = []
        for row in range(tab.pin_pout_table.rowCount()):
            pin_widget = tab.pin_pout_table.cellWidget(row, 0)
            pout_widget = tab.pin_pout_table.cellWidget(row, 1)
            im3_widget = tab.pin_pout_table.cellWidget(row, 2)
            
            if pin_widget and pout_widget and im3_widget:
                pin_pout_im3_requirements.append(PinPoutIM3Requirement(
                    pin_dbm=pin_widget.value(),
                    pout_min_dbm=pout_widget.value(),
                    im3_max_dbc=im3_widget.value()
                ))
        
        return TestStageRequirements(
            gain_min_db=tab.gain_min_spin.value(),
            gain_max_db=tab.gain_max_spin.value(),
            gain_flatness_db=tab.flatness_spin.value(),
            vswr_max=tab.vswr_spin.value(),
            out_of_band_requirements=oob_requirements,
            p1db_min_dbm=tab.p1db_spin.value(),
            pin_pout_im3_requirements=pin_pout_im3_requirements,
            nf_max_db=tab.nf_spin.value()
        )
