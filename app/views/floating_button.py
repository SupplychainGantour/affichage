from PyQt6.QtWidgets import QWidget, QPushButton, QApplication, QMenu, QWidgetAction
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, pyqtSignal
from PyQt6.QtGui import QPainter, QColor

def get_scaled_size(base_size):
    """Get size scaled for high DPI displays"""
    screen = QApplication.primaryScreen()
    dpi_ratio = screen.logicalDotsPerInch() / 96.0  # 96 DPI is standard
    # More conservative scaling to prevent oversized elements
    return max(base_size, int(base_size * min(dpi_ratio * 0.8, 1.5)))  # Cap at 1.5x scaling

class MainButton(QPushButton):
    """
    A custom button that handles both clicking and dragging its parent widget.
    This acts as the "handle" for the entire floating menu.
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._drag_start_position = None
        self._mouse_press_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # We get the position relative to the parent (the FloatingActionMenu)
            gp = event.globalPosition().toPoint()
            self._drag_start_position = gp - self.parent().frameGeometry().topLeft()
            self._mouse_press_position = gp
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_start_position:
            # We move the parent widget, not the button itself
            self.parent().move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._mouse_press_position is not None:
            moved = event.globalPosition().toPoint() - self._mouse_press_position
            if moved.manhattanLength() < QApplication.startDragDistance():
                # If it was a click, not a drag, emit the standard clicked signal
                self.click()

            self._drag_start_position = None
            self._mouse_press_position = None
            event.accept()
    
    def paintEvent(self, event):
        """Custom paint event to ensure perfect text centering."""
        super().paintEvent(event)
        
        # Draw the text manually in the center
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())
        painter.setPen(QColor("white"))
        
        # Calculate the center position
        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())


class ChildButton(QPushButton):
    """A small, circular button that is part of the main menu."""
    def __init__(self, icon_char, parent=None):
        super().__init__(icon_char, parent)
        
        # Scale button size based on DPI
        button_size = get_scaled_size(50)
        font_size = max(12, get_scaled_size(14))  # Smaller font to fit better
        border_radius = button_size // 2
        
        self.setFixedSize(button_size, button_size)
        
        # Use a more compatible font for better Unicode support
        font = self.font()
        font.setPixelSize(font_size)  # Use pixel size for more precise control
        font.setBold(True)
        font.setFamily("Arial Unicode MS")  # Better Unicode symbol support
        self.setFont(font)
        
        # Improved centering with proper padding
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #55595f;
                color: white;
                border-radius: {border_radius}px;
                border: 1px solid #777;
                padding: 0px;
                margin: 0px;
                text-align: center;
                vertical-align: middle;
            }}
            QPushButton:hover {{
                background-color: #6c7178;
            }}
        """)
        
        # Force center alignment
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)
    
    def paintEvent(self, event):
        """Custom paint event to ensure perfect text centering."""
        super().paintEvent(event)
        
        # Draw the text manually in the center
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())
        painter.setPen(QColor("white"))
        
        # Calculate the center position
        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())


