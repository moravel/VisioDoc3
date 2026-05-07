"""Top toolbar with cascading menus for VisioDoc3."""
# Barre d'outils supérieure avec menus en cascade pour VisioDoc3

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Tuple

from ui.language_manager import get_language_manager


# Top toolbar with File, Annotate, View, Export menus and camera selection
# Barre d'outils supérieure avec menus Fichier, Annotations, Affichage et sélection de caméra
class TopToolbar(ttk.Frame):
    # Initializes the top toolbar with menu buttons and camera selector
    # Initialise la barre d'outils supérieure avec les boutons de menu et le sélecteur de caméra
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = (
            app  # Reference to main application / Référence à l'application principale
        )
        self.camera_var = tk.StringVar(
            self
        )  # Camera selection variable / Variable de sélection de caméra
        self.camera_menu = None  # Camera dropdown menu / Menu déroulant de caméra
        self.language_manager = get_language_manager()
        self.menu_buttons = {}  # Store menu buttons for dynamic updates
        self.file_menu = None  # Store menu references for updates
        self.annotate_menu = None
        self.view_menu = None
        self.language_menu = None
        self._build_toolbar()

    # Build menu-style toolbar with File, Annotate, View menus
    # Construit la barre d'outils style menu avec les menus Fichier, Annotations, Affichage
    def _build_toolbar(self):
        # Padding indicator
        # Indicateur d'espacement
        ttk.Label(self, width=2).pack(side=tk.LEFT)

        # File menu - file operations (open, save, close, exit)
        # Menu Fichier - opérations sur les fichiers (ouvrir, sauvegarder, fermer, quitter)
        file_btn = self._create_menu_button(
            self.language_manager.tr("menus.file.label"), self._create_file_menu
        )
        file_btn.pack(side=tk.LEFT, padx=2)
        self.menu_buttons["file"] = file_btn

        # Annotate menu - annotation tools selection
        # Menu Annotations - sélection des outils d'annotation
        annotate_btn = self._create_menu_button(
            self.language_manager.tr("menus.annotations.label"),
            self._create_annotate_menu,
        )
        annotate_btn.pack(side=tk.LEFT, padx=2)
        self.menu_buttons["annotations"] = annotate_btn

        # View menu - display options and settings
        # Menu Affichage - options d'affichage et paramètres
        view_btn = self._create_menu_button(
            self.language_manager.tr("menus.view.label"), self._create_view_menu
        )
        view_btn.pack(side=tk.LEFT, padx=2)
        self.menu_buttons["view"] = view_btn

        # Language menu - language selection
        # Menu Langue - sélection de la langue
        language_btn = self._create_menu_button(
            self.language_manager.tr("menus.language.label"), self._create_language_menu
        )
        language_btn.pack(side=tk.LEFT, padx=2)
        self.menu_buttons["language"] = language_btn

        # Camera selection dropdown (populated when cameras are detected)
        # Sélection de caméra déroulante (remplie lorsque les caméras sont détectées)
        self.camera_btn = ttk.Menubutton(self, text="Webcam")
        self.camera_menu = tk.Menu(self.camera_btn, tearoff=0)
        self.camera_btn["menu"] = self.camera_menu
        self.camera_btn.pack(side=tk.LEFT, padx=2)

        # Spacer to push status to the right
        # Espacement pour pousser le statut à droite
        ttk.Label(self).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Status indicator label
        # Étiquette d'indicateur de statut
        self.status_label = ttk.Label(
            self,
            text="Prêt",
            style="Status.TLabel",
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Exit button - closes the application
        # Bouton Quitter - ferme l'application
        exit_btn = ttk.Button(
            self,
            text="✕",
            style="Icon.TButton",
            command=self.app.on_closing,
            width=3,
        )
        exit_btn.pack(side=tk.RIGHT, padx=2)

    # Create a menu button with the given text and menu factory
    # Crée un bouton de menu avec le texte et la fabrique de menu donnés
    def _create_menu_button(self, text: str, menu_factory: Callable):
        btn = ttk.Menubutton(self, text=text)
        menu = menu_factory(btn)
        btn["menu"] = menu
        return btn

    def refresh_labels(self):
        """
        Refresh all menu button labels with current language translations.

        Updates the text displayed on all menu buttons (File, Annotations, View,
        Language) to reflect the current language settings. Also triggers updates
        to the individual menu contents if they have been created.
        """
        self.menu_buttons["file"].config(
            text=self.language_manager.tr("menus.file.label")
        )
        self.menu_buttons["annotations"].config(
            text=self.language_manager.tr("menus.annotations.label")
        )
        self.menu_buttons["view"].config(
            text=self.language_manager.tr("menus.view.label")
        )
        self.menu_buttons["language"].config(
            text=self.language_manager.tr("menus.language.label")
        )
        if self.file_menu:
            self._update_file_menu()
        if self.annotate_menu:
            self._update_annotate_menu()
        if self.view_menu:
            self._update_view_menu()
        if self.language_menu:
            self._update_language_menu()

    def _create_file_menu(self, parent):
        """
        Create the File menu with file operation options.

        Creates a dropdown menu containing commands for opening, saving,
        closing files, and exiting the application. The menu items are
        populated with language-specific labels.

        Args:
            parent: The parent widget (Menubutton) that owns this menu.

        Returns:
            tk.Menu: The configured menu widget.
        """
        self.file_menu = tk.Menu(parent, tearoff=0)
        self._update_file_menu()
        return self.file_menu

    def _update_file_menu(self):
        """
        Update the File menu contents with current language translations.

        Repopulates the File menu with translated labels for open, save,
        close, and exit commands based on the current language setting.
        """
        self.file_menu.delete(0, tk.END)
        lm = self.language_manager
        self.file_menu.add_command(
            label=f"{lm.tr('menus.file.open')} (Ctrl+O)", command=self.app.open_file
        )
        self.file_menu.add_command(
            label=f"{lm.tr('menus.file.save')} (Ctrl+Shift+S)",
            command=self.app.save_image,
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label=lm.tr("menus.file.close"), command=self.app.close_file
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label=lm.tr("menus.file.exit"), command=self.app.on_closing
        )

    # Create Annotations menu with all annotation tool options
    # Crée le menu Annotations avec toutes les options d'outils d'annotation
    def _create_annotate_menu(self, parent):
        """
        Create the Annotations menu with annotation tool shortcuts.

        Creates a dropdown menu containing commands for all annotation tools
        (freedraw, rectangle, circle, line, text, blur, arrow, highlight,
        selection, color picker, size picker) with keyboard shortcut hints.

        Args:
            parent: The parent widget (Menubutton) that owns this menu.

        Returns:
            tk.Menu: The configured menu widget.
        """
        self.annotate_menu = tk.Menu(parent, tearoff=0)
        self._update_annotate_menu()
        return self.annotate_menu

    def _update_annotate_menu(self):
        """
        Update the Annotations menu contents with current language translations.

        Repopulates the menu with translated labels for all annotation tools,
        including keyboard shortcut hints that match the actual shortcuts.
        """
        self.annotate_menu.delete(0, tk.END)
        lm = self.language_manager
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.freedraw.name')} (Ctrl+F)",
            command=lambda: self.app.set_tool("freedraw"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.rectangle.name')} (Ctrl+R)",
            command=lambda: self.app.set_tool("rectangle"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.circle.name')} (Ctrl+C)",
            command=lambda: self.app.set_tool("circle"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.line.name')} (Ctrl+L)",
            command=lambda: self.app.set_tool("line"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.text.name')} (Ctrl+T)",
            command=lambda: self.app.set_tool("text"),
        )
        self.annotate_menu.add_separator()
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.arrow.name')} (Ctrl+A)",
            command=lambda: self.app.set_tool("arrow"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.highlight.name')} (Ctrl+H)",
            command=lambda: self.app.set_tool("highlight"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.blur.name')} (Ctrl+B)",
            command=lambda: self.app.set_tool("blur"),
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.selection.name')} (Ctrl+S)",
            command=lambda: self.app.set_tool("selection"),
        )
        self.annotate_menu.add_separator()
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.color_picker.name')} (Ctrl+K)",
            command=self.app.choose_annotation_color,
        )
        self.annotate_menu.add_command(
            label=f"{lm.tr('tools.size_picker.name')} (Ctrl+I)",
            command=self.app.choose_annotation_size,
        )

    # Create View menu with zoom, flip, fullscreen, and settings options
    # Crée le menu Affichage avec les options zoom, retournement, plein écran et paramètres
    def _create_view_menu(self, parent):
        """
        Create the View menu with display options.

        Creates a dropdown menu containing commands for zoom in/out, flip
        horizontal/vertical, fullscreen toggle, and settings dialog.

        Args:
            parent: The parent widget (Menubutton) that owns this menu.

        Returns:
            tk.Menu: The configured menu widget.
        """
        self.view_menu = tk.Menu(parent, tearoff=0)
        self._update_view_menu()
        return self.view_menu

    def _update_view_menu(self):
        """
        Update the View menu contents with current language translations.

        Repopulates the menu with translated labels for zoom, flip, fullscreen,
        and settings commands.
        """
        self.view_menu.delete(0, tk.END)
        lm = self.language_manager
        self.view_menu.add_command(
            label=f"{lm.tr('view.zoom_in')} (Ctrl++)", command=self.app.zoom_in
        )
        self.view_menu.add_command(
            label=f"{lm.tr('view.zoom_out')} (Ctrl+-)", command=self.app.zoom_out
        )
        self.view_menu.add_separator()
        self.view_menu.add_command(
            label=f"{lm.tr('view.flip_horizontal')} (Ctrl+J)",
            command=self.app.flip_horizontal,
        )
        self.view_menu.add_command(
            label=f"{lm.tr('view.flip_vertical')} (Ctrl+U)",
            command=self.app.flip_vertical,
        )
        self.view_menu.add_separator()
        self.view_menu.add_command(
            label=f"{lm.tr('view.fullscreen')} (F11)",
            command=self.app.toggle_fullscreen,
        )
        self.view_menu.add_command(
            label=f"{lm.tr('view.settings')} (Ctrl+P)",
            command=self.app.open_settings_dialog,
        )

    # Create Language menu with language options
    # Crée le menu Langue avec les options de langue
    def _create_language_menu(self, parent):
        """
        Create the Language menu with language selection options.

        Creates a dropdown menu containing commands to switch between
        available languages (French and English).

        Args:
            parent: The parent widget (Menubutton) that owns this menu.

        Returns:
            tk.Menu: The configured menu widget.
        """
        self.language_menu = tk.Menu(parent, tearoff=0)
        self._update_language_menu()
        return self.language_menu

    def _update_language_menu(self):
        """
        Update the Language menu contents with current language translations.

        Repopulates the menu with translated labels for French and English
        language selection options.
        """
        self.language_menu.delete(0, tk.END)
        lm = self.language_manager
        self.language_menu.add_command(
            label=lm.tr("menus.language.french"),
            command=lambda: self._change_language("fr"),
        )
        self.language_menu.add_command(
            label=lm.tr("menus.language.english"),
            command=lambda: self._change_language("en"),
        )

    # Change language and refresh UI
    # Change la langue et rafraîchit l'interface
    def _change_language(self, lang_code: str):
        """
        Change the application language and refresh the UI.

        Switches the language manager to the specified language code and
        triggers a refresh of all UI components to display translated text.

        Args:
            lang_code (str): The language code to switch to ('en' or 'fr').
        """
        if self.language_manager.set_language(lang_code):
            self.refresh_labels()
            if hasattr(self.app, "on_language_change"):
                self.app.on_language_change()

    # Update camera menu with available cameras
    # Met à jour le menu de caméra avec les caméras disponibles
    def update_cameras(self, camera_options: List[Tuple[str, int]]):
        """
        Update the camera dropdown menu with available camera devices.

        Repopulates the webcam dropdown with the list of detected cameras,
        sorted by index for consistent ordering. Displays a disabled
        "No cameras found" message if the list is empty.

        Args:
            camera_options (List[Tuple[str, int]]): List of tuples
                containing (camera_name, camera_index) for each detected camera.
        """
        if self.camera_menu:
            self.camera_menu.delete(0, tk.END)

        if camera_options:
            # Sort cameras by index for consistent ordering
            # Trie les caméras par index pour un ordre cohérent
            camera_options = sorted(camera_options, key=lambda x: x[1])
            for name, index in camera_options:
                self.camera_menu.add_command(
                    label=name,
                    command=lambda i=index: self.app.select_camera_by_index(i),
                )
            self.camera_btn.config(text="Webcam")
        else:
            self.camera_menu.add_command(
                label=self.language_manager.tr("dialogs.no_cameras"), state="disabled"
            )
            self.camera_btn.config(text="Webcam")

    # Update status text displayed in the toolbar
    # Met à jour le texte de statut affiché dans la barre d'outils
    def update_status(self, text: str):
        """
        Update the status text displayed in the top toolbar.

        Displays a brief status message in the right side of the toolbar
        to provide user feedback about current operations or state.

        Args:
            text (str): The status message to display.
        """
        self.status_label.config(text=text)
