from PyQt6.QtCore import Qt, QRect, QUrl, QPoint
from PyQt6.QtWidgets import QMainWindow, QWidget
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
        new_page = CustomWebEnginePage(self.profile())
        # load new page in current view for simplicity
        try:
            new_page.urlChanged.connect(self.parent().browser.setUrl)
        except Exception:
            pass
        print("Pop-up window requested.")
        return new_page


class BrowserWindow(QMainWindow):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authenticated Browser")
        self.setGeometry(50, 50, 1280, 800)

        self.page = CustomWebEnginePage(profile, self)
        self.browser = QWebEngineView(self)
        self.browser.setPage(self.page)
        self.setCentralWidget(self.browser)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # PyQt6: widget attributes are in Qt.WidgetAttribute
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

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
        """Shows or hides the edit overlay."""
        if enabled:
            self.edit_overlay.setGeometry(self.rect())
            self.edit_overlay.show()
            self.edit_overlay.raise_()
        else:
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