import sys
import os # <-- IMPORT THE 'os' MODULE
import json

from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QNetworkProxyFactory
from PyQt6.QtCore import Qt
from app.controllers.application_controller import ApplicationController

if __name__ == "__main__":
    # --- DISABLE HiDPI SCALING TO PREVENT ZOOM ISSUES ---
    # Comment out high DPI scaling to fix zoom issues
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # --- ADDITIONAL WEBENGINE ZOOM FIXES ---
    # Disable WebEngine's device scale factor
    os.environ["QT_WEBENGINE_DISABLE_DEVICE_SCALE_FACTOR"] = "1"
    # Force WebEngine to use 100% zoom
    os.environ["QT_SCALE_FACTOR"] = "1"

    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

    # Allow Windows Integrated Authentication (NTLM/Negotiate) for corporate domains
    chrome_flags = [
        "--auth-server-allowlist=*.ocpgroup.ma",
        "--auth-negotiate-delegate-whitelist=*.ocpgroup.ma",
        "--auth-schemes=basic,digest,ntlm,negotiate",
        # Performance flags for heavy dashboards
        "--ignore-gpu-blocklist",
        "--enable-gpu-rasterization",
        "--enable-zero-copy",
        "--enable-accelerated-2d-canvas",
        "--js-flags=--max-old-space-size=4096",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
    ]
    # If an explicit proxy server is defined, prefer it
    
    existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    combo = (existing + " " + " ".join(chrome_flags)).strip()
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = combo

    app = QApplication(sys.argv)
    # Ensure Qt uses system proxy settings as a baseline
    try:
        QNetworkProxyFactory.setUseSystemConfiguration(True)
    except Exception:
        pass

    # The controller takes care of everything
    controller = ApplicationController(
        config_path="config/windows.json",
        layouts_path="config/layouts.json"
    )
    controller.run()

    sys.exit(app.exec())