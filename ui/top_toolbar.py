"""Top toolbar with cascading menus for VisioDoc3."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class TopToolbar(ttk.Frame):
    """Top toolbar with File, Annotate, View, Export menus."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self._build_toolbar()

    def _build_toolbar(self):
        """Build menu-style toolbar."""
        # Padding indicator
        ttk.Label(self, width=2).pack(side=tk.LEFT)

        # File menu
        file_btn = self._create_menu_button("Fichier", self._create_file_menu)
        file_btn.pack(side=tk.LEFT, padx=2)

        # Annotate menu
        annotate_btn = self._create_menu_button(
            "Annotations", self._create_annotate_menu
        )
        annotate_btn.pack(side=tk.LEFT, padx=2)

        # View menu
        view_btn = self._create_menu_button("Affichage", self._create_view_menu)
        view_btn.pack(side=tk.LEFT, padx=2)

        # Spacer
        ttk.Label(self).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Status indicator
        self.status_label = ttk.Label(
            self,
            text="Prêt",
            style="Status.TLabel",
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Exit button
        exit_btn = ttk.Button(
            self,
            text="✕",
            style="Icon.TButton",
            command=self.app.on_closing,
            width=3,
        )
        exit_btn.pack(side=tk.RIGHT, padx=2)

    def _create_menu_button(self, text: str, menu_factory: Callable):
        """Create a menu button."""
        btn = ttk.Menubutton(self, text=text)
        menu = menu_factory(btn)
        btn["menu"] = menu
        return btn

    def _create_file_menu(self, parent):
        """Create File menu."""
        menu = tk.Menu(parent, tearoff=0)
        menu.add_command(label="Ouvrir (Ctrl+O)", command=self.app.open_file)
        menu.add_command(
            label="Sauvegarder (Ctrl+Shift+S)", command=self.app.save_image
        )
        menu.add_separator()
        menu.add_command(label="Fermer le fichier", command=self.app.close_file)
        menu.add_separator()
        menu.add_command(label="Quitter", command=self.app.on_closing)
        return menu

    def _create_annotate_menu(self, parent):
        """Create Annotations menu."""
        menu = tk.Menu(parent, tearoff=0)
        menu.add_command(
            label="Dessin Main Levée (Ctrl+F)",
            command=lambda: self.app.set_tool("freedraw"),
        )
        menu.add_command(
            label="Rectangle (Ctrl+R)", command=lambda: self.app.set_tool("rectangle")
        )
        menu.add_command(
            label="Cercle (Ctrl+C)", command=lambda: self.app.set_tool("circle")
        )
        menu.add_command(
            label="Ligne (Ctrl+L)", command=lambda: self.app.set_tool("line")
        )
        menu.add_command(
            label="Texte (Ctrl+T)", command=lambda: self.app.set_tool("text")
        )
        menu.add_separator()
        menu.add_command(
            label="Flèche (Ctrl+A)", command=lambda: self.app.set_tool("arrow")
        )
        menu.add_command(
            label="Surlignage (Ctrl+H)", command=lambda: self.app.set_tool("highlight")
        )
        menu.add_command(
            label="Zone de Flou (Ctrl+B)", command=lambda: self.app.set_tool("blur")
        )
        menu.add_command(
            label="Sélection (Ctrl+S)", command=lambda: self.app.set_tool("selection")
        )
        menu.add_separator()
        menu.add_command(
            label="Choisir Couleur (Ctrl+K)", command=self.app.choose_annotation_color
        )
        menu.add_command(
            label="Choisir Taille (Ctrl+I)", command=self.app.choose_annotation_size
        )
        return menu

    def _create_view_menu(self, parent):
        """Create View menu."""
        menu = tk.Menu(parent, tearoff=0)
        menu.add_command(label="Zoom + (Ctrl++)", command=self.app.zoom_in)
        menu.add_command(label="Zoom - (Ctrl+-)", command=self.app.zoom_out)
        menu.add_separator()
        menu.add_command(
            label="Flip Horizontal (Ctrl+J)", command=self.app.flip_horizontal
        )
        menu.add_command(label="Flip Vertical (Ctrl+U)", command=self.app.flip_vertical)
        menu.add_separator()
        menu.add_command(label="Plein Écran (F11)", command=self.app.toggle_fullscreen)
        menu.add_command(
            label="Paramètres (Ctrl+P)", command=self.app.open_settings_dialog
        )
        return menu

    def update_status(self, text: str):
        """Update status text."""
        self.status_label.config(text=text)
