"""Icon loading and management for VisioDoc3 application."""
# Chargement et gestion des icônes pour l'application VisioDoc3

import os
import sys
from PIL import Image, ImageTk, ImageDraw
from typing import Dict, Optional


# Manages loading and caching of application icons
# Gère le chargement et la mise en cache des icônes de l'application
class IconLoader:
    # Initializes the icon loader with the icon directory path
    # Initialise le chargeur d'icônes avec le chemin du répertoire d'icônes
    def __init__(self, icon_dir: Optional[str] = None):
        if icon_dir is None:
            # Check if running in frozen (PyInstaller) mode
            # Vérifie si l'exécution est en mode gelé (PyInstaller)
            if getattr(sys, "frozen", False):
                icon_dir = os.path.join(sys._MEIPASS, "icons")
            else:
                icon_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "..", "icons"
                )

        self.icon_dir = (
            icon_dir  # Path to icon directory / Chemin du répertoire d'icônes
        )
        self._cache: Dict[
            str, ImageTk.PhotoImage
        ] = {}  # Icon cache dictionary / Dictionnaire de cache d'icônes
        self._default_size = (
            24,
            24,
        )  # Default icon size in pixels / Taille d'icône par défaut en pixels

    # Get the file path for an icon by name
    # Obtient le chemin du fichier pour une icône par nom
    def get_icon_path(self, name: str) -> str:
        return os.path.join(self.icon_dir, f"{name}.png")

    # Load an icon by name with optional resizing, using cache
    # Charge une icône par nom avec redimensionnement optionnel, utilisant le cache
    def load_icon(self, name: str, size: tuple = None) -> Optional[ImageTk.PhotoImage]:
        if size is None:
            size = self._default_size

        # Check cache first to avoid reloading
        # Vérifie le cache d'abord pour éviter de recharger
        cache_key = f"{name}_{size[0]}x{size[1]}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            path = self.get_icon_path(name)
            img = Image.open(path)
            img = img.resize(
                size, Image.LANCZOS
            )  # High-quality resize / Redimensionnement de haute qualité
            photo = ImageTk.PhotoImage(img)
            self._cache[cache_key] = photo
            return photo
        except FileNotFoundError:
            return self._create_placeholder(name, size)
        except Exception:
            return self._create_placeholder(name, size)

    # Create a placeholder icon when the file is not found
    # Crée une icône de remplacement lorsque le fichier n'est pas trouvé
    def _create_placeholder(
        self, name: str, size: tuple
    ) -> Optional[ImageTk.PhotoImage]:
        try:
            placeholder = Image.new(
                "RGBA", size, (0, 0, 0, 0)
            )  # Transparent background / Arrière-plan transparent
            draw = ImageDraw.Draw(placeholder)
            text = (
                name[0].upper() if name else "?"
            )  # First letter or question mark / Première lettre ou point d'interrogation
            draw.text(
                (size[0] // 3, 0), text, fill=(128, 128, 128, 255)
            )  # Gray text / Texte gris
            photo = ImageTk.PhotoImage(placeholder)
            self._cache[f"{name}_{size[0]}x{size[1]}"] = photo
            return photo
        except Exception:
            return None

    # Load the logo with appropriate sizing
    # Charge le logo avec une taille appropriée
    def load_logo(self, max_width: int = 140) -> Optional[ImageTk.PhotoImage]:
        cache_key = f"logo_{max_width}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            path = self.get_icon_path("logoVisioDoc3")
            img = Image.open(path)
            # Calculate proportional height based on max width
            # Calcule la hauteur proportionnelle basée sur la largeur maximale
            w_percent = max_width / float(img.size[0])
            h_size = int(float(img.size[1]) * float(w_percent))
            img = img.resize((max_width, h_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._cache[cache_key] = photo
            return photo
        except Exception:
            return None

    # Load multiple icons at once, returning a dictionary of results
    # Charge plusieurs icônes à la fois, retournant un dictionnaire de résultats
    def preload_icons(
        self, icon_names: list
    ) -> Dict[str, Optional[ImageTk.PhotoImage]]:
        result = {}
        for name in icon_names:
            result[name] = self.load_icon(name)
        return result

    # Clear the icon cache to free memory
    # Vide le cache d'icônes pour libérer de la mémoire
    def clear_cache(self) -> None:
        self._cache.clear()


# Singleton instance for global icon access
# Instance singleton pour un accès global aux icônes
_icon_loader: Optional[IconLoader] = None


# Get the singleton IconLoader instance
# Obtient l'instance singleton de IconLoader
def get_icon_loader() -> IconLoader:
    global _icon_loader
    if _icon_loader is None:
        _icon_loader = IconLoader()
    return _icon_loader
