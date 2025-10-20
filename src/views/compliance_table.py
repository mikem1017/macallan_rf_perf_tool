"""
Reusable compliance table widget with export capabilities
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from src.utils.export_utils import ExportUtils
from typing import List, Dict, Any, Optional

class ComplianceTable(QWidget):
    """Reusable compliance table widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # Export buttons
        button_layout = QHBoxLayout()
        
        self.copy_image_btn = QPushButton("Copy as Image")
        self.copy_image_btn.clicked.connect(self.copy_as_image)
        button_layout.addWidget(self.copy_image_btn)
        
        self.save_png_btn = QPushButton("Save as PNG")
        self.save_png_btn.clicked.connect(self.save_as_png)
        button_layout.addWidget(self.save_png_btn)
        
        self.save_pdf_btn = QPushButton("Save as PDF")
        self.save_pdf_btn.clicked.connect(self.save_as_pdf)
        button_layout.addWidget(self.save_pdf_btn)
        
        self.copy_text_btn = QPushButton("Copy as Text")
        self.copy_text_btn.clicked.connect(self.copy_as_text)
        button_layout.addWidget(self.copy_text_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect to section resize events to track manual column width changes
        self.table.horizontalHeader().sectionResized.connect(self.on_column_resized)
    
    def on_column_resized(self, logical_index: int, old_size: int, new_size: int):
        """Handle manual column resize to preserve user preferences."""
        if hasattr(self, '_column_widths'):
            if logical_index < len(self._column_widths):
                self._column_widths[logical_index] = new_size
            else:
                # Extend the list if needed
                while len(self._column_widths) <= logical_index:
                    self._column_widths.append(100)  # Default width
                self._column_widths[logical_index] = new_size
    
    def set_data(self, data: List[Dict[str, Any]], columns: List[str], 
                 hg_lg_enabled: bool = False):
        """Set the compliance table data."""
        if not data:
            self.show_no_data_message()
            return
        
        # Determine column structure based on HG/LG setting
        if hg_lg_enabled:
            # Columns: Requirement | Limit | PRI HG | PRI HG Status | PRI LG | PRI LG Status | RED HG | RED HG Status | RED LG | RED LG Status
            base_columns = ["Requirement", "Limit"]
            data_columns = ["PRI HG", "PRI HG Status", "PRI LG", "PRI LG Status", 
                          "RED HG", "RED HG Status", "RED LG", "RED LG Status"]
            all_columns = base_columns + data_columns
        else:
            # Columns: Requirement | Limit | PRI | PRI Status | RED | RED Status
            base_columns = ["Requirement", "Limit"]
            data_columns = ["PRI", "PRI Status", "RED", "RED Status"]
            all_columns = base_columns + data_columns
        
        # Set up table dimensions
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(all_columns))
        self.table.setHorizontalHeaderLabels(all_columns)
        
        # Preserve table size by maintaining window-filling behavior
        # Store current column widths if they exist
        current_widths = []
        if hasattr(self, '_column_widths') and len(self._column_widths) == len(all_columns):
            current_widths = self._column_widths
        
        # Restore column widths if available, otherwise use stretch behavior
        if current_widths:
            for col, width in enumerate(current_widths):
                self.table.setColumnWidth(col, width)
        else:
            # First time - use stretch behavior to fill window width
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            # Store the widths for future updates
            self._column_widths = [self.table.columnWidth(col) for col in range(len(all_columns))]
        
        # Populate table
        for row, item in enumerate(data):
            # Requirement
            req_item = QTableWidgetItem(str(item.get('requirement', '')))
            req_item.setFlags(req_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, req_item)
            
            # Limit
            limit_item = QTableWidgetItem(str(item.get('limit', '')))
            limit_item.setFlags(limit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, limit_item)
            
            # Data columns
            col_idx = 2
            for col_name in data_columns:
                if col_name.endswith('Status'):
                    # Status column
                    status_value = item.get(col_name.lower().replace(' ', '_'), 'N/A')
                    status_item = QTableWidgetItem(str(status_value))
                    status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    # Color coding
                    if status_value == 'Pass':
                        status_item.setBackground(QColor(200, 255, 200))  # Light green
                        status_item.setForeground(QColor(0, 0, 0))  # Black text
                    elif status_value == 'Fail':
                        status_item.setBackground(QColor(255, 200, 200))  # Light red
                        status_item.setForeground(QColor(0, 0, 0))  # Black text
                    
                    self.table.setItem(row, col_idx, status_item)
                else:
                    # Value column
                    value = item.get(col_name.lower().replace(' ', '_'), 'N/A')
                    value_item = QTableWidgetItem(str(value))
                    value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, col_idx, value_item)
                
                col_idx += 1
    
    def show_no_data_message(self):
        """Show 'No data loaded' message."""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Status"])
        
        no_data_item = QTableWidgetItem("No data loaded")
        no_data_item.setFlags(no_data_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        no_data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        no_data_item.setFont(QFont("Arial", 12))
        self.table.setItem(0, 0, no_data_item)
        
        # Center the single cell
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    
    def clear_data(self):
        """Clear the table data."""
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
    
    def copy_as_image(self):
        """Copy table as image to clipboard."""
        if ExportUtils.copy_table_to_clipboard(self.table):
            QMessageBox.information(self, "Success", "Table copied to clipboard as image.")
        else:
            QMessageBox.warning(self, "Error", "Failed to copy table to clipboard.")
    
    def save_as_png(self):
        """Save table as PNG file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Table as PNG", "", "PNG Files (*.png)")
        
        if file_path:
            if ExportUtils.save_table_as_png(self.table, file_path):
                QMessageBox.information(self, "Success", f"Table saved as PNG: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save table as PNG.")
    
    def save_as_pdf(self):
        """Save table as PDF file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Table as PDF", "", "PDF Files (*.pdf)")
        
        if file_path:
            # For PDF, we'll need to create a matplotlib figure
            # This is a simplified implementation
            QMessageBox.information(self, "Info", "PDF export not yet implemented.")
    
    def copy_as_text(self):
        """Copy table as formatted text for Excel/Word."""
        if ExportUtils.copy_table_as_text(self.table):
            QMessageBox.information(self, "Success", "Table copied to clipboard as text.")
        else:
            QMessageBox.warning(self, "Error", "Failed to copy table as text.")
    
    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the current table data as a list of dictionaries."""
        data = []
        
        for row in range(self.table.rowCount()):
            item = {}
            
            # Get requirement
            req_item = self.table.item(row, 0)
            if req_item:
                item['requirement'] = req_item.text()
            
            # Get limit
            limit_item = self.table.item(row, 1)
            if limit_item:
                item['limit'] = limit_item.text()
            
            # Get data columns
            for col in range(2, self.table.columnCount()):
                header = self.table.horizontalHeaderItem(col)
                if header:
                    col_name = header.text().lower().replace(' ', '_')
                    cell_item = self.table.item(row, col)
                    if cell_item:
                        item[col_name] = cell_item.text()
            
            data.append(item)
        
        return data
