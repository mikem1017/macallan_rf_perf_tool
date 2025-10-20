"""
Simplified PlotWindow to isolate the crash issue.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
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
        
        # Plot canvas
        layout.addWidget(self.canvas)
        
        print("DEBUG: Basic UI initialized successfully")
    
    def plot_multiple_data(self, plot_data_dict: Dict[str, Dict[str, Any]], metadata: Dict[str, str] = None):
        """Plot multiple datasets in a single plot."""
        print("DEBUG: plot_multiple_data started")
        
        try:
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
                if 'freq_min' in region and 'freq_max' in region:
                    freq_expansion = (region['freq_max'] - region['freq_min']) * 0.1
                    ax.set_xlim(region['freq_min'] - freq_expansion, region['freq_max'] + freq_expansion)
                    
                    if 'vswr_max' in region:
                        # For VSWR plots, show horizontal span
                        ax.axhspan(0, region['vswr_max'], 
                                  alpha=0.3, color='green', label='Acceptance Region')
                        ax.set_ylim(0, region['vswr_max'] * 1.2)
            
            # Set labels and title
            ax.set_xlabel(first_data.get('x_label', 'Frequency (GHz)'))
            ax.set_ylabel(first_data.get('y_label', 'VSWR'))
            ax.set_title(first_data.get('title', 'VSWR Plot'))
            ax.legend()
            
            # Draw the plot
            self.canvas.draw()
            print("DEBUG: plot_multiple_data completed successfully")
            
        except Exception as e:
            print(f"ERROR in plot_multiple_data: {e}")
            import traceback
            traceback.print_exc()
            raise



