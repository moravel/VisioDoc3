"""Theme management for VisioDoc3 application."""
# Gestion des thèmes pour l'application VisioDoc3

import os
import yaml
from typing import Dict, Any, Optional


# Manages application themes and provides color/color scheme access
# Gère les thèmes de l'application et fournit l'accès aux couleurs et schémas de couleurs
class ThemeManager:
    # Initializes the theme manager and loads themes from YAML file
    # Initialise le gestionnaire de thèmes et charge les thèmes depuis le fichier YAML
    def __init__(self, themes_file: Optional[str] = None):
        self.themes: Dict[
            str, Dict[str, Any]
        ] = {}  # Dictionary of theme definitions / Dictionnaire des définitions de thèmes
        self.current_theme: str = (
            "light"  # Currently active theme name / Nom du thème actif
        )
        self._defaults: Dict[
            str, Any
        ] = {}  # Default configuration values / Valeurs de configuration par défaut

        if themes_file is None:
            themes_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "themes.yaml"
            )
        self._load_themes(themes_file)

    # Load theme definitions from YAML file
    # Charger les définitions de thèmes depuis le fichier YAML
    def _load_themes(self, themes_file: str) -> None:
        try:
            with open(themes_file, "r") as f:
                data = yaml.safe_load(f)

            self.themes = data.get("themes", {})
            self._defaults = data.get("defaults", {})

            if "theme" in self._defaults:
                self.current_theme = self._defaults["theme"]
        except FileNotFoundError:
            self._create_default_themes()
        except yaml.YAMLError:
            self._create_default_themes()

    # Create default theme definitions if file not found
    # Crée des définitions de thèmes par défaut si le fichier n'est pas trouvé
    def _create_default_themes(self) -> None:
        self.themes = {
            "light": {
                "name": "Modern Light",  # Theme display name / Nom d'affichage du thème
                "background": "#ffffff",  # Main background color / Couleur d'arrière-plan principale
                "surface": "#f9fafb",  # Surface color for widgets / Couleur de surface pour les widgets
                "primary": "#2563eb",  # Primary accent color / Couleur d'accent principale
                "text_primary": "#111827",  # Primary text color / Couleur de texte principale
                "text_secondary": "#374151",  # Secondary text color / Couleur de texte secondaire
                "border": "#d1d5db",  # Border color / Couleur de bordure
            },
        }
        self._defaults = {"theme": "light"}

    # Get the current theme's color definitions
    # Obtient les définitions de couleur du thème actuel
    def get_current_theme(self) -> Dict[str, Any]:
        return self.themes.get(self.current_theme, self.themes.get("light", {}))

    # Get a specific color from current theme with fallback
    # Obtient une couleur spécifique du thème actuel avec valeur de secours
    def get_color(self, name: str, fallback: str = "#000000") -> str:
        theme = self.get_current_theme()
        return theme.get(name, fallback)

    # Switch to a different theme by name
    # Change pour un thème différent par nom
    def set_theme(self, theme_name: str) -> bool:
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False

    # Get list of available theme names
    # Obtient la liste des noms de thèmes disponibles
    def get_theme_names(self) -> list:
        return list(self.themes.keys())

    # Get a default configuration value by key
    # Obtient une valeur de configuration par défaut par clé
    def get_default(self, key: str, fallback: Any = None) -> Any:
        return self._defaults.get(key, fallback)

    # Apply theme colors to ttk style for consistent widget appearance
    # Applique les couleurs du thème au style ttk pour un aspect cohérent des widgets
    def apply_ttk_style(self, style) -> None:
        theme = self.get_current_theme()

        style.theme_use(
            "clam"
        )  # Use clam theme as base / Utilise le thème clam comme base

        bg = theme.get("background", "#ffffff")
        surface = theme.get("surface", "#f9fafb")
        primary = theme.get("primary", "#2563eb")
        text = theme.get("text_primary", "#111827")
        border = theme.get("border", "#d1d5db")
        hover = theme.get("button_hover", "#e5e7eb")
        pressed = theme.get("button_pressed", "#d1d5db")

        style.configure("TFrame", background=surface)
        style.configure("TLabel", background=surface, foreground=text)
        style.configure(
            "TButton",
            background=surface,
            foreground=text,
            borderwidth=1,
            relief="solid",
        )
        style.map("TButton", background=[("active", hover), ("pressed", pressed)])
        style.configure(
            "TMenubutton",
            background=surface,
            foreground=text,
            borderwidth=1,
            relief="solid",
        )

        style.configure("Status.TLabel", background=surface, foreground=text)
        style.configure("TopToolbar.TFrame", background=bg)
        style.configure(
            "Icon.TButton",
            background=surface,
            foreground=text,
            borderwidth=0,
            padding=2,
        )
        style.map("Icon.TButton", background=[("active", hover)])

    # Setup styles for compact sidebar and toolbar components
    # Configure les styles pour les composants de barre latérale et barre d'outils compactes
    def setup_compact_styles(self, style) -> None:
        theme = self.get_current_theme()
        surface = theme.get("surface", "#f9fafb")
        text = theme.get("text_primary", "#111827")
        border = theme.get("border", "#d1d5db")
        hover = theme.get("button_hover", "#e5e7eb")

        style.configure(
            "Sidebar.TButton",
            background=surface,
            foreground=text,
            borderwidth=0,
            padding=4,
            anchor="w",
        )
        style.map("Sidebar.TButton", background=[("active", hover)])

        style.configure(
            "Toolbar.TButton",
            background=surface,
            foreground=text,
            borderwidth=0,
            padding=2,
        )
        style.map("Toolbar.TButton", background=[("active", hover)])


# Singleton instance for global theme access
# Instance singleton pour un accès global aux thèmes
_theme_manager: Optional[ThemeManager] = None


# Get the singleton ThemeManager instance
# Obtient l'instance singleton de ThemeManager
def get_theme_manager() -> ThemeManager:
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
