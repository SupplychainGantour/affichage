from PyQt6.QtCore import Qt, QRect, QUrl, QPoint, QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QSlider, QLabel, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from app.core.profile_manager import WebProfileManager

# ---------- Minimal UI classes (EditOverlay + BrowserWindow) ----------
class EditOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._is_resizing = False
        self._is_dragging = False
        self._drag_start_position = QPoint()
        self._resize_margin = 16
        
        # Create zoom slider widget - minimal design at bottom
        self._zoom_widget = QWidget(self)
        self._zoom_widget.setFixedSize(150, 25)
        self._zoom_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
                border-radius: 12px;
                padding: 2px;
            }
            QSlider::groove:horizontal {
                border: 2px solid rgba(0, 122, 204, 0.8);
                height: 4px;
                background: rgba(255, 255, 255, 0.9);
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007ACC;
                border: 2px solid #ffffff;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.3);
            }
            QSlider::handle:horizontal:hover {
                background: #1e90ff;
                border: 2px solid #ffffff;
            }
            QSlider::handle:horizontal:pressed {
                background: #0066cc;
            }
        """)
        
        # Setup zoom controls - only slider, no label
        layout = QHBoxLayout(self._zoom_widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)
        
        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(25, 300)  # 25% to 300% zoom
        self._zoom_slider.setValue(100)
        
        layout.addWidget(self._zoom_slider)
        
        # Connect zoom slider
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        
        # Initially hide zoom widget
        self._zoom_widget.hide()

    def _on_zoom_changed(self, value):
        """Handle zoom slider changes."""
        zoom_factor = value / 100.0
        
        # Apply zoom to the parent browser window
        if hasattr(self.parent(), 'browser'):
            self.parent().browser.setZoomFactor(zoom_factor)

    def show_zoom_controls(self):
        """Show the zoom slider widget."""
        self._zoom_widget.show()
        self._position_zoom_widget()

    def hide_zoom_controls(self):
        """Hide the zoom slider widget."""
        self._zoom_widget.hide()

    def _position_zoom_widget(self):
        """Position zoom widget at bottom-center of overlay."""
        if self.width() > 0 and self.height() > 0:
            x = (self.width() - self._zoom_widget.width()) // 2
            y = self.height() - self._zoom_widget.height() - 15  # 15px from bottom
            self._zoom_widget.move(x, y)

    def resizeEvent(self, event):
        """Reposition zoom widget when overlay is resized."""
        super().resizeEvent(event)
        if self._zoom_widget.isVisible():
            self._position_zoom_widget()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        border_color = QColor(0, 170, 255, 200)
        pen = QPen(border_color, 4)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))
        handle_rect = self.get_resize_handle_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(border_color))
        painter.drawRect(handle_rect)

    def get_resize_handle_rect(self):
        return QRect(self.width() - self._resize_margin,
                     self.height() - self._resize_margin,
                     self._resize_margin,
                     self._resize_margin)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.globalPosition().toPoint()
            if self.get_resize_handle_rect().contains(event.pos()):
                self._is_resizing = True
            else:
                self._is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        if self.get_resize_handle_rect().contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_start_position
            parent = self.parent()
            if self._is_dragging:
                parent.move(parent.pos() + delta)
                self._drag_start_position = event.globalPosition().toPoint()
            elif self._is_resizing:
                new_width = parent.width() + delta.x()
                new_height = parent.height() + delta.y()
                parent.resize(max(200, new_width), max(200, new_height))
                self._drag_start_position = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        self._is_resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()


class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        try:
            print(f"JS Console ({sourceID}:{lineNumber}): {message}")
        except Exception:
            pass

    def createWindow(self, _type):
        """Handle popup window requests - create a simple popup that works."""
        print(f"Pop-up window requested (type: {_type}). Creating popup...")
        try:
            # Import here to avoid circular imports
            from PyQt6.QtWidgets import QDialog, QVBoxLayout
            
            # Create a simple dialog instead of QMainWindow
            popup_dialog = QDialog()
            popup_dialog.setWindowTitle("Authentication Required")
            popup_dialog.setModal(False)  # Non-modal so user can interact with main window
            popup_dialog.resize(800, 600)
            
            # Create layout
            layout = QVBoxLayout()
            popup_dialog.setLayout(layout)
            
            # Create the web view
            popup_browser = QWebEngineView()
            layout.addWidget(popup_browser)
            
            # Create new page with same profile
            new_page = CustomWebEnginePage(self.profile(), popup_browser)
            popup_browser.setPage(new_page)
            
            # Store reference to prevent garbage collection
            if not hasattr(self, '_popup_refs'):
                self._popup_refs = []
            self._popup_refs.append((popup_dialog, popup_browser, new_page))
            
            # Connect signals
            def on_load_finished(success):
                print(f"Popup load finished: {success}")
                
            def on_url_changed(url):
                url_str = url.toString()
                print(f"Popup URL: {url_str}")
                
                # Check for various Microsoft authentication success indicators
                success_indicators = [
                    'dashboard', 'authenticated', 'success', 'login_successful',
                    'app.powerbi.com/reportEmbed', 'app.powerbi.com/groups',
                    'sharepoint.com/personal', 'sharepoint.com/_layouts',
                    'office.com/login/success', 'login.microsoftonline.com/common/reprocess',
                    'powerbi.com/view', 'powerbi.com/reports'
                ]
                
                # Also check for specific Power BI embed URLs
                if any(indicator in url_str.lower() for indicator in success_indicators):
                    print("Authentication appears successful, closing popup")
                    popup_dialog.accept()
                    if hasattr(self, 'view') and self.view():
                        # Delay reload to allow session to propagate
                        def delayed_reload():
                            self.view().reload()
                        QTimer.singleShot(1000, delayed_reload)  # 1 second delay
            
            new_page.loadFinished.connect(on_load_finished)
            new_page.urlChanged.connect(on_url_changed)
            
            # Show popup in non-blocking way
            popup_dialog.show()
            
            print("Popup dialog created and shown")
            return new_page
            
        except Exception as e:
            print(f"Error in createWindow: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        """Handle navigation requests, including popup attempts."""
        print(f"Navigation request: {url.toString()} (type: {_type}, mainFrame: {isMainFrame})")
        # Allow all navigation requests
        return True


class BrowserWindow(QMainWindow):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authenticated Browser")
        self.setGeometry(50, 50, 1280, 800)

        # Create a container widget for the border effect
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #2d5a2d;
                border-radius: 8px;
                padding: 3px;
            }
        """)
        
        # Create layout for container
        from PyQt6.QtWidgets import QVBoxLayout
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(3, 3, 3, 3)
        container_layout.setSpacing(0)

        self.page = CustomWebEnginePage(profile, self)
        self.browser = QWebEngineView(self)
        self.browser.setPage(self.page)
        
        # Style the browser view
        self.browser.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: white;
            }
        """)
        
        # Add browser to container
        container_layout.addWidget(self.browser)
        self.setCentralWidget(container)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # Remove translucent background to show borders
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.edit_overlay = EditOverlay(self)
        self.edit_overlay.hide()

        # debug signals
        self.browser.loadProgress.connect(lambda p: print(f"[browser] load {p}%"))
        self.browser.loadFinished.connect(lambda ok: print("[browser] finished:", ok))
        # Provide credentials if the engine requests them at the page level
        if WebProfileManager().has_credentials():
            try:
                self.page.authenticationRequired.connect(self._on_auth_required)
            except Exception:
                pass


    def load_url(self, url):
        print("Loading:", url)
        # If we have explicit creds, attempt NTLM session first to prime cookies
        try:
            pm = WebProfileManager()
            if pm.has_credentials():
                pm.ntlm_session_and_inject(url)
        except Exception as e:
            print("[auth] NTLM pre-injection failed:", e)
        self.browser.setUrl(QUrl(url))

    def set_geometry(self, x, y, width, height):
        """Set the geometry of the browser window."""
        self.setGeometry(QRect(x, y, width, height))

    def set_edit_mode(self, enabled):
        """Shows or hides the edit overlay with zoom controls."""
        if enabled:
            self.edit_overlay.setGeometry(self.rect())
            self.edit_overlay.show()
            self.edit_overlay.show_zoom_controls()
            self.edit_overlay.raise_()
        else:
            self.edit_overlay.hide_zoom_controls()
            self.edit_overlay.hide()
    
    def _on_auth_required(self, requestUrl, auth):
        try:
            user, pwd = WebProfileManager().get_auth_credentials()
            if hasattr(auth, "setUser") and hasattr(auth, "setPassword"):
                auth.setUser(user)
                auth.setPassword(pwd)
                print("[auth] Provided credentials to authenticationRequired signal")
        except Exception as e:
            print("[auth] Error supplying credentials:", e)
            
    def resizeEvent(self, event):
        """Ensure the overlay is always the same size as the window."""
        super().resizeEvent(event)
        if self.edit_overlay.isVisible():
            self.edit_overlay.setGeometry(self.rect())