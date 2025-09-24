import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QScrollArea, QWidget, QGraphicsDropShadowEffect, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QColor, QDrag, QPainter, QPen, QFont, QPixmap

# --- REFINED STYLESHEET FOR CLARITY AND DEPTH ---
STYLESHEET = """
/* ---- Main Dialog Frame ---- */
#main_frame {
    /* Solid, very dark, and mostly opaque for legibility */
    background-color: rgba(25, 28, 32, 0.97); 
    border-radius: 12px;
    border: 1px solid rgba(0, 170, 255, 0.4);
}

/* ---- Labels and Titles ---- */
QLabel {
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: white;
    padding: 10px;
}
QLabel#panel_title {
    font-size: 14px;
    font-weight: bold;
    color: white;
    padding: 5px;
    border-bottom: 1px solid #444;
    margin-bottom: 10px;
}

/* ---- Buttons ---- */
QPushButton {
    background-color: #007BFF;
    color: white;
    border: none;
    padding: 10px 20px;
    font-size: 13px;
    font-family: 'Segoe UI', Arial, sans-serif;
    border-radius: 6px;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #009cff;
}
QPushButton#cancel_button {
    background-color: #444950;
}
QPushButton#cancel_button:hover {
    background-color: #5a5f66;
}

/* ---- Scroll Area and Panels ---- */
QScrollArea {
    border: none;
    background-color: transparent;
}
#panel_frame {
    /* Slightly lighter background for internal panels to create contrast */
    background-color: rgba(42, 45, 49, 0.8);
    border-radius: 8px;
}

/* ---- Custom Widget States ---- */
DraggablePageLabel, DropZoneWidget {
    background-color: #2a2d31;
    border: 2px dashed #555;
    border-radius: 8px;
    color: #ccc;
    font-size: 12px;
    padding: 8px;
}
DropZoneWidget[assigned="true"] {
    background-color: #003366;
    border: 2px solid #00aaff;
    color: white;
}
DropZoneWidget[dragover="true"] {
    background-color: #004488;
    border: 2px solid #33ccff;
}
LayoutPreviewWidget {
    background-color: #2a2d31;
    border: 2px solid #555;
    border-radius: 8px;
    font-size: 12px;
}
LayoutPreviewWidget:hover {
    border-color: #007BFF;
}
LayoutPreviewWidget[selected="true"] {
    border: 2px solid #00aaff;
    background-color: #003366;
}
"""

# The DraggablePageLabel, DropZoneWidget, and LayoutPreviewWidget classes
# are unchanged from the previous version. I am including them here again
# so you can replace the entire file without issue.

class DraggablePageLabel(QLabel):
    """A label representing a webpage that can be dragged."""
    def __init__(self, page_id, parent=None):
        super().__init__(page_id, parent)

        self.page_id = page_id
        self.setMinimumHeight(60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return
        
        mime_data = QMimeData()
        mime_data.setText(self.page_id)
        
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)
        painter.drawPixmap(self.rect(), self.grab())
        painter.end()

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec(Qt.DropAction.MoveAction)

class DropZoneWidget(QFrame):
    """A drop zone representing a layout slot."""
    pageDropped = pyqtSignal(str, str)

    def __init__(self, slot_id, parent=None):
        super().__init__(parent)
        self.slot_id = slot_id
        self.setAcceptDrops(True)
        self.assigned_page_id = None
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)
        self.main_layout.setSpacing(10)

        self.slot_label = QLabel(f"Slot: {slot_id}")
        self.slot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label = QLabel("(Drop Page Here)")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-style: italic; color: #777;")
        self.page_label.setWordWrap(True)
        self.page_label.setMinimumHeight(40)

        self.main_layout.addWidget(self.slot_label)
        self.main_layout.addWidget(self.page_label)

        self.setProperty("assigned", False)
        self.setProperty("dragover", False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setProperty("dragover", True)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dragover", False)
        self.style().polish(self)

    def dropEvent(self, event):
        page_id = event.mimeData().text()
        self.assigned_page_id = page_id
        
        self.page_label.setText(page_id)
        self.page_label.setStyleSheet("")
        
        self.setProperty("assigned", True)
        self.setProperty("dragover", False)
        self.style().polish(self)
        
        self.pageDropped.emit(self.slot_id, self.assigned_page_id)

class LayoutPreviewWidget(QFrame):
    """A clickable widget that shows a visual preview of a layout."""
    selected = pyqtSignal(str)

    def __init__(self, layout_name, slots_data, parent=None):
        super().__init__(parent)
        self.layout_name = layout_name
        self.slots_data = slots_data
        
        self.setMinimumSize(200, 150)
        self.setMaximumHeight(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("selected", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        label = QLabel(layout_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setMaximumHeight(25)
        layout.addWidget(label)
        layout.addStretch()

    def set_selected(self, is_selected):
        self.setProperty("selected", is_selected)
        self.style().polish(self)

    def mousePressEvent(self, event):
        self.selected.emit(self.layout_name)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define the area where we'll draw the preview (leave space for the label)
        preview_area = self.rect().adjusted(10, 30, -10, -10)
        
        # Set up drawing style
        pen = QPen(QColor("#00aaff"), 2)
        painter.setPen(pen)
        painter.setBrush(QColor("#3a3d41"))
        
        # Draw each slot as a rectangle
        for slot in self.slots_data:
            geo = slot['geometry']
            # Use normalized coordinates (0.0 to 1.0) directly
            x = preview_area.x() + (geo['x'] * preview_area.width())
            y = preview_area.y() + (geo['y'] * preview_area.height())
            w = geo['width'] * preview_area.width()
            h = geo['height'] * preview_area.height()
            
            # Draw the rectangle
            painter.drawRect(int(x), int(y), int(w), int(h))
            
            # Draw slot ID text in the center of each rectangle
            text_rect = painter.boundingRect(int(x), int(y), int(w), int(h), Qt.AlignmentFlag.AlignCenter, slot['id'])
            if text_rect.width() < w and text_rect.height() < h:
                painter.setPen(QColor("#ffffff"))
                painter.drawText(int(x), int(y), int(w), int(h), Qt.AlignmentFlag.AlignCenter, slot['id'])
                painter.setPen(pen)

class ScreenManagerDialog(QDialog):
    layoutApplied = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Screen Layout Manager")
        
        # --- Get screen geometry for adaptive sizing ---
        screen_geom = QApplication.primaryScreen().geometry()
        # Set size relative to the screen but with reasonable limits
        dialog_width = max(1000, min(int(screen_geom.width() * 0.7), 1400))
        dialog_height = max(700, min(int(screen_geom.height() * 0.8), 900))
        self.setMinimumSize(dialog_width, dialog_height)
        
        # --- KEY CHANGE: REMOVE BLUR EFFECT ---
        # The blur effect is removed. We now control the look with the background color and shadow.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        # --- DROP SHADOW FOR DEPTH ---
        # This is now the primary effect for separating the dialog from the background.
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(50) # Increased blur radius for a softer, more prominent shadow
        self.shadow.setColor(QColor(0, 0, 0, 200)) # Darker shadow
        self.shadow.setOffset(0, 0)

        # The main frame holds all content. The shadow is applied to it.
        self.main_frame = QFrame(self, objectName="main_frame")
        self.main_frame.setGraphicsEffect(self.shadow)
        
        # This layout centers the main_frame, providing margin for the shadow to appear.
        self.super_layout = QVBoxLayout(self)
        self.super_layout.setContentsMargins(40, 40, 40, 40)
        self.super_layout.addWidget(self.main_frame)

        self.main_frame.setStyleSheet(STYLESHEET)
        
        # Data and other setup remains the same
        self._layouts_data = {}
        self._pages_data = []
        self._current_assignments = {}
        self._selected_layout_name = None
        self._layout_widgets = {}

        # --- Main Layout (inside the main_frame) ---
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_layout.setContentsMargins(20, 10, 20, 20)
        
        # --- Title Bar ---
        title = QLabel("Screen Layout Manager", objectName="title")
        self.main_layout.addWidget(title)

        # --- Content Area ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        self.main_layout.addLayout(content_layout, stretch=1)

        # --- Left, Middle, Right Panels ---
        self.layouts_container = self._create_panel("1. Select Layout")
        self.pages_container = self._create_panel("2. Available Pages")
        self.slots_container = self._create_panel("3. Assign to Slots")
        content_layout.addWidget(self.layouts_container, stretch=3)
        content_layout.addWidget(self.pages_container, stretch=2)
        content_layout.addWidget(self.slots_container, stretch=3)
        
        # --- Bottom Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_button = QPushButton("  Cancel", objectName="cancel_button")
        apply_button = QPushButton("  Apply Layout")
        cancel_button.setText("\u2716 " + cancel_button.text()) # Unicode X
        apply_button.setText("\u2714 " + apply_button.text()) # Unicode Checkmark
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(apply_button)
        self.main_layout.addLayout(button_layout)
        
        # --- Connections ---
        cancel_button.clicked.connect(self.reject)
        apply_button.clicked.connect(self.on_accept)

    # All helper methods (_create_panel, load_data, _clear_layout_container, etc.)
    # remain the same as the previous version. I am including them for completeness.

    def _create_panel(self, title):
        panel_frame = QFrame(objectName="panel_frame")
        panel_layout = QVBoxLayout(panel_frame)
        panel_layout.addWidget(QLabel(title, objectName="panel_title"))
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container_widget = QWidget()
        self.container_layout = QVBoxLayout(container_widget)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()
        
        scroll_area.setWidget(container_widget)
        panel_layout.addWidget(scroll_area)
        
        return panel_frame

    def load_data(self, layouts_data, pages_data):
        self._layouts_data = layouts_data
        self._pages_data = pages_data
        self._populate_layouts()
        self._populate_pages()
        if layouts_data:
            first_layout_name = list(layouts_data.keys())[0]
            self.on_layout_selected(first_layout_name)

    def _clear_layout_container(self, panel):
        scroll_area = panel.findChild(QScrollArea)
        container_widget = scroll_area.widget()
        layout = container_widget.layout()
        while layout.count() > 1:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _populate_layouts(self):
        self._clear_layout_container(self.layouts_container)
        self._layout_widgets = {}
        layout = self.layouts_container.findChild(QScrollArea).widget().layout()
        for name, data in self._layouts_data.items():
            preview = LayoutPreviewWidget(name, data.get("slots", []))
            preview.selected.connect(self.on_layout_selected)
            layout.insertWidget(layout.count() - 1, preview)
            self._layout_widgets[name] = preview
            
    def _populate_pages(self):
        self._clear_layout_container(self.pages_container)
        layout = self.pages_container.findChild(QScrollArea).widget().layout()
        for page in self._pages_data:
            page_label = DraggablePageLabel(page["id"])
            layout.insertWidget(layout.count() - 1, page_label)

    def on_layout_selected(self, layout_name):
        self._selected_layout_name = layout_name
        self._current_assignments = {}
        self._clear_layout_container(self.slots_container)

        for name, widget in self._layout_widgets.items():
            widget.set_selected(name == layout_name)
        
        layout = self.slots_container.findChild(QScrollArea).widget().layout()
        layout_data = self._layouts_data.get(layout_name, {})
        for slot in layout_data.get("slots", []):
            slot_id = slot["id"]
            drop_zone = DropZoneWidget(slot_id)
            drop_zone.pageDropped.connect(self.on_page_assigned)
            layout.insertWidget(layout.count() - 1, drop_zone)

    def on_page_assigned(self, slot_id, page_id):
        self._current_assignments[slot_id] = page_id
        
    def on_accept(self):
        if self._selected_layout_name:
            self.layoutApplied.emit(self._selected_layout_name, self._current_assignments)
        self.accept()