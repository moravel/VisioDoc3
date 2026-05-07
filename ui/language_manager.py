"""Language management for VisioDoc3 application."""
# Gestion des langues pour l'application VisioDoc3

import os
import sys
import locale
import yaml
from typing import Dict, Any, Optional


# Manages application languages and provides translation access
# Gère les langues de l'application et fournit l'accès aux traductions
class LanguageManager:
    # Initializes the language manager and loads languages from YAML files
    # Initialise le gestionnaire de langues et charge les langues depuis les fichiers YAML
    def __init__(self, languages_dir: Optional[str] = None):
        self.languages: Dict[
            str, Dict[str, Any]
        ] = {}  # Dictionary of language definitions / Dictionnaire des définitions de langues
        self.current_language: str = (
            "en"  # Currently active language code / Code de langue actif
        )
        self._defaults: Dict[
            str, Any
        ] = {}  # Default configuration values / Valeurs de configuration par défaut

        if languages_dir is None:
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                languages_dir = os.path.join(sys._MEIPASS, "config", "languages")
            else:
                languages_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "config", "languages"
                )
        self.languages_dir = languages_dir
        self._load_languages()

    # Load language definitions from YAML files
    # Charger les définitions de langues depuis les fichiers YAML
    def _load_languages(self) -> None:
        default_lang = self._get_default_language()

        for filename in os.listdir(self.languages_dir):
            if filename.endswith(".yaml"):
                lang_code = filename[:-5]  # Remove .yaml extension
                filepath = os.path.join(self.languages_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.languages[lang_code] = yaml.safe_load(f)
                except (FileNotFoundError, yaml.YAMLError):
                    pass

        if not self.languages:
            self._create_default_languages()
        elif default_lang in self.languages:
            self.current_language = default_lang

    # Determine default language based on system locale
    # Détermine la langue par défaut basée sur la locale système
    def _get_default_language(self) -> str:
        system_locale = None
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split("_")[0].lower()
                if lang_code in ["fr", "en"]:
                    return lang_code
        except:
            pass
        if system_locale and system_locale.lower().startswith("fr"):
            return "fr"
        return "en"

    # Create default language definitions if files not found
    # Crée des définitions de langues par défaut si les fichiers n'existent pas
    def _create_default_languages(self) -> None:
        self.languages = {
            "en": {
                "app": {"title": "VisioDoc3 - Document Viewer"},
                "menus": {
                    "file": {
                        "label": "File",
                        "open": "Open",
                        "save": "Save",
                        "close": "Close File",
                        "exit": "Exit",
                    },
                    "annotations": {"label": "Annotations"},
                    "view": {"label": "View"},
                },
                "tools": {
                    "freedraw": {
                        "name": "Freehand Draw",
                        "tooltip": "Active the freehand drawing tool (Ctrl+F)",
                    },
                    "rectangle": {
                        "name": "Rectangle",
                        "tooltip": "Active the rectangle tool (Ctrl+R)",
                    },
                    "circle": {
                        "name": "Circle",
                        "tooltip": "Active the circle tool (Ctrl+C)",
                    },
                    "line": {
                        "name": "Line",
                        "tooltip": "Active the line tool (Ctrl+L)",
                    },
                    "text": {
                        "name": "Add Text",
                        "tooltip": "Active the text tool (Ctrl+T)",
                    },
                    "blur": {
                        "name": "Blur Area",
                        "tooltip": "Active the blur tool (Ctrl+B)",
                    },
                    "arrow": {
                        "name": "Arrow",
                        "tooltip": "Active the arrow tool (Ctrl+A)",
                    },
                    "highlight": {
                        "name": "Highlight",
                        "tooltip": "Active the highlight tool (Ctrl+H)",
                    },
                    "selection": {
                        "name": "Selection",
                        "tooltip": "Active the selection tool (Ctrl+S)",
                    },
                },
                "view": {
                    "zoom_in": "Zoom +",
                    "zoom_out": "Zoom -",
                    "flip_horizontal": "Flip Horizontal",
                    "flip_vertical": "Flip Vertical",
                    "fullscreen": "Fullscreen",
                    "settings": "Settings",
                },
                "actions": {
                    "undo": "Undo",
                    "redo": "Redo",
                    "delete": "Delete",
                    "clear": "Clear All",
                    "save": "Save",
                    "help": "Help",
                },
            },
            "fr": {
                "app": {"title": "VisioDoc3 - Visionneuse de Documents"},
                "menus": {
                    "file": {
                        "label": "Fichier",
                        "open": "Ouvrir",
                        "save": "Sauvegarder",
                        "close": "Fermer le fichier",
                        "exit": "Quitter",
                    },
                    "annotations": {"label": "Annotations"},
                    "view": {"label": "Affichage"},
                },
                "tools": {
                    "freedraw": {
                        "name": "Dessin Main Levée",
                        "tooltip": "Active l'outil de dessin à main levée (Ctrl+F)",
                    },
                    "rectangle": {
                        "name": "Rectangle",
                        "tooltip": "Active l'outil rectangle (Ctrl+R)",
                    },
                    "circle": {
                        "name": "Cercle",
                        "tooltip": "Active l'outil cercle (Ctrl+C)",
                    },
                    "line": {
                        "name": "Ligne",
                        "tooltip": "Active l'outil ligne (Ctrl+L)",
                    },
                    "text": {
                        "name": "Ajouter Texte",
                        "tooltip": "Active l'outil texte (Ctrl+T)",
                    },
                    "blur": {
                        "name": "Zone de Flou",
                        "tooltip": "Active l'outil de flou (Ctrl+B)",
                    },
                    "arrow": {
                        "name": "Flèche",
                        "tooltip": "Active l'outil flèche (Ctrl+A)",
                    },
                    "highlight": {
                        "name": "Surlignage",
                        "tooltip": "Active l'outil surlignage (Ctrl+H)",
                    },
                    "selection": {
                        "name": "Sélection",
                        "tooltip": "Active l'outil de sélection (Ctrl+S)",
                    },
                },
                "view": {
                    "zoom_in": "Zoom +",
                    "zoom_out": "Zoom -",
                    "flip_horizontal": "Flip Horizontal",
                    "flip_vertical": "Flip Vertical",
                    "fullscreen": "Plein Écran",
                    "settings": "Paramètres",
                },
                "actions": {
                    "undo": "Annuler",
                    "redo": "Rétablir",
                    "delete": "Supprimer",
                    "clear": "Effacer Tout",
                    "save": "Sauvegarder",
                    "help": "Aide",
                },
            },
        }
        self.current_language = "fr" if self._get_default_language() == "fr" else "en"

    # Get a translation value by key with dot notation support
    # Obtient une valeur de traduction par clé avec support de notation pointée
    def tr(self, key: str, fallback: str = "") -> str:
        lang = self.languages.get(self.current_language, {})
        keys = key.split(".")
        value = lang
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return fallback
            if value is None:
                # Try fallback to English
                lang = self.languages.get("en", {})
                value = lang
                for k2 in keys:
                    if isinstance(value, dict):
                        value = value.get(k2)
                    else:
                        return fallback
                    if value is None:
                        return fallback
                return str(value) if value else fallback
        return str(value) if value else fallback

    # Switch to a different language by language code
    # Change pour une langue différente par code de langue
    def set_language(self, lang_code: str) -> bool:
        if lang_code in self.languages:
            self.current_language = lang_code
            return True
        return False

    # Get list of available language codes
    # Obtient la liste des codes de langues disponibles
    def get_language_codes(self) -> list:
        return list(self.languages.keys())

    # Get the current language dictionary
    # Obtient le dictionnaire de la langue actuelle
    def get_current_language_dict(self) -> Dict[str, Any]:
        return self.languages.get(self.current_language, {})


# Singleton instance for global language access
# Instance singleton pour un accès global aux langues
_language_manager: Optional[LanguageManager] = None


# Get the singleton LanguageManager instance
# Obtient l'instance singleton de LanguageManager
def get_language_manager() -> LanguageManager:
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager
