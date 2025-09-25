import json
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from app.core.profile_manager import WebProfileManager
from app.core.view_manager import ViewManager
from app.views.browser_window import BrowserWindow
from app.views.floating_button import FloatingActionMenu
from app.views.screen_manager_dialog import ScreenManagerDialog
from app.views.save_layout_dialog import SaveLayoutDialog
from app.views.save_view_dialog import SaveViewDialog
from app.views.view_selector_bar import ViewSelectorBar

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
        
        # Initialize view manager
        self._view_manager = ViewManager()
        
        # Initialize view selector bar
        self._view_selector = ViewSelectorBar(self._view_manager)
        self._view_selector.view_selected.connect(self._on_view_selected)
        
        self._floating_menu = FloatingActionMenu()
        self._floating_menu.set_view_manager(self._view_manager)
        self._floating_menu.view_switch_requested.connect(self.switch_view)
        
        self._screen_manager = ScreenManagerDialog()
        self._save_layout_dialog = SaveLayoutDialog()
        self._save_view_dialog = SaveViewDialog()
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
                ("\u2713", self.save_current_view),      # Save icon (checkmark) - now saves view
                ("\u270E", self.toggle_edit_mode),       # Edit icon (toggle back to normal)
                ("Q", self.quit_application)             # Quit
            ]
        else:
            # Normal mode actions
            actions = [
                ("\ud83d\udcca", self._floating_menu.show_view_menu),  # View selector (chart icon)
                ("\u2630", self.open_screen_manager),    # Menu icon
                ("\u21BB", self.reload_all_pages),       # Reload icon
                ("\u270E", self.toggle_edit_mode),       # Edit icon
                ("Q", self.quit_application)             # Quit
            ]
        
        self._floating_menu.update_actions(actions)
        

    def run(self):
        """Shows the view selector bar instead of loading windows immediately."""
        # Load configs for later use
        self._load_configs()
        
        # Show only the view selector bar on startup
        self._view_selector.show_centered()
        print("View selector shown - waiting for user selection...")

    def _on_view_selected(self, view_id):
        """Handle view selection from the view selector bar."""
        print(f"User selected view: {view_id}")
        
        # Switch to the selected view
        self.switch_view(view_id)
        
        # Show the floating menu after view is loaded
        self._floating_menu.show()
        self._floating_menu.move(10, 10)
        
        # Update menu actions
        self._update_menu_actions()

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
    
    def switch_view(self, view_id):
        """Switch to a specific view."""
        print(f"[Controller] Switching to view: {view_id}")
        
        if self._view_manager.switch_view(view_id):
            # Apply the view to the current controller
            self._view_manager.apply_view_to_controller(self)
            print(f"[Controller] Successfully switched to view: {view_id}")
        else:
            print(f"[Controller] Failed to switch to view: {view_id}")
    
    def close_all_windows(self):
        """Close all browser windows."""
        for window in self._windows.values():
            window.close()
        self._windows.clear()
    
    def get_screen_size(self):
        """Get screen dimensions for view calculations."""
        return self.screen_geometry.width(), self.screen_geometry.height()

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
                
                # Create slot data - allow off-screen positioning
                slot_data = {
                    "id": f"Slot for {window_id}",
                    "geometry": {
                        "x": normalized_x,  # No clamping - preserve off-screen positions
                        "y": normalized_y,  # No clamping - preserve off-screen positions
                        "width": max(0.05, min(2.0, normalized_width)),   # Allow up to 2x screen width
                        "height": max(0.05, min(2.0, normalized_height))  # Allow up to 2x screen height
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
    
    def save_current_view(self):
        """Saves the current window arrangement as either a view or layout."""
        self._floating_menu.toggle_menu()
        
        # Check if there are any visible windows to save
        visible_windows = {window_id: window for window_id, window in self._windows.items() if window.isVisible()}
        if not visible_windows:
            QMessageBox.warning(None, "No Windows", "There are no visible windows to save.")
            return
            
        # Show the save view dialog
        if self._save_view_dialog.exec() == QDialog.DialogCode.Accepted:
            save_data = self._save_view_dialog.get_save_data()
            
            if save_data["type"] == "view":
                self._save_as_view(save_data, visible_windows)
            else:
                self._save_as_layout_from_view_dialog(save_data, visible_windows)
    
    def _save_as_view(self, save_data, visible_windows):
        """Save current arrangement as a view."""
        view_id = save_data["name"].lower().replace(" ", "_")
        
        # Check if view already exists
        if self._view_manager.get_view(view_id):
            reply = QMessageBox.question(
                None,
                "View Exists",
                f"A view named '{save_data['name']}' already exists. Do you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Get screen dimensions for normalization
        screen_w = self.screen_geometry.width()
        screen_h = self.screen_geometry.height()
        
        # Create window definitions with positions and IDs
        windows = []
        for window_id, window in visible_windows.items():
            geometry = window.geometry()
            
            # Normalize coordinates to 0.0-1.0 range
            normalized_x = geometry.x() / screen_w
            normalized_y = geometry.y() / screen_h
            normalized_width = geometry.width() / screen_w
            normalized_height = geometry.height() / screen_h
            
            window_def = {
                "id": window_id,
                "position": {
                    "x": normalized_x,  # No clamping - preserve off-screen positions
                    "y": normalized_y,  # No clamping - preserve off-screen positions
                    "width": max(0.05, min(2.0, normalized_width)),   # Allow up to 2x screen width
                    "height": max(0.05, min(2.0, normalized_height))  # Allow up to 2x screen height
                }
            }
            windows.append(window_def)
        
        # Create or update the view
        success = self._view_manager.create_view(
            view_id=view_id,
            name=save_data["name"],
            description=save_data["description"] or f"Custom view: {save_data['name']}",
            layout=view_id,  # Use view_id as layout name
            windows=windows
        ) or self._view_manager.update_view(
            view_id=view_id,
            name=save_data["name"],
            description=save_data["description"] or f"Custom view: {save_data['name']}",
            layout=view_id,
            windows=windows
        )
        
        if success:
            QMessageBox.information(None, "View Saved", f"View '{save_data['name']}' has been saved successfully!")
            print(f"Saved view '{save_data['name']}' with {len(windows)} windows")
        else:
            QMessageBox.critical(None, "Save Error", "Failed to save view.")
    
    def _save_as_layout_from_view_dialog(self, save_data, visible_windows):
        """Save current arrangement as a layout (from view dialog)."""
        layout_name = save_data["name"]
        
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
            "description": save_data["description"] or f"Custom layout: {layout_name}",
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
            
            # Create slot data - allow off-screen positioning
            slot_data = {
                "id": f"Slot for {window_id}",
                "geometry": {
                    "x": normalized_x,  # No clamping - preserve off-screen positions
                    "y": normalized_y,  # No clamping - preserve off-screen positions
                    "width": max(0.05, min(2.0, normalized_width)),   # Allow up to 2x screen width
                    "height": max(0.05, min(2.0, normalized_height))  # Allow up to 2x screen height
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