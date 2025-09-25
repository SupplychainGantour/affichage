"""
ViewManager - Manages predefined views that combine layouts and window configurations.

A view is a combination of:
- Layout: Window positions and sizes
- Windows: Which URLs to display in each window
- Metadata: View name, description, etc.
"""

import json
import os
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class ViewManager(QObject):
    """Manages predefined views combining layouts and window configurations."""
    
    # Signals for view changes
    view_changed = pyqtSignal(str)  # Emitted when view is switched
    view_loaded = pyqtSignal(dict)  # Emitted when view is loaded
    
    def __init__(self, config_dir: str = "config"):
        super().__init__()
        self.config_dir = config_dir
        self.views_config_path = os.path.join(config_dir, "views.json")
        self.windows_config_path = os.path.join(config_dir, "windows.json")
        self.layouts_config_path = os.path.join(config_dir, "layouts.json")
        
        self.current_view = None
        self.views = {}
        
        self._load_views()
    
    def _load_views(self):
        """Load view definitions from config file."""
        try:
            if os.path.exists(self.views_config_path):
                with open(self.views_config_path, 'r', encoding='utf-8') as f:
                    self.views = json.load(f)
                print(f"[ViewManager] Loaded {len(self.views)} views from {self.views_config_path}")
            else:
                # Create default views if config doesn't exist
                self._create_default_views()
        except Exception as e:
            print(f"[ViewManager] Error loading views: {e}")
            self._create_default_views()
    
    def _create_default_views(self):
        """Create default view configurations."""
        self.views = {
            "dashboard": {
                "name": "Dashboard View",
                "description": "Main dashboard with Power BI and SharePoint",
                "layout": "default",
                "windows": [
                    {"id": "powerbi_report", "position": {"x": 0.0, "y": 0.0, "width": 0.6, "height": 0.7}},
                    {"id": "sharepoint_document", "position": {"x": 0.0, "y": 0.7, "width": 1.0, "height": 0.3}}
                ]
            },
            "monitoring": {
                "name": "Process Monitoring", 
                "description": "PI Vision process monitoring view",
                "layout": "monitoring",
                "windows": [
                    {"id": "google_search", "position": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}}
                ]
            },
            "overview": {
                "name": "Complete Overview",
                "description": "All windows visible for comprehensive monitoring",
                "layout": "overview", 
                "windows": [
                    {"id": "powerbi_report", "position": {"x": 0.5, "y": 0.0, "width": 0.5, "height": 0.6}},
                    {"id": "google_search", "position": {"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.6}},
                    {"id": "sharepoint_document", "position": {"x": 0.0, "y": 0.6, "width": 1.0, "height": 0.4}}
                ]
            }
        }
        self._save_views()
    
    def _save_views(self):
        """Save current views to config file."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.views_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.views, f, indent=2, ensure_ascii=False)
            print(f"[ViewManager] Saved views to {self.views_config_path}")
        except Exception as e:
            print(f"[ViewManager] Error saving views: {e}")
    
    def get_views(self) -> Dict[str, Dict[str, Any]]:
        """Get all available views."""
        return self.views.copy()
    
    def get_view(self, view_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific view by ID."""
        return self.views.get(view_id)
    
    def get_view_names(self) -> List[str]:
        """Get list of view names for UI display."""
        return [view["name"] for view in self.views.values()]
    
    def get_view_ids(self) -> List[str]:
        """Get list of view IDs."""
        return list(self.views.keys())
    
    def switch_view(self, view_id: str) -> bool:
        """Switch to a specific view."""
        if view_id not in self.views:
            print(f"[ViewManager] View '{view_id}' not found")
            return False
        
        view = self.views[view_id]
        print(f"[ViewManager] Switching to view: {view['name']}")
        
        self.current_view = view_id
        self.view_changed.emit(view_id)
        self.view_loaded.emit(view)
        
        return True
    
    def get_current_view_id(self) -> Optional[str]:
        """Get the current view ID."""
        return self.current_view
    
    def get_current_view(self) -> Optional[Dict[str, Any]]:
        """Get the current view configuration."""
        if self.current_view:
            return self.views.get(self.current_view)
        return None
    
    def create_view(self, view_id: str, name: str, description: str, layout: str, windows: List[Dict]) -> bool:
        """Create a new view."""
        if view_id in self.views:
            print(f"[ViewManager] View '{view_id}' already exists")
            return False
        
        self.views[view_id] = {
            "name": name,
            "description": description,
            "layout": layout,
            "windows": windows
        }
        
        self._save_views()
        print(f"[ViewManager] Created new view: {name}")
        return True
    
    def delete_view(self, view_id: str) -> bool:
        """Delete a view."""
        if view_id not in self.views:
            print(f"[ViewManager] View '{view_id}' not found")
            return False
        
        if self.current_view == view_id:
            self.current_view = None
        
        del self.views[view_id]
        self._save_views()
        print(f"[ViewManager] Deleted view: {view_id}")
        return True
    
    def update_view(self, view_id: str, **kwargs) -> bool:
        """Update an existing view."""
        if view_id not in self.views:
            print(f"[ViewManager] View '{view_id}' not found")
            return False
        
        for key, value in kwargs.items():
            if key in ["name", "description", "layout", "windows"]:
                self.views[view_id][key] = value
        
        self._save_views()
        print(f"[ViewManager] Updated view: {view_id}")
        return True
    
    def get_window_configs(self) -> List[Dict]:
        """Load window configurations from windows.json."""
        try:
            with open(self.windows_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ViewManager] Error loading windows config: {e}")
            return []
    
    def apply_view_to_controller(self, controller) -> bool:
        """Apply current view to the application controller."""
        if not self.current_view:
            print("[ViewManager] No current view to apply")
            return False
        
        view = self.views[self.current_view]
        window_configs = self.get_window_configs()
        
        # Create a mapping of window ID to config
        window_map = {w['id']: w for w in window_configs}
        
        # Close existing windows first
        if hasattr(controller, 'close_all_windows'):
            controller.close_all_windows()
        
        # Create windows according to view
        for window_def in view['windows']:
            window_id = window_def['id']
            position = window_def['position']
            
            if window_id in window_map:
                window_config = window_map[window_id].copy()
                
                # Convert normalized positions to pixel coordinates
                if hasattr(controller, 'get_screen_size'):
                    screen_width, screen_height = controller.get_screen_size()
                    
                    window_config['geometry'] = {
                        'x': int(position['x'] * screen_width),
                        'y': int(position['y'] * screen_height),
                        'width': int(position['width'] * screen_width),
                        'height': int(position['height'] * screen_height)
                    }
                
                # Create the window
                if hasattr(controller, 'create_window_from_config'):
                    controller.create_window_from_config(window_config)
                    
                    # Apply zoom level if saved and window was created
                    if 'zoom' in window_def and hasattr(controller, '_windows') and window_id in controller._windows:
                        window = controller._windows[window_id]
                        if hasattr(window, 'set_zoom_level'):
                            window.set_zoom_level(window_def['zoom'])
                            print(f"[ViewManager] Applied zoom level {window_def['zoom']}% to window {window_id}")
        
        print(f"[ViewManager] Applied view '{view['name']}'")
        return True