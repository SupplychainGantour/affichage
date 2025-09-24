import os
import sys
import time
import json
from urllib.parse import urlparse

import requests
from requests_ntlm import HttpNtlmAuth

from PyQt6.QtCore import QStandardPaths, QUrl, QTimer, Qt, QRect, QPoint
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtNetwork import QNetworkCookie

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings


class WebProfileManager:
    """Singleton manager for a persistent QWebEngineProfile with auth support (callback or cookie fallback)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Creating the single WebProfileManager instance.")
            cls._instance = super(WebProfileManager, cls).__new__(cls)
            cls._instance._initialize_profile()
        return cls._instance

    def _initialize_profile(self):
        # PyQt6: use StandardLocation enum for writableLocation
        data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        profile_path = os.path.join(data_path, "DigitalDisplayApp_Profile")
        if not os.path.exists(profile_path):
            os.makedirs(profile_path, exist_ok=True)

        # Use a dedicated profile
        self.profile = QWebEngineProfile("DigitalDisplayProfile", None)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(profile_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

        # Credentials: prefer config/auth.json, fallback to env vars; else rely on Windows SSO.
        self._username, self._password = self._load_credentials()
        self._has_creds = bool(self._username and self._password)

        # Use a Chrome-like user agent to avoid enterprise proxy filtering on unknown UAs
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
        self.profile.setHttpUserAgent(ua)

        # Enable performance-related settings
        try:
            settings = self.profile.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        except Exception:
            pass

        # Increase cache size for heavy PI Vision assets
        try:
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            self.profile.setHttpCacheMaximumSize(512 * 1024 * 1024)  # 512MB
        except Exception:
            pass

        # First try: setHttpAuthRequestedCallback (Qt >= 5.12 / PyQt versions)
        if hasattr(self.profile, "setHttpAuthRequestedCallback") and self._has_creds:
            try:
                print("Registering HTTP auth callback using setHttpAuthRequestedCallback(...)")
                # The callback signature differs by bindings; accept variable args and try to set credentials.
                def _http_auth_callback(*args):
                    # args might be (request_url, auth) or (request_url, auth, authenticator) depending on Qt/PyQt
                    try:
                        # Try common Qt style: authenticator object with setUser/setPassword
                        # If 'auth' object is provided directly, it may have setUser/setPassword
                        # We'll inspect args to find an object with setUser
                        for a in args:
                            if hasattr(a, "setUser") and hasattr(a, "setPassword"):
                                a.setUser(self._username)
                                a.setPassword(self._password)
                                print("HTTP auth callback: provided credentials via authenticator object.")
                                return
                        # Sometimes a tuple (host, realm, auth) etc - fallback to printing
                        print("HTTP auth callback invoked but no authenticator object found in args:", args)
                    except Exception as e:
                        print("Error in http auth callback:", e)

                self.profile.setHttpAuthRequestedCallback(_http_auth_callback)
                self._using_http_callback = True
            except Exception as e:
                print("Failed to register setHttpAuthRequestedCallback:", e)
                self._using_http_callback = False
        else:
            if not hasattr(self.profile, "setHttpAuthRequestedCallback"):
                print("Profile has no setHttpAuthRequestedCallback API.")
            else:
                print("No explicit credentials provided; relying on Windows SSO (Chromium allowlist).")
            self._using_http_callback = False

        print(f"Web profile storage location: {profile_path}")
        
        # Proxy auth handling (some enterprises require NTLM/Kerberos on the proxy)
        try:
            if hasattr(self.profile, "proxyAuthenticationRequired"):
                self._proxy_user, self._proxy_pwd = self._load_proxy_credentials()
                def _on_proxy_auth(request_url, authenticator, proxy_host):
                    try:
                        user = self._proxy_user or self._username
                        pwd = self._proxy_pwd or self._password
                        if user and pwd and hasattr(authenticator, "setUser"):
                            authenticator.setUser(user)
                            authenticator.setPassword(pwd)
                            print(f"[proxy] Provided credentials for proxy {proxy_host}")
                    except Exception as e:
                        print("[proxy] Error supplying proxy credentials:", e)
                self.profile.proxyAuthenticationRequired.connect(_on_proxy_auth)
        except Exception as e:
            print("[proxy] Failed to attach proxy auth handler:", e)

    def get_profile(self):
        return self.profile

    def _load_credentials(self):
        """Load credentials from config/auth.json (preferred), then env vars.
        Returns a tuple (username, password) or (None, None) if not available.
        """
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            auth_path = os.path.join(base_dir, "config", "auth.json")
            if os.path.exists(auth_path):
                with open(auth_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                user = data.get("username") or data.get("user")
                pwd = data.get("password") or data.get("pass") or data.get("pwd")
                if user and pwd:
                    print("Loaded credentials from config/auth.json")
                    return user, pwd
        except Exception as e:
            print("Error reading config/auth.json:", e)

        # Fallback to environment variables
        user = os.environ.get("IWA_USERNAME") or os.environ.get("NTLM_USERNAME")
        pwd = os.environ.get("IWA_PASSWORD") or os.environ.get("NTLM_PASSWORD")
        if user and pwd:
            print("Loaded credentials from environment variables")
            return user, pwd
        
        print("No explicit credentials found; relying on Windows SSO if available.")
        return None, None

    def _load_proxy_credentials(self):
        """Load proxy credentials from config/proxy.json or env vars.
        Returns (username, password) or (None, None).
        """
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            proxy_path = os.path.join(base_dir, "config", "proxy.json")
            if os.path.exists(proxy_path):
                with open(proxy_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                user = data.get("username") or data.get("user")
                pwd = data.get("password") or data.get("pass") or data.get("pwd")
                if user and pwd:
                    print("Loaded proxy credentials from config/proxy.json")
                    return user, pwd
        except Exception as e:
            print("Error reading config/proxy.json:", e)
        
        user = os.environ.get("PROXY_USERNAME")
        pwd = os.environ.get("PROXY_PASSWORD")
        if user and pwd:
            print("Loaded proxy credentials from environment variables")
            return user, pwd
        return None, None

    def get_auth_credentials(self):
        """Return (username, password) for NTLM/Kerberos challenges.
        Username should include domain as DOMAIN\\user if required by the server.
        """
        return self._username, self._password

    def has_credentials(self) -> bool:
        return self._has_creds

    # Fallback: NTLM via requests + cookie injection
    def ntlm_session_and_inject(self, target_url: str):
        """
        If HTTP callback isn't available or doesn't work, call this to perform NTLM auth with requests
        and inject cookies into the profile's cookie store.
        """
        if getattr(self, "_using_http_callback", False):
            print("Note: HTTP callback is enabled; cookie-injection fallback not required.")
            return True
        if not self._has_creds:
            print("No explicit credentials available; skip NTLM cookie injection.")
            return False

        # 1) authenticate with requests + requests-ntlm
        session = requests.Session()
        user, pwd = self.get_auth_credentials()
        session.auth = HttpNtlmAuth(user, pwd)

        # Helpful headers to resemble a browser
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PyQtWebEngine/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        print("[ntlm] Attempting NTLM-authenticated GET to:", target_url)
        try:
            resp = session.get(target_url, timeout=30, verify=True)
            resp.raise_for_status()
            print("[ntlm] Authenticated OK. Status:", resp.status_code)
        except Exception as e:
            print("[ntlm] NTLM authentication GET failed:", e)
            return False

        # 2) inject cookies into QWebEngineProfile cookie store
        cookie_store = self.profile.cookieStore()
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.hostname}"

        injected = 0
        for c in session.cookies:
            # Build a QNetworkCookie
            qcookie = QNetworkCookie()
            qcookie.setName(c.name.encode("utf-8"))
            qcookie.setValue(c.value.encode("utf-8"))
            if c.domain:
                try:
                    qcookie.setDomain(c.domain)
                except Exception:
                    pass
            if c.path:
                try:
                    qcookie.setPath(c.path)
                except Exception:
                    pass
            try:
                qcookie.setSecure(bool(c.secure))
            except Exception:
                pass

            if c.expires and c.expires < time.time():
                continue

            cookie_store.setCookie(qcookie, QUrl(base_url))
            injected += 1
            print(f"[cookie] Injected: {c.name}; domain={c.domain} path={c.path} secure={c.secure}")

        print(f"[cookie] Total injected cookies: {injected}")
        return True

