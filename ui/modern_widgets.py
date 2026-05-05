"""Modern animated widgets for VisioDoc3 application."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any


class AnimatedButton(ttk.Button):
    """Button with hover and click animations."""

    def __init__(
        self,
        parent,
        style: str = "Modern.TButton",
        animation_speed: int = 200,
        **kwargs,
    ):
        super().__init__(parent, style=style, **kwargs)
        self.animation_speed = animation_speed
        self._original_bg = None
        self._animating = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Handle mouse enter for hover effect."""
        if not self._animating:
            self.state(["active"])

    def _on_leave(self, event):
        """Handle mouse leave for hover effect."""
        self.state(["!active"])


class ModernButton(ttk.Button):
    """Enhanced button with modern styling and smooth transitions."""

    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        style: str = "Modern.TButton",
        **kwargs,
    ):
        super().__init__(parent, text=text, command=command, style=style, **kwargs)
        self._hover_animation_id = None

    def bind_hover(self, enter_callback: Callable, leave_callback: Callable):
        """Bind custom hover callbacks."""
        self.bind("<Enter>", enter_callback)
        self.bind("<Leave>", leave_callback)


def create_modern_button_style(style: ttk.Style, theme_colors: dict):
    """Create modern button styles for ttk."""
    bg = theme_colors.get("surface", "#f9fafb")
    text = theme_colors.get("text_primary", "#111827")
    hover = theme_colors.get("button_hover", "#e5e7eb")
    primary = theme_colors.get("primary", "#2563eb")

    style.configure(
        "Modern.TButton",
        background=bg,
        foreground=text,
        borderwidth=1,
        relief="solid",
        padding=6,
    )

    style.map(
        "Modern.TButton",
        background=[("active", hover), ("pressed", "#d1d5db")],
        relief=[("pressed", "sunken")],
    )

    style.configure(
        "ModernPrimary.TButton",
        background=primary,
        foreground="#ffffff",
        borderwidth=0,
        padding=6,
    )

    style.map(
        "ModernPrimary.TButton",
        background=[("active", theme_colors.get("primary_hover", "#1d4ed8"))],
    )


class HoverLabel(ttk.Label):
    """Label with hover effect support."""

    def __init__(self, parent, hover_bg: str = None, hover_fg: str = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg
        self.default_bg = kwargs.get("background")
        self.default_fg = kwargs.get("foreground")

        if hover_bg:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        if self.hover_bg:
            self.configure(background=self.hover_bg)
        if self.hover_fg:
            self.configure(foreground=self.hover_fg)

    def _on_leave(self, event):
        if self.default_bg:
            self.configure(background=self.default_bg)
        if self.default_fg:
            self.configure(foreground=self.default_fg)


class ToggleButton(ttk.Checkbutton):
    """A toggle button widget."""

    def __init__(
        self,
        parent,
        text: str = "",
        variable: tk.Variable = None,
        command: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(
            parent, text=text, variable=variable, command=command, **kwargs
        )
        self.variable = variable or tk.BooleanVar()


def setup_modern_styles(style: ttk.Style, theme_colors: dict):
    """Setup all modern widget styles."""
    bg = theme_colors.get("background", "#ffffff")
    surface = theme_colors.get("surface", "#f9fafb")
    text = theme_colors.get("text_primary", "#111827")
    border = theme_colors.get("border", "#d1d5db")
    primary = theme_colors.get("primary", "#2563eb")
    hover = theme_colors.get("button_hover", "#e5e7eb")
    pressed = theme_colors.get("button_pressed", "#d1d5db")

    style.configure("Modern.TFrame", background=surface)
    style.configure("Modern.TLabel", background=surface, foreground=text)

    style.configure(
        "Modern.TButton",
        background=surface,
        foreground=text,
        borderwidth=1,
        relief="solid",
        padding=6,
    )
    style.map("Modern.TButton", background=[("active", hover), ("pressed", pressed)])

    style.configure(
        "ModernPrimary.TButton",
        background=primary,
        foreground="#ffffff",
        borderwidth=0,
        padding=6,
    )

    style.configure(
        "Modern.TMenubutton",
        background=surface,
        foreground=text,
        borderwidth=1,
        relief="solid",
    )
    style.map("Modern.TMenubutton", background=[("active", hover)])
