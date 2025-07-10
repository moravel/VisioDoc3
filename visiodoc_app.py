import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import datetime
import os
import sys # Import sys module for executable path / Importe le module sys pour le chemin de l'exécutable
import threading
import time
import json # Import json for config file handling / Importe json pour la gestion des fichiers de configuration
import pyi_splash # Import pyi_splash for PyInstaller splash screen control / Importe pyi_splash pour le contrôle de l'écran de démarrage de PyInstaller
import platform

# Conditional import for Windows-specific camera enumeration
# Importation conditionnelle pour l'énumération des caméras spécifique à Windows
if platform.system() == "Windows":
    try:
        from pygrabber.dshow_graph import DSShow
    except ImportError:
        DSShow = None # Set to None if pygrabber is not available / Définit à Aucun si pygrabber n'est pas disponible

import fitz  # PyMuPDF for PDF handling / PyMuPDF pour la gestion des PDF

# Import custom annotation classes
# Importe les classes d'annotation personnalisées
from annotations import LineAnnotation, RectangleAnnotation, CircleAnnotation, FreeDrawAnnotation, TextAnnotation, BlurAnnotation, ArrowAnnotation, HighlightAnnotation
from tooltip import Tooltip # Import Tooltip class for hover help / Importe la classe Tooltip pour l'aide au survol
from video_stream import VideoStreamThread # Import VideoStreamThread for camera handling / Importe VideoStreamThread pour la gestion de la caméra

