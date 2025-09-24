from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SaveLayoutDialog(QDialog):
    """Dialog for saving a custom layout with a name and description."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Custom Layout")
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit, QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #007BFF;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton#cancel_button {
                background-color: #6c757d;
            }
            QPushButton#cancel_button:hover {
                background-color: #545b62;
            }
        """)
        
        self.layout_name = ""
        self.layout_description = ""
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Save Current Layout")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Name field
        name_label = QLabel("Layout Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for your layout...")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # Description field
        desc_label = QLabel("Description (optional):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter a description for your layout...")
        self.desc_input.setMaximumHeight(60)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.clicked.connect(self.reject)
        
        save_button = QPushButton("Save Layout")
        save_button.clicked.connect(self._on_save)
        save_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        # Set focus to name input
        self.name_input.setFocus()
        
    def _on_save(self):
        """Handle save button click."""
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setStyleSheet("""
                QLineEdit {
                    background-color: #3c3c3c;
                    border: 2px solid #dc3545;
                    border-radius: 4px;
                    padding: 6px;
                    color: #ffffff;
                    font-size: 11px;
                }
            """)
            self.name_input.setPlaceholderText("Please enter a layout name!")
            return
            
        self.layout_name = name
        self.layout_description = self.desc_input.toPlainText().strip()
        self.accept()
        
    def get_layout_info(self):
        """Returns the entered layout name and description."""
        return self.layout_name, self.layout_description
