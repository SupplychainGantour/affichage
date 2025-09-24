import sys
import os # Ajout pour la gestion des chemins
from PyQt5.QtCore import Qt, QRect, QUrl, QStandardPaths
from PyQt5.QtWidgets import QApplication, QMainWindow
# QWebEnginePage et QWebEngineProfile sont nécessaires
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

class Browser(QMainWindow):
    # On modifie le constructeur pour accepter un profil
    def __init__(self, url, profile, x=100, y=100, width=800, height=600):
        super().__init__()

        # Créer une page web en utilisant le profil partagé
        # C'est cette étape qui lie la vue au profil persistant
        self.page = QWebEnginePage(profile, self)

        # Créer un moteur de rendu web (Chromium)
        self.browser = QWebEngineView()
        self.browser.setPage(self.page) # Assigner la page à la vue
        self.browser.setUrl(QUrl(url))
        self.setCentralWidget(self.browser)

        # Enlever les bordures Windows
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Définir la position et taille
        self.setGeometry(QRect(x, y, width, height))

        # Optionnel : rendre redimensionnable avec la souris
        self.setAttribute(Qt.WA_TranslucentBackground, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- CONFIGURATION DU PROFIL PERSISTANT ---
    # 1. Définir un chemin pour sauvegarder les données
    # Utiliser QStandardPaths est la meilleure pratique pour la compatibilité (Windows, macOS, Linux)
    data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    profile_path = os.path.join(data_path, "web_profile") # Crée un sous-dossier "web_profile"

    # S'assurer que le dossier existe
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    # 2. Obtenir le profil par défaut et lui donner le chemin de sauvegarde
    default_profile = QWebEngineProfile.defaultProfile()
    default_profile.setPersistentStoragePath(profile_path)
    default_profile.setCachePath(profile_path) # Important de définir aussi le cache
    default_profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)

    print(f"Les données du profil seront sauvegardées dans : {profile_path}")
    # -------------------------------------------

    # Exemple : ouvrir deux fenêtres qui PARTAGENT la même session
    # Si vous vous connectez à Google dans l'une, vous serez connecté dans l'autre.
    # Et la connexion sera conservée au prochain lancement.

    window1 = Browser("https://accounts.google.com", default_profile, 100, 100, 800, 600)
    window1.show()

    window2 = Browser("https://www.youtube.com", default_profile, 900, 100, 800, 600)
    window2.show()


    sys.exit(app.exec_())