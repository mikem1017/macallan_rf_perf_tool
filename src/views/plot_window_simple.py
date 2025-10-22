"""
Simplified PlotWindow to isolate the crash issue.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
import numpy as np
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
            
            # Interactive components
            self.cursor = None
            self.hover_annotations = []
            self.current_ax = None
            
            # Curve filtering components
            self.filter_checkboxes = {}
            self.plotted_lines = []  # List of (line_object, label, attributes_dict)
            
            self.setWindowTitle("Plot Window")
            self.resize(800, 700)  # Reduced width by 20% (1000 -> 800)
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
        
        # X-axis controls - label on own row
        axis_layout.addWidget(QLabel("X Axis:"), 0, 0, 1, 4)  # Span 4 columns
        axis_layout.addWidget(QLabel("Min:"), 1, 0)
        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-999999, 999999)
        self.x_min_spin.setDecimals(3)
        axis_layout.addWidget(self.x_min_spin, 1, 1)
        axis_layout.addWidget(QLabel("Max:"), 1, 2)
        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-999999, 999999)
        self.x_max_spin.setDecimals(3)
        axis_layout.addWidget(self.x_max_spin, 1, 3)
        
        # Y-axis controls - label on own row
        axis_layout.addWidget(QLabel("Y Axis:"), 2, 0, 1, 4)  # Span 4 columns
        axis_layout.addWidget(QLabel("Min:"), 3, 0)
        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(-999999, 999999)
        self.y_min_spin.setDecimals(3)
        axis_layout.addWidget(self.y_min_spin, 3, 1)
        axis_layout.addWidget(QLabel("Max:"), 3, 2)
        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(-999999, 999999)
        self.y_max_spin.setDecimals(3)
        axis_layout.addWidget(self.y_max_spin, 3, 3)
        
        # Buttons on row 4
        self.apply_axis_btn = QPushButton("Apply Axis")
        self.apply_axis_btn.clicked.connect(self.apply_axis_changes)
        axis_layout.addWidget(self.apply_axis_btn, 4, 0, 1, 2)
        self.reset_axis_btn = QPushButton("Reset Axis")
        self.reset_axis_btn.clicked.connect(self.reset_axis_to_defaults)
        axis_layout.addWidget(self.reset_axis_btn, 4, 2, 1, 2)
        
        control_layout.addWidget(axis_group)
        
        # Labels and Title Group
        labels_group = QGroupBox("Labels & Title")
        labels_layout = QGridLayout(labels_group)
        
        labels_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = QLineEdit()
        labels_layout.addWidget(self.title_edit, 0, 1, 1, 1)
        
        labels_layout.addWidget(QLabel("X-Label:"), 1, 0)
        self.x_label_edit = QLineEdit()
        labels_layout.addWidget(self.x_label_edit, 1, 1, 1, 1)
        
        labels_layout.addWidget(QLabel("Y-Label:"), 2, 0)
        self.y_label_edit = QLineEdit()
        labels_layout.addWidget(self.y_label_edit, 2, 1, 1, 1)
        
        labels_layout.addWidget(QLabel("Subtitle:"), 3, 0)
        self.subtitle_edit = QLineEdit()
        labels_layout.addWidget(self.subtitle_edit, 3, 1, 1, 1)
        
        # Apply labels button
        self.apply_labels_btn = QPushButton("Apply Labels")
        self.apply_labels_btn.clicked.connect(self.apply_label_changes)
        labels_layout.addWidget(self.apply_labels_btn, 4, 0, 1, 1)
        
        # Reset labels button
        self.reset_labels_btn = QPushButton("Reset Labels")
        self.reset_labels_btn.clicked.connect(self.reset_labels_to_defaults)
        labels_layout.addWidget(self.reset_labels_btn, 4, 1, 1, 1)
        
        control_layout.addWidget(labels_group)
        
        # Display & Interactive Options Group (combined)
        display_group = QGroupBox("Display & Interactive")
        display_layout = QGridLayout(display_group)
        
        # Grid toggle
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.stateChanged.connect(self.toggle_grid)
        display_layout.addWidget(self.grid_checkbox, 0, 0)
        
        # Hover tooltips
        self.hover_checkbox = QCheckBox("Hover Tooltips")
        self.hover_checkbox.setChecked(True)
        self.hover_checkbox.stateChanged.connect(self.toggle_hover)
        display_layout.addWidget(self.hover_checkbox, 0, 1)
        
        # Legend position
        display_layout.addWidget(QLabel("Legend:"), 1, 0)
        self.legend_combo = QComboBox()
        self.legend_combo.addItems(["best", "upper right", "upper left", "lower left", 
                                   "lower right", "center left", "center right", 
                                   "lower center", "upper center", "center", "none"])
        self.legend_combo.setCurrentText("best")
        self.legend_combo.currentTextChanged.connect(self.update_legend)
        display_layout.addWidget(self.legend_combo, 1, 1)
        
        # Crosshair cursor
        self.crosshair_checkbox = QCheckBox("Crosshair")
        self.crosshair_checkbox.setChecked(True)
        self.crosshair_checkbox.stateChanged.connect(self.toggle_crosshair)
        display_layout.addWidget(self.crosshair_checkbox, 2, 0)
        
        # Number of axis dividers
        display_layout.addWidget(QLabel("Axis Ticks:"), 2, 1)
        self.dividers_spin = QSpinBox()
        self.dividers_spin.setRange(2, 20)
        self.dividers_spin.setValue(10)
        self.dividers_spin.valueChanged.connect(self.update_dividers)
        display_layout.addWidget(self.dividers_spin, 2, 2)
        
        control_layout.addWidget(display_group)
        
        # Curve Filters Group (Collapsible)
        filter_group = QGroupBox("Curve Filters")
        filter_group.setCheckable(True)
        filter_group.setChecked(False)  # Collapsed by default
        filter_group.toggled.connect(self.toggle_filter_section)
        filter_layout = QVBoxLayout(filter_group)
        
        # Set consistent spacing for better layout
        filter_layout.setSpacing(4)  # Consistent 4px between rows
        
        # Filter controls will be populated dynamically
        self.filter_group = filter_group
        self.filter_layout = filter_layout
        
        # Reset filters button
        self.reset_filters_btn = QPushButton("Reset Filters")
        self.reset_filters_btn.clicked.connect(self.reset_all_filters)
        filter_layout.addWidget(self.reset_filters_btn)
        
        control_layout.addWidget(filter_group)
        
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
        """Update legend position and filter visible curves."""
        if hasattr(self, 'current_ax') and self.current_ax:
            legend_pos = self.legend_combo.currentText()
            if legend_pos == "none":
                self.current_ax.legend().set_visible(False)
            else:
                # Create legend with only visible curves
                handles, labels = self.current_ax.get_legend_handles_labels()
                
                # Filter to only show visible curves
                visible_handles = []
                visible_labels = []
                
                if hasattr(self, 'plotted_lines'):
                    visible_labels_set = set()
                    for line_obj, label, attributes in self.plotted_lines:
                        if line_obj.get_visible() and label not in visible_labels_set:
                            visible_handles.append(line_obj)
                            visible_labels.append(label)
                            visible_labels_set.add(label)
                
                # Update legend with filtered entries
                if visible_handles:
                    self.current_ax.legend(visible_handles, visible_labels, loc=legend_pos)
                else:
                    self.current_ax.legend().set_visible(False)
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
            
            # Format tick labels - use smart formatting for power plots
            if hasattr(self, 'metadata') and self.metadata:
                # Check if this is a power plot by looking at axis labels
                x_label = self.current_ax.get_xlabel()
                y_label = self.current_ax.get_ylabel()
                if 'Pin' in x_label or 'Pout' in y_label:
                    # For power plots, create clean 0.5 dBm increments
                    import numpy as np
                    
                    # Calculate appropriate tick spacing for X-axis (Pin)
                    x_range = x_max - x_min
                    if x_range <= 5:
                        x_tick_spacing = 0.5
                    elif x_range <= 10:
                        x_tick_spacing = 0.5
                    elif x_range <= 20:
                        x_tick_spacing = 1.0
                    else:
                        x_tick_spacing = 1.0
                    
                    # Create clean X-axis ticks
                    x_tick_start = np.ceil(x_min / x_tick_spacing) * x_tick_spacing
                    x_tick_end = np.floor(x_max / x_tick_spacing) * x_tick_spacing
                    x_ticks = np.arange(x_tick_start, x_tick_end + x_tick_spacing/2, x_tick_spacing)
                    self.current_ax.set_xticks(x_ticks)
                    
                    # Calculate appropriate tick spacing for Y-axis (Pout)
                    y_range = y_max - y_min
                    if y_range <= 5:
                        y_tick_spacing = 0.5
                    elif y_range <= 10:
                        y_tick_spacing = 0.5
                    elif y_range <= 20:
                        y_tick_spacing = 1.0
                    else:
                        y_tick_spacing = 1.0
                    
                    # Create clean Y-axis ticks
                    y_tick_start = np.ceil(y_min / y_tick_spacing) * y_tick_spacing
                    y_tick_end = np.floor(y_max / y_tick_spacing) * y_tick_spacing
                    y_ticks = np.arange(y_tick_start, y_tick_end + y_tick_spacing/2, y_tick_spacing)
                    self.current_ax.set_yticks(y_ticks)
                    
                    # Format with 1 decimal place for clean values
                    self.current_ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
                    self.current_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.1f}'))
                else:
                    # For other plots, use 2 decimal places
                    self.current_ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
                    self.current_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.2f}'))
            else:
                # Default to 2 decimal places
                self.current_ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
                self.current_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.2f}'))
            
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
            
            # Clear previous plotted lines
            self.plotted_lines = []
            
            # Collect all curves for filter population
            all_curves = []
            
            # Plot each dataset
            for s_param_name, data in plot_data_dict.items():
                if 'curves' in data:
                    for curve in data['curves']:
                        # Convert to lists to avoid numpy array issues
                        x_data = list(curve['x']) if hasattr(curve['x'], '__iter__') else [curve['x']]
                        y_data = list(curve['y']) if hasattr(curve['y'], '__iter__') else [curve['y']]
                        
                        try:
                            line_obj = ax.plot(x_data, y_data, 
                                   label=curve.get('label', f'{s_param_name}'),
                                   linestyle=curve.get('linestyle', '-'),
                                   color=curve.get('color', None))[0]  # Get the Line2D object
                            
                            # Store line object and attributes for filtering
                            label = curve.get('label', f'{s_param_name}')
                            attributes = self.extract_curve_attributes(label)
                            self.plotted_lines.append((line_obj, label, attributes))
                            
                            # Add to curves list for filter population
                            all_curves.append(curve)
                            
                        except Exception as e:
                            print(f"ERROR plotting curve {curve.get('label', 'unknown')}: {e}")
                            continue
            
            # Add acceptance region if available
            first_data = next(iter(plot_data_dict.values()))
            if 'acceptance_region' in first_data:
                region = first_data['acceptance_region']
                
                # X-axis range is set by default_x_min/default_x_max from plot data
                
                # Handle VSWR acceptance region
                if 'vswr_max' in region:
                    # For VSWR plots, show rectangular acceptance region over operational frequency range only
                    from matplotlib.patches import Rectangle
                    vswr_min = region.get('vswr_min', 1.0)
                    rect = Rectangle((region['freq_min'], vswr_min), 
                                   region['freq_max'] - region['freq_min'],
                                   region['vswr_max'] - vswr_min,
                                   alpha=0.2, color='green', label='Acceptance Region')
                    ax.add_patch(rect)
                    
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
                
                # Handle IM3 acceptance region (check this BEFORE power to avoid conflicts)
                elif 'im3_min' in region and 'im3_max' in region:
                    # For IM3 plots, show area below maximum requirements (better IM3 = more negative)
                    # Extract Pin and IM3_max values from requirements
                    pin_values = []
                    im3_max_values = []
                    
                    # We need to get the actual requirement points from the acceptance_region
                    # These should be sorted by Pin
                    if 'requirement_points' in region:
                        # If we have the actual points, use them
                        sorted_points = sorted(region['requirement_points'], key=lambda p: p[0])
                        pin_values = [p[0] for p in sorted_points]
                        im3_max_values = [p[1] for p in sorted_points]
                    else:
                        # Fall back to corner points if detailed points aren't available
                        pin_values = [region['pin_min'], region['pin_max']]
                        im3_max_values = [region['im3_min'], region['im3_max']]
                    
                    # Draw a line connecting the maximum requirements
                    ax.plot(pin_values, im3_max_values, 'g--', linewidth=2, label='IM3 Limit', zorder=5)
                    
                    # Set axis limits from region data first
                    ax.set_xlim(region['x_min'], region['x_max'])
                    ax.set_ylim(region['y_min'], region['y_max'])
                    
                    # Shade the area from the requirement line down to the bottom of the plot (better IM3 = more negative)
                    # Get the actual plot limits after they're set
                    plot_y_min, plot_y_max = ax.get_ylim()
                    # For IM3, we want to fill from the requirement line down to the bottom (more negative = better)
                    # Since im3_max_values are less negative (higher) than plot_y_min, we need to swap the order
                    ax.fill_between(pin_values, plot_y_min, im3_max_values, 
                                    alpha=0.2, color='green', label='Acceptable Region')
                
                # Handle power acceptance region
                elif 'pin_min' in region and 'pin_max' in region:
                    # For power plots, show area above minimum requirements
                    # Extract Pin and Pout_min values from requirements
                    pin_values = []
                    pout_min_values = []
                    
                    # We need to get the actual requirement points from the acceptance_region
                    # These should be sorted by Pin
                    if 'requirement_points' in region:
                        # If we have the actual points, use them
                        sorted_points = sorted(region['requirement_points'], key=lambda p: p[0])
                        pin_values = [p[0] for p in sorted_points]
                        pout_min_values = [p[1] for p in sorted_points]
                    else:
                        # Fall back to corner points if detailed points aren't available
                        pin_values = [region['pin_min'], region['pin_max']]
                        pout_min_values = [region['pout_min'], region['pout_max']]
                    
                    # Draw a line connecting the minimum requirements
                    ax.plot(pin_values, pout_min_values, 'g--', linewidth=2, label='Minimum Requirement', zorder=5)
                    
                    # Shade the area above the minimum requirements line
                    ax.fill_between(pin_values, pout_min_values, region['y_max'], 
                                    alpha=0.2, color='green', label='Acceptable Region')
                    
                    # Set axis limits from region data
                    ax.set_xlim(region['x_min'], region['x_max'])
                    ax.set_ylim(region['y_min'], region['y_max'])
                
            
            # Set axis dividers based on current setting
            num_dividers = self.dividers_spin.value()
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            # Override with default axis limits from plot data if available
            # Skip this for IM3 plots since they handle their own axis limits
            is_im3_plot = 'IM3' in first_data.get('y_label', '')
            if 'default_x_min' in first_data and not is_im3_plot:
                x_min = first_data['default_x_min']
                ax.set_xlim(x_min, first_data.get('default_x_max', x_max))
            if 'default_y_min' in first_data and not is_im3_plot:
                y_min = first_data['default_y_min']
                ax.set_ylim(y_min, first_data.get('default_y_max', y_max))
            
            # For power plots, round axis limits to clean 0.25 or 0.5 increments
            if 'Pin' in first_data.get('x_label', '') or 'Pout' in first_data.get('y_label', ''):
                import numpy as np
                
                # Round X-axis limits to 0.5 increments
                x_min_rounded = np.floor(x_min / 0.5) * 0.5
                x_max_rounded = np.ceil(x_max / 0.5) * 0.5
                ax.set_xlim(x_min_rounded, x_max_rounded)
                
                # Round Y-axis limits to 0.5 increments  
                y_min_rounded = np.floor(y_min / 0.5) * 0.5
                y_max_rounded = np.ceil(y_max / 0.5) * 0.5
                ax.set_ylim(y_min_rounded, y_max_rounded)
                
                # Update the variables for later use
                x_min, x_max = x_min_rounded, x_max_rounded
                y_min, y_max = y_min_rounded, y_max_rounded
            
            # Update x_min, x_max, y_min, y_max with final values
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            x_ticks = [x_min + (x_max - x_min) * i / (num_dividers - 1) for i in range(num_dividers)]
            y_ticks = [y_min + (y_max - y_min) * i / (num_dividers - 1) for i in range(num_dividers)]
            
            ax.set_xticks(x_ticks)
            ax.set_yticks(y_ticks)
            
            # Format tick labels - use smart formatting for power plots
            if 'Pin' in first_data.get('x_label', '') or 'Pout' in first_data.get('y_label', ''):
                # For power plots, create clean 0.5 dBm increments
                import numpy as np
                
                # Calculate appropriate tick spacing for X-axis (Pin)
                x_range = x_max - x_min
                if x_range <= 5:
                    x_tick_spacing = 0.5
                elif x_range <= 10:
                    x_tick_spacing = 0.5
                elif x_range <= 20:
                    x_tick_spacing = 1.0
                else:
                    x_tick_spacing = 1.0
                
                # Create clean X-axis ticks
                x_tick_start = np.ceil(x_min / x_tick_spacing) * x_tick_spacing
                x_tick_end = np.floor(x_max / x_tick_spacing) * x_tick_spacing
                x_ticks = np.arange(x_tick_start, x_tick_end + x_tick_spacing/2, x_tick_spacing)
                ax.set_xticks(x_ticks)
                
                # Calculate appropriate tick spacing for Y-axis (Pout)
                y_range = y_max - y_min
                if y_range <= 5:
                    y_tick_spacing = 0.5
                elif y_range <= 10:
                    y_tick_spacing = 0.5
                elif y_range <= 20:
                    y_tick_spacing = 1.0
                else:
                    y_tick_spacing = 1.0
                
                # Create clean Y-axis ticks
                y_tick_start = np.ceil(y_min / y_tick_spacing) * y_tick_spacing
                y_tick_end = np.floor(y_max / y_tick_spacing) * y_tick_spacing
                y_ticks = np.arange(y_tick_start, y_tick_end + y_tick_spacing/2, y_tick_spacing)
                ax.set_yticks(y_ticks)
                
                # Format with 1 decimal place for clean values
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.1f}'))
            else:
                # For other plots, use 2 decimal places
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.2f}'))
            
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
                    # Handle SN/EM prefixes correctly
                    serial = metadata['serial']
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
            
            # Populate curve filters based on available curves
            self.populate_curve_filters(all_curves)
            
            # Draw the plot
            self.canvas.draw()
            # Setup interactive features
            self.current_ax = ax
            
            # Setup hover tooltips if enabled
            if self.hover_checkbox.isChecked():
                self.setup_hover_tooltips()
            
            # Setup crosshair cursor if enabled
            if self.crosshair_checkbox.isChecked():
                self.setup_crosshair()
            
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

    def toggle_hover(self):
        """Toggle hover tooltips on/off."""
        if self.hover_checkbox.isChecked():
            self.setup_hover_tooltips()
        else:
            self.remove_hover_tooltips()
    
    def toggle_crosshair(self):
        """Toggle crosshair cursor on/off."""
        if self.crosshair_checkbox.isChecked():
            self.setup_crosshair()
        else:
            self.remove_crosshair()
    
    def setup_hover_tooltips(self):
        """Setup hover tooltips for data points."""
        if not hasattr(self, 'current_ax') or not self.current_ax:
            return
        
        # Remove existing hover annotations
        self.remove_hover_tooltips()
        
        # Connect mouse motion event
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
    
    def remove_hover_tooltips(self):
        """Remove hover tooltips."""
        # Remove existing annotations
        for annotation in self.hover_annotations:
            if annotation in self.current_ax.texts:
                annotation.remove()
        self.hover_annotations.clear()
        
        # Disconnect mouse motion event
        self.canvas.mpl_disconnect('motion_notify_event')
    
    def setup_crosshair(self):
        """Setup crosshair cursor."""
        if not hasattr(self, 'current_ax') or not self.current_ax:
            return
        
        # Remove existing cursor
        self.remove_crosshair()
        
        # Create crosshair cursor
        self.cursor = Cursor(self.current_ax, useblit=True, color='red', linewidth=1)
    
    def remove_crosshair(self):
        """Remove crosshair cursor."""
        if self.cursor:
            self.cursor = None
    
    def on_hover(self, event):
        """Handle mouse hover events for tooltips."""
        if not hasattr(self, 'current_ax') or not self.current_ax:
            return
        
        if event.inaxes != self.current_ax:
            return
        
        # Remove existing annotations
        for annotation in self.hover_annotations:
            if annotation in self.current_ax.texts:
                annotation.remove()
        self.hover_annotations.clear()
        
        # Find the closest data point
        min_distance = float('inf')
        closest_line = None
        closest_index = None
        
        for line in self.current_ax.get_lines():
            if len(line.get_xdata()) == 0 or len(line.get_ydata()) == 0:
                continue
                
            # Get data points
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            
            # Calculate distance from mouse to each point
            for i, (x, y) in enumerate(zip(xdata, ydata)):
                # Transform to display coordinates
                display_x, display_y = self.current_ax.transData.transform((x, y))
                mouse_x, mouse_y = event.x, event.y
                
                distance = np.sqrt((display_x - mouse_x)**2 + (display_y - mouse_y)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_line = line
                    closest_index = i
        
        # Show tooltip if close enough (within 20 pixels)
        if min_distance < 20 and closest_line is not None:
            x = closest_line.get_xdata()[closest_index]
            y = closest_line.get_ydata()[closest_index]
            label = closest_line.get_label()
            
            # Create tooltip text
            tooltip_text = f"{label}\nX: {x:.3f}\nY: {y:.3f}"
            
            # Create annotation
            annotation = self.current_ax.annotate(
                tooltip_text,
                xy=(x, y),
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                fontsize=9
            )
            
            self.hover_annotations.append(annotation)
            self.canvas.draw_idle()
    
    def extract_curve_attributes(self, label: str) -> Dict[str, str]:
        """Extract filterable attributes from curve label."""
        attributes = {}
        
        # Extract frequency (patterns like @ 2.20 GHz, @ 2240 MHz)
        import re
        freq_patterns = [
            r'@\s*(\d+\.?\d*)\s*GHz',
            r'@\s*(\d+\.?\d*)\s*MHz',
        ]
        
        for pattern in freq_patterns:
            match = re.search(pattern, label)
            if match:
                freq_value = float(match.group(1))
                # Convert MHz to GHz for consistency
                if 'MHz' in label:
                    freq_value = freq_value / 1000.0
                
                # Format cleanly: 2.2, 2.24, 2.28 (no units, minimal decimals)
                # Remove trailing zeros for cleaner display
                formatted = f"{freq_value:.2f}".rstrip('0').rstrip('.')
                attributes['frequency'] = formatted
                break
        
        # Extract path (PRI/RED)
        if 'PRI' in label:
            attributes['path'] = 'PRI'
        elif 'RED' in label:
            attributes['path'] = 'RED'
        
        # Extract measurement type (IM3, IM5, S11, S21, etc.)
        type_patterns = [
            r'(IM3|IM5)',
            r'(S\d+)',
            r'(Temperature)',
            r'(Pout|Pin)'
        ]
        
        for pattern in type_patterns:
            match = re.search(pattern, label)
            if match:
                attributes['type'] = match.group(1)
                break
        
        # Extract sideband (Upper/Lower)
        if 'Upper' in label:
            attributes['sideband'] = 'Upper'
        elif 'Lower' in label:
            attributes['sideband'] = 'Lower'
        
        return attributes
    
    def populate_curve_filters(self, curves: List[Dict]):
        """Dynamically populate filter checkboxes based on available curves."""
        # Clear existing filter checkboxes
        for checkbox in self.filter_checkboxes.values():
            checkbox.setParent(None)
        self.filter_checkboxes.clear()
        
        # Extract all unique attributes
        all_attributes = {}
        for curve in curves:
            label = curve.get('label', '')
            attrs = self.extract_curve_attributes(label)
            for category, value in attrs.items():
                if category not in all_attributes:
                    all_attributes[category] = set()
                all_attributes[category].add(value)
        
        # Only show filter section if there are multiple curves with different attributes
        if len(all_attributes) == 0 or all(len(values) <= 1 for values in all_attributes.values()):
            self.filter_group.setVisible(False)
            return
        
        self.filter_group.setVisible(True)
        
        # Create checkboxes for each category using vertical layout
        for category, values in sorted(all_attributes.items()):
            if len(values) <= 1:
                continue
            
            # Add category label on its own row
            category_label = QLabel(f"{category.title()}:")
            self.filter_layout.addWidget(category_label)
            
            # Create horizontal layout for checkboxes
            checkbox_layout = QHBoxLayout()
            checkbox_layout.setSpacing(8)  # 8px between checkboxes
            
            # Add checkboxes
            for value in sorted(values):
                checkbox = QCheckBox(value)
                checkbox.setChecked(True)  # All checked by default
                checkbox.stateChanged.connect(self.apply_curve_filters)
                
                checkbox_key = f"{category}_{value}"
                self.filter_checkboxes[checkbox_key] = checkbox
                
                checkbox_layout.addWidget(checkbox)
            
            # Add stretch to push everything to the left
            checkbox_layout.addStretch()
            
            # Add this checkbox layout to the main filter layout
            self.filter_layout.addLayout(checkbox_layout)
    
    def apply_curve_filters(self):
        """Apply curve filtering based on checkbox selections."""
        if not self.plotted_lines:
            return
        
        # Get current filter selections
        active_filters = {}
        for key, checkbox in self.filter_checkboxes.items():
            category, value = key.split('_', 1)
            if checkbox.isChecked():
                if category not in active_filters:
                    active_filters[category] = set()
                active_filters[category].add(value)
        
        # Apply filters to each line
        for line_obj, label, attributes in self.plotted_lines:
            should_show = True
            
            # Check if line matches all active filter categories
            for category, active_values in active_filters.items():
                if category in attributes:
                    if attributes[category] not in active_values:
                        should_show = False
                        break
                else:
                    # If line doesn't have this category, hide it
                    should_show = False
                    break
            
            line_obj.set_visible(should_show)
        
        # Update legend to only show visible curves
        self.update_legend()
        self.canvas.draw_idle()
    
    def reset_all_filters(self):
        """Reset all filter checkboxes to checked state."""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(True)
        self.apply_curve_filters()
    
    def toggle_filter_section(self, checked: bool):
        """Handle filter section expand/collapse."""
        # This is handled automatically by QGroupBox.setCheckable()
        pass


