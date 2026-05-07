"""Compact icon-only sidebar for VisioDoc3."""
# Barre latérale compacte avec icônes uniquement pour VisioDoc3

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional

from ui.language_manager import get_language_manager


# TooltipInfo class to store per-button tooltip data
# Classe TooltipInfo pour stocker les données d'info-bulle par bouton
class TooltipInfo:
    """
    Stores tooltip data for a sidebar button.

    Manages the tooltip text display for a specific button widget,
    allowing the text to be dynamically updated when the language changes.
    """

    def __init__(self, widget, tooltip_key, fallback):
        """
        Initialize the TooltipInfo with widget and translation key.

        Args:
            widget: The Tkinter widget that will display the tooltip.
            tooltip_key (str): Translation key for the tooltip text.
            fallback (str): Fallback text if translation is not found.
        """
        self.widget = widget
        self.tooltip_key = tooltip_key
        self.fallback = fallback
        self.text_var = tk.StringVar()

    def update_text(self, language_manager):
        """
        Update the tooltip text based on current language.

        Retrieves the translated text from the language manager and updates
        the internal StringVar used for display.

        Args:
            language_manager: The LanguageManager instance for translation lookup.
        """
        self.text_var.set(language_manager.tr(self.tooltip_key, self.fallback))

    def get_text(self):
        """
        Get the current tooltip text.

        Returns:
            str: The current tooltip text value.
        """
        return self.text_var.get()


