"""Theme management for VisioDoc3 application."""

import os
import yaml
from typing import Dict, Any, Optional


class ThemeManager:
    """Manages application themes and provides color/color scheme access."""

    def __init__(self, themes_file: Optional[str] = None):
        self.themes: Dict[str, Dict[str, Any]] = {}
        self.current_theme: str = "dark"
        self._defaults: Dict[str, Any] = {}

        if themes_file is None:
            themes_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "themes.yaml"
            )
        self._load_themes(themes_file)

    def _load_themes(self, themes_file: str) -> None:
        """Load theme definitions from YAML file."""
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

    def _create_default_themes(self) -> None:
        """Create default theme definitions if file not found."""
        self.themes = {
            "dark": {
                "name": "Modern Dark",
                "background": "#111827",
                "surface": "#1f2937",
                "primary": "#3b82f6",
                "text_primary": "#f9fafb",
                "text_secondary": "#d1d5db",
                "border": "#374151",
            },
            "light": {
                "name": "Modern Light",
                "background": "#ffffff",
                "surface": "#f9fafb",
                "primary": "#2563eb",
                "text_primary": "#111827",
                "text_secondary": "#374151",
                "border": "#d1d5db",
            },
        }
        self._defaults = {"theme": "dark"}

    def get_current_theme(self) -> Dict[str, Any]:
        """Get the current theme's color definitions."""
        return self.themes.get(self.current_theme, self.themes.get("dark", {}))

    def get_color(self, name: str, fallback: str = "#000000") -> str:
        """Get a specific color from current theme."""
        theme = self.get_current_theme()
        return theme.get(name, fallback)

    def set_theme(self, theme_name: str) -> bool:
        """Switch to a different theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False

    def get_theme_names(self) -> list:
        """Get list of available theme names."""
        return list(self.themes.keys())

    def get_default(self, key: str, fallback: Any = None) -> Any:
        """Get a default configuration value."""
        return self._defaults.get(key, fallback)

    def apply_ttk_style(self, style) -> None:
        """Apply theme colors to ttk style."""
        theme = self.get_current_theme()

        style.theme_use("clam")

        bg = theme.get("background", "#ffffff")
        surface = theme.get("surface", "#f9fafb")
        primary = theme.get("primary", "#3b82f6")
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


_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the singleton ThemeManager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
