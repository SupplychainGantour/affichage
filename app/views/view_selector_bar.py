from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QFrame, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ViewSelectorBar(QWidget):
    """
    Horizontal bar that shows available views for selection.
    Displayed on app startup instead of opening windows immediately.
    """
    view_selected = pyqtSignal(str)  # Emits view_id when a view is selected
    
    def __init__(self, view_manager):
        super().__init__()
        self._view_manager = view_manager
        self._setup_ui()
        self._load_views()
        self._center_on_screen()
        
    def _center_on_screen(self):
        """Center the view selector on screen for 1920x1080 resolution."""
        # Set window size optimized for 1920x1080
        self.resize(1200, 120)  # Wide horizontal bar
        
        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate center position
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        
        self.move(x, y)
        
    def _setup_ui(self):
        """Set up the horizontal selector bar UI."""
        self.setWindowTitle("Select View")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create the bar container
        bar_frame = QFrame()
        bar_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #404040;
                border-radius: 12px;
            }
        """)
        
        # Bar layout
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(25, 20, 25, 20)
        bar_layout.setSpacing(15)
        
        # Title label - bigger for 1920x1080
        title_label = QLabel("Select View")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        bar_layout.addWidget(title_label)
        
        # Buttons container
        self._buttons_layout = QHBoxLayout()
        self._buttons_layout.setSpacing(20)
        bar_layout.addLayout(self._buttons_layout)
        
        main_layout.addWidget(bar_frame)
        
        self.setLayout(main_layout)
        
        # Apply window styling
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
    def _load_views(self):
        """Load available views and create buttons for them."""
        views = self._view_manager.get_views()
        
        if not views:
            # Show a message if no views available
            no_views_label = QLabel("No views available")
            no_views_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-style: italic;
                    padding: 5px;
                }
            """)
            self._buttons_layout.addWidget(no_views_label)
            return
            
        # Create a button for each view
        for view_id, view_data in views.items():
            button = self._create_view_button(view_id, view_data)
            self._buttons_layout.addWidget(button)
            
    def _create_view_button(self, view_id, view_data):
        """Create a styled button for a view."""
        # Get view name and description
        view_name = view_data.get('name', view_id.title())
        view_description = view_data.get('description', '')
        
        button = QPushButton()
        button.setText(view_name)
        button.setToolTip(view_description)
        
        # Style the button - bigger for 1920x1080 resolution
        button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 2px solid #505050;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                min-width: 150px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #606060;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #606060;
                border-color: #707070;
            }
        """)
        
        # Connect button click to view selection
        button.clicked.connect(lambda checked, vid=view_id: self._on_view_selected(vid))
        
        return button
        
    def _on_view_selected(self, view_id):
        """Handle view selection."""
        print(f"View selected: {view_id}")
        self.view_selected.emit(view_id)
        self.hide()  # Hide the selector bar after selection
        
    def show_centered(self):
        """Show the bar centered on screen."""
        self.show()
        self.raise_()
        self.activateWindow()