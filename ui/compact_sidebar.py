"""Compact icon-only sidebar for VisioDoc3."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional


class CompactSidebar(ttk.Frame):
    """Ultra-thin icon-only sidebar with tooltips for VisioDoc3."""

    def __init__(
        self,
        parent,
        icons: Dict,
        commands: Dict[str, Callable],
        app=None,
        **kwargs,
    ):
        super().__init__(parent, width=48, **kwargs)
        self.icons = icons
        self.commands = commands
        self.app = app
        self.buttons = {}
        self.tooltip_window = None
        self._build_sidebar()

    def _build_sidebar(self):
        """Build icon-only sidebar."""
        # Tool button mapping
        tool_items = [
            ("freedraw", "Dessin Libre"),
            ("rectangle", "Rectangle"),
            ("circle", "Cercle"),
            ("line", "Ligne"),
            ("text", "Texte"),
            ("blur", "Flou"),
            ("arrow", "Flèche"),
            ("highlight", "Surlignage"),
            ("selection", "Sélection"),
        ]

        for tool_key, tool_label in tool_items:
            icon = self.icons.get(tool_key)
            if icon:
                # Create a proper closure for the command
                cmd = self.commands.get(f"set_tool_{tool_key}")
                if cmd is None and self.app and hasattr(self.app, "set_tool"):
                    cmd = lambda t=tool_key: self.app.set_tool(t)
                btn = ttk.Button(
                    self,
                    image=icon,
                    style="Compact.TButton",
                    command=cmd,
                    width=48,
                )
                btn.pack(fill=tk.X, pady=1)
                self._add_tooltip(btn, tool_label)
                self.buttons[tool_key] = btn

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Color and size pickers
        color_items = [
            ("color_picker", "Choisir Couleur", "choose_annotation_color"),
            ("size_picker", "Choisir Taille", "choose_annotation_size"),
        ]

        for icon_key, label, method_name in color_items:
            icon = self.icons.get(icon_key)
            if icon:
                btn = ttk.Button(
                    self,
                    image=icon,
                    style="Compact.TButton",
                    command=self.commands.get(method_name),
                    width=48,
                )
                btn.pack(fill=tk.X, pady=1)
                self._add_tooltip(btn, label)

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Display functions
        display_items = [
            ("flip_horizontal", "Retourner Horizontal", "flip_horizontal"),
            ("flip_vertical", "Retourner Vertical", "flip_vertical"),
            ("fullscreen", "Plein Écran", "toggle_fullscreen"),
        ]

        for icon_key, label, method_name in display_items:
            icon = self.icons.get(icon_key)
            if icon:
                btn = ttk.Button(
                    self,
                    image=icon,
                    style="Compact.TButton",
                    command=self.commands.get(method_name),
                    width=48,
                )
                btn.pack(fill=tk.X, pady=1)
                self._add_tooltip(btn, label)

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # File functions
        file_items = [
            ("open_file", "Ouvrir Fichier", "open_file"),
            ("close_file", "Fermer Fichier", "close_file"),
        ]

        for icon_key, label, method_name in file_items:
            icon = self.icons.get(icon_key)
            if icon:
                btn = ttk.Button(
                    self,
                    image=icon,
                    style="Compact.TButton",
                    command=self.commands.get(method_name),
                    width=48,
                )
                btn.pack(fill=tk.X, pady=1)
                self._add_tooltip(btn, label)

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Action buttons
        action_items = [
            ("undo", "Annuler", "undo_last_annotation"),
            ("redo", "Rétablir", "redo_last_annotation"),
            ("save", "Sauvegarder", "save_image"),
            ("clear", "Effacer", "clear_all_annotations"),
        ]

        for icon_key, label, method_name in action_items:
            icon = self.icons.get(icon_key)
            if icon:
                btn = ttk.Button(
                    self,
                    image=icon,
                    style="Compact.TButton",
                    command=self.commands.get(method_name),
                    width=48,
                )
                btn.pack(fill=tk.X, pady=1)
                self._add_tooltip(btn, label)

    def _add_tooltip(self, widget, text):
        """Add tooltip on hover."""

        def show_tooltip(event):
            if self.tooltip_window:
                self.tooltip_window.destroy()
            x = widget.winfo_rootx() + 35
            y = widget.winfo_rooty() + 10
            self.tooltip_window = tk.Toplevel(widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            label = ttk.Label(
                self.tooltip_window,
                text=text,
                background="#333",
                foreground="white",
                padding=(4, 2),
            )
            label.pack()

        def hide_tooltip(event):
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
