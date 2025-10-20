"""
Simplified PlotWindow to isolate the crash issue.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
                             QLineEdit, QLabel, QDoubleSpinBox, QComboBox, QPushButton,
                             QGroupBox, QGridLayout, QSpinBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap
from typing import Dict, List, Any, Optional

class PlotWindow(QMainWindow):
    """Simplified plot window to isolate crash issues."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print("DEBUG: PlotWindow constructor started")
        
        try:
            self.figure = Figure(figsize=(10, 6))
            print("DEBUG: Figure created successfully")
            
            self.canvas = FigureCanvas(self.figure)
            print("DEBUG: Canvas created successfully")
            
            self.plot_data = {}
            self.metadata = {}
            
            # Store default axis values for reset functionality
            self.default_x_min = None
            self.default_x_max = None
            self.default_y_min = None
            self.default_y_max = None
            
            # Store default label values for reset functionality
            self.default_title = None
            self.default_x_label = None
            self.default_y_label = None
            self.default_subtitle = None
            
            # Store reference to subtitle text object for proper replacement
            self.subtitle_text_obj = None
            
            self.setWindowTitle("Plot Window")
            self.resize(1000, 700)
            print("DEBUG: Window properties set")
            
            self.init_ui()
            print("DEBUG: PlotWindow constructor completed successfully")
            
        except Exception as e:
            print(f"ERROR in PlotWindow constructor: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget for QMainWindow
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create control panels
        self.create_control_panels(layout)
        
        # Plot canvas
        layout.addWidget(self.canvas)
        
        print("DEBUG: Basic UI initialized successfully")
    
    def create_control_panels(self, main_layout):
        """Create control panels for plot customization."""
        # Main control layout
        control_layout = QHBoxLayout()
        
        # Axis Controls Group
        axis_group = QGroupBox("Axis Controls")
        axis_layout = QGridLayout(axis_group)
        
        # X-axis controls
        axis_layout.addWidget(QLabel("X-Axis:"), 0, 0)
        axis_layout.addWidget(QLabel("Min:"), 0, 1)
        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-999999, 999999)
        self.x_min_spin.setDecimals(3)
        axis_layout.addWidget(self.x_min_spin, 0, 2)
        
        axis_layout.addWidget(QLabel("Max:"), 0, 3)
        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-999999, 999999)
        self.x_max_spin.setDecimals(3)
        axis_layout.addWidget(self.x_max_spin, 0, 4)
        
        # Y-axis controls
        axis_layout.addWidget(QLabel("Y-Axis:"), 1, 0)
        axis_layout.addWidget(QLabel("Min:"), 1, 1)
        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(-999999, 999999)
        self.y_min_spin.setDecimals(3)
        axis_layout.addWidget(self.y_min_spin, 1, 2)
        
        axis_layout.addWidget(QLabel("Max:"), 1, 3)
        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(-999999, 999999)
        self.y_max_spin.setDecimals(3)
        axis_layout.addWidget(self.y_max_spin, 1, 4)
        
        # Apply axis changes button
        self.apply_axis_btn = QPushButton("Apply Axis")
        self.apply_axis_btn.clicked.connect(self.apply_axis_changes)
        axis_layout.addWidget(self.apply_axis_btn, 2, 0, 1, 3)
        
        # Reset axis button
        self.reset_axis_btn = QPushButton("Reset Axis")
        self.reset_axis_btn.clicked.connect(self.reset_axis_to_defaults)
        axis_layout.addWidget(self.reset_axis_btn, 2, 3, 1, 2)
        
        control_layout.addWidget(axis_group)
        
        # Labels and Title Group
        labels_group = QGroupBox("Labels & Title")
        labels_layout = QGridLayout(labels_group)
        
        labels_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = QLineEdit()
        labels_layout.addWidget(self.title_edit, 0, 1, 1, 2)
        
        labels_layout.addWidget(QLabel("X-Label:"), 1, 0)
        self.x_label_edit = QLineEdit()
        labels_layout.addWidget(self.x_label_edit, 1, 1, 1, 2)
        
        labels_layout.addWidget(QLabel("Y-Label:"), 2, 0)
        self.y_label_edit = QLineEdit()
        labels_layout.addWidget(self.y_label_edit, 2, 1, 1, 2)
        
        labels_layout.addWidget(QLabel("Subtitle:"), 3, 0)
        self.subtitle_edit = QLineEdit()
        labels_layout.addWidget(self.subtitle_edit, 3, 1, 1, 2)
        
        # Apply labels button
        self.apply_labels_btn = QPushButton("Apply Labels")
        self.apply_labels_btn.clicked.connect(self.apply_label_changes)
        labels_layout.addWidget(self.apply_labels_btn, 4, 0, 1, 2)
        
        # Reset labels button
        self.reset_labels_btn = QPushButton("Reset Labels")
        self.reset_labels_btn.clicked.connect(self.reset_labels_to_defaults)
        labels_layout.addWidget(self.reset_labels_btn, 4, 2, 1, 1)
        
        control_layout.addWidget(labels_group)
        
        # Display Options Group
        display_group = QGroupBox("Display Options")
        display_layout = QGridLayout(display_group)
        
        # Grid toggle
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.stateChanged.connect(self.toggle_grid)
        display_layout.addWidget(self.grid_checkbox, 0, 0)
        
        # Legend position
        display_layout.addWidget(QLabel("Legend:"), 1, 0)
        self.legend_combo = QComboBox()
        self.legend_combo.addItems(["best", "upper right", "upper left", "lower left", 
                                   "lower right", "center left", "center right", 
                                   "lower center", "upper center", "center", "none"])
        self.legend_combo.setCurrentText("best")
        self.legend_combo.currentTextChanged.connect(self.update_legend)
        display_layout.addWidget(self.legend_combo, 1, 1)
        
        # Number of axis dividers
        display_layout.addWidget(QLabel("Axis Dividers:"), 2, 0)
        self.dividers_spin = QSpinBox()
        self.dividers_spin.setRange(2, 20)
        self.dividers_spin.setValue(10)
        self.dividers_spin.valueChanged.connect(self.update_dividers)
        display_layout.addWidget(self.dividers_spin, 2, 1)
        
        control_layout.addWidget(display_group)
        
        # Export Options Group
        export_group = QGroupBox("Export Options")
        export_layout = QGridLayout(export_group)
        
        # Copy to clipboard button
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        export_layout.addWidget(self.copy_btn, 0, 0)
        
        # Save to file button
        self.save_btn = QPushButton("Save to File")
        self.save_btn.clicked.connect(self.save_to_file)
        export_layout.addWidget(self.save_btn, 0, 1)
        
        control_layout.addWidget(export_group)
        
        # Add stretch to push controls to the left
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
    
    def toggle_grid(self):
        """Toggle grid visibility."""
        if hasattr(self, 'current_ax') and self.current_ax:
            self.current_ax.grid(self.grid_checkbox.isChecked())
            self.canvas.draw()
    
    def apply_axis_changes(self):
        """Apply axis min/max changes."""
        if hasattr(self, 'current_ax') and self.current_ax:
            x_min = self.x_min_spin.value()
            x_max = self.x_max_spin.value()
            y_min = self.y_min_spin.value()
            y_max = self.y_max_spin.value()
            
            self.current_ax.set_xlim(x_min, x_max)
            self.current_ax.set_ylim(y_min, y_max)
            
            # Update dividers with new range
            self.update_dividers()
            self.canvas.draw()
    
    def reset_axis_to_defaults(self):
        """Reset axis values to their original defaults."""
        if (hasattr(self, 'current_ax') and self.current_ax and 
            self.default_x_min is not None):
            
            # Reset axis limits to defaults
            self.current_ax.set_xlim(self.default_x_min, self.default_x_max)
            self.current_ax.set_ylim(self.default_y_min, self.default_y_max)
            
            # Update spin boxes to show default values
            self.x_min_spin.setValue(self.default_x_min)
            self.x_max_spin.setValue(self.default_x_max)
            self.y_min_spin.setValue(self.default_y_min)
            self.y_max_spin.setValue(self.default_y_max)
            
            # Update dividers with default range
            self.update_dividers()
            self.canvas.draw()
    
    def apply_label_changes(self):
        """Apply title and label changes."""
        if hasattr(self, 'current_ax') and self.current_ax:
            title = self.title_edit.text()
            x_label = self.x_label_edit.text()
            y_label = self.y_label_edit.text()
            subtitle = self.subtitle_edit.text()
            
            # Remove existing subtitle text object if it exists
            if self.subtitle_text_obj is not None:
                self.subtitle_text_obj.remove()
                self.subtitle_text_obj = None
            
            # Update figure title (suptitle) instead of axis title to avoid overlap
            if title:
                self.figure.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
            if x_label:
                self.current_ax.set_xlabel(x_label)
            if y_label:
                self.current_ax.set_ylabel(y_label)
            
            # Update subtitle
            if subtitle:
                self.subtitle_text_obj = self.figure.text(0.5, 0.92, subtitle, ha='center', va='top', fontsize=10, style='italic')
            
            self.canvas.draw()
    
    def reset_labels_to_defaults(self):
        """Reset labels to their original defaults."""
        if self.default_title is not None:
            # Reset text fields to defaults
            self.title_edit.setText(self.default_title)
            self.x_label_edit.setText(self.default_x_label)
            self.y_label_edit.setText(self.default_y_label)
            self.subtitle_edit.setText(self.default_subtitle)
            
            # Apply the reset values
            self.apply_label_changes()
    
    def update_legend(self):
        """Update legend position."""
        if hasattr(self, 'current_ax') and self.current_ax:
            legend_pos = self.legend_combo.currentText()
            if legend_pos == "none":
                self.current_ax.legend().set_visible(False)
            else:
                self.current_ax.legend(loc=legend_pos)
            self.canvas.draw()
    
    def update_dividers(self):
        """Update number of axis dividers."""
        if hasattr(self, 'current_ax') and self.current_ax:
            num_dividers = self.dividers_spin.value()
            
            # Get current axis limits
            x_min, x_max = self.current_ax.get_xlim()
            y_min, y_max = self.current_ax.get_ylim()
            
            # Create equally spaced ticks
            x_ticks = [x_min + (x_max - x_min) * i / (num_dividers - 1) for i in range(num_dividers)]
            y_ticks = [y_min + (y_max - y_min) * i / (num_dividers - 1) for i in range(num_dividers)]
            
            self.current_ax.set_xticks(x_ticks)
            self.current_ax.set_yticks(y_ticks)
            
            # Format tick labels to 2 decimal places
            self.current_ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            self.current_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            
            self.canvas.draw()
    
    def plot_multiple_data(self, plot_data_dict: Dict[str, Dict[str, Any]], metadata: Dict[str, str] = None):
        """Plot multiple datasets in a single plot."""
        print("DEBUG: plot_multiple_data started")
        
        try:
            self.metadata = metadata or {}
            
            # Clear previous plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            self.current_ax = ax  # Store reference for grid toggle
            
            # Check if we have any data to plot BEFORE trying to access it
            if not plot_data_dict:
                # No data to plot
                ax.text(0.5, 0.5, 'No data available in operational range', 
                       transform=ax.transAxes, ha='center', va='center', fontsize=12)
                ax.set_xlabel('Frequency (GHz)')
                ax.set_ylabel('VSWR')
                ax.set_title('Operational VSWR - No Data')
                self.canvas.draw()
                print("DEBUG: No data message displayed")
                return
            
            # Plot each dataset
            for s_param_name, data in plot_data_dict.items():
                if 'curves' in data:
                    for curve in data['curves']:
                        # Convert to lists to avoid numpy array issues
                        x_data = list(curve['x']) if hasattr(curve['x'], '__iter__') else [curve['x']]
                        y_data = list(curve['y']) if hasattr(curve['y'], '__iter__') else [curve['y']]
                        
                        try:
                            ax.plot(x_data, y_data, 
                                   label=curve.get('label', f'{s_param_name}'),
                                   linestyle=curve.get('linestyle', '-'),
                                   color=curve.get('color', None))
                        except Exception as e:
                            print(f"ERROR plotting curve {curve.get('label', 'unknown')}: {e}")
                            continue
            
            # Add acceptance region if available
            first_data = next(iter(plot_data_dict.values()))
            if 'acceptance_region' in first_data:
                region = first_data['acceptance_region']
                
                # Set frequency range
                if 'freq_min' in region and 'freq_max' in region:
                    freq_expansion = (region['freq_max'] - region['freq_min']) * 0.1
                    ax.set_xlim(region['freq_min'] - freq_expansion, region['freq_max'] + freq_expansion)
                
                # Handle VSWR acceptance region
                if 'vswr_max' in region:
                    # For VSWR plots, show horizontal span from 1.0 to vswr_max
                    vswr_min = region.get('vswr_min', 1.0)
                    ax.axhspan(vswr_min, region['vswr_max'], 
                              alpha=0.3, color='green', label='Acceptance Region')
                    
                    # Set Y-axis range
                    y_min = region.get('y_min', 1.0)
                    y_max = region.get('y_max', 2.0)
                    ax.set_ylim(y_min, y_max)
                
                # Handle gain acceptance region
                elif 'gain_min' in region and 'gain_max' in region:
                    # For gain plots, show single rectangular acceptance region
                    from matplotlib.patches import Rectangle
                    rect = Rectangle((region['freq_min'], region['gain_min']), 
                                   region['freq_max'] - region['freq_min'],
                                   region['gain_max'] - region['gain_min'],
                                   alpha=0.2, color='green', label='Acceptance Region')
                    ax.add_patch(rect)
                    
                    # Set Y-axis range
                    y_min = region.get('y_min', region['gain_min'] - 2.0)
                    y_max = region.get('y_max', region['gain_max'] + 2.0)
                    ax.set_ylim(y_min, y_max)
            
            # Set axis dividers based on current setting
            num_dividers = self.dividers_spin.value()
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            # Override with default axis limits from plot data if available
            if 'default_x_min' in first_data:
                x_min = first_data['default_x_min']
                ax.set_xlim(x_min, first_data.get('default_x_max', x_max))
            if 'default_y_min' in first_data:
                y_min = first_data['default_y_min']
                ax.set_ylim(y_min, first_data.get('default_y_max', y_max))
            
            # Update x_min, x_max, y_min, y_max with final values
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            x_ticks = [x_min + (x_max - x_min) * i / (num_dividers - 1) for i in range(num_dividers)]
            y_ticks = [y_min + (y_max - y_min) * i / (num_dividers - 1) for i in range(num_dividers)]
            
            ax.set_xticks(x_ticks)
            ax.set_yticks(y_ticks)
            
            # Format tick labels to 2 decimal places
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            
            # Enable grid based on checkbox state
            ax.grid(self.grid_checkbox.isChecked())
            
            # Store default values if not already set
            if self.default_x_min is None:
                self.default_x_min = x_min
                self.default_x_max = x_max
                self.default_y_min = y_min
                self.default_y_max = y_max
            
            # Populate control fields with current values
            self.x_min_spin.setValue(x_min)
            self.x_max_spin.setValue(x_max)
            self.y_min_spin.setValue(y_min)
            self.y_max_spin.setValue(y_max)
            
            # Store default label values if not already set
            if self.default_title is None:
                self.default_title = first_data.get('title', '')
                self.default_x_label = first_data.get('x_label', '')
                self.default_y_label = first_data.get('y_label', '')
                # Create default subtitle from metadata with better formatting
                if metadata:
                    subtitle_parts = []
                    if 'serial' in metadata:
                        serial = metadata['serial']
                        if serial.startswith('SNSN'):
                            serial = 'SN' + serial[4:]
                        subtitle_parts.append(f"Serial: {serial}")
                    if 'part_number' in metadata:
                        part_number = metadata['part_number']
                        if part_number.startswith('LL'):
                            part_number = 'L' + part_number[2:]
                        subtitle_parts.append(f"Part Number: {part_number}")
                    if 'date' in metadata:
                        subtitle_parts.append(f"Date: {metadata['date']}")
                    if 'pri_red' in metadata:
                        subtitle_parts.append(f"Type: {metadata['pri_red']}")
                    if 'test_stage' in metadata:
                        subtitle_parts.append(f"Stage: {metadata['test_stage']}")
                    if 'temperature' in metadata:
                        subtitle_parts.append(f"Temperature: {metadata['temperature']}")
                    if 'notes' in metadata and metadata['notes']:
                        subtitle_parts.append(f"Notes: {metadata['notes']}")
                    self.default_subtitle = " | ".join(subtitle_parts) if subtitle_parts else ""
                else:
                    self.default_subtitle = ""
            
            # Populate label fields
            self.title_edit.setText(first_data.get('title', ''))
            self.x_label_edit.setText(first_data.get('x_label', ''))
            self.y_label_edit.setText(first_data.get('y_label', ''))
            self.subtitle_edit.setText(self.default_subtitle)
            
            # Set labels and title
            ax.set_xlabel(first_data.get('x_label', 'Frequency (GHz)'))
            ax.set_ylabel(first_data.get('y_label', 'VSWR'))
            ax.legend()
            
            # Add metadata subtitle if available
            print(f"DEBUG: Metadata received: {metadata}")
            if metadata:
                subtitle_parts = []
                if 'serial' in metadata:
                    # Remove redundant "SN" prefix if present (e.g., SNSN0003 -> SN0003)
                    serial = metadata['serial']
                    if serial.startswith('SNSN'):
                        serial = 'SN' + serial[4:]  # Remove first "SN" from "SNSN0003"
                    subtitle_parts.append(f"Serial: {serial}")
                if 'part_number' in metadata:
                    # Remove redundant "L" prefix if present (e.g., LL109908 -> L109908)
                    part_number = metadata['part_number']
                    if part_number.startswith('LL'):
                        part_number = 'L' + part_number[2:]  # Remove first "L" from "LL109908"
                    subtitle_parts.append(f"Part Number: {part_number}")
                if 'date' in metadata:
                    subtitle_parts.append(f"Date: {metadata['date']}")
                if 'pri_red' in metadata:
                    subtitle_parts.append(f"Type: {metadata['pri_red']}")
                if 'test_stage' in metadata:
                    subtitle_parts.append(f"Stage: {metadata['test_stage']}")
                if 'temperature' in metadata:
                    subtitle_parts.append(f"Temperature: {metadata['temperature']}")
                if 'notes' in metadata and metadata['notes']:
                    subtitle_parts.append(f"Notes: {metadata['notes']}")
                
                if subtitle_parts:
                    subtitle = " | ".join(subtitle_parts)
                    print(f"DEBUG: Adding subtitle: {subtitle}")
                    # Set main title and subtitle using matplotlib's figure suptitle
                    main_title = first_data.get('title', 'VSWR Plot')
                    self.figure.suptitle(main_title, fontsize=14, fontweight='bold', y=0.98)
                    self.subtitle_text_obj = self.figure.text(0.5, 0.92, subtitle, ha='center', va='top', fontsize=10, style='italic')
                else:
                    print("DEBUG: No subtitle parts found")
                    # Just set the main title if no metadata
                    ax.set_title(first_data.get('title', 'VSWR Plot'))
            else:
                print("DEBUG: No metadata provided")
                # Just set the main title if no metadata
                ax.set_title(first_data.get('title', 'VSWR Plot'))
            
            # Draw the plot
            self.canvas.draw()
            print("DEBUG: plot_multiple_data completed successfully")
            
        except Exception as e:
            print(f"ERROR in plot_multiple_data: {e}")
            import traceback
            traceback.print_exc()
            raise

    def copy_to_clipboard(self):
        """Copy the current plot to clipboard."""
        try:
            # Get the current figure as a QPixmap
            pixmap = self.canvas.grab()
            
            # Copy to clipboard
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            
            QMessageBox.information(self, "Success", "Plot copied to clipboard!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy to clipboard: {e}")
    
    def save_to_file(self):
        """Save the current plot to a file."""
        try:
            # Open file dialog with PNG as default
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Save Plot",
                "plot.png",
                "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)"
            )
            
            if file_path:
                # Determine format from file extension or selected filter
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
                    format_type = file_path.split('.')[-1].lower()
                elif 'PNG' in selected_filter:
                    format_type = 'png'
                elif 'JPEG' in selected_filter:
                    format_type = 'jpg'
                elif 'PDF' in selected_filter:
                    format_type = 'pdf'
                elif 'SVG' in selected_filter:
                    format_type = 'svg'
                else:
                    format_type = 'png'  # Default to PNG
                
                # Save the figure
                self.figure.savefig(file_path, format=format_type, dpi=300, bbox_inches='tight')
                
                QMessageBox.information(self, "Success", f"Plot saved to {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save plot: {e}")



