"""
Main window for Macallan RF Performance Tool
"""

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QMenuBar, QStatusBar, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from src.version import get_version
from src.models.dut_config import DUTConfigManager
from src.views.dut_configurator import DUTConfiguratorDialog
from src.views.sparam_tab import SParamTab
from src.views.power_linearity_tab import PowerLinearityTab
from src.views.nf_tab import NFTab
from src.views.spurious_tab import SpuriousTab
from src.views.psd_tab import PSDTab
from src.constants import DEFAULT_TEST_STAGE, TEST_STAGE_DISPLAY_NAMES

class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    dut_changed = pyqtSignal(str)  # Emitted when DUT selection changes
    test_stage_changed = pyqtSignal(str)  # Emitted when test stage changes
    
    def __init__(self):
        super().__init__()
        self.dut_config_manager = DUTConfigManager()
        self.current_dut = None
        self.current_test_stage = DEFAULT_TEST_STAGE
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Macallan RF Performance Tool v{get_version()}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # DUT selection
        toolbar_layout.addWidget(QLabel("DUT Type:"))
        self.dut_combo = QComboBox()
        self.dut_combo.setMinimumWidth(200)
        self.update_dut_combo()
        toolbar_layout.addWidget(self.dut_combo)
        
        # Test stage selection
        toolbar_layout.addWidget(QLabel("Test Stage:"))
        self.stage_combo = QComboBox()
        self.stage_combo.addItems(list(TEST_STAGE_DISPLAY_NAMES.values()))
        self.stage_combo.setCurrentText("Board Bring-up")
        toolbar_layout.addWidget(self.stage_combo)
        
        # DUT configuration button
        self.config_button = QPushButton("Configure DUTs")
        toolbar_layout.addWidget(self.config_button)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create test tabs
        self.sparam_tab = SParamTab(self)
        self.power_tab = PowerLinearityTab(self)
        self.nf_tab = NFTab(self)
        self.spurious_tab = SpuriousTab(self)
        self.psd_tab = PSDTab(self)
        
        # Add tabs
        self.tab_widget.addTab(self.sparam_tab, "S-Parameters")
        self.tab_widget.addTab(self.power_tab, "Power/Linearity")
        self.tab_widget.addTab(self.nf_tab, "Noise Figure")
        self.tab_widget.addTab(self.spurious_tab, "Spurious Emissions")
        self.tab_widget.addTab(self.psd_tab, "PSD")
        
        main_layout.addWidget(self.tab_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # New action
        new_action = QAction('New Session', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)
        
        # Load DUT config action
        load_config_action = QAction('Load DUT Config', self)
        load_config_action.setShortcut('Ctrl+L')
        load_config_action.triggered.connect(self.load_dut_config)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # DUT menu
        dut_menu = menubar.addMenu('DUT')
        
        # Configure DUTs action
        config_duts_action = QAction('Configure DUTs', self)
        config_duts_action.triggered.connect(self.open_dut_configurator)
        dut_menu.addAction(config_duts_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # User Guide action
        guide_action = QAction('User Guide', self)
        guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(guide_action)
    
    def setup_connections(self):
        """Setup signal connections."""
        self.dut_combo.currentTextChanged.connect(self.on_dut_changed)
        self.stage_combo.currentTextChanged.connect(self.on_stage_changed)
        self.config_button.clicked.connect(self.open_dut_configurator)
    
    def update_dut_combo(self):
        """Update the DUT combo box with available DUTs."""
        print("DEBUG: update_dut_combo called")
        self.dut_combo.clear()
        dut_names = self.dut_config_manager.list_duts()
        print(f"DEBUG: Found DUTs: {dut_names}")
        
        if dut_names:
            self.dut_combo.addItems(dut_names)
            self.current_dut = dut_names[0]
        else:
            self.dut_combo.addItem("No DUTs configured")
            self.current_dut = None
    
    def on_dut_changed(self, dut_name: str):
        """Handle DUT selection change."""
        if dut_name != "No DUTs configured":
            self.current_dut = dut_name
            self.dut_changed.emit(dut_name)
            self.status_bar.showMessage(f"Selected DUT: {dut_name}")
        else:
            self.current_dut = None
            self.status_bar.showMessage("No DUT selected")
    
    def on_stage_changed(self, stage_text: str):
        """Handle test stage change."""
        stage_mapping = {v: k for k, v in TEST_STAGE_DISPLAY_NAMES.items()}
        self.current_test_stage = stage_mapping.get(stage_text, DEFAULT_TEST_STAGE)
        self.status_bar.showMessage(f"Test stage: {stage_text}")
        
        # Emit signal to notify tabs
        self.test_stage_changed.emit(self.current_test_stage)
    
    def get_current_dut_config(self):
        """Get the current DUT configuration."""
        if self.current_dut:
            return self.dut_config_manager.get_dut(self.current_dut)
        return None
    
    def open_dut_configurator(self):
        """Open the DUT configurator dialog."""
        dialog = DUTConfiguratorDialog(self.dut_config_manager, self)
        # Connect the signal to update the combo box when DUTs are modified
        dialog.duts_updated.connect(self.update_dut_combo)
        if dialog.exec():
            self.update_dut_combo()
            self.status_bar.showMessage("DUT configuration updated")
    
    def new_session(self):
        """Start a new session."""
        reply = QMessageBox.question(self, 'New Session', 
                                   'Are you sure you want to start a new session? All unsaved data will be lost.',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear all tabs
            self.sparam_tab.clear_data()
            self.power_tab.clear_data()
            self.nf_tab.clear_data()
            self.status_bar.showMessage("New session started")
    
    def load_dut_config(self):
        """Load DUT configuration from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load DUT Configuration", "", "JSON Files (*.json)")
        
        if file_path:
            # This would load a different config file
            # For now, just show a message
            QMessageBox.information(self, "Load Config", 
                                  "DUT configuration loading not yet implemented")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Macallan RF Tool",
                         f"Macallan RF Performance Visualization Tool\n"
                         f"Version {get_version()}\n\n"
                         f"A comprehensive tool for RF performance analysis and compliance checking.")
    
    def show_user_guide(self):
        """Show user guide."""
        QMessageBox.information(self, "User Guide",
                               "User guide not yet implemented.\n\n"
                               "This will contain detailed instructions for using the tool.")
