"""Compact icon-only sidebar for VisioDoc3."""
# Barre latérale compacte avec icônes uniquement pour VisioDoc3

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional


# Ultra-thin icon-only sidebar with tooltips for VisioDoc3
# Barre latérale ultra-fine avec icônes uniquement et info-bulles pour VisioDoc3
class CompactSidebar(ttk.Frame):
    # Initializes the compact sidebar with icons and command mappings
    # Initialise la barre latérale compacte avec les icônes et les mappages de commandes
    def __init__(
        self,
        parent,
        icons: Dict,
        commands: Dict[str, Callable],
        app=None,
        **kwargs,
    ):
        super().__init__(parent, width=48, **kwargs)
        self.icons = (
            icons  # Dictionary of icon images / Dictionnaire des images d'icônes
        )
        self.commands = commands  # Dictionary of command callbacks / Dictionnaire des rappels de commandes
        self.app = (
            app  # Reference to main application / Référence à l'application principale
        )
        self.buttons = {}  # Dictionary of created buttons / Dictionnaire des boutons créés
        self.tooltip_window = (
            None  # Current tooltip window / Fenêtre d'info-bulle actuelle
        )
        self._build_sidebar()

    # Build icon-only sidebar with categorized button groups
    # Construit la barre latérale avec icônes uniquement avec des groupes de boutons catégorisés
    def _build_sidebar(self):
        # Build icon-only sidebar
        # Construit la barre latérale avec icônes uniquement
        # Tool button mapping - annotation tools
        # Mappage des boutons d'outils - outils d'annotation
        tool_items = [
            ("freedraw", "Dessin Libre"),  # Freehand drawing / Dessin à main levée
            ("rectangle", "Rectangle"),  # Rectangle annotation / Annotation rectangle
            ("circle", "Cercle"),  # Circle annotation / Annotation cercle
            ("line", "Ligne"),  # Line annotation / Annotation ligne
            ("text", "Texte"),  # Text annotation / Annotation texte
            ("blur", "Flou"),  # Blur annotation / Annotation flou
            ("arrow", "Flèche"),  # Arrow annotation / Annotation flèche
            ("highlight", "Surlignage"),  # Highlight annotation / Annotation surlignage
            ("selection", "Sélection"),  # Selection tool / Outil de sélection
        ]

        for tool_key, tool_label in tool_items:
            icon = self.icons.get(tool_key)
            if icon:
                # Create a proper closure for the command
                # Crée une fermeture appropriée pour la commande
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

        # Separator - visual divider between tool groups
        # Séparateur - diviseur visuel entre les groupes d'outils
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Color and size picker buttons
        # Boutons de sélection de couleur et de taille
        color_items = [
            (
                "color_picker",
                "Choisir Couleur",
                "choose_annotation_color",
            ),  # Color picker / Sélecteur de couleur
            (
                "size_picker",
                "Choisir Taille",
                "choose_annotation_size",
            ),  # Size picker / Sélecteur de taille
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
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Display function buttons - flip and fullscreen
        # Boutons des fonctions d'affichage - retournement et plein écran
        display_items = [
            (
                "flip_horizontal",
                "Retourner Horizontal",
                "flip_horizontal",
            ),  # Flip horizontal / Retourner horizontalement
            (
                "flip_vertical",
                "Retourner Vertical",
                "flip_vertical",
            ),  # Flip vertical / Retourner verticalement
            (
                "fullscreen",
                "Plein Écran",
                "toggle_fullscreen",
            ),  # Fullscreen toggle / Basculer en plein écran
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
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # File operation buttons - open and close files
        # Boutons des opérations de fichiers - ouvrir et fermer des fichiers
        file_items = [
            (
                "open_file",
                "Ouvrir Fichier",
                "open_file",
            ),  # Open file button / Bouton ouvrir fichier
            (
                "close_file",
                "Fermer Fichier",
                "close_file",
            ),  # Close file button / Bouton fermer fichier
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
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Action buttons - undo, redo, save, clear
        # Boutons d'actions - annuler, rétablir, sauvegarder, effacer
        action_items = [
            ("undo", "Annuler", "undo_last_annotation"),  # Undo button / Bouton annuler
            (
                "redo",
                "Rétablir",
                "redo_last_annotation",
            ),  # Redo button / Bouton rétablir
            ("save", "Sauvegarder", "save_image"),  # Save button / Bouton sauvegarder
            (
                "clear",
                "Effacer",
                "clear_all_annotations",
            ),  # Clear button / Bouton effacer
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

    # Add tooltip on hover to a widget
    # Ajoute une info-bulle au survol d'un widget
    def _add_tooltip(self, widget, text):
        """Add tooltip on hover."""

        def show_tooltip(event):
            # Destroy existing tooltip before creating new one
            # Détruit l'info-bulle existante avant en créer une nouvelle
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
            # Destroy tooltip when mouse leaves widget
            # Détruit l'info-bulle lorsque la souris quitte le widget
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