# Ultra-thin icon-only sidebar with tooltips for VisioDoc3
# Barre latérale ultra-fine avec icônes uniquement et info-bulles pour VisioDoc3
class CompactSidebar(ttk.Frame):
    """
    Ultra-thin sidebar with icon-only buttons for VisioDoc3.

    Provides a compact toolbar containing categorized tool buttons for
    annotation, display control, file operations, and actions. Each button
    displays a tooltip on hover with the tool name in the current language.
    """

    # Initializes the compact sidebar with icons and command mappings
    # Initialise la barre latérale compacte avec les icônes et les mappages de commandes
    def __init__(
        self,
        parent,
        icons: Dict,
        commands: Dict[str, Callable],
        app=None,
        language_manager=None,
        **kwargs,
    ):
        """
        Initialize the CompactSidebar with icons and command callbacks.

        Sets up the sidebar frame with buttons for all annotation tools,
        display controls, file operations, and action buttons. Each button
        is configured with appropriate icons and tooltips.

        Args:
            parent: The parent widget.
            icons (Dict): Dictionary mapping tool keys to PhotoImage objects.
            commands (Dict[str, Callable]): Dictionary mapping action names
                to callback functions.
            app: Reference to the main application instance.
            language_manager: Optional LanguageManager instance for translations.
                Uses the global singleton if not provided.
            **kwargs: Additional keyword arguments passed to ttk.Frame.
        """
        super().__init__(parent, width=48, **kwargs)
        self.icons = (
            icons  # Dictionary of icon images / Dictionnaire des images d'icônes
        )
        self.commands = commands  # Dictionary of command callbacks / Dictionnaire des rappels de commandes
        self.app = (
            app  # Reference to main application / Référence à l'application principale
        )
        self.language_manager = (
            language_manager if language_manager else get_language_manager()
        )
        self.buttons = {}  # Dictionary of created buttons / Dictionnaire des boutons créés
        self.tooltip_window = (
            None  # Current tooltip window / Fenêtre d'info-bulle actuelle
        )
        self.tooltip_infos = {}  # Store TooltipInfo per button
        self._build_sidebar()

    # Build icon-only sidebar with categorized button groups
    # Construit la barre latérale avec icônes uniquement avec des groupes de boutons catégorisés
    def _build_sidebar(self):
        """
        Build the icon-only sidebar with categorized button groups.

        Creates and arranges all sidebar buttons organized by function:
        - Annotation tools (freedraw, rectangle, circle, line, text, blur, arrow, highlight, selection)
        - Color and size pickers
        - Display controls (flip, fullscreen)
        - File operations (open, close)
        - Action buttons (undo, redo, save, clear)

        Separators are added between functional groups for visual organization.
        """
        # Build icon-only sidebar
        # Construit la barre latérale avec icônes uniquement
        # Tool button mapping - annotation tools
        # Mappage des boutons d'outils - outils d'annotation
        tool_items = [
            ("freedraw", "sidebar.tooltips.freedraw"),
            ("rectangle", "sidebar.tooltips.rectangle"),
            ("circle", "sidebar.tooltips.circle"),
            ("line", "sidebar.tooltips.line"),
            ("text", "sidebar.tooltips.text"),
            ("blur", "sidebar.tooltips.blur"),
            ("arrow", "sidebar.tooltips.arrow"),
            ("highlight", "sidebar.tooltips.highlight"),
            ("selection", "sidebar.tooltips.selection"),
        ]

        for tool_key, tooltip_key in tool_items:
            icon = self.icons.get(tool_key)
            if icon:
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
                tooltip_info = TooltipInfo(btn, tooltip_key, tool_key)
                tooltip_info.update_text(self.language_manager)
                self._add_tooltip(btn, tooltip_info)
                self.buttons[tool_key] = btn
                self.tooltip_infos[tool_key] = tooltip_info

        # Separator - visual divider between tool groups
        # Séparateur - diviseur visuel entre les groupes d'outils
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Color and size picker buttons
        # Boutons de sélection de couleur et de taille
        color_items = [
            (
                "color_picker",
                "sidebar.tooltips.color_picker",
                "choose_annotation_color",
            ),
            (
                "size_picker",
                "sidebar.tooltips.size_picker",
                "choose_annotation_size",
            ),
        ]

        for icon_key, tooltip_key, method_name in color_items:
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
                tooltip_info = TooltipInfo(btn, tooltip_key, icon_key)
                tooltip_info.update_text(self.language_manager)
                self._add_tooltip(btn, tooltip_info)
                self.tooltip_infos[icon_key] = tooltip_info

        # Separator
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Display function buttons - flip and fullscreen
        # Boutons des fonctions d'affichage - retournement et plein écran
        display_items = [
            (
                "flip_horizontal",
                "sidebar.tooltips.flip_horizontal",
                "flip_horizontal",
            ),
            (
                "flip_vertical",
                "sidebar.tooltips.flip_vertical",
                "flip_vertical",
            ),
            (
                "fullscreen",
                "sidebar.tooltips.fullscreen",
                "toggle_fullscreen",
            ),
        ]

        for icon_key, tooltip_key, method_name in display_items:
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
                tooltip_info = TooltipInfo(btn, tooltip_key, icon_key)
                tooltip_info.update_text(self.language_manager)
                self._add_tooltip(btn, tooltip_info)
                self.tooltip_infos[icon_key] = tooltip_info

        # Separator
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # File operation buttons - open and close files
        # Boutons des opérations de fichiers - ouvrir et fermer des fichiers
        file_items = [
            (
                "open_file",
                "sidebar.tooltips.open_file",
                "open_file",
            ),
            (
                "close_file",
                "sidebar.tooltips.close_file",
                "close_file",
            ),
        ]

        for icon_key, tooltip_key, method_name in file_items:
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
                tooltip_info = TooltipInfo(btn, tooltip_key, icon_key)
                tooltip_info.update_text(self.language_manager)
                self._add_tooltip(btn, tooltip_info)
                self.tooltip_infos[icon_key] = tooltip_info

        # Separator
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # Action buttons - undo, redo, save, clear
        # Boutons d'actions - annuler, rétablir, sauvegarder, effacer
        action_items = [
            ("undo", "sidebar.tooltips.undo", "undo_last_annotation"),
            ("redo", "sidebar.tooltips.redo", "redo_last_annotation"),
            ("save", "sidebar.tooltips.save", "save_image"),
            ("clear", "sidebar.tooltips.clear", "clear_all_annotations"),
        ]

        for icon_key, tooltip_key, method_name in action_items:
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
                tooltip_info = TooltipInfo(btn, tooltip_key, icon_key)
                tooltip_info.update_text(self.language_manager)
                self._add_tooltip(btn, tooltip_info)
                self.tooltip_infos[icon_key] = tooltip_info

    # Add tooltip on hover to a widget
    # Ajoute une info-bulle au survol d'un widget
    def _add_tooltip(self, widget, tooltip_info: TooltipInfo):
        """
        Add hover-triggered tooltip functionality to a widget.

        Binds mouse enter and leave events to show and hide a tooltip window
        containing the translated tooltip text for the associated button.

        Args:
            widget: The Tkinter widget to attach tooltip behavior to.
            tooltip_info (TooltipInfo): The TooltipInfo object containing
                the text and translation key for this tooltip.
        """
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
                text=tooltip_info.get_text(),
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

    # Refresh tooltips when language changes
    # Actualise les info-bulles lors du changement de langue
    def refresh_tooltips(self):
        """
        Refresh all tooltip texts with current language translations.

        Iterates through all stored TooltipInfo objects and calls their
        update_text method to retrieve new translations in the current language.
        """
        """Update all tooltip texts based on current language."""
        for tool_key, tooltip_info in self.tooltip_infos.items():
            tooltip_info.update_text(self.language_manager)
