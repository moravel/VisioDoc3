"""Top toolbar with cascading menus for VisioDoc3."""
# Barre d'outils supérieure avec menus en cascade pour VisioDoc3

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Tuple


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
        self._build_toolbar()

    # Build menu-style toolbar with File, Annotate, View menus
    # Construit la barre d'outils style menu avec les menus Fichier, Annotations, Affichage
    def _build_toolbar(self):
        # Padding indicator
        # Indicateur d'espacement
        ttk.Label(self, width=2).pack(side=tk.LEFT)

        # File menu - file operations (open, save, close, exit)
        # Menu Fichier - opérations sur les fichiers (ouvrir, sauvegarder, fermer, quitter)
        file_btn = self._create_menu_button("Fichier", self._create_file_menu)
        file_btn.pack(side=tk.LEFT, padx=2)

        # Annotate menu - annotation tools selection
        # Menu Annotations - sélection des outils d'annotation
        annotate_btn = self._create_menu_button(
            "Annotations", self._create_annotate_menu
        )
        annotate_btn.pack(side=tk.LEFT, padx=2)

        # View menu - display options and settings
        # Menu Affichage - options d'affichage et paramètres
        view_btn = self._create_menu_button("Affichage", self._create_view_menu)
        view_btn.pack(side=tk.LEFT, padx=2)

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

    # Create File menu with open, save, close, and exit options
    # Crée le menu Fichier avec les options ouvrir, sauvegarder, fermer et quitter
    def _create_file_menu(self, parent):
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

    # Create Annotations menu with all annotation tool options
    # Crée le menu Annotations avec toutes les options d'outils d'annotation
    def _create_annotate_menu(self, parent):
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

    # Create View menu with zoom, flip, fullscreen, and settings options
    # Crée le menu Affichage avec les options zoom, retournement, plein écran et paramètres
    def _create_view_menu(self, parent):
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

    # Update camera menu with available cameras
    # Met à jour le menu de caméra avec les caméras disponibles
    def update_cameras(self, camera_options: List[Tuple[str, int]]):
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
                label="Aucune webcam trouvée", state="disabled"
            )
            self.camera_btn.config(text="Webcam")

    # Update status text displayed in the toolbar
    # Met à jour le texte de statut affiché dans la barre d'outils
    def update_status(self, text: str):
        self.status_label.config(text=text)