class FloatingActionMenu(QWidget):
    """
    A draggable, expandable floating action menu.
    It contains a main button that reveals child action buttons when clicked.
    """
    
    # Signals for view management
    view_switch_requested = pyqtSignal(str)  # Emitted when user wants to switch view
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self._child_buttons = []
        self._animation_group = QParallelAnimationGroup()
        self.view_manager = None  # Will be set from controller
        
        # Main Container Widget Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Use our custom MainButton
        self.main_button = MainButton("M", self)
        
        # Scale main button size based on DPI
        main_button_size = get_scaled_size(65)
        main_font_size = max(16, get_scaled_size(18))  # More conservative font size
        main_border_radius = main_button_size // 2
        
        self.main_button.setFixedSize(main_button_size, main_button_size)
        font = self.main_button.font()
        font.setPixelSize(main_font_size)  # Use pixel size for precise control
        font.setBold(True)
        font.setFamily("Arial")  # Simple, reliable font
        self.main_button.setFont(font)
        
        self.main_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #007BFF;
                color: white;
                border-radius: {main_border_radius}px;
                border: 2px solid white;
                padding: 0px;
                margin: 0px;
                text-align: center;
                vertical-align: middle;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
        """)
        self.main_button.setContentsMargins(0, 0, 0, 0)
        self.main_button.clicked.connect(self.toggle_menu)

        # Initial size is just the main button
        self.resize(self.main_button.size())
    
    def set_view_manager(self, view_manager):
        """Set the view manager for this menu."""
        self.view_manager = view_manager
    
    def show_view_menu(self):
        """Show a context menu for view switching."""
        if not self.view_manager:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4a5568;
            }
        """)
        
        views = self.view_manager.get_views()
        current_view_id = self.view_manager.get_current_view_id()
        
        for view_id, view_data in views.items():
            action = menu.addAction(view_data['name'])
            action.setData(view_id)
            
            # Mark current view
            if view_id == current_view_id:
                action.setText(f"✓ {view_data['name']}")
                action.setEnabled(False)
        
        # Show menu near the button
        global_pos = self.main_button.mapToGlobal(QPoint(0, 0))
        menu.move(global_pos.x() - menu.sizeHint().width(), global_pos.y())
        
        action = menu.exec()
        if action:
            view_id = action.data()
            if view_id:
                self.view_switch_requested.emit(view_id)

    def add_action(self, icon_char, action_callable):
        """Adds a new action button to the menu."""
        button = ChildButton(icon_char, self)
        button.move(self.main_button.pos()) 
        button.hide()
        button.clicked.connect(action_callable)
        self._child_buttons.append(button)

    def clear_actions(self):
        """Removes all action buttons from the menu."""
        for button in self._child_buttons:
            button.deleteLater()
        self._child_buttons.clear()
        
    def update_actions(self, actions):
        """Updates the menu with a new set of actions.
        
        Args:
            actions: List of tuples (icon_char, action_callable)
        """
        self.clear_actions()
        for icon_char, action_callable in actions:
            self.add_action(icon_char, action_callable)

    def toggle_menu(self):
        self.raise_()
        
        self._animation_group.stop()
        self._animation_group = QParallelAnimationGroup()

        # Calculate spacing based on scaled sizes
        button_spacing = get_scaled_size(60)  # Adjusted for new button size
        button_offset = get_scaled_size(8)    # Adjusted offset
        expanded_height = (len(self._child_buttons) + 1) * button_spacing + get_scaled_size(5)

        if self._is_expanded:
            self.main_button.setText("M")
            self._is_expanded = False
            
            # COLLAPSE LOGIC
            buttons_to_animate = self._child_buttons[:]
            buttons_to_animate.reverse()

            for i, button in enumerate(buttons_to_animate):
                anim = QPropertyAnimation(button, b"pos")
                anim.setEndValue(QPoint(0,0)) # Animate back to the top-left of the container
                anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
                anim.setDuration(200 + i * 40)
                self._animation_group.addAnimation(anim)
                anim.finished.connect(button.hide)

            # Animate the container back to its original size AND position
            size_anim = QPropertyAnimation(self, b"geometry")
            current_geo = self.geometry()
            # The final geometry is the original 60x60, but at the current x,y location
            size_anim.setEndValue(current_geo.adjusted(0, expanded_height - self.main_button.height(), 0, 0))
            size_anim.setDuration(300)
            self._animation_group.addAnimation(size_anim)
            
            # Move the main button back to the top as the container shrinks
            button_pos_anim = QPropertyAnimation(self.main_button, b"pos")
            button_pos_anim.setEndValue(QPoint(0,0))
            button_pos_anim.setDuration(300)
            self._animation_group.addAnimation(button_pos_anim)

        else:
            self.main_button.setText("\u2715") # X Symbol
            self._is_expanded = True
            
            # EXPAND LOGIC
            current_pos = self.pos()
            self.setGeometry(current_pos.x(), 
                             current_pos.y() - (expanded_height - self.main_button.height()), 
                             self.main_button.width(), 
                             expanded_height)
            
            # Move main button to the bottom of the now larger widget
            self.main_button.move(0, self.height() - self.main_button.height())

            for i, button in enumerate(self._child_buttons):
                button.show()
                # Ensure child buttons are also at the bottom before animating up
                button.move(self.main_button.pos()) 
                
                anim = QPropertyAnimation(button, b"pos")
                start_pos = self.main_button.pos()
                end_pos = QPoint(start_pos.x() + button_offset, start_pos.y() - (i + 1) * button_spacing)
                anim.setStartValue(start_pos)
                anim.setEndValue(end_pos)
                anim.setEasingCurve(QEasingCurve.Type.OutBounce)
                anim.setDuration(350 + i * 50)
                self._animation_group.addAnimation(anim)

        self._animation_group.start()