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
    """
    Singleton class for managing multilingual support in VisioDoc3.

    Handles loading of language definitions from YAML files, provides
    translation lookup with dot-notation key support, and manages
    the current active language state.

    Attributes:
        languages (Dict[str, Dict[str, Any]]): Dictionary of loaded language
            definitions keyed by language code (e.g., 'en', 'fr').
        current_language (str): The currently active language code.
        _defaults (Dict[str, Any]): Default configuration values.
    """

    # Initializes the language manager and loads languages from YAML files
    # Initialise le gestionnaire de langues et charge les langues depuis les fichiers YAML
    def __init__(self, languages_dir: Optional[str] = None):
        """
        Initialize the LanguageManager with optional custom languages directory.

        Sets up the languages dictionary and determines the languages directory
        path. Handles both development mode and PyInstaller frozen builds.

        Args:
            languages_dir (Optional[str]): Custom path to languages directory.
                If None, uses default path based on execution context.
        """
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
            # Determine languages directory based on execution context
            # Déterminer le répertoire de langues selon le contexte d'exécution
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                # PyInstaller frozen build: use bundled languages directory
                # Build PyInstaller: utilise le répertoire de langues groupé
                languages_dir = os.path.join(sys._MEIPASS, "config", "languages")
            else:
                # Development mode: use local config/languages directory
                # Mode développement: utilise le répertoire config/languages local
                languages_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "config", "languages"
                )
        self.languages_dir = languages_dir
        self._load_languages()

    # Load language definitions from YAML files
    # Charger les définitions de langues depuis les fichiers YAML
    def _load_languages(self) -> None:
        """
        Load language definitions from YAML files in the languages directory.

        Scans the languages directory for .yaml files and loads each one.
        Files should be named with the language code (e.g., 'en.yaml', 'fr.yaml').

        Implements fallback behavior: if no languages are found, creates
        default embedded language definitions. Sets the current language
        based on the system locale if available.
        """
        default_lang = self._get_default_language()

        # Iterate through YAML files in the languages directory
        # Itérer à travers les fichiers YAML dans le répertoire de langues
        for filename in os.listdir(self.languages_dir):
            if filename.endswith(".yaml"):
                lang_code = filename[:-5]  # Remove .yaml extension
                filepath = os.path.join(self.languages_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.languages[lang_code] = yaml.safe_load(f)
                except (FileNotFoundError, yaml.YAMLError):
                    pass  # Silently skip files that cannot be loaded

        # Fallback to embedded default languages if none loaded
        # Repli vers les langues par défaut intégrées si aucune n'est chargée
        if not self.languages:
            self._create_default_languages()
        elif default_lang in self.languages:
            self.current_language = default_lang

    # Determine default language based on system locale
    # Détermine la langue par défaut basée sur la locale système
    def _get_default_language(self) -> str:
        """
        Determine the default language based on system locale.

        Checks the system's default locale and returns the corresponding
        language code if supported. Falls back to 'en' if the locale
        cannot be determined or is not a supported language.

        Returns:
            str: Language code ('fr' or 'en') based on system locale.
        """
        system_locale = None
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split("_")[0].lower()
                if lang_code in ["fr", "en"]:
                    return lang_code
        except:
            pass  # Fall through to default
        # Additional check for French locale variations
        # Vérification supplémentaire pour les variantes de locale française
        if system_locale and system_locale.lower().startswith("fr"):
            return "fr"
        return "en"  # Default to English / Défaut en anglais

    # Create default language definitions if files not found
    # Crée des définitions de langues par défaut si les fichiers n'existent pas
    def _create_default_languages(self) -> None:
        """
        Create built-in default language definitions.

        Embedded fallback that provides English and French translations
        for all UI strings. Used when no language YAML files are found.
        """
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
                    "language": {
                        "label": "Language",
                        "french": "Français",
                        "english": "English",
                    },
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
                    "color_picker": {
                        "name": "Color Picker",
                        "tooltip": "Choose annotation color",
                    },
                    "size_picker": {
                        "name": "Size Picker",
                        "tooltip": "Choose annotation size",
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
                "help": {
                    "loading": "Loading...",
                    "title": "Help",
                    "manual": "VisioDoc3 User Manual\n\nKeyboard Shortcuts:\n\nFile Operations:\n  Ctrl+O: Open file\n  Ctrl+Shift+S: Save annotated image\n  Ctrl+E: Clear all annotations\n\nAnnotation Tools:\n  Ctrl+F: Freehand draw\n  Ctrl+R: Rectangle\n  Ctrl+C: Circle\n  Ctrl+L: Line\n  Ctrl+T: Text\n  Ctrl+B: Blur\n  Ctrl+A: Arrow\n  Ctrl+H: Highlight\n  Ctrl+S: Selection\n\nView:\n  Ctrl++ / Ctrl+=: Zoom in\n  Ctrl+-: Zoom out\n  Ctrl+J: Flip horizontal\n  Ctrl+U: Flip vertical\n  F11: Fullscreen\n  Ctrl+P: Settings\n\nEdit:\n  Ctrl+Z: Undo\n  Ctrl+Y: Redo\n  Delete: Delete selected annotation\n",
                },
                "dialogs": {
                    "no_cameras": "No cameras found",
                    "close_file": "Close current file",
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
                    "language": {
                        "label": "Langue",
                        "french": "Français",
                        "english": "Anglais",
                    },
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
                    "color_picker": {
                        "name": "Choix Couleur",
                        "tooltip": "Choisir la couleur d'annotation",
                    },
                    "size_picker": {
                        "name": "Choix Taille",
                        "tooltip": "Choisir la taille d'annotation",
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
                "help": {
                    "loading": "Chargement...",
                    "title": "Aide",
                    "manual": "Manuel d'utilisation VisioDoc3\n\nRaccourcis clavier:\n\nOpérations fichier:\n  Ctrl+O: Ouvrir un fichier\n  Ctrl+Shift+S: Sauvegarder l'image annotée\n  Ctrl+E: Effacer toutes les annotations\n\nOutils d'annotation:\n  Ctrl+F: Dessin à main levée\n  Ctrl+R: Rectangle\n  Ctrl+C: Cercle\n  Ctrl+L: Ligne\n  Ctrl+T: Texte\n  Ctrl+B: Flou\n  Ctrl+A: Flèche\n  Ctrl+H: Surlignage\n  Ctrl+S: Sélection\n\nAffichage:\n  Ctrl++ / Ctrl+=: Zoom avant\n  Ctrl+-: Zoom arrière\n  Ctrl+J: Retourner horizontalement\n  Ctrl+U: Retourner verticalement\n  F11: Plein écran\n  Ctrl+P: Paramètres\n\nEdition:\n  Ctrl+Z: Annuler\n  Ctrl+Y: Rétablir\n  Suppr: Supprimer l'annotation sélectionnée\n",
                },
                "dialogs": {
                    "no_cameras": "Aucune webcam trouvée",
                    "close_file": "Fermer le fichier actuel",
                },
            },
        }
        self.current_language = "fr" if self._get_default_language() == "fr" else "en"

    # Get a translation value by key with dot notation support
    # Obtient une valeur de traduction par clé avec support de notation pointée
    def tr(self, key: str, fallback: str = "") -> str:
        """
        Get a translation value by key with dot notation support.

        Retrieves a translation from the current language dictionary using
        dot-separated keys (e.g., 'menus.file.open'). Falls back to English
        if the key is not found in the current language.

        Args:
            key (str): Translation key in dot notation (e.g., 'menus.file.open').
            fallback (str): Default value if translation is not found.

        Returns:
            str: The translated string, fallback value, or the key itself.
        """
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
                # Essayer le repli vers l'anglais
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
        """
        Switch to a different language by language code.

        Changes the current language if the language code exists in the
        loaded languages dictionary.

        Args:
            lang_code (str): The language code to switch to (e.g., 'en', 'fr').

        Returns:
            bool: True if language was changed, False if language not found.
        """
        if lang_code in self.languages:
            self.current_language = lang_code
            return True
        return False

    # Get list of available language codes
    # Obtient la liste des codes de langues disponibles
    def get_language_codes(self) -> list:
        """
        Get list of available language codes.

        Returns:
            list: List of language codes that have been loaded.
        """
        return list(self.languages.keys())

    # Get the current language dictionary
    # Obtient le dictionnaire de la langue actuelle
    def get_current_language_dict(self) -> Dict[str, Any]:
        """
        Get the current language's full dictionary.

        Returns:
            Dict[str, Any]: The dictionary containing all translations
                for the currently active language.
        """
        return self.languages.get(self.current_language, {})


# Singleton instance for global language access
# Instance singleton pour un accès global aux langues
_language_manager: Optional[LanguageManager] = None


# Get the singleton LanguageManager instance
# Obtient l'instance singleton de LanguageManager
def get_language_manager() -> LanguageManager:
    """
    Get the singleton LanguageManager instance.

    Creates a new LanguageManager on first call, then returns the same
    instance on subsequent calls. This ensures consistent language state
    across the entire application.

    Returns:
        LanguageManager: The singleton LanguageManager instance.
    """
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager
