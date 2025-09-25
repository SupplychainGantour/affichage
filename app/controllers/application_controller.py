import json
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from app.core.profile_manager import WebProfileManager
from app.views.browser_window import BrowserWindow
from app.views.floating_button import FloatingActionMenu
from app.views.screen_manager_dialog import ScreenManagerDialog
from app.views.save_layout_dialog import SaveLayoutDialog

class ApplicationController:
    """
    The main controller of the application.
    """
    def __init__(self, config_path, layouts_path):
        self._windows = {}
        self._window_configs = []
        self._layouts_data = {}

        self.screen_geometry = QApplication.primaryScreen().geometry()
        print(f"Detected screen resolution: {self.screen_geometry.width()}x{self.screen_geometry.height()}")

        self._config_path = config_path
        self._layouts_path = layouts_path
        
        self._profile_manager = WebProfileManager()
        self._shared_profile = self._profile_manager.get_profile()
        
        self._floating_menu = FloatingActionMenu()
        self._screen_manager = ScreenManagerDialog()
        self._save_layout_dialog = SaveLayoutDialog()
        self._is_edit_mode = False

        self._setup_menu_actions()

        self._screen_manager.layoutApplied.connect(self.apply_layout)

    def _setup_menu_actions(self):
        """Creates and connects all actions for the floating menu."""
        self._update_menu_actions()

    def _update_menu_actions(self):
        """Updates menu actions based on current mode."""
        if self._is_edit_mode:
            # Edit mode actions
            actions = [
                ("\u2630", self.open_screen_manager),    # Menu icon
                ("\u21BB", self.reload_all_pages),       # Reload icon
                ("\u2713", self.save_current_layout),    # Save icon (checkmark)
                ("\u270E", self.toggle_edit_mode),       # Edit icon (toggle back to normal)
                ("Q", self.quit_application)             # Quit
            ]
        else:
            # Normal mode actions
            actions = [
                ("\u2630", self.open_screen_manager),    # Menu icon
                ("\u21BB", self.reload_all_pages),       # Reload icon
                ("\u270E", self.toggle_edit_mode),       # Edit icon
                ("Q", self.quit_application)             # Quit
            ]
        
        self._floating_menu.update_actions(actions)
        

    def run(self):
        """Loads configs and shows all initial windows and the menu."""
        # This call will now work because the method is present
        self._load_configs()

        for config in self._window_configs:
            self.create_window_from_config(config)
        
        self._floating_menu.show()
        self._floating_menu.move(10, 10)

    # --- THIS METHOD WAS MISSING ---
    def _load_configs(self):
        """Loads window and layout configurations from JSON files."""
        try:
            with open(self._config_path, 'r') as f:
                self._window_configs = json.load(f)
            with open(self._layouts_path, 'r') as f:
                self._layouts_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading configuration: {e}")
            self._window_configs = []
            self._layouts_data = {}

    def toggle_edit_mode(self):
        """Toggles drag-and-resize mode for all windows."""
        self._is_edit_mode = not self._is_edit_mode
        print(f"Toggling Edit Mode to: {self._is_edit_mode}")
        
        # Update menu actions based on new mode
        self._update_menu_actions()
        
        # Broadcast the new state to all browser windows
        for window in self._windows.values():
            window.set_edit_mode(self._is_edit_mode)
            
        self._floating_menu.toggle_menu() # Auto-close menu

    # --- THIS METHOD WAS ALSO MISSING ---
    def create_window_from_config(self, config):
        """Creates and shows a single browser window."""
        window_id = config.get("id")
        if not window_id:
            return

        geo = config.get("geometry", {})
        window = BrowserWindow(profile=self._shared_profile)
        window.load_url(config.get("url", "about:blank"), window_id=window_id)
        window.set_geometry(
            geo.get("x", 100), geo.get("y", 100),
            geo.get("width", 800), geo.get("height", 600)
        )
        window.show()
        self._windows[window_id] = window

    # --- SLOTS for menu actions ---
    
    def open_screen_manager(self):
        """Opens the screen manager dialog."""
        print("Opening Screen Manager...")
        self._floating_menu.toggle_menu()
        self._screen_manager.load_data(self._layouts_data, self._window_configs)
        self._screen_manager.exec()

    def reload_all_pages(self):
        """Reloads the web content of every open browser window."""
        print("Reloading all pages...")
        for window in self._windows.values():
            window.browser.reload()
        self._floating_menu.toggle_menu()

    def quit_application(self):
        """Closes the entire application."""
        print("Quitting application...")
        QApplication.instance().quit()

    def save_current_layout(self):
        """Saves the current window positions as a new layout."""
        self._floating_menu.toggle_menu()
        
        # Check if there are any visible windows to save
        visible_windows = {window_id: window for window_id, window in self._windows.items() if window.isVisible()}
        if not visible_windows:
            QMessageBox.warning(None, "No Windows", "There are no visible windows to save as a layout.")
            return
            
        # Show the save dialog
        if self._save_layout_dialog.exec() == QDialog.DialogCode.Accepted:
            layout_name, layout_description = self._save_layout_dialog.get_layout_info()
            
            # Check if layout name already exists
            if layout_name in self._layouts_data:
                reply = QMessageBox.question(
                    None,
                    "Layout Exists",
                    f"A layout named '{layout_name}' already exists. Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Create the new layout data
            new_layout = {
                "description": layout_description or f"Custom layout: {layout_name}",
                "slots": []
            }
            
            # Get screen dimensions for normalization
            screen_w = self.screen_geometry.width()
            screen_h = self.screen_geometry.height()
            
            # Capture current window positions
            for window_id, window in visible_windows.items():
                geometry = window.geometry()
                
                # Normalize coordinates to 0.0-1.0 range
                normalized_x = geometry.x() / screen_w
                normalized_y = geometry.y() / screen_h
                normalized_width = geometry.width() / screen_w
                normalized_height = geometry.height() / screen_h
                
                # Create slot data
                slot_data = {
                    "id": f"Slot for {window_id}",
                    "geometry": {
                        "x": max(0.0, min(1.0, normalized_x)),
                        "y": max(0.0, min(1.0, normalized_y)),
                        "width": max(0.05, min(1.0, normalized_width)),
                        "height": max(0.05, min(1.0, normalized_height))
                    }
                }
                new_layout["slots"].append(slot_data)
            
            # Add the new layout to our data
            self._layouts_data[layout_name] = new_layout
            
            # Save to file
            try:
                with open(self._layouts_path, 'w') as f:
                    json.dump(self._layouts_data, f, indent=2)
                QMessageBox.information(None, "Layout Saved", f"Layout '{layout_name}' has been saved successfully!")
                print(f"Saved layout '{layout_name}' with {len(new_layout['slots'])} slots")
            except Exception as e:
                QMessageBox.critical(None, "Save Error", f"Failed to save layout: {str(e)}")
                print(f"Error saving layout: {e}")

    def apply_layout(self, layout_name, assignments):
        """
        Receives the signal from the dialog and reconfigures the browser windows
        using relative geometry.
        """
        if self._is_edit_mode:
            self.toggle_edit_mode()

        print(f"Applying layout '{layout_name}' with assignments: {assignments}")
        layout_info = self._layouts_data.get(layout_name)
        if not layout_info:
            return

        for window in self._windows.values():
            window.hide()

        assigned_pages = set(assignments.values())
        
        # Get screen dimensions
        screen_w = self.screen_geometry.width()
        screen_h = self.screen_geometry.height()

        for slot in layout_info.get("slots", []):
            slot_id = slot["id"]
            page_id = assignments.get(slot_id)
            
            if page_id and page_id in self._windows:
                window_to_configure = self._windows[page_id]
                
                # --- Calculate geometry from percentages ---
                geo = slot["geometry"]
                pixel_x = int(geo["x"] * screen_w)
                pixel_y = int(geo["y"] * screen_h)
                pixel_w = int(geo["width"] * screen_w)
                pixel_h = int(geo["height"] * screen_h)
                
                window_to_configure.set_geometry(
                    pixel_x, pixel_y, pixel_w, pixel_h
                )
                window_to_configure.show()
        
        for page_id, window in self._windows.items():
            if page_id not in assigned_pages:
                window.hide()