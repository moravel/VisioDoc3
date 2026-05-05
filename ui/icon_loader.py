"""Icon loading and management for VisioDoc3 application."""

import os
import sys
from PIL import Image, ImageTk, ImageDraw
from typing import Dict, Optional


class IconLoader:
    """Manages loading and caching of application icons."""

    def __init__(self, icon_dir: Optional[str] = None):
        if icon_dir is None:
            if getattr(sys, "frozen", False):
                icon_dir = os.path.join(sys._MEIPASS, "icons")
            else:
                icon_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "..", "icons"
                )

        self.icon_dir = icon_dir
        self._cache: Dict[str, ImageTk.PhotoImage] = {}
        self._default_size = (24, 24)

    def get_icon_path(self, name: str) -> str:
        """Get the file path for an icon by name."""
        return os.path.join(self.icon_dir, f"{name}.png")

    def load_icon(self, name: str, size: tuple = None) -> Optional[ImageTk.PhotoImage]:
        """Load an icon by name, with optional resizing."""
        if size is None:
            size = self._default_size

        cache_key = f"{name}_{size[0]}x{size[1]}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            path = self.get_icon_path(name)
            img = Image.open(path)
            img = img.resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._cache[cache_key] = photo
            return photo
        except FileNotFoundError:
            return self._create_placeholder(name, size)
        except Exception:
            return self._create_placeholder(name, size)

    def _create_placeholder(
        self, name: str, size: tuple
    ) -> Optional[ImageTk.PhotoImage]:
        """Create a placeholder icon when the file is not found."""
        try:
            placeholder = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(placeholder)
            text = name[0].upper() if name else "?"
            draw.text((size[0] // 3, 0), text, fill=(128, 128, 128, 255))
            photo = ImageTk.PhotoImage(placeholder)
            self._cache[f"{name}_{size[0]}x{size[1]}"] = photo
            return photo
        except Exception:
            return None

    def load_logo(self, max_width: int = 140) -> Optional[ImageTk.PhotoImage]:
        """Load the logo with appropriate sizing."""
        cache_key = f"logo_{max_width}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            path = self.get_icon_path("logoVisioDoc3")
            img = Image.open(path)
            w_percent = max_width / float(img.size[0])
            h_size = int(float(img.size[1]) * float(w_percent))
            img = img.resize((max_width, h_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def preload_icons(
        self, icon_names: list
    ) -> Dict[str, Optional[ImageTk.PhotoImage]]:
        """Load multiple icons at once."""
        result = {}
        for name in icon_names:
            result[name] = self.load_icon(name)
        return result

    def clear_cache(self) -> None:
        """Clear the icon cache."""
        self._cache.clear()


_icon_loader: Optional[IconLoader] = None


def get_icon_loader() -> IconLoader:
    """Get the singleton IconLoader instance."""
    global _icon_loader
    if _icon_loader is None:
        _icon_loader = IconLoader()
    return _icon_loader
