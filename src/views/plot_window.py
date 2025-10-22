"""
Interactive plot window with Matplotlib
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QDoubleSpinBox,
                             QGroupBox, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt
from src.utils.export_utils import ExportUtils
from typing import Dict, List, Any, Optional
from src.constants import PLOT_EXPANSION_FACTOR, VSWR_Y_AXIS_EXPANSION_FACTOR, ACCEPTANCE_REGION_ALPHA, ACCEPTANCE_REGION_COLOR, SUBTITLE_Y_POSITION, SUBTITLE_X_POSITION

class PlotWindow(QMainWindow):
    """Interactive plot window with editing capabilities."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.current_plot_data = {}
        self.metadata = {}
        
        self.setWindowTitle("Plot Window")
        # setModal is not available for QWidget, only QDialog
        self.resize(1000, 700)
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget for QMainWindow
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Plot canvas
        layout.addWidget(self.canvas)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Plot editing controls
        edit_group = QGroupBox("Plot Editing")
        edit_layout = QGridLayout(edit_group)
        
        # Title
        edit_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = QLineEdit()
        edit_layout.addWidget(self.title_edit, 0, 1)
        
        # X-axis
        edit_layout.addWidget(QLabel("X-Axis:"), 1, 0)
        self.x_label_edit = QLineEdit()
        edit_layout.addWidget(self.x_label_edit, 1, 1)
        
        edit_layout.addWidget(QLabel("X Min:"), 1, 2)
        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-10000, 10000)
        self.x_min_spin.setDecimals(3)
        edit_layout.addWidget(self.x_min_spin, 1, 3)
        
        edit_layout.addWidget(QLabel("X Max:"), 1, 4)
        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-10000, 10000)
        self.x_max_spin.setDecimals(3)
        edit_layout.addWidget(self.x_max_spin, 1, 5)
        
        # Y-axis
        edit_layout.addWidget(QLabel("Y-Axis:"), 2, 0)
        self.y_label_edit = QLineEdit()
        edit_layout.addWidget(self.y_label_edit, 2, 1)
        
        edit_layout.addWidget(QLabel("Y Min:"), 2, 2)
        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(-10000, 10000)
        self.y_min_spin.setDecimals(3)
        edit_layout.addWidget(self.y_min_spin, 2, 3)
        
        edit_layout.addWidget(QLabel("Y Max:"), 2, 4)
        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(-10000, 10000)
        self.y_max_spin.setDecimals(3)
        edit_layout.addWidget(self.y_max_spin, 2, 5)
        
        # Legend
        edit_layout.addWidget(QLabel("Legend Location:"), 3, 0)
        self.legend_combo = QComboBox()
        self.legend_combo.addItems(["best", "upper right", "upper left", "lower right", 
                                   "lower left", "center right", "center left", "upper center", 
                                   "lower center", "center"])
        edit_layout.addWidget(self.legend_combo, 3, 1)
        
        control_layout.addWidget(edit_group)
        
        # Export buttons
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        export_layout.addWidget(self.copy_btn)
        
        self.save_png_btn = QPushButton("Save as PNG")
        self.save_png_btn.clicked.connect(self.save_as_png)
        export_layout.addWidget(self.save_png_btn)
        
        self.save_pdf_btn = QPushButton("Save as PDF")
        self.save_pdf_btn.clicked.connect(self.save_as_pdf)
        export_layout.addWidget(self.save_pdf_btn)
        
        control_layout.addWidget(export_group)
        
        # Apply button
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        control_layout.addWidget(self.apply_btn)
        
        layout.addLayout(control_layout)
    
    def setup_connections(self):
        """Setup signal connections."""
        # Auto-apply changes when spin boxes change
        self.x_min_spin.valueChanged.connect(self.apply_changes)
        self.x_max_spin.valueChanged.connect(self.apply_changes)
        self.y_min_spin.valueChanged.connect(self.apply_changes)
        self.y_max_spin.valueChanged.connect(self.apply_changes)
        self.legend_combo.currentTextChanged.connect(self.apply_changes)
    
    def plot_data(self, plot_data: Dict[str, Any], metadata: Dict[str, str] = None):
        """Plot data with optional metadata."""
        self.current_plot_data = plot_data
        self.metadata = metadata or {}
        
        # Clear previous plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Plot the data
        if 'x' in plot_data and 'y' in plot_data:
            ax.plot(plot_data['x'], plot_data['y'], label=plot_data.get('label', 'Data'))
        
        # Plot secondary Y-axis data if present
        if 'y2' in plot_data and 'y2_label' in plot_data:
            ax2 = ax.twinx()
            ax2.plot(plot_data['x'], plot_data['y2'], 
                    linestyle='--', color='red', label=plot_data['y2_label'])
            ax2.set_ylabel(plot_data['y2_label'])
        
        # Plot multiple curves if present
        if 'curves' in plot_data:
            for curve in plot_data['curves']:
                ax.plot(curve['x'], curve['y'], 
                       label=curve.get('label', 'Curve'),
                       linestyle=curve.get('linestyle', '-'),
                       color=curve.get('color', None))
        
        # Add acceptance region if present
        if 'acceptance_region' in plot_data:
            region = plot_data['acceptance_region']
            if 'freq_min' in region and 'freq_max' in region:
                ax.axvspan(region['freq_min'], region['freq_max'], 
                          alpha=0.3, color='green', label='Acceptance Region')
        
        # Set labels and title
        ax.set_xlabel(plot_data.get('x_label', 'X'))
        ax.set_ylabel(plot_data.get('y_label', 'Y'))
        ax.set_title(plot_data.get('title', 'Plot'))
        
        # Add legend
        ax.legend(loc='best')
        
        # Add metadata as subtitle
        if self.metadata:
            subtitle = self.format_metadata()
            ax.text(SUBTITLE_X_POSITION, SUBTITLE_Y_POSITION, subtitle, transform=ax.transAxes, 
                   ha='center', fontsize=8, style='italic')
        
        # Update control values
        self.update_controls()
        
        # Refresh canvas
        self.canvas.draw()
    
    def plot_multiple_data(self, plot_data_dict: Dict[str, Dict[str, Any]], metadata: Dict[str, str] = None):
        """Plot multiple datasets in a single plot."""
        self.metadata = metadata or {}
        
        # Clear previous plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Check if we have any data to plot BEFORE trying to access it
        if not plot_data_dict:
            # No data to plot
            ax.text(0.5, 0.5, 'No data available in operational range', 
                   transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('VSWR')
            ax.set_title('Operational VSWR - No Data')
            self.canvas.draw()
            return
        
        # Plot each dataset
        for s_param_name, data in plot_data_dict.items():
            # Plot multiple curves if present
            if 'curves' in data:
                for curve in data['curves']:
                    # Validate data before plotting
                    if 'x' in curve and 'y' in curve and len(curve['x']) > 0 and len(curve['y']) > 0:
                        try:
                            # Convert to lists to avoid numpy array issues
                            x_data = list(curve['x']) if hasattr(curve['x'], '__iter__') else [curve['x']]
                            y_data = list(curve['y']) if hasattr(curve['y'], '__iter__') else [curve['y']]
                            
                            ax.plot(x_data, y_data, 
                                   label=curve.get('label', f'{s_param_name}'),
                                   linestyle=curve.get('linestyle', '-'),
                                   color=curve.get('color', None))
                        except Exception as e:
                            print(f"DEBUG: Error plotting curve {curve.get('label', s_param_name)}: {e}")
                            continue
            elif 'x' in data and 'y' in data:
                # Validate data before plotting
                if len(data['x']) > 0 and len(data['y']) > 0:
                    try:
                        # Convert to lists to avoid numpy array issues
                        x_data = list(data['x']) if hasattr(data['x'], '__iter__') else [data['x']]
                        y_data = list(data['y']) if hasattr(data['y'], '__iter__') else [data['y']]
                        
                        ax.plot(x_data, y_data, 
                               label=data.get('label', s_param_name),
                               linestyle=data.get('linestyle', '-'),
                               color=data.get('color', None))
                    except Exception as e:
                        print(f"DEBUG: Error plotting data {s_param_name}: {e}")
                        continue
        
        # Add acceptance region if present (use first dataset's region)
        if plot_data_dict:
            first_data = next(iter(plot_data_dict.values()))
            if 'acceptance_region' in first_data:
                region = first_data['acceptance_region']
                if 'freq_min' in region and 'freq_max' in region:
                    # Set axis limits based on acceptance region for operational plots
                    freq_expansion = (region['freq_max'] - region['freq_min']) * PLOT_EXPANSION_FACTOR
                    ax.set_xlim(region['freq_min'] - freq_expansion, region['freq_max'] + freq_expansion)
                
                if 'gain_min' in region and 'gain_max' in region:
                    # For gain plots, show vertical span (frequency range)
                    ax.axvspan(region['freq_min'], region['freq_max'], 
                              alpha=ACCEPTANCE_REGION_ALPHA, color=ACCEPTANCE_REGION_COLOR, label='Acceptance Region')
                    gain_expansion = (region['gain_max'] - region['gain_min']) * PLOT_EXPANSION_FACTOR
                    ax.set_ylim(region['gain_min'] - gain_expansion, region['gain_max'] + gain_expansion)
                elif 'vswr_max' in region:
                    # For VSWR plots, show horizontal span (VSWR limit) within frequency range
                    ax.axhspan(0, region['vswr_max'], 
                              alpha=ACCEPTANCE_REGION_ALPHA, color=ACCEPTANCE_REGION_COLOR, label='Acceptance Region')
                    ax.set_ylim(0, region['vswr_max'] * VSWR_Y_AXIS_EXPANSION_FACTOR)
        
        # Set labels and title (use first dataset's labels)
        if plot_data_dict:
            first_data = next(iter(plot_data_dict.values()))
            ax.set_xlabel(first_data.get('x_label', 'Frequency (GHz)'))
            ax.set_ylabel(first_data.get('y_label', 'Gain (dB)'))
            
            # Set title without metadata (metadata will be subtitle)
            main_title = first_data.get('title', 'S-Parameter Plot')
            ax.set_title(main_title)
        else:
            # Default labels when no data
            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('VSWR')
            ax.set_title('Operational VSWR - No Data')
        
        # Add legend
        ax.legend(loc='best')
        
        # Add metadata as subtitle
        if self.metadata:
            subtitle = self.format_metadata()
            ax.text(SUBTITLE_X_POSITION, SUBTITLE_Y_POSITION, subtitle, transform=ax.transAxes, 
                   ha='center', fontsize=8, style='italic')
        
        # Update control values
        self.update_controls()
        
        # Refresh canvas
        self.canvas.draw()
    
    def format_metadata(self) -> str:
        """Format metadata for display."""
        parts = []
        
        if 'serial' in self.metadata:
            parts.append(f"Serial: {self.metadata['serial']}")
        if 'part_number' in self.metadata:
            parts.append(f"Part: {self.metadata['part_number']}")
        if 'date' in self.metadata:
            parts.append(f"Date: {self.metadata['date']}")
        if 'pri_red' in self.metadata:
            parts.append(f"{self.metadata['pri_red']}")
        if 'temperature' in self.metadata:
            parts.append(f"Temp: {self.metadata['temperature']}")
        
        metadata_line = " | ".join(parts)
        
        if 'test_stage' in self.metadata or 'notes' in self.metadata:
            second_line_parts = []
            if 'test_stage' in self.metadata:
                second_line_parts.append(f"Test Stage: {self.metadata['test_stage']}")
            if 'notes' in self.metadata and self.metadata['notes']:
                second_line_parts.append(f"Notes: {self.metadata['notes']}")
            
            if second_line_parts:
                metadata_line += "\n" + " | ".join(second_line_parts)
        
        return metadata_line
    
    def update_controls(self):
        """Update control values from current plot."""
        ax = self.figure.axes[0] if self.figure.axes else None
        if not ax:
            return
        
        # Update title
        self.title_edit.setText(ax.get_title())
        
        # Update axis labels
        self.x_label_edit.setText(ax.get_xlabel())
        self.y_label_edit.setText(ax.get_ylabel())
        
        # Update axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        self.x_min_spin.setValue(xlim[0])
        self.x_max_spin.setValue(xlim[1])
        self.y_min_spin.setValue(ylim[0])
        self.y_max_spin.setValue(ylim[1])
    
    def apply_changes(self):
        """Apply changes to the plot."""
        ax = self.figure.axes[0] if self.figure.axes else None
        if not ax:
            return
        
        # Update title
        if self.title_edit.text():
            ax.set_title(self.title_edit.text())
        
        # Update axis labels
        if self.x_label_edit.text():
            ax.set_xlabel(self.x_label_edit.text())
        if self.y_label_edit.text():
            ax.set_ylabel(self.y_label_edit.text())
        
        # Update axis limits
        ax.set_xlim(self.x_min_spin.value(), self.x_max_spin.value())
        ax.set_ylim(self.y_min_spin.value(), self.y_max_spin.value())
        
        # Update legend location
        legend = ax.get_legend()
        if legend:
            legend.set_loc(self.legend_combo.currentText())
        
        # Refresh canvas
        self.canvas.draw()
    
    def copy_to_clipboard(self):
        """Copy plot to clipboard."""
        if ExportUtils.copy_plot_to_clipboard(self.figure):
            QMessageBox.information(self, "Success", "Plot copied to clipboard.")
        else:
            QMessageBox.warning(self, "Error", "Failed to copy plot to clipboard.")
    
    def save_as_png(self):
        """Save plot as PNG."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot as PNG", "", "PNG Files (*.png)")
        
        if file_path:
            if ExportUtils.save_plot_as_png(self.figure, file_path):
                QMessageBox.information(self, "Success", f"Plot saved as PNG: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save plot as PNG.")
    
    def save_as_pdf(self):
        """Save plot as PDF."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot as PDF", "", "PDF Files (*.pdf)")
        
        if file_path:
            if ExportUtils.save_plot_as_pdf(self.figure, file_path):
                QMessageBox.information(self, "Success", f"Plot saved as PDF: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save plot as PDF.")
