"""
Export utilities for plots and tables
"""

import os
import io
from typing import Optional
from PyQt6.QtWidgets import QWidget, QTableWidget, QApplication
from PyQt6.QtCore import QMimeData, QByteArray
from PyQt6.QtGui import QPixmap, QPainter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ExportUtils:
    """Utilities for exporting plots and tables."""
    
    @staticmethod
    def copy_plot_to_clipboard(figure: Figure) -> bool:
        """Copy a matplotlib figure to clipboard as image."""
        try:
            # Convert figure to pixmap
            canvas = FigureCanvas(figure)
            canvas.draw()
            
            # Get the pixmap
            pixmap = canvas.grab()
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            
            return True
        except Exception as e:
            print(f"Error copying plot to clipboard: {e}")
            return False
    
    @staticmethod
    def save_plot_as_png(figure: Figure, file_path: str) -> bool:
        """Save a matplotlib figure as PNG."""
        try:
            figure.savefig(file_path, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving plot as PNG: {e}")
            return False
    
    @staticmethod
    def save_plot_as_pdf(figure: Figure, file_path: str) -> bool:
        """Save a matplotlib figure as PDF."""
        try:
            figure.savefig(file_path, format='pdf', bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving plot as PDF: {e}")
            return False
    
    @staticmethod
    def copy_table_to_clipboard(table_widget: QTableWidget) -> bool:
        """Copy table widget to clipboard as image."""
        try:
            # Create pixmap of the table
            pixmap = table_widget.grab()
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            
            return True
        except Exception as e:
            print(f"Error copying table to clipboard: {e}")
            return False
    
    @staticmethod
    def save_table_as_png(table_widget: QTableWidget, file_path: str) -> bool:
        """Save table widget as PNG."""
        try:
            # Create pixmap of the table
            pixmap = table_widget.grab()
            
            # Save to file
            pixmap.save(file_path)
            
            return True
        except Exception as e:
            print(f"Error saving table as PNG: {e}")
            return False
    
    @staticmethod
    def copy_table_as_text(table_widget: QTableWidget) -> bool:
        """Copy table as formatted text for Excel/Word."""
        try:
            text_data = ""
            
            # Get table dimensions
            rows = table_widget.rowCount()
            cols = table_widget.columnCount()
            
            # Build text representation
            for row in range(rows):
                row_data = []
                for col in range(cols):
                    item = table_widget.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                
                text_data += "\t".join(row_data) + "\n"
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            mime_data = QMimeData()
            mime_data.setText(text_data)
            clipboard.setMimeData(mime_data)
            
            return True
        except Exception as e:
            print(f"Error copying table as text: {e}")
            return False
    
    @staticmethod
    def generate_pdf_report(plots: list, tables: list, metadata: dict, file_path: str) -> bool:
        """Generate a comprehensive PDF report."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("Macallan RF Performance Test Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Metadata
            if metadata:
                meta_text = f"""
                <b>Test Information:</b><br/>
                DUT: {metadata.get('dut_name', 'N/A')}<br/>
                Serial Number: {metadata.get('serial_number', 'N/A')}<br/>
                Part Number: {metadata.get('part_number', 'N/A')}<br/>
                Date: {metadata.get('date_code', 'N/A')}<br/>
                Test Stage: {metadata.get('test_stage', 'N/A')}<br/>
                """
                meta_para = Paragraph(meta_text, styles['Normal'])
                story.append(meta_para)
                story.append(Spacer(1, 12))
            
            # Add plots
            for i, plot in enumerate(plots):
                if plot:
                    # Save plot to temporary file
                    temp_path = f"temp_plot_{i}.png"
                    if ExportUtils.save_plot_as_png(plot, temp_path):
                        # Add to PDF
                        img = Image(temp_path, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 12))
                        
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
            
            # Build PDF
            doc.build(story)
            
            return True
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return False