# Main application class for VisioDoc3
# Classe principale de l'application pour VisioDoc3
class VisioDoc3(tk.Tk):
    # Directory where icons are stored, relative to the script's location
    # Répertoire où les icônes sont stockées, relatif à l'emplacement du script
    ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
    # Configuration file path for camera settings (placed next to the executable in PyInstaller builds)
    # Chemin du fichier de configuration pour les paramètres de la caméra (placé à côté de l'exécutable dans les builds PyInstaller)
    CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "camera_config.json"))

    def __init__(self):
        """
        Initializes the VisioDoc3 application window and its components.
        Initialise la fenêtre de l'application VisioDoc3 et ses composants.
        """
        super().__init__()
        self.title("VisioDoc3 - Visionneuse de Documents") # Set window title / Définit le titre de la fenêtre
        
        # Get screen dimensions and set window geometry to full screen
        # Obtient les dimensions de l'écran et définit la géométrie de la fenêtre en plein écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}")
        self.configure(bg='white') # Set main window background to white / Définit l'arrière-plan de la fenêtre principale en blanc

        # Configure style for a consistent white theme across ttk widgets
        # Configure le style pour un thème blanc cohérent sur les widgets ttk
        style = ttk.Style()
        style.theme_use('clam') # Use clam theme as a base for better customization / Utilise le thème clam comme base pour une meilleure personnalisation
        style.configure('White.TFrame', background='white')
        style.configure('White.TButton', background='white', foreground='black', borderwidth=1, relief="solid")
        style.map('White.TButton', background=[('active', '#e0e0e0'), ('pressed', '#d0d0d0')]) # Lighter white on hover, slightly darker on press / Blanc plus clair au survol, légèrement plus foncé à la pression
        style.configure('White.TLabel', background='white', foreground='black')
        style.configure('White.TMenubutton', background='white', foreground='black', borderwidth=1, relief="solid")
        style.map('White.TMenubutton', background=[('active', '#e0e0e0'), ('pressed', '#d0d0d0')])
        style.configure('White.Horizontal.TScale', background='white', troughcolor='#e0e0e0')

        # Default resolution for the camera stream
        # Résolution par défaut pour le flux de la caméra
        self.current_resolution = (1280, 720)

        # Video stream and image display variables
        # Variables de flux vidéo et d'affichage d'image
        self.video_stream_thread = None # Thread managing camera capture / Fil gérant la capture de la caméra
        self.current_photo = None # PhotoImage object for displaying on Tkinter label / Objet PhotoImage pour l'affichage sur l'étiquette Tkinter
        self.annotations = [] # List to store all annotation objects / Liste pour stocker tous les objets d'annotation
        self.undo_stack = [] # Stack for storing undone annotations for redo functionality / Pile pour stocker les annotations annulées pour la fonctionnalité de rétablissement
        self.redo_stack = [] # Stack for storing annotations that can be redone / Pile pour stocker les annotations qui peuvent être rétablies
        
        # Annotation tool state variables
        # Variables d'état de l'outil d'annotation
        self.current_tool = "none" # Current active tool (e.g., "line", "rectangle", "text") / Outil actif actuel (par exemple, "line", "rectangle", "text")
        self.start_point = None # Starting point for drawing operations / Point de départ pour les opérations de dessin
        self.end_point = None # Ending point for drawing operations / Point de fin pour les opérations de dessin
        self.drawing = False # Flag indicating if a drawing operation is in progress / Drapeau indiquant si une opération de dessin est en cours
        self.current_freedraw_points = [] # List of points for freehand drawing / Liste de points pour le dessin à main levée
        self.current_annotation_color = (0, 0, 255) # Default annotation color (BGR for OpenCV: Blue) / Couleur d'annotation par défaut (BGR pour OpenCV : Bleu)
        self.current_annotation_thickness = 2 # Default thickness for lines and borders / Épaisseur par défaut pour les lignes et les bordures
        self.current_font_size = 20 # Default font size for text annotations / Taille de police par défaut pour les annotations de texte
        self.selected_annotation = None # The annotation currently selected for manipulation / L'annotation actuellement sélectionnée pour la manipulation
        self.hovered_annotation = None # The annotation currently under the mouse cursor / L'annotation actuellement sous le curseur de la souris
        self.resize_handle = None # The specific resize handle being dragged / La poignée de redimensionnement spécifique en cours de glissement

        # File mode variables (for image and PDF viewing)
        # Variables du mode fichier (pour la visualisation d'images et de PDF)
        self.file_mode = False # True if an image/PDF file is loaded, False for webcam / Vrai si un fichier image/PDF est chargé, Faux pour la webcam
        self.loaded_image = None # PIL Image object of the loaded file / Objet PIL Image du fichier chargé
        self.pdf_document = None # PyMuPDF document object for PDFs / Objet document PyMuPDF pour les PDF
        self.pdf_pages = [] # List of PDF page objects / Liste d'objets de page PDF
        self.current_pdf_page = 0 # Current page number for PDF documents / Numéro de page actuel pour les documents PDF

        # Zoom and Pan state variables
        # Variables d'état de zoom et de panoramique
        self.zoom_level = 1.0 # Current zoom level (1.0 is original size) / Niveau de zoom actuel (1.0 est la taille originale)
        self.view_offset_x = 0 # X-offset for panning / Décalage X pour le panoramique
        self.view_offset_y = 0 # Y-offset for panning / Décalage Y pour le panoramique
        self.pan_start_x = 0 # Starting X-coordinate for pan operation / Coordonnée X de départ pour l'opération de panoramique
        self.pan_start_y = 0 # Starting Y-coordinate for pan operation / Coordonnée Y de départ pour l'opération de panoramique
        self.is_panning = False # Flag indicating if panning is in progress / Drapeau indiquant si le panoramique est en cours
        self.view_for_saving = None # The final rendered image ready for saving / L'image finale rendue prête à être sauvegardée

        # Main layout frame setup
        # Configuration du cadre de mise en page principal
        self.main_frame = ttk.Frame(self, style='White.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure grid weights for responsive layout
        # Configure les poids de la grille pour une mise en page réactive
        self.main_frame.grid_columnconfigure(0, weight=0) # Left panel (fixed width) / Panneau gauche (largeur fixe)
        self.main_frame.grid_columnconfigure(1, weight=1) # Video area (expands) / Zone vidéo (s'étend)
        self.main_frame.grid_columnconfigure(2, weight=0) # Right panel (fixed width) / Panneau droit (largeur fixe)
        self.main_frame.grid_rowconfigure(0, weight=1) # Main row (expands vertically) / Ligne principale (s'étend verticalement)

        # Left Panel (Annotation Tools) setup
        # Configuration du panneau gauche (Outils d'annotation)
        self.left_panel = ttk.Frame(self.main_frame, width=150, style='White.TFrame')
        self.left_panel.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        self.left_panel.grid_propagate(False) # Prevent frame from resizing to content / Empêche le cadre de se redimensionner au contenu

        # Load icons for buttons
        # Charge les icônes pour les boutons
        self.icons = {}
        self._load_icons()

        # Create and pack annotation tool buttons with tooltips
        # Crée et emballe les boutons d'outils d'annotation avec des info-bulles
        ttk.Button(self.left_panel, text="Dessin Main Levée", image=self.icons.get("freedraw"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("freedraw")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil de dessin à main levée (Ctrl+F)")
        ttk.Button(self.left_panel, text="Rectangle", image=self.icons.get("rectangle"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("rectangle")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil rectangle (Ctrl+R)")
        ttk.Button(self.left_panel, text="Cercle", image=self.icons.get("circle"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("circle")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil cercle (Ctrl+C)")
        ttk.Button(self.left_panel, text="Ligne", image=self.icons.get("line"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("line")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil ligne (Ctrl+L)")
        ttk.Button(self.left_panel, text="Ajouter Texte", image=self.icons.get("text"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("text")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil texte (Ctrl+T)")
        ttk.Button(self.left_panel, text="Zone de Flou", image=self.icons.get("blur"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("blur")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil de flou (Ctrl+B)")
        ttk.Button(self.left_panel, text="Flèche", image=self.icons.get("arrow"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("arrow")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil flèche (Ctrl+A)")
        ttk.Button(self.left_panel, text="Surlignage", image=self.icons.get("highlight"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("highlight")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil surlignage (Ctrl+H)")
        ttk.Button(self.left_panel, text="Sélection", image=self.icons.get("selection"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("selection")).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Active l'outil de sélection (Ctrl+S)")
        ttk.Button(self.left_panel, text="Choisir Couleur", image=self.icons.get("color_picker"), compound=tk.LEFT, style='White.TButton', command=self.choose_annotation_color).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Ouvre la palette de couleurs (Ctrl+K)")
        ttk.Button(self.left_panel, text="Choisir Taille", image=self.icons.get("size_picker"), compound=tk.LEFT, style='White.TButton', command=self.choose_annotation_size).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Ouvre le sélecteur de taille (Ctrl+I)")
        
ttk.Button(self.left_panel, text="Flip Horizontal", image=self.icons.get("flip_horizontal"), compound=tk.LEFT, style='White.TButton', command=self.flip_horizontal).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Retournement horizontal de l'image (Ctrl+J)")
        ttk.Button(self.left_panel, text="Flip Vertical", image=self.icons.get("flip_vertical"), compound=tk.LEFT, style='White.TButton', command=self.flip_vertical).pack(fill=tk.X, pady=2)
        Tooltip(self.left_panel.winfo_children()[-1], "Retournement vertical de l'image (Ctrl+U)")

        # Separator and zoom controls
        # Séparateur et contrôles de zoom
        ttk.Separator(self.left_panel, orient='horizontal').pack(fill='x', pady=10, padx=5)
        zoom_frame = ttk.Frame(self.left_panel, style='White.TFrame')
        zoom_frame.pack(fill=tk.X, pady=2)
        ttk.Label(zoom_frame, text="Zoom:", style='White.TLabel').pack(side=tk.LEFT, padx=5)
        zoom_in_button = ttk.Button(zoom_frame, text="+ 개발", style='White.TButton', command=self.zoom_in, width=3)
        zoom_in_button.pack(side=tk.LEFT)
        Tooltip(zoom_in_button, "Zoom avant (Ctrl++)")
        zoom_out_button = ttk.Button(zoom_frame, text="- 개발", style='White.TButton', command=self.zoom_out, width=3)
        zoom_out_button.pack(side=tk.LEFT)
        Tooltip(zoom_out_button, "Zoom arrière (Ctrl+-)")

        # Video Display Area setup
        # Configuration de la zone d'affichage vidéo
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ttk.Label(self.video_frame) # Label to display video frames or images / Étiquette pour afficher les cadres vidéo ou les images
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Display a placeholder image while camera is loading
        # Affiche une image de remplacement pendant le chargement de la caméra
        self.placeholder_image = Image.new('RGB', (self.current_resolution[0], self.current_resolution[1]), (50, 50, 50)) # Dark grey background / Fond gris foncé
        draw = ImageDraw.Draw(self.placeholder_image)
        text = "Chargement de la caméra..."
        text_color = (200, 200, 200) # Light grey text / Texte gris clair
        try:
            font = ImageFont.truetype("arial.ttf", 30) # Use a common font / Utilise une police courante
        except IOError:
            font = ImageFont.load_default() # Fallback to default font if not found / Repli sur la police par défaut si non trouvée
        
        # Calculate text position to center it
        # Calcule la position du texte pour le centrer
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (self.current_resolution[0] - text_width) // 2
        text_y = (self.current_resolution[1] - text_height) // 2
        draw.text((text_x, text_y), text, font=font, fill=text_color)
        self.current_photo = ImageTk.PhotoImage(self.placeholder_image)
        self.image_label.config(image=self.current_photo)

        # Bind mouse events for drawing, selection, zoom, and pan
        # Lie les événements de la souris pour le dessin, la sélection, le zoom et le panoramique
        self.image_label.bind("<Button-1>", self.on_mouse_down) # Left click / Clic gauche
        self.image_label.bind("<B1-Motion>", self.on_mouse_drag) # Left click drag / Glisser-déposer avec le clic gauche
        self.image_label.bind("<ButtonRelease-1>", self.on_mouse_up) # Left click release / Relâchement du clic gauche
        self.image_label.bind("<Motion>", self.on_mouse_move) # Mouse movement / Mouvement de la souris
        self.image_label.bind("<MouseWheel>", self.on_mouse_wheel) # Mouse wheel for Windows/macOS / Molette de la souris pour Windows/macOS
        self.image_label.bind("<Button-4>", self.on_mouse_wheel) # Mouse wheel up for Linux / Molette de la souris vers le haut pour Linux
        self.image_label.bind("<Button-5>", self.on_mouse_wheel) # Mouse wheel down for Linux / Molette de la souris vers le bas pour Linux
        self.image_label.bind("<Button-2>", self.on_pan_start) # Middle mouse button for pan start / Bouton central de la souris pour le début du panoramique
        self.image_label.bind("<B2-Motion>", self.on_pan_move) # Middle mouse button drag for pan / Glisser-déposer avec le bouton central de la souris pour le panoramique
        self.image_label.bind("<ButtonRelease-2>", self.on_pan_end) # Middle mouse button release for pan end / Relâchement du bouton central de la souris pour la fin du panoramique

        # Camera and PDF Controls frame
        # Cadre des contrôles de la caméra et du PDF
        self.controls_frame = ttk.Frame(self.video_frame)
        self.controls_frame.grid(row=1, column=0, pady=5)

        # Camera selection UI
        # Interface utilisateur de sélection de la caméra
        self.camera_selection_frame = ttk.Frame(self.controls_frame)
        self.camera_selection_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(self.camera_selection_frame, text="Sélectionner Webcam:").pack(side=tk.LEFT, padx=5)
        self.camera_var = tk.StringVar(self) # Variable to hold selected camera name / Variable pour contenir le nom de la caméra sélectionnée
        self.camera_options = [] # List to store available camera options / Liste pour stocker les options de caméra disponibles
        self.camera_menu_placeholder = ttk.Label(self.camera_selection_frame, text="Recherche de caméras en cours...")
        self.camera_menu_placeholder.pack(side=tk.LEFT)
        
        # PDF navigation UI (initially hidden)
        # Interface utilisateur de navigation PDF (initialement masquée)
        self.pdf_navigation_frame = ttk.Frame(self.controls_frame)
        self.pdf_navigation_frame.pack(side=tk.LEFT, padx=10)
        self.prev_page_button = ttk.Button(self.pdf_navigation_frame, text="< 개발", command=self.prev_pdf_page, width=3)
        self.page_label = ttk.Label(self.pdf_navigation_frame, text="")
        self.next_page_button = ttk.Button(self.pdf_navigation_frame, text="> 개발", command=self.next_pdf_page, width=3)

        # Start a separate thread to initialize camera (prevents UI freeze)
        # Démarre un fil séparé pour initialiser la caméra (empêche le gel de l'interface utilisateur)
        self.camera_population_thread = threading.Thread(target=self._initialize_camera, daemon=True)
        self.camera_population_thread.start()

        # Right Panel (Action Buttons) setup
        # Configuration du panneau droit (Boutons d'action)
        self.right_panel = ttk.Frame(self.main_frame, width=150, style='White.TFrame')
        self.right_panel.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        self.right_panel.grid_propagate(False) # Prevent frame from resizing / Empêche le cadre de se redimensionner

        # Create and pack action buttons with tooltips
        # Crée et emballe les boutons d'action avec des info-bulles
        open_file_button = ttk.Button(self.right_panel, text="Ouvrir Fichier", image=self.icons.get("open_file"), compound=tk.LEFT, style='White.TButton', command=self.open_file)
        open_file_button.pack(fill=tk.X, pady=2)
        Tooltip(open_file_button, "Ouvre un fichier image ou PDF (Ctrl+O)")
        close_file_button = ttk.Button(self.right_panel, text="Fermer Fichier", image=self.icons.get("close_file"), compound=tk.LEFT, style='White.TButton', command=self.close_file)
        close_file_button.pack(fill=tk.X, pady=2)
        Tooltip(close_file_button, "Ferme le fichier et réactive la webcam")

        save_button = ttk.Button(self.right_panel, text="Sauvegarder", image=self.icons.get("save"), compound=tk.LEFT, style='White.TButton', command=self.save_image)
        save_button.pack(fill=tk.X, pady=2)
        Tooltip(save_button, "Sauvegarde l'image actuelle (Ctrl+Shift+S)")
        clear_button = ttk.Button(self.right_panel, text="Effacer Tout", image=self.icons.get("clear"), compound=tk.LEFT, style='White.TButton', command=self.clear_all_annotations)
        clear_button.pack(fill=tk.X, pady=2)
        Tooltip(clear_button, "Efface toutes les annotations (Ctrl+E)")
        undo_button = ttk.Button(self.right_panel, text="Annuler (Undo)", image=self.icons.get("undo"), compound=tk.LEFT, style='White.TButton', command=self.undo_last_annotation)
        undo_button.pack(fill=tk.X, pady=2)
        Tooltip(undo_button, "Annule la dernière action (Ctrl+Z)")
        redo_button = ttk.Button(self.right_panel, text="Rétablir (Redo)", image=self.icons.get("redo"), compound=tk.LEFT, style='White.TButton', command=self.redo_last_annotation)
        redo_button.pack(fill=tk.X, pady=2)
        Tooltip(redo_button, "Rétablit la dernière action annulée (Ctrl+Y)")
        delete_button = ttk.Button(self.right_panel, text="Supprimer", image=self.icons.get("delete"), compound=tk.LEFT, style='White.TButton', command=self.delete_selected_annotation)
        delete_button.pack(fill=tk.X, pady=2)
        Tooltip(delete_button, "Supprime l'annotation sélectionnée (Suppr)")
        settings_button = ttk.Button(self.right_panel, text="Paramètres", image=self.icons.get("settings"), compound=tk.LEFT, style='White.TButton', command=self.open_settings_dialog)
        settings_button.pack(fill=tk.X, pady=2)
        Tooltip(settings_button, "Ouvre les paramètres de la caméra (Ctrl+P)")

        help_button = ttk.Button(self.right_panel, text="Aide", image=self.icons.get("help"), compound=tk.LEFT, style='White.TButton', command=self.show_help)
        help_button.pack(fill=tk.X, pady=2)
        Tooltip(help_button, "Ouvre le manuel d'utilisation (Ctrl+?)")

        # Add application logo to the bottom of the right panel
        # Ajoute le logo de l'application en bas du panneau droit
        self.logo_photo = self.icons.get("logo") # Store a reference to prevent garbage collection / Stocke une référence pour éviter la suppression par le ramasse-miettes
        logo_label = ttk.Label(self.right_panel, image=self.logo_photo, background='white')
        logo_label.pack(side=tk.BOTTOM, pady=10)

        # Bind Delete key for deleting selected annotations
        # Lie la touche Suppr pour supprimer les annotations sélectionnées
        self.bind("<Delete>", self.delete_selected_annotation)
        
        # Keyboard Shortcuts for various actions and tools
        # Raccourcis clavier pour diverses actions et outils
        self.bind("<Control-o>", lambda event: self.open_file()) # Open file / Ouvrir fichier
        self.bind("<Control-f>", lambda event: self.set_tool("freedraw")) # Freehand draw tool / Outil de dessin à main levée
        self.bind("<Control-r>", lambda event: self.set_tool("rectangle")) # Rectangle tool / Outil rectangle
        self.bind("<Control-c>", lambda event: self.set_tool("circle")) # Circle tool / Outil cercle
        self.bind("<Control-l>", lambda event: self.set_tool("line")) # Line tool / Outil ligne
        self.bind("<Control-t>", lambda event: self.set_tool("text")) # Text tool / Outil texte
        self.bind("<Control-b>", lambda event: self.set_tool("blur")) # Blur tool / Outil de flou
        self.bind("<Control-a>", lambda event: self.set_tool("arrow")) # Arrow tool / Outil flèche
        self.bind("<Control-h>", lambda event: self.set_tool("highlight")) # Highlight tool / Outil surlignage
        self.bind("<Control-s>", lambda event: self.set_tool("selection")) # Selection tool / Outil de sélection
        
        self.bind("<Control-Shift-S>", lambda event: self.save_image()) # Save image / Sauvegarder l'image
        self.bind("<Control-e>", lambda event: self.clear_all_annotations()) # Clear all annotations / Effacer toutes les annotations
        self.bind("<Control-z>", lambda event: self.undo_last_annotation()) # Undo last action / Annuler la dernière action
        self.bind("<Control-y>", lambda event: self.redo_last_annotation()) # Redo last undone action / Rétablir la dernière action annulée
        self.bind("<Control-p>", lambda event: self.open_settings_dialog()) # Open settings dialog / Ouvrir la boîte de dialogue des paramètres
        
        self.bind("<Control-plus>", self.zoom_in) # Zoom in / Zoom avant
        self.bind("<Control-equal>", self.zoom_in) # Zoom in (alternative for some keyboards) / Zoom avant (alternative pour certains claviers)
        self.bind("<Control-minus>", self.zoom_out) # Zoom out / Zoom arrière

        self.bind("<Control-k>", lambda event: self.choose_annotation_color()) # Choose annotation color / Choisir la couleur de l'annotation
        self.bind("<Control-i>", lambda event: self.choose_annotation_size()) # Choose annotation size / Choisir la taille de l'annotation
        self.bind("<Control-j>", lambda event: self.flip_horizontal()) # Flip image horizontally / Retourner l'image horizontalement
        self.bind("<Control-u>", lambda event: self.flip_vertical()) # Flip image vertically / Retourner l'image verticalement

        self.bind("<Control-question>", lambda event: self.show_help()) # Show help manual / Afficher le manuel d'aide

        # Protocol for handling window closing event
        # Protocole pour la gestion de l'événement de fermeture de fenêtre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start updating the display (main loop for rendering)
        # Commence la mise à jour de l'affichage (boucle principale pour le rendu)
        self.update_display()
        
        # Close PyInstaller splash screen if it's active
        # Ferme l'écran de démarrage de PyInstaller s'il est actif
        if pyi_splash.is_alive():
            pyi_splash.close()

    def _load_icons(self):
        """
        Loads all application icons from the ICON_DIR.
        Charge toutes les icônes de l'application depuis ICON_DIR.
        """
        icon_names = {
            "freedraw": "freedraw.png", "rectangle": "rectangle.png",
            "circle": "circle.png", "line": "line.png",
            "text": "text.png", "blur": "blur.png",
            "arrow": "arrow.png", "highlight": "highlight.png",
            "color_picker": "color_picker.png", "size_picker": "size_picker.png",
            "save": "save.png", "clear": "clear.png",
            "undo": "undo.png", "redo": "redo.png",
            "settings": "settings.png", "logo": "logoVisioDoc3.png",
            "selection": "selection.png", "delete": "delete.png",
            "help": "help.png", "open_file": "open_file.png",
            "close_file": "close_file.png", "flip_horizontal": "flip_horizontal.png",
            "flip_vertical": "flip_vertical.png"
        }
        for name, filename in icon_names.items():
            try:
                path = os.path.join(self.ICON_DIR, filename)
                img = Image.open(path)
                img = img.resize((16, 16), Image.LANCZOS) # Resize icons to 16x16 for buttons / Redimensionne les icônes à 16x16 pour les boutons
                self.icons[name] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Warning: Icon file not found: {filename}")
                # Create a simple placeholder image if the icon is not found, especially for help icon
                # Crée une image de remplacement simple si l'icône n'est pas trouvée, en particulier pour l'icône d'aide
                if name == "help":
                    placeholder_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0)) # Transparent background / Fond transparent
                    draw = ImageDraw.Draw(placeholder_img)
                    draw.text((0, 0), "?", fill=(0, 0, 0)) # Black question mark / Point d'interrogation noir
                    self.icons[name] = ImageTk.PhotoImage(placeholder_img)
                else:
                    self.icons[name] = None # Set to None if not found / Définit à Aucun si non trouvé
            except Exception as e:
                print(f"Error loading icon {filename}: {e}")
                # Fallback for other errors during icon loading
                # Repli pour d'autres erreurs lors du chargement des icônes
                if name == "help":
                    placeholder_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0)) # Transparent background / Fond transparent
                    draw = ImageDraw.Draw(placeholder_img)
                    draw.text((0, 0), "?", fill=(0, 0, 0)) # Black question mark / Point d'interrogation noir
                    self.icons[name] = ImageTk.PhotoImage(placeholder_img)
                else:
                    self.icons[name] = None # Set to None if not found / Définit à Aucun si non trouvé
        
        # Special handling for the logo to make it larger and fit the panel
        # Traitement spécial pour le logo afin de le rendre plus grand et de l'adapter au panneau
        try:
            path = os.path.join(self.ICON_DIR, "logoVisioDoc3.png")
            img = Image.open(path)
            base_width = 140 # Desired width with some padding / Largeur souhaitée avec un certain rembourrage
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent))) # Calculate height to maintain aspect ratio / Calcule la hauteur pour maintenir le rapport d'aspect
            img = img.resize((base_width, h_size), Image.LANCZOS)
            self.icons["logo"] = ImageTk.PhotoImage(img)
        except FileNotFoundError:
            print(f"Warning: Icon file not found: logoVisioDoc3.png")
            self.icons["logo"] = None

    def show_help(self):
        """
        Displays the user manual in a new Toplevel window.
        Affiche le manuel d'utilisation dans une nouvelle fenêtre Toplevel.
        """
        help_dialog = tk.Toplevel(self)
        help_dialog.title("Manuel d'Utilisateur VisioDoc3")
        help_dialog.transient(self) # Make it transient to the main window / Le rend transitoire à la fenêtre principale
        help_dialog.grab_set() # Make it modal (blocks interaction with main window) / Le rend modal (bloque l'interaction avec la fenêtre principale)

        # Content of the user manual (multiline string)
        # Contenu du manuel d'utilisation (chaîne de caractères multiligne)
        manual_content = """
# Manuel d'Utilisateur VisioDoc3

## Introduction

VisioDoc3 est une application intuitive conçue pour la visualisation de flux vidéo en temps réel provenant de votre webcam, avec des capacités d'annotation avancées. Que vous ayez besoin de mettre en évidence des détails, d'ajouter des notes ou de flouter des informations sensibles, VisioDoc3 offre une suite complète d'outils pour améliorer votre expérience de capture et de manipulation d'images.

## Interface Utilisateur

L'interface de VisioDoc3 est divisée en trois sections principales :

1.  **Panneau Gauche (Outils d'Annotation) :** Contient tous les outils de dessin et de modification, ainsi que les contrôles de zoom.
2.  **Zone d'Affichage Vidéo :** Affiche le flux en direct de la webcam et les annotations appliquées.
3.  **Panneau Droit (Actions) :** Comprend les boutons pour sauvegarder, effacer, annuler/rétablir et accéder aux paramètres de la caméra.

## Outils d'Annotation (Panneau Gauche)

### 1. Dessin Main Levée

Permet de dessiner des lignes continues et irrégulières sur l'image, comme avec un crayon.

*   **Utilisation :** Cliquez et maintenez le bouton gauche de la souris enfoncé, puis faites glisser pour dessiner. (Raccourci : `Ctrl+F`)

### 2. Rectangle

Permet de dessiner des formes rectangulaires.

*   **Utilisation :** Cliquez et faites glisser la souris pour définir les coins opposés du rectangle. (Raccourci : `Ctrl+R`)

### 3. Cercle

Permet de dessiner des formes circulaires.

*   **Utilisation :** Cliquez et faites glisser la souris pour définir le rayon du cercle à partir de son centre. (Raccourci : `Ctrl+C`)

### 4. Ligne

Permet de dessiner des lignes droites.

*   **Utilisation :** Cliquez pour le point de départ, puis cliquez à nouveau pour le point d'arrivée de la ligne. (Raccourci : `Ctrl+L`)

### 5. Ajouter Texte

Permet d'ajouter du texte sur l'image.

*   **Utilisation :** Cliquez à l'endroit où vous souhaitez placer le texte. Une boîte de dialogue apparaîtra pour que vous puissiez saisir votre texte. Validez avec "OK". (Raccourci : `Ctrl+T`)

### 6. Zone de Flou

Permet d'appliquer un effet de flou sur une zone rectangulaire de l'image, utile pour masquer des informations sensibles.

*   **Utilisation :** Cliquez et faites glisser la souris pour définir la zone à flouter. (Raccourci : `Ctrl+B`)

### 7. Flèche

Permet de dessiner des flèches pour indiquer des directions ou des éléments spécifiques.

*   **Utilisation :** Cliquez et faites glisser la souris pour définir le point de départ et la direction de la flèche. (Raccourci : `Ctrl+A`)

### 8. Surlignage

Permet de surligner une zone rectangulaire avec une couleur translucide.

*   **Utilisation :** Cliquez et faites glisser la souris pour définir la zone à surligner. (Raccourci : `Ctrl+H`)

### 9. Sélection

Cet outil est essentiel pour interagir avec les annotations existantes.

*   **Sélectionner :** Cliquez sur une annotation pour la sélectionner. Une fois sélectionnée, une boîte englobante verte et des poignées de redimensionnement apparaissent. (Raccourci : `Ctrl+S`)
*   **Déplacer :** Cliquez et faites glisser une annotation sélectionnée pour la déplacer.
*   **Redimensionner :** Cliquez et faites glisser l'une des poignées de redimensionnement (petits carrés verts aux coins/bords de la boîte englobante) pour ajuster la taille de l'annotation.

### 10. Choisir Couleur

Ouvre une boîte de dialogue pour sélectionner la couleur des annotations futures.

*   **Utilisation :** Cliquez sur le bouton, choisissez votre couleur et validez. (Raccourci : `Ctrl+K`)

### 11. Choisir Taille

Ouvre une boîte de dialogue pour ajuster l'épaisseur du trait des annotations et la taille de la police pour le texte.

*   **Utilisation :** Utilisez les curseurs pour définir les valeurs souhaitées et validez avec "OK". (Raccourci : `Ctrl+I`)

### 12. Zoom

Contrôle le niveau de zoom de l'image affichée.

*   **Boutons +/- :** Cliquez sur "+" pour zoomer, sur "-" pour dézoomer. (Raccourcis : `Ctrl++` / `Ctrl+=` pour zoomer, `Ctrl+-` pour dézoomer)
*   **Molette de la souris :** Faites défiler la molette vers le haut pour zoomer, vers le bas pour dézoomer. Le zoom est centré sur la position du curseur de la souris.

### 13. Retournement (Flip)

Permet de retourner l'image horizontalement ou verticalement.

*   **Retournement Horizontal :** Inverse l'image de gauche à droite. (Raccourci : `Ctrl+J`)
*   **Retournement Vertical :** Inverse l'image de haut en bas. (Raccourci : `Ctrl+U`)

## Zone d'Affichage Vidéo

Cette zone affiche le flux en direct de votre webcam. Toutes les annotations sont superposées sur ce flux.

*   **Panoramique (Déplacement de la vue) :** Maintenez le bouton central de la souris (molette) enfoncé et faites glisser pour déplacer la vue lorsque l'image est zoomée.

## Panneau Droit (Actions)

### 1. Sauvegarder

Permet de sauvegarder l'image actuelle (avec toutes les annotations et le niveau de zoom/panoramique appliqué) dans un fichier.

*   **Utilisation :** Cliquez sur le bouton. Une boîte de dialogue vous permettra de choisir le nom du fichier et le format (PNG ou PDF). (Raccourci : `Ctrl+Shift+S`)

### 2. Effacer Tout

Supprime toutes les annotations de l'image.

*   **Utilisation :** Cliquez sur le bouton pour effacer toutes les annotations. (Raccourci : `Ctrl+E`)

### 3. Annuler (Undo)

Annule la dernière action d'annotation.

*   **Utilisation :** Cliquez sur le bouton. Vous pouvez annuler plusieurs actions consécutives. (Raccourci : `Ctrl+Z`)

### 4. Rétablir (Redo)

Rétablit une action qui a été annulée.

*   **Utilisation :** Cliquez sur le bouton. Fonctionne après avoir utilisé "Annuler". (Raccourci : `Ctrl+Y`)

### 5. Supprimer

Supprime l'annotation actuellement sélectionnée.

*   **Utilisation :** Sélectionnez une annotation avec l'outil "Sélection", puis cliquez sur ce bouton ou appuyez sur la touche `Suppr` de votre clavier. (Raccourci : `Suppr`)

### 6. Paramètres

Ouvre une boîte de dialogue pour ajuster les paramètres de la webcam.

*   **Luminosité :** Ajuste la luminosité du flux vidéo.
*   **Contraste :** Ajuste le contraste du flux vidéo.
*   **Résolution :** Permet de choisir la résolution de la webcam parmi les options disponibles. (Raccourci : `Ctrl+P`)

### 7. Aide

Ouvre le manuel d'utilisation directement dans l'application.

*   **Utilisation :** Cliquez sur le bouton. (Raccourci : `Ctrl+?`)

## Dépannage

*   **"Aucune webcam trouvée" :** Assurez-vous que votre webcam est correctement connectée et que les pilotes sont installés. Redémarrez l'application.
*   **Problèmes de performance :** Si le flux vidéo est lent, essayez de réduire la résolution de la webcam dans les paramètres.
*   **Annotations incorrectes :** Assurez-vous que l'outil "Sélection" est désactivé lorsque vous dessinez de nouvelles annotations. Si vous redimensionnez, assurez-vous de bien cliquer sur les poignées de redimensionnement.

Pour toute autre question ou problème, veuillez consulter la documentation du projet ou contacter le support.
"""

        text_widget = tk.Text(help_dialog, wrap="word", font=("TkDefaultFont", 10))
        text_widget.insert(tk.END, manual_content)
        text_widget.config(state="disabled") # Make it read-only / Le rend en lecture seule
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)

        # Add a scrollbar to the text widget
        # Ajoute une barre de défilement au widget texte
        scrollbar = ttk.Scrollbar(help_dialog, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        ttk.Button(help_dialog, text="Fermer", command=help_dialog.destroy).pack(pady=10)

        # Center the help dialog on the screen
        # Centre la boîte de dialogue d'aide sur l'écran
        help_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (help_dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (help_dialog.winfo_height() // 2)
        help_dialog.geometry(f"{help_dialog.winfo_width()}x{help_dialog.winfo_height()}+{x}+{y}")

    def _initialize_camera(self):
        """
        Initializes the camera by trying to load a cached camera index first.
        If not found or fails, it populates all available cameras.
        This function runs in a separate thread to avoid blocking the UI.
        Initialise la caméra en essayant d'abord de charger un index de caméra mis en cache.
        Si non trouvé ou échoue, il peuple toutes les caméras disponibles.
        Cette fonction s'exécute dans un fil séparé pour éviter de bloquer l'interface utilisateur.
        """
        # Try to load cached camera index from config file
        # Essaie de charger l'index de caméra mis en cache à partir du fichier de configuration
        cached_camera_index = self._load_camera_config()
        if cached_camera_index is not None:
            print(f"Attempting to open cached camera {cached_camera_index}...")
            # On Windows, direct check might not be reliable; populate all devices first
            # Sous Windows, la vérification directe peut ne pas être fiable ; peuple d'abord tous les périphériques
            if platform.system() == "Windows":
                self.populate_cameras()
                return

            # For Linux/macOS, try to open the cached camera directly
            # Pour Linux/macOS, essaie d'ouvrir directement la caméra mise en cache
            cap = cv2.VideoCapture(cached_camera_index)
            if cap.isOpened():
                print(f"Successfully opened cached camera {cached_camera_index}.")
                self.camera_options.append((f"Webcam {cached_camera_index}", cached_camera_index))
                cap.release()
                # Update UI on the main thread after successful camera open
                # Met à jour l'interface utilisateur sur le fil principal après l'ouverture réussie de la caméra
                self.after(0, lambda: self.update_camera_menu(initial_camera_index=cached_camera_index))
                return
            else:
                print(f"Cached camera {cached_camera_index} not available. Scanning for cameras...")

        # If cached camera fails or not found, proceed with full scan for cameras
        # Si la caméra mise en cache échoue ou n'est pas trouvée, procède à une analyse complète des caméras
        self.populate_cameras()

    def _load_camera_config(self):
        """
        Loads the last used camera index from the configuration file.
        Charge le dernier index de caméra utilisé à partir du fichier de configuration.

        Returns:
            int or None: The cached camera index, or None if not found or error.
                         L'index de caméra mis en cache, ou Aucun si non trouvé ou erreur.
        """
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('last_camera_index')
            except json.JSONDecodeError:
                print("Error decoding camera config file.")
        return None

    def _save_camera_config(self, camera_index):
        """
        Saves the currently selected camera index to the configuration file.
        Sauvegarde l'index de caméra actuellement sélectionné dans le fichier de configuration.

        Args:
            camera_index (int): The index of the camera to save.
                                L'index de la caméra à sauvegarder.
        """
        config = {'last_camera_index': camera_index}
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except IOError as e:
            print(f"Error saving camera config file: {e}")

    def update_camera_menu(self, initial_camera_index=None):
        """
        Updates the camera selection dropdown menu with found cameras.
        Mise à jour du menu déroulant de sélection de la caméra avec les caméras trouvées.

        Args:
            initial_camera_index (int, optional): The index of the camera to pre-select.
                                                   L'index de la caméra à présélectionner.
        """
        self.camera_menu_placeholder.pack_forget() # Remove the "Searching for cameras..." placeholder / Supprime l'espace réservé "Recherche de caméras en cours..."

        if self.camera_options: # If cameras were found / Si des caméras ont été trouvées
            # Sort cameras by index for consistent ordering in the menu
            # Trie les caméras par index pour un ordre cohérent dans le menu
            self.camera_options.sort(key=lambda x: x[1])
            
            # Set the initial selected value in the dropdown
            # Définit la valeur initiale sélectionnée dans le menu déroulant
            if initial_camera_index is not None and any(opt[1] == initial_camera_index for opt in self.camera_options):
                self.camera_var.set(f"Webcam {initial_camera_index}")
                selected_index = initial_camera_index
            else:
                self.camera_var.set(self.camera_options[0][0]) # Default to the first found camera / Par défaut à la première caméra trouvée
                selected_index = self.camera_options[0][1]

            # Create the OptionMenu for camera selection
            # Crée l'OptionMenu pour la sélection de la caméra
            self.camera_menu = ttk.OptionMenu(self.camera_selection_frame, self.camera_var, self.camera_var.get(), *[opt[0] for opt in self.camera_options], style='White.TMenubutton', command=self.select_camera)
            self.camera_menu.pack(side=tk.LEFT)
            Tooltip(self.camera_menu, "Sélectionne la webcam à utiliser")
            
            # Start video stream with the selected camera
            # Démarre le flux vidéo avec la caméra sélectionnée
            self.start_video_stream(selected_index, self.current_resolution[0], self.current_resolution[1])
            self._save_camera_config(selected_index) # Save the successfully opened camera to config / Sauvegarde la caméra ouverte avec succès dans la configuration
        else:
            # Display a message if no cameras are found
            # Affiche un message si aucune caméra n'est trouvée
            ttk.Label(self.camera_selection_frame, text="Aucune webcam trouvée", style='White.TLabel').pack(side=tk.LEFT)

    def _check_camera(self, index, results_list, initial_camera_found):
        """
        Helper function to check if a camera at a given index can be opened.
        Used in a separate thread for non-blocking camera detection.
        Fonction d'aide pour vérifier si une caméra à un index donné peut être ouverte.
        Utilisée dans un fil séparé pour la détection de caméra non bloquante.

        Args:
            index (int): The camera index to check.
                         L'index de la caméra à vérifier.
            results_list (list): A shared list to append found cameras.
                                 Une liste partagée pour ajouter les caméras trouvées.
            initial_camera_found (list): A mutable list (e.g., [False]) to signal if the first camera was found.
                                         Une liste mutable (par exemple, [False]) pour signaler si la première caméra a été trouvée.
        """
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            results_list.append((f"Webcam {index}", index))
            # If this is the first camera found, start its stream and save to config
            # Si c'est la première caméra trouvée, démarre son flux et la sauvegarde dans la configuration
            if not initial_camera_found[0]:
                self.after(0, lambda: self.start_video_stream(index, self.current_resolution[0], self.current_resolution[1]))
                self.after(0, lambda: self._save_camera_config(index))
                initial_camera_found[0] = True
            cap.release()

    def populate_cameras(self):
        """
        Detects and populates the list of available cameras.
        Uses pygrabber for Windows for more robust detection, falls back to OpenCV for others.
        Détecte et peuple la liste des caméras disponibles.
        Utilise pygrabber pour Windows pour une détection plus robuste, se replie sur OpenCV pour les autres.
        """
        if platform.system() == "Windows" and DSShow is not None: # Use pygrabber on Windows if available / Utilise pygrabber sous Windows si disponible
            try:
                devices = DSShow.get_input_devices()
                for i, device_name in enumerate(devices):
                    self.camera_options.append((device_name, i))
                self.after(0, self.update_camera_menu) # Update UI on main thread / Met à jour l'interface utilisateur sur le fil principal
            except Exception as e:
                print(f"Error using pygrabber: {e}")
                # Fallback to the generic OpenCV method if pygrabber fails
                # Repli sur la méthode OpenCV générique si pygrabber échoue
                self._populate_cameras_linux()
        else:
            # For Linux/macOS or if pygrabber fails, use generic OpenCV camera check
            # Pour Linux/macOS ou si pygrabber échoue, utilise la vérification générique de la caméra OpenCV
            self._populate_cameras_linux()

    def _populate_cameras_linux(self):
        """
        Populates available cameras by trying indices 0-9 using OpenCV.
        Each check is done in a separate sub-thread for parallelism.
        Peuple les caméras disponibles en essayant les indices 0-9 à l'aide d'OpenCV.
        Chaque vérification est effectuée dans un sous-fil séparé pour le parallélisme.
        """
        threads = []
        found_cameras = []
        initial_camera_found = [False] # Use a mutable list to pass by reference / Utilise une liste mutable pour passer par référence
        for i in range(10): # Check up to 10 potential camera indices / Vérifie jusqu'à 10 indices de caméra potentiels
            thread = threading.Thread(target=self._check_camera, args=(i, found_cameras, initial_camera_found), daemon=True)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join() # Wait for all camera check threads to complete / Attend que tous les fils de vérification de caméra se terminent

        self.camera_options = found_cameras
        # Update the camera menu on the main Tkinter thread
        # Met à jour le menu de la caméra sur le fil principal de Tkinter
        self.after(0, self.update_camera_menu) 

    def start_video_stream(self, camera_index, width, height):
        """
        Starts or restarts the video stream thread with the given camera parameters.
        Démarre ou redémarre le fil du flux vidéo avec les paramètres de caméra donnés.

        Args:
            camera_index (int): Index of the camera to stream from.
                                Indice de la caméra à partir de laquelle diffuser.
            width (int): Desired width of the video frame.
                         Largeur souhaitée du cadre vidéo.
            height (int): Desired height of the video frame.
                          Hauteur souhaitée du cadre vidéo.
        """
        # Stop any existing video stream thread before starting a new one
        # Arrête tout fil de flux vidéo existant avant d'en démarrer un nouveau
        if self.video_stream_thread and self.video_stream_thread.is_alive():
            self.video_stream_thread.stop()
            self.video_stream_thread.join() # Wait for the thread to terminate / Attend que le fil se termine
        
        # Create and start a new VideoStreamThread
        # Crée et démarre un nouveau VideoStreamThread
        self.video_stream_thread = VideoStreamThread(camera_index, width, height)
        self.video_stream_thread.start()

    def select_camera(self, camera_name):
        """
        Callback function when a camera is selected from the dropdown menu.
        Fonction de rappel lorsqu'une caméra est sélectionnée dans le menu déroulant.

        Args:
            camera_name (str): The display name of the selected camera.
                                Le nom d'affichage de la caméra sélectionnée.
        """
        for name, index in self.camera_options:
            if name == camera_name:
                self.start_video_stream(index, self.current_resolution[0], self.current_resolution[1])
                self._save_camera_config(index) # Save the newly selected camera to config / Sauvegarde la caméra nouvellement sélectionnée dans la configuration
                break

    def update_display(self):
        """
        Periodically updates the image displayed on the image_label.
        This is the main rendering loop of the application.
        Met à jour périodiquement l'image affichée sur image_label.
        C'est la boucle de rendu principale de l'application.
        """
        if self.file_mode: # If in file viewing mode / Si en mode d'affichage de fichier
            if self.loaded_image:
                self.display_image(self.loaded_image)
        elif self.video_stream_thread and self.video_stream_thread.is_alive(): # If in webcam mode and thread is active / Si en mode webcam et que le fil est actif
            frame = self.video_stream_thread.get_frame()
            if frame is not None:
                # Convert OpenCV BGR frame to PIL RGB image for display
                # Convertit le cadre BGR d'OpenCV en image PIL RGB pour l'affichage
                self.display_image(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        
        # Schedule the next update after 10 milliseconds (approx 100 FPS, but limited by camera/processing)
        # Planifie la prochaine mise à jour après 10 millisecondes (environ 100 FPS, mais limité par la caméra/le traitement)
        self.after(10, self.update_display)

    def display_image(self, pil_image):
        """
        Processes and displays a PIL Image on the image_label, including annotations, zoom, and pan.
        Traite et affiche une image PIL sur image_label, y compris les annotations, le zoom et le panoramique.

        Args:
            pil_image (PIL.Image.Image): The base image to display.
                                         L'image de base à afficher.
        """
        # Create a copy of the image to draw on without modifying the original source
        # Crée une copie de l'image pour dessiner sans modifier la source originale
        display_image = pil_image.copy()
        # Convert PIL RGB image to OpenCV BGR format for drawing with cv2
        # Convertit l'image PIL RGB en format OpenCV BGR pour dessiner avec cv2
        display_image_cv = cv2.cvtColor(np.array(display_image), cv2.COLOR_RGB2BGR)

        # Draw all existing annotations on the OpenCV frame
        # Dessine toutes les annotations existantes sur le cadre OpenCV
        for annotation in self.annotations:
            annotation.draw(display_image_cv)

        # Draw bounding box and resize handles for the selected annotation
        # Dessine la boîte englobante et les poignées de redimensionnement pour l'annotation sélectionnée
        if self.selected_annotation:
            bbox = self.selected_annotation.get_bounding_box()
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[2]), int(bbox[3]))
                cv2.rectangle(display_image_cv, p1, p2, (0, 255, 0), 2, cv2.LINE_AA) # Green bounding box / Boîte englobante verte
                # Draw resize handles (small filled rectangles)
                # Dessine les poignées de redimensionnement (petits rectangles remplis)
                handles = self.selected_annotation.get_resize_handles()
                for handle in handles.values():
                    cv2.rectangle(display_image_cv, (int(handle[0])-8, int(handle[1])-8), (int(handle[0])+8, int(handle[1])+8), (0, 255, 0), -1)
        # Draw bounding box for the hovered annotation (if no annotation is selected)
        # Dessine la boîte englobante pour l'annotation survolée (si aucune annotation n'est sélectionnée)
        elif self.hovered_annotation:
            bbox = self.hovered_annotation.get_bounding_box()
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[2]), int(bbox[3]))
                cv2.rectangle(display_image_cv, p1, p2, (255, 165, 0), 2, cv2.LINE_AA) # Orange for hover / Orange pour le survol

        # Draw temporary annotation while drawing (before mouse release)
        # Dessine l'annotation temporaire pendant le dessin (avant le relâchement de la souris)
        if self.drawing and self.start_point and self.end_point and self.current_tool != "selection":
            if self.current_tool == "line":
                temp_annotation = LineAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "rectangle":
                temp_annotation = RectangleAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "circle":
                center_x = (self.start_point[0] + self.end_point[0]) // 2
                center_y = (self.start_point[1] + self.end_point[1]) // 2
                radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                temp_annotation = CircleAnnotation((center_x, center_y), radius, color=self.current_annotation_color, thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "freedraw" and self.current_freedraw_points: # For freehand, draw the current path / Pour le dessin à main levée, dessine le chemin actuel
                temp_annotation = FreeDrawAnnotation(self.current_freedraw_points, color=(0, 255, 255), thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "blur":
                overlay = display_image_cv.copy()
                x1, y1 = self.start_point
                x2, y2 = self.end_point
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 0), -1) # Draw a temporary yellow filled rectangle / Dessine un rectangle rempli jaune temporaire
                alpha = 0.3 # Opacity for the temporary blur preview / Opacité pour l'aperçu de flou temporaire
                display_image_cv = cv2.addWeighted(overlay, alpha, display_image_cv, 1 - alpha, 0)
            elif self.current_tool == "arrow":
                temp_annotation = ArrowAnnotation(self.start_point, self.end_point, color=(0, 0, 255), thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "highlight":
                overlay = display_image_cv.copy()
                x1, y1 = self.start_point
                x2, y2 = self.end_point
                cv2.rectangle(overlay, (x1, y1), (x2, y2), self.current_annotation_color, -1)
                alpha = 0.3 # Opacity for the temporary highlight preview / Opacité pour l'aperçu de surlignage temporaire
                display_image_cv = cv2.addWeighted(overlay, alpha, display_image_cv, 1 - alpha, 0)

        # Convert the final annotated OpenCV frame back to PIL Image
        # Convertit le cadre OpenCV annoté final en image PIL
        final_annotated_pil = Image.fromarray(cv2.cvtColor(display_image_cv, cv2.COLOR_BGR2RGB))
        original_width, original_height = final_annotated_pil.size

        # Apply zoom to the image
        # Applique le zoom à l'image
        scaled_width = int(original_width * self.zoom_level)
        scaled_height = int(original_height * self.zoom_level)
        
        # Prevent issues with zero or negative dimensions after scaling
        # Prévient les problèmes avec des dimensions nulles ou négatives après la mise à l'échelle
        if scaled_width <= 0 or scaled_height <= 0:
            return

        scaled_image = final_annotated_pil.resize((scaled_width, scaled_height), Image.LANCZOS)

        # Create a new blank canvas (final view) to paste the scaled image onto
        # Crée un nouveau canevas vierge (vue finale) pour y coller l'image mise à l'échelle
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        final_view = Image.new('RGB', (label_width, label_height), (200, 200, 200)) # Grey background for empty areas / Fond gris pour les zones vides

        # Clamp offsets to ensure the image stays within bounds during pan
        # Clampe les décalages pour s'assurer que l'image reste dans les limites pendant le panoramique
        self.clamp_offsets()

        # Calculate paste position based on pan offsets
        # Calcule la position de collage en fonction des décalages de panoramique
        paste_x = -int(self.view_offset_x)
        paste_y = -int(self.view_offset_y)
        
        # If the scaled image is smaller than the label, center it
        # Si l'image mise à l'échelle est plus petite que l'étiquette, la centre
        if scaled_width < label_width:
            paste_x = (label_width - scaled_width) // 2
        if scaled_height < label_height:
            paste_y = (label_height - scaled_height) // 2

        final_view.paste(scaled_image, (paste_x, paste_y)) # Paste the scaled image onto the final view canvas / Colle l'image mise à l'échelle sur le canevas de la vue finale

        # Update the Tkinter PhotoImage and the label to display the new frame
        # Met à jour le PhotoImage Tkinter et l'étiquette pour afficher le nouveau cadre
        self.current_photo = ImageTk.PhotoImage(image=final_view)
        self.image_label.config(image=self.current_photo)
        
        # Store references to the images for saving functionality
        # Stocke les références aux images pour la fonctionnalité de sauvegarde
        self.pil_image_to_save = final_annotated_pil # Original resolution with annotations / Résolution originale avec annotations
        self.view_for_saving = final_view # What is currently displayed on screen (with zoom/pan) / Ce qui est actuellement affiché à l'écran (avec zoom/panoramique)

    def on_closing(self):
        """
        Handles the window closing event.
        Stops the video stream thread before destroying the window.
        Gère les événements de fermeture de la fenêtre.
        Arrête le fil du flux vidéo avant de détruire la fenêtre.
        """
        if self.video_stream_thread: # If a video stream is active / Si un flux vidéo est actif
            self.video_stream_thread.stop() # Signal the thread to stop / Signale au fil de s'arrêter
            self.video_stream_thread.join() # Wait for the thread to finish / Attend que le fil se termine
        self.destroy() # Destroy the Tkinter window / Détruit la fenêtre Tkinter

    def choose_annotation_color(self):
        """
        Opens a color chooser dialog and updates the current annotation color.
        Ouvre une boîte de dialogue de sélection de couleur et met à jour la couleur d'annotation actuelle.
        """
        color_code = colorchooser.askcolor(title="Choisir la couleur de l'annotation")
        if color_code[1]: # If a color was selected (color_code[1] is the hex string) / Si une couleur a été sélectionnée (color_code[1] est la chaîne hexadécimale)
            rgb_color = color_code[0] # RGB tuple (e.g., (255, 0, 0) for red) / Tuple RGB (par exemple, (255, 0, 0) pour le rouge)
            # Convert RGB to BGR for OpenCV compatibility
            # Convertit RGB en BGR pour la compatibilité OpenCV
            self.current_annotation_color = (rgb_color[2], rgb_color[1], rgb_color[0])

    def choose_annotation_size(self):
        """
        Opens a dialog to allow the user to choose annotation thickness and font size.
        Ouvre une boîte de dialogue pour permettre à l'utilisateur de choisir l'épaisseur de l'annotation et la taille de la police.
        """
        size_dialog = tk.Toplevel(self, bg='white')
        size_dialog.title("Choisir la taille")
        size_dialog.transient(self) # Make it transient to the main window / Le rend transitoire à la fenêtre principale
        size_dialog.grab_set() # Make it modal / Le rend modal

        # Thickness slider
        # Curseur d'épaisseur
        ttk.Label(size_dialog, text="Épaisseur du trait:").pack(pady=5)
        thickness_slider = ttk.Scale(size_dialog, from_=1, to_=50, orient=tk.HORIZONTAL)
        thickness_slider.set(self.current_annotation_thickness) # Set initial value / Définit la valeur initiale
        thickness_slider.pack(fill=tk.X, padx=10, pady=5)

        # Font size slider
        # Curseur de taille de police
        ttk.Label(size_dialog, text="Taille de la police:").pack(pady=5)
        font_size_slider = ttk.Scale(size_dialog, from_=8, to_=72, orient=tk.HORIZONTAL)
        font_size_slider.set(self.current_font_size) # Set initial value / Définit la valeur initiale
        font_size_slider.pack(fill=tk.X, padx=10, pady=5)

        def on_ok():
            """
            Callback for the OK button in the size dialog.
            Updates the annotation thickness and font size.
            Rappel pour le bouton OK dans la boîte de dialogue de taille.
            Met à jour l'épaisseur de l'annotation et la taille de la police.
            """
            self.current_annotation_thickness = int(thickness_slider.get())
            self.current_font_size = int(font_size_slider.get())
            size_dialog.destroy() # Close the dialog / Ferme la boîte de dialogue

        ttk.Button(size_dialog, text="OK", command=on_ok).pack(pady=10)

    def set_tool(self, tool_name):
        """
        Sets the currently active annotation tool.
        Définit l'outil d'annotation actuellement actif.

        Args:
            tool_name (str): The name of the tool to activate (e.g., "line", "rectangle").
                             Le nom de l'outil à activer (par exemple, "line", "rectangle").
        """
        self.current_tool = tool_name
        # Reset drawing state variables
        # Réinitialise les variables d'état de dessin
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self.current_freedraw_points = []
        self.entered_text = "" # Reset entered text for text tool / Réinitialise le texte saisi pour l'outil texte
        
        # Specific resets or actions based on the tool
        # Réinitialisations ou actions spécifiques basées sur l'outil
        if tool_name == "text":
            pass # Text input dialog is triggered on mouse click, not tool selection / La boîte de dialogue de saisie de texte est déclenchée au clic de souris, pas à la sélection de l'outil
        elif tool_name in ["blur", "arrow", "highlight"]:
            self.start_point = None
            self.end_point = None
        elif tool_name == "selection":
            self.selected_annotation = None # Deselect any currently selected annotation / Désélectionne toute annotation actuellement sélectionnée
            self.hovered_annotation = None # Clear hovered annotation / Efface l'annotation survolée

    def save_image(self):
        """
        Prompts the user to save the current displayed image (with annotations, zoom, and pan) as PNG or PDF.
        Invite l'utilisateur à sauvegarder l'image affichée actuelle (avec annotations, zoom et panoramique) au format PNG ou PDF.
        """
        if hasattr(self, 'view_for_saving'): # Ensure there is an image to save / S'assure qu'il y a une image à sauvegarder
            img_to_save = self.view_for_saving

            # Open a file dialog for saving
            # Ouvre une boîte de dialogue de fichier pour la sauvegarde
            file_path = filedialog.asksaveasfilename(
                filetypes=[("Fichiers PNG", "*.png"), ("Fichiers PDF", "*.pdf")],
                title="Sauvegarder l'image annotée"
            )

            if file_path: # If a file path was selected / Si un chemin de fichier a été sélectionné
                selected_ext = ".png" # Default extension / Extension par défaut
                # Determine the selected extension based on filetypes
                # Détermine l'extension sélectionnée en fonction des types de fichiers
                for desc, pattern in [("Fichiers PNG", "*.png"), ("Fichiers PDF", "*.pdf")]:
                    if file_path.lower().endswith(pattern[1:]): # Check if path ends with .png or .pdf
                                                               # Vérifie si le chemin se termine par .png ou .pdf
                        selected_ext = pattern[1:]
                        break
                
                name, ext = os.path.splitext(file_path)
                # Append extension if not already present or incorrect
                # Ajoute l'extension si elle n'est pas déjà présente ou incorrecte
                if not ext or ext.lower() != selected_ext:
                    file_path = name + selected_ext

                # Generate a timestamp for unique filenames
                # Génère un horodatage pour des noms de fichiers uniques
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                directory, filename = os.path.split(file_path)
                name, ext = os.path.splitext(filename)
                
                final_filename = os.path.join(directory, f"{timestamp}_{name}{ext}")

                try:
                    if ext.lower() == ".pdf":
                        # Convert to RGB before saving as PDF (PDFs typically don't support RGBA)
                        # Convertit en RGB avant de sauvegarder en PDF (les PDF ne prennent généralement pas en charge RGBA)
                        img_to_save.convert('RGB').save(final_filename, "PDF", resolution=100.0)
                    else:
                        img_to_save.save(final_filename)
                    messagebox.showinfo("Sauvegarde", f"Image sauvegardée avec succès :\n{final_filename}")
                except Exception as e:
                    messagebox.showerror("Erreur de Sauvegarde", f"Impossible de sauvegarder l'image :\n{e}")
        else:
            messagebox.showwarning("Avertissement", "Aucune image à sauvegarder.")

    def _convert_event_to_original_coords(self, event):
        """
        Converts mouse event coordinates (relative to image_label) to original image coordinates,
        accounting for zoom and pan.
        Convertit les coordonnées d'événement de la souris (relatives à image_label) en coordonnées d'image originales,
        en tenant compte du zoom et du panoramique.

        Args:
            event (tk.Event): The mouse event object.
                              L'objet événement de la souris.

        Returns:
            tuple: (x, y) coordinates in the original image's coordinate system.
                   Coordonnées (x, y) dans le système de coordonnées de l'image originale.
        """
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        
        original_width, original_height = (0, 0)
        if self.file_mode:
            if self.loaded_image is None:
                return (0,0)
            original_width, original_height = self.loaded_image.size
        elif self.video_stream_thread and self.video_stream_thread.get_frame() is not None:
            original_height, original_width, _ = self.video_stream_thread.get_frame().shape
        else:
            return (0,0)
        
        scaled_width = original_width * self.zoom_level
        scaled_height = original_height * self.zoom_level

        # Calculate the effective paste position of the scaled image on the label
        # Calcule la position de collage effective de l'image mise à l'échelle sur l'étiquette
        paste_x = -int(self.view_offset_x)
        paste_y = -int(self.view_offset_y)
        if scaled_width < label_width:
            paste_x = (label_width - scaled_width) // 2
        if scaled_height < label_height:
            paste_y = (label_height - scaled_height) // 2

        # Convert mouse coordinates relative to the scaled image
        # Convertit les coordonnées de la souris par rapport à l'image mise à l'échelle
        scaled_image_x = event.x - paste_x
        scaled_image_y = event.y - paste_y

        # Convert scaled image coordinates back to original image coordinates
        # Convertit les coordonnées de l'image mise à l'échelle en coordonnées d'image originales
        original_x = scaled_image_x / self.zoom_level
        original_y = scaled_image_y / self.zoom_level

        return (int(original_x), int(original_y))

    def on_mouse_down(self, event):
        """
        Handles mouse button press events on the image display area.
        Gère les événements de pression du bouton de la souris sur la zone d'affichage de l'image.
        """
        click_point = self._convert_event_to_original_coords(event)

        if self.current_tool == "selection":
            self.resize_handle = None # Reset resize handle / Réinitialise la poignée de redimensionnement
            if self.selected_annotation: # If an annotation is already selected / Si une annotation est déjà sélectionnée
                handles = self.selected_annotation.get_resize_handles()
                for handle_name, handle_pos in handles.items():
                    # Check if the click is on a resize handle (with a tolerance area)
                    # Vérifie si le clic est sur une poignée de redimensionnement (avec une zone de tolérance)
                    if abs(handle_pos[0] - click_point[0]) < 15 / self.zoom_level and abs(handle_pos[1] - click_point[1]) < 15 / self.zoom_level:
                        self.resize_handle = handle_name # Store the name of the dragged handle / Stocke le nom de la poignée glissée
                        self.initial_drag_point_for_resize = click_point # Store initial drag point for resize calculation / Stocke le point de glissement initial pour le calcul de redimensionnement
                        self.drawing = True # Indicate that a resize operation is starting / Indique qu'une opération de redimensionnement commence
                        return

            newly_selected = None
            # Iterate annotations in reverse order to select the topmost one
            # Itère les annotations dans l'ordre inverse pour sélectionner celle du dessus
            for annotation in reversed(self.annotations):
                if annotation.is_point_inside(click_point):
                    newly_selected = annotation
                    break
            
            if newly_selected: # If an annotation was clicked / Si une annotation a été cliquée
                self.selected_annotation = newly_selected
                self.start_point = click_point # Store click point for moving the annotation / Stocke le point de clic pour déplacer l'annotation
                self.drawing = True # Indicate that a move operation is starting / Indique qu'une opération de déplacement commence
            else:
                self.selected_annotation = None # Deselect if clicked outside any annotation / Désélectionne si cliqué en dehors de toute annotation
                self.drawing = False

        elif self.current_tool == "text":
            entered_text = self.get_text_input() # Open text input dialog / Ouvre la boîte de dialogue de saisie de texte
            if entered_text: # If text was entered / Si du texte a été saisi
                self.annotations.append(TextAnnotation(click_point, entered_text, color=self.current_annotation_color, font_size=self.current_font_size))
                self.redo_stack.clear() # Clear redo stack after a new action / Efface la pile de rétablissement après une nouvelle action
                self.set_tool("selection") # Switch to selection tool after adding text / Passe à l'outil de sélection après avoir ajouté du texte
        elif self.current_tool != "none": # For other drawing tools / Pour les autres outils de dessin
            self.drawing = True
            self.start_point = click_point
            self.end_point = click_point # Initialize end_point to start_point / Initialise end_point à start_point

    def on_mouse_drag(self, event):
        """
        Handles mouse drag events on the image display area.
        Gère les événements de glisser-déposer de la souris sur la zone d'affichage de l'image.
        """
        if not self.drawing: # Only process if a drawing/moving/resizing operation is active / Traite uniquement si une opération de dessin/déplacement/redimensionnement est active
            return

        current_point = self._convert_event_to_original_coords(event)

        if self.current_tool == "selection" and self.selected_annotation: # If selection tool is active and an annotation is selected / Si l'outil de sélection est actif et qu'une annotation est sélectionnée
            dx = current_point[0] - self.start_point[0]
            dy = current_point[1] - self.start_point[1]
            if self.resize_handle: # If a resize handle is being dragged / Si une poignée de redimensionnement est glissée
                self.selected_annotation.resize(self.resize_handle, current_point, self.initial_drag_point_for_resize)
            else:
                self.selected_annotation.move(dx, dy) # Move the selected annotation / Déplace l'annotation sélectionnée
            self.start_point = current_point # Update start_point for continuous dragging / Met à jour start_point pour un glissement continu
        elif self.current_tool != "selection": # For other drawing tools / Pour les autres outils de dessin
            self.end_point = current_point # Update end_point to draw temporary shape / Met à jour end_point pour dessiner la forme temporaire
            if self.current_tool == "freedraw":
                self.current_freedraw_points.append(self.end_point) # Add points for freehand drawing / Ajoute des points pour le dessin à main levée

    def on_mouse_up(self, event):
        """
        Handles mouse button release events on the image display area.
        Finalizes drawing operations.
        Gère les événements de relâchement du bouton de la souris sur la zone d'affichage de l'image.
        Finalise les opérations de dessin.
        """
        if not self.drawing: # Only process if a drawing/moving/resizing operation was active / Traite uniquement si une opération de dessin/déplacement/redimensionnement était active
            return

        self.drawing = False # End drawing/moving/resizing operation / Termine l'opération de dessin/déplacement/redimensionnement
        self.resize_handle = None # Clear resize handle / Efface la poignée de redimensionnement
        
        if self.current_tool != "selection": # If a drawing tool was active / Si un outil de dessin était actif
            final_point = self._convert_event_to_original_coords(event)
            self.end_point = final_point

            if self.start_point == self.end_point: # Ignore zero-size shapes (e.g., simple clicks) / Ignore les formes de taille nulle (par exemple, les simples clics)
                return

            # Create and add the appropriate annotation object based on the current tool
            # Crée et ajoute l'objet d'annotation approprié en fonction de l'outil actuel
            if self.current_tool == "line":
                self.annotations.append(LineAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "rectangle":
                self.annotations.append(RectangleAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "circle":
                center_x = (self.start_point[0] + self.end_point[0]) // 2
                center_y = (self.start_point[1] + self.end_point[1]) // 2
                radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                if radius > 0: # Only add if radius is positive / Ajoute uniquement si le rayon est positif
                    self.annotations.append(CircleAnnotation((center_x, center_y), radius, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "freedraw":
                if self.current_freedraw_points: # Only add if points exist / Ajoute uniquement si des points existent
                    self.annotations.append(FreeDrawAnnotation(list(self.current_freedraw_points), color=self.current_annotation_color, thickness=self.current_annotation_thickness))
                self.current_freedraw_points = [] # Reset points for next freehand draw / Réinitialise les points pour le prochain dessin à main levée
            elif self.current_tool == "blur":
                self.annotations.append(BlurAnnotation(self.start_point, self.end_point))
            elif self.current_tool == "arrow":
                self.annotations.append(ArrowAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "highlight":
                self.annotations.append(HighlightAnnotation(self.start_point, self.end_point, color=self.current_annotation_color))
            
            self.redo_stack.clear() # Clear redo stack after a new annotation is added / Efface la pile de rétablissement après l'ajout d'une nouvelle annotation
            self.start_point = None # Reset start and end points / Réinitialise les points de début et de fin
            self.end_point = None

    def on_mouse_move(self, event):
        """
        Handles mouse movement events on the image display area.
        Used for hovering over annotations in selection mode.
        Gère les événements de mouvement de la souris sur la zone d'affichage de l'image.
        Utilisé pour survoler les annotations en mode sélection.
        """
        if self.current_tool == "selection" and not self.drawing: # Only in selection mode and not currently dragging / Uniquement en mode sélection et non en cours de glissement
            mouse_point = self._convert_event_to_original_coords(event)
            self.hovered_annotation = None # Reset hovered annotation / Réinitialise l'annotation survolée
            # Check for annotation under mouse, iterating in reverse to find topmost
            # Vérifie l'annotation sous la souris, en itérant en sens inverse pour trouver celle du dessus
            for annotation in reversed(self.annotations):
                if annotation.is_point_inside(mouse_point):
                    self.hovered_annotation = annotation
                    break

    def zoom_in(self, event=None):
        """
        Increases the zoom level of the displayed image.
        Augmente le niveau de zoom de l'image affichée.
        """
        # If event is None (e.g., called by keyboard shortcut), set a default center point for zoom
        # Si l'événement est Aucun (par exemple, appelé par un raccourci clavier), définit un point central par défaut pour le zoom
        if event is None:
            event = tk.Event()
            event.x = self.image_label.winfo_width() / 2
            event.y = self.image_label.winfo_height() / 2
        self.zoom(1.1, event.x, event.y) # Zoom in by a factor of 1.1 / Zoom avant d'un facteur de 1.1

    def zoom_out(self, event=None):
        """
        Decreases the zoom level of the displayed image.
        Diminue le niveau de zoom de l'image affichée.
        """
        # If event is None (e.g., called by keyboard shortcut), set a default center point for zoom
        # Si l'événement est Aucun (par exemple, appelé par un raccourci clavier), définit un point central par défaut pour le zoom
        if event is None:
            event = tk.Event()
            event.x = self.image_label.winfo_width() / 2
            event.y = self.image_label.winfo_height() / 2
        self.zoom(0.9, event.x, event.y) # Zoom out by a factor of 0.9 / Zoom arrière d'un facteur de 0.9

    def on_mouse_wheel(self, event):
        """
        Handles mouse wheel events for zooming in/out.
        Gère les événements de la molette de la souris pour le zoom avant/arrière.
        """
        if event.num == 5 or event.delta < 0: # Scroll down (zoom out) / Défilement vers le bas (zoom arrière)
            self.zoom(0.9, event.x, event.y)
        elif event.num == 4 or event.delta > 0: # Scroll up (zoom in) / Défilement vers le haut (zoom avant)
            self.zoom(1.1, event.x, event.y)

    def zoom(self, factor, x, y):
        """
        Applies zoom to the image, centering the zoom around the mouse cursor position.
        Applique le zoom à l'image, en centrant le zoom autour de la position du curseur de la souris.

        Args:
            factor (float): Zoom factor (e.g., 1.1 for zoom in, 0.9 for zoom out).
                            Facteur de zoom (par exemple, 1.1 pour zoom avant, 0.9 pour zoom arrière).
            x (int): X-coordinate of the zoom center (relative to image_label).
                     Coordonnée X du centre du zoom (relative à image_label).
            y (int): Y-coordinate of the zoom center (relative to image_label).
                     Coordonnée Y du centre du zoom (relative à image_label).
        """
        old_zoom_level = self.zoom_level
        new_zoom_level = old_zoom_level * factor
        # Clamp zoom level to a reasonable range
        # Clampe le niveau de zoom à une plage raisonnable
        new_zoom_level = max(0.1, min(new_zoom_level, 10.0))
        self.zoom_level = new_zoom_level

        # Adjust view offsets to keep the zoom center fixed on screen
        # Ajuste les décalages de vue pour maintenir le centre du zoom fixe à l'écran
        original_x = (x + self.view_offset_x) / old_zoom_level
        original_y = (y + self.view_offset_y) / old_zoom_level

        self.view_offset_x = (original_x * self.zoom_level) - x
        self.view_offset_y = (original_y * self.zoom_level) - y
        
        self.clamp_offsets() # Ensure offsets are within valid bounds / S'assure que les décalages sont dans des limites valides

    def on_pan_start(self, event):
        """
        Initiates a pan operation when the middle mouse button is pressed.
        Démarre une opération de panoramique lorsque le bouton central de la souris est enfoncé.
        """
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_pan_move(self, event):
        """
        Handles mouse drag events during a pan operation.
        Gère les événements de glisser-déposer de la souris pendant une opération de panoramique.
        """
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.view_offset_x -= dx # Invert dx/dy for intuitive panning / Inverse dx/dy pour un panoramique intuitif
            self.view_offset_y -= dy
            self.pan_start_x = event.x # Update start point for next drag segment / Met à jour le point de départ pour le prochain segment de glissement
            self.pan_start_y = event.y
            self.clamp_offsets() # Keep offsets within bounds / Maintient les décalages dans les limites

    def on_pan_end(self, event):
        """
        Ends the pan operation when the middle mouse button is released.
        Termine l'opération de panoramique lorsque le bouton central de la souris est relâché.
        """
        self.is_panning = False

    def clamp_offsets(self):
        """
        Ensures that the view offsets (pan position) keep the image within the display area.
        S'assure que les décalages de vue (position du panoramique) maintiennent l'image dans la zone d'affichage.
        """
        original_width, original_height = (0, 0)
        if self.file_mode:
            if self.loaded_image is None:
                return
            original_width, original_height = self.loaded_image.size
        elif self.video_stream_thread and self.video_stream_thread.get_frame() is not None:
            original_height, original_width, _ = self.video_stream_thread.get_frame().shape
        else:
            return

        scaled_width = original_width * self.zoom_level
        scaled_height = original_height * self.zoom_level

        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()

        # Clamp X offset
        # Clampe le décalage X
        if scaled_width < label_width: # If image is smaller than label, center it / Si l'image est plus petite que l'étiquette, la centre
            self.view_offset_x = (scaled_width - label_width) / 2
        else:
            max_offset_x = scaled_width - label_width
            self.view_offset_x = max(0, min(self.view_offset_x, max_offset_x)) # Ensure offset is between 0 and max_offset_x / S'assure que le décalage est entre 0 et max_offset_x

        # Clamp Y offset
        # Clampe le décalage Y
        if scaled_height < label_height: # If image is smaller than label, center it / Si l'image est plus petite que l'étiquette, la centre
            self.view_offset_y = (scaled_height - label_height) / 2
        else:
            max_offset_y = scaled_height - label_height
            self.view_offset_y = max(0, min(self.view_offset_y, max_offset_y)) # Ensure offset is between 0 and max_offset_y / S'assure que le décalage est entre 0 et max_offset_y

    def get_text_input(self):
        """
        Opens a modal dialog to get text input from the user for TextAnnotation.
        Ouvre une boîte de dialogue modale pour obtenir la saisie de texte de l'utilisateur pour TextAnnotation.

        Returns:
            str or None: The text entered by the user, or None if dialog was cancelled.
                         Le texte saisi par l'utilisateur, ou Aucun si la boîte de dialogue a été annulée.
        """
        self.entered_text = None # Initialize to None, will be set by process_text_input / Initialise à Aucun, sera défini par process_text_input
        self.text_input_dialog = tk.Toplevel(self, bg='white')
        self.text_input_dialog.title("Ajouter du Texte")
        self.text_input_dialog.transient(self) # Make it a transient window of the main app / Le rend transitoire à la fenêtre principale de l'application
        self.text_input_dialog.update_idletasks() # Ensure window is drawn before centering / S'assure que la fenêtre est dessinée avant de centrer
        self.text_input_dialog.grab_set() # Make it modal (blocks interaction with main window) / Le rend modal (bloque l'interaction avec la fenêtre principale)

        tk.Label(self.text_input_dialog, text="Entrez le texte:").pack(pady=5)
        self.text_entry = ttk.Entry(self.text_input_dialog, width=40)
        self.text_entry.pack(pady=5)
        self.text_entry.focus_set() # Set focus to the entry widget / Définit le focus sur le widget de saisie

        ttk.Button(self.text_input_dialog, text="OK", command=self.process_text_input).pack(pady=5)

        # Center the dialog on the screen
        # Centre la boîte de dialogue sur l'écran
        self.text_input_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (self.text_input_dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (self.text_input_dialog.winfo_height() // 2)
        self.text_input_dialog.geometry(f"{self.text_input_dialog.winfo_width()}x{self.text_input_dialog.winfo_height()}+{x}+{y}")

        self.wait_window(self.text_input_dialog) # Wait for the dialog to close before returning / Attend que la boîte de dialogue se ferme avant de retourner
        return self.entered_text # Return the text after the dialog closes / Retourne le texte après la fermeture de la boîte de dialogue

    def process_text_input(self):
        """
        Callback for the text input dialog's OK button.
        Stores the entered text and destroys the dialog.
        Rappel pour le bouton OK de la boîte de dialogue de saisie de texte.
        Stocke le texte saisi et détruit la boîte de dialogue.
        """
        self.entered_text = self.text_entry.get()
        self.text_input_dialog.destroy()

    def clear_all_annotations(self):
        """
        Clears all annotations from the display and resets undo/redo stacks.
        Efface toutes les annotations de l'affichage et réinitialise les piles d'annulation/rétablissement.
        """
        self.annotations.clear() # Remove all annotations / Supprime toutes les annotations
        self.redo_stack.clear() # Clear redo stack as well / Efface également la pile de rétablissement
        self.undo_stack.clear() # Clear undo stack as well / Efface également la pile d'annulation

    def undo_last_annotation(self):
        """
        Undoes the last annotation action by moving it from annotations to redo_stack.
        Annule la dernière action d'annotation en la déplaçant des annotations vers redo_stack.
        """
        if self.annotations: # Only if there are annotations to undo / Uniquement s'il y a des annotations à annuler
            last_annotation = self.annotations.pop() # Remove the last annotation / Supprime la dernière annotation
            self.redo_stack.append(last_annotation) # Add it to the redo stack / L'ajoute à la pile de rétablissement

    def redo_last_annotation(self):
        """
        Redoes the last undone annotation action by moving it from redo_stack back to annotations.
        Rétablit la dernière action d'annotation annulée en la déplaçant de redo_stack vers les annotations.
        """
        if self.redo_stack: # Only if there are actions to redo / Uniquement s'il y a des actions à rétablir
            last_redone = self.redo_stack.pop() # Get the last item from redo stack / Obtient le dernier élément de la pile de rétablissement
            self.annotations.append(last_redone) # Add it back to active annotations / Le rajoute aux annotations actives

    def delete_selected_annotation(self, event=None):
        """
        Deletes the currently selected or hovered annotation.
        Supprime l'annotation actuellement sélectionnée ou survolée.

        Args:
            event (tk.Event, optional): The event object (e.g., from keyboard shortcut).
                                        L'objet événement (par exemple, à partir d'un raccourci clavier).
        """
        if self.selected_annotation: # If an annotation is explicitly selected / Si une annotation est explicitement sélectionnée
            self.annotations.remove(self.selected_annotation)
            self.selected_annotation = None # Clear selection / Efface la sélection
            self.hovered_annotation = None # Clear hover state / Efface l'état de survol
        elif self.hovered_annotation: # If an annotation is hovered but not selected / Si une annotation est survolée mais non sélectionnée
            self.annotations.remove(self.hovered_annotation)
            self.hovered_annotation = None # Clear hover state / Efface l'état de survol

    def open_settings_dialog(self):
        """
        Opens a modal dialog for camera settings (brightness, contrast, resolution).
        Ouvre une boîte de dialogue modale pour les paramètres de la caméra (luminosité, contraste, résolution).
        """
        settings_dialog = tk.Toplevel(self, bg='white')
        settings_dialog.title("Paramètres de la Caméra")
        settings_dialog.transient(self) # Make it transient / Le rend transitoire
        settings_dialog.grab_set() # Make it modal / Le rend modal

        # Brightness control slider
        # Curseur de contrôle de la luminosité
        ttk.Label(settings_dialog, text="Luminosité:").pack(pady=5)
        self.brightness_slider = ttk.Scale(settings_dialog, from_=0, to_=255, orient=tk.HORIZONTAL, command=self.set_brightness)
        # Set initial slider value from current camera setting or default
        # Définit la valeur initiale du curseur à partir du paramètre actuel de la caméra ou par défaut
        self.brightness_slider.set(self.video_stream_thread.cap.get(cv2.CAP_PROP_BRIGHTNESS) if self.video_stream_thread and self.video_stream_thread.cap else 128)
        self.brightness_slider.pack(fill=tk.X, padx=10, pady=5)

        # Contrast control slider
        # Curseur de contrôle du contraste
        ttk.Label(settings_dialog, text="Contraste:", background='white', style='White.TLabel').pack(pady=5)
        self.contrast_slider = ttk.Scale(settings_dialog, from_=0, to_=255, orient=tk.HORIZONTAL, style='White.Horizontal.TScale', command=self.set_contrast)
        # Set initial slider value from current camera setting or default
        # Définit la valeur initiale du curseur à partir du paramètre actuel de la caméra ou par défaut
        self.contrast_slider.set(self.video_stream_thread.cap.get(cv2.CAP_PROP_CONTRAST) if self.video_stream_thread and self.video_stream_thread.cap else 128)
        self.contrast_slider.pack(fill=tk.X, padx=10, pady=5)

        # Resolution control dropdown
        # Menu déroulant de contrôle de la résolution
        ttk.Label(settings_dialog, text="Résolution:", style='White.TLabel').pack(pady=5)
        self.resolution_var = tk.StringVar(settings_dialog)
        self.resolutions = ["640x480", "800x600", "1280x720", "1920x1080"] # Common resolutions / Résolutions courantes
        self.resolution_var.set(f"{self.current_resolution[0]}x{self.current_resolution[1]}") # Set current resolution as default / Définit la résolution actuelle comme valeur par défaut
        resolution_menu = ttk.OptionMenu(settings_dialog, self.resolution_var, self.resolution_var.get(), *self.resolutions, command=self.set_resolution)
        resolution_menu.pack(pady=5)

        ttk.Button(settings_dialog, text="Fermer", command=settings_dialog.destroy).pack(pady=10)

    def set_brightness(self, value):
        """
        Sets the camera's brightness property.
        Définit la propriété de luminosité de la caméra.

        Args:
            value (float): Brightness value (0-255).
                           Valeur de luminosité (0-255).
        """
        if self.video_stream_thread and self.video_stream_thread.cap:
            self.video_stream_thread.cap.set(cv2.CAP_PROP_BRIGHTNESS, float(value))

    def set_contrast(self, value):
        """
        Sets the camera's contrast property.
        Définit la propriété de contraste de la caméra.

        Args:
            value (float): Contrast value (0-255).
                           Valeur de contraste (0-255).
        """
        if self.video_stream_thread and self.video_stream_thread.cap:
            self.video_stream_thread.cap.set(cv2.CAP_PROP_CONTRAST, float(value))

    def set_resolution(self, resolution_str):
        """
        Sets the camera's resolution and restarts the video stream.
        Définit la résolution de la caméra et redémarre le flux vidéo.

        Args:
            resolution_str (str): Resolution string (e.g., "1280x720").
                                  Chaîne de résolution (par exemple, "1280x720").
        """
        width, height = map(int, resolution_str.split('x'))
        self.current_resolution = (width, height)
        if self.video_stream_thread: # If a video stream is active / Si un flux vidéo est actif
            self.video_stream_thread.stop() # Stop the current stream / Arrête le flux actuel
            self.video_stream_thread.join() # Wait for it to terminate / Attend qu'il se termine
            # Restart the video stream with the new resolution
            # Redémarre le flux vidéo avec la nouvelle résolution
            self.start_video_stream(self.video_stream_thread.camera_index, width, height)

    def flip_horizontal(self):
        """
        Flips the displayed image horizontally (for both file mode and webcam mode).
        Retourne l'image affichée horizontalement (pour le mode fichier et le mode webcam).
        """
        if self.file_mode and self.loaded_image: # If in file mode, flip the loaded image / Si en mode fichier, retourne l'image chargée
            self.loaded_image = self.loaded_image.transpose(Image.FLIP_LEFT_RIGHT)
        elif not self.file_mode and self.video_stream_thread and self.video_stream_thread.is_alive(): # If in webcam mode, tell the thread to flip / Si en mode webcam, indique au fil de retourner
            self.video_stream_thread.flip_horizontal()

    def flip_vertical(self):
        """
        Flips the displayed image vertically (for both file mode and webcam mode).
        Retourne l'image affichée verticalement (pour le mode fichier et le mode webcam).
        """
        if self.file_mode and self.loaded_image: # If in file mode, flip the loaded image / Si en mode fichier, retourne l'image chargée
            self.loaded_image = self.loaded_image.transpose(Image.FLIP_TOP_BOTTOM)
        elif not self.file_mode and self.video_stream_thread and self.video_stream_thread.is_alive(): # If in webcam mode, tell the thread to flip / Si en mode webcam, indique au fil de retourner
            self.video_stream_thread.flip_vertical()

    def open_file(self):
        """
        Opens a file dialog to select an image or PDF file for display.
        Ouvre une boîte de dialogue de fichier pour sélectionner un fichier image ou PDF à afficher.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("PDF Files", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        if not file_path: # If no file was selected / Si aucun fichier n'a été sélectionné
            return

        self.close_file() # Close any currently open file or stop webcam / Ferme tout fichier actuellement ouvert ou arrête la webcam
        self.file_mode = True # Switch to file mode / Passe en mode fichier
        self.camera_selection_frame.pack_forget() # Hide camera selection UI / Masque l'interface utilisateur de sélection de la caméra

        if file_path.lower().endswith('.pdf'): # If it's a PDF file / Si c'est un fichier PDF
            self.pdf_document = fitz.open(file_path) # Open PDF document / Ouvre le document PDF
            self.pdf_pages = [page for page in self.pdf_document] # Get all pages / Obtient toutes les pages
            self.current_pdf_page = 0 # Start at the first page / Commence à la première page
            self.load_pdf_page(self.current_pdf_page) # Load and display the first page / Charge et affiche la première page
            self.show_pdf_nav() # Show PDF navigation buttons / Affiche les boutons de navigation PDF
        else: # If it's an image file / Si c'est un fichier image
            try:
                self.loaded_image = Image.open(file_path).convert("RGB") # Open and convert image to RGB / Ouvre et convertit l'image en RGB
                self.display_image(self.loaded_image)
            except Exception as e:
                messagebox.showerror("Erreur d'ouverture", f"Impossible d'ouvrir le fichier image:\n{e}")
                self.close_file() # Revert to webcam mode on error / Revient au mode webcam en cas d'erreur

    def close_file(self):
        """
        Closes the currently open file (image or PDF) and reverts to webcam mode.
        Ferme le fichier actuellement ouvert (image ou PDF) et revient au mode webcam.
        """
        self.file_mode = False # Exit file mode / Quitte le mode fichier
        self.loaded_image = None # Clear loaded image / Efface l'image chargée
        if self.pdf_document: # If a PDF was open, close it / Si un PDF était ouvert, le ferme
            self.pdf_document.close()
        self.pdf_document = None
        self.pdf_pages = []
        self.current_pdf_page = 0
        self.hide_pdf_nav() # Hide PDF navigation buttons / Masque les boutons de navigation PDF
        self.camera_selection_frame.pack(side=tk.LEFT, padx=10) # Show camera selection UI / Affiche l'interface utilisateur de sélection de la caméra
        if self.camera_options: # If cameras are available, restart the stream / Si des caméras sont disponibles, redémarre le flux
            self.select_camera(self.camera_var.get())

    def load_pdf_page(self, page_number):
        """
        Loads and displays a specific page from the loaded PDF document.
        Charge et affiche une page spécifique du document PDF chargé.

        Args:
            page_number (int): The 0-based index of the PDF page to load.
                                L'index (base 0) de la page PDF à charger.
        """
        if self.pdf_document and 0 <= page_number < len(self.pdf_pages): # Ensure document is open and page number is valid / S'assure que le document est ouvert et que le numéro de page est valide
            page = self.pdf_pages[page_number]
            pix = page.get_pixmap() # Render page to pixmap / Rend la page en pixmap
            self.loaded_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) # Convert pixmap to PIL Image / Convertit le pixmap en image PIL
            self.current_pdf_page = page_number
            self.display_image(self.loaded_image) # Display the loaded page / Affiche la page chargée
            self.page_label.config(text=f"Page {self.current_pdf_page + 1} / {len(self.pdf_pages)}") # Update page number display / Met à jour l'affichage du numéro de page

    def next_pdf_page(self):
        """
        Navigates to the next page of the PDF document, if available.
        Navigue vers la page suivante du document PDF, si disponible.
        """
        if self.current_pdf_page < len(self.pdf_pages) - 1: # Check if not on the last page / Vérifie si ce n'est pas la dernière page
            self.load_pdf_page(self.current_pdf_page + 1)

    def prev_pdf_page(self):
        """
        Navigates to the previous page of the PDF document, if available.
        Navigue vers la page précédente du document PDF, si disponible.
        """
        if self.current_pdf_page > 0: # Check if not on the first page / Vérifie si ce n'est pas la première page
            self.load_pdf_page(self.current_pdf_page - 1)

    def show_pdf_nav(self):
        """
        Shows the PDF navigation buttons and page label.
        Affiche les boutons de navigation PDF et l'étiquette de page.
        """
        self.prev_page_button.pack(side=tk.LEFT)
        self.page_label.pack(side=tk.LEFT, padx=5)
        self.next_page_button.pack(side=tk.LEFT)

    def hide_pdf_nav(self):
        """
        Hides the PDF navigation buttons and page label.
        Masque les boutons de navigation PDF et l'étiquette de page.
        """
        self.prev_page_button.pack_forget()
        self.page_label.pack_forget()
        self.next_page_button.pack_forget()