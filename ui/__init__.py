"""VisioDoc3 UI module."""

from ui.theme_manager import ThemeManager, get_theme_manager
from ui.icon_loader import IconLoader, get_icon_loader
from ui.compact_sidebar import CompactSidebar
from ui.top_toolbar import TopToolbar

__all__ = [
    "ThemeManager",
    "get_theme_manager",
    "IconLoader",
    "get_icon_loader",
    "CompactSidebar",
    "TopToolbar",
]
