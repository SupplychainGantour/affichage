from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt

class SaveViewDialog(QDialog):
    """Dialog for saving a custom view with a name and description."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Current View")
        self.setMinimumSize(420, 320)
        self.resize(420, 400)  # Initial size, but allow resize
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # Simple dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton#cancel_button {
                background-color: #666666;
            }
            QPushButton#cancel_button:hover {
                background-color: #777777;
            }
            QRadioButton {
                color: #ffffff;
                font-size: 12px;
            }
        """)
        
        self.view_name = ""
        self.view_description = ""
        self.save_type = "view"
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title_label = QLabel("Save Current Arrangement")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center; padding: 8px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(5)
        
        # Save type - NO FRAME, just direct widgets
        save_type_label = QLabel("Save as:")
        layout.addWidget(save_type_label)
        
        self.button_group = QButtonGroup(self)
        
        self.view_radio = QRadioButton("View (layout + content)")
        self.view_radio.setChecked(True)
        layout.addWidget(self.view_radio)
        
        self.layout_radio = QRadioButton("Layout only (positions)")  
        layout.addWidget(self.layout_radio)
        
        self.button_group.addButton(self.view_radio)
        self.button_group.addButton(self.layout_radio)
        
        layout.addSpacing(8)
        
        # Name field
        name_label = QLabel("Name:")
        name_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a descriptive name...")
        layout.addWidget(self.name_input)
        
        # Description field
        desc_label = QLabel("Description (optional):")
        desc_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Brief description...")
        # Remove fixed height constraints to let it size naturally
        self.desc_input.setMinimumHeight(50)
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)
        
        # Add spacing before buttons
        layout.addSpacing(15)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.setMinimumHeight(35)
        cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Save View")
        self.save_button.setMinimumHeight(35)
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setDefault(True)
        
        # Update button text based on selection
        self.view_radio.toggled.connect(self._update_button_text)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
        
        # Set focus to name input
        self.name_input.setFocus()
        
    def _update_button_text(self):
        """Update button text based on selected save type."""
        if self.view_radio.isChecked():
            self.save_button.setText("Save View")
        else:
            self.save_button.setText("Save Layout")
    
    def _on_save(self):
        """Handle save button click."""
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        
        self.view_name = name
        self.view_description = self.desc_input.toPlainText().strip()
        self.save_type = "view" if self.view_radio.isChecked() else "layout"
        self.accept()
    
    def get_save_data(self):
        """Get the entered save data."""
        return {
            "name": self.view_name,
            "description": self.view_description,
            "type": self.save_type
        }