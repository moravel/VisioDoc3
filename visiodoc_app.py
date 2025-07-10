import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import datetime
import os
import sys # Import sys
import threading
import time
import json # Import json for config file
import pyi_splash # Import pyi_splash
import platform
if platform.system() == "Windows":
    try:
        from pygrabber.dshow_graph import DSShow
    except ImportError:
        DSShow = None
import fitz  # PyMuPDF
from annotations import LineAnnotation, RectangleAnnotation, CircleAnnotation, FreeDrawAnnotation, TextAnnotation, BlurAnnotation, ArrowAnnotation, HighlightAnnotation # Import new annotation classes
from tooltip import Tooltip
from video_stream import VideoStreamThread

class VisioDoc3(tk.Tk):
    ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
    CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "camera_config.json"))
    def __init__(self):
        super().__init__()
        self.title("VisioDoc3 - Visionneuse de Documents")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}")
        self.configure(bg='white') # Set main window background to white

        # Configure style for white theme
        style = ttk.Style()
        style.theme_use('clam') # Use clam theme as a base for better customization
        style.configure('White.TFrame', background='white')
        style.configure('White.TButton', background='white', foreground='black', borderwidth=1, relief="solid")
        style.map('White.TButton', background=[('active', '#e0e0e0'), ('pressed', '#d0d0d0')]) # Lighter white on hover, slightly darker on press
        style.configure('White.TLabel', background='white', foreground='black')
        style.configure('White.TMenubutton', background='white', foreground='black', borderwidth=1, relief="solid")
        style.map('White.TMenubutton', background=[('active', '#e0e0e0'), ('pressed', '#d0d0d0')])
        style.configure('White.Horizontal.TScale', background='white', troughcolor='#e0e0e0')

        # Default resolution for the camera
        self.current_resolution = (1280, 720)

        self.video_stream_thread = None
        self.current_photo = None
        self.annotations = []
        self.undo_stack = [] # For storing undone annotations
        self.redo_stack = [] # For storing annotations that can be redone
        self.current_tool = "none" # "none", "line", "rectangle", "circle", "text", "blur", "arrow", "highlight", "freedraw"
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self.current_freedraw_points = [] # For freedraw tool
        self.current_annotation_color = (0, 0, 255) # Default to blue (BGR for OpenCV)
        self.current_annotation_thickness = 2 # Default thickness
        self.current_font_size = 20 # Default font size
        self.selected_annotation = None # To store the selected annotation object
        self.hovered_annotation = None # To store the annotation currently under the mouse
        self.resize_handle = None # To store the selected resize handle

        # File mode variables
        self.file_mode = False
        self.loaded_image = None
        self.pdf_document = None
        self.pdf_pages = []
        self.current_pdf_page = 0

        # Zoom and Pan state
        self.zoom_level = 1.0 # Initial zoom level, fills the entire space
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        self.view_for_saving = None

        # Main layout
        self.main_frame = ttk.Frame(self, style='White.TFrame') # Apply custom style
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.main_frame.grid_columnconfigure(0, weight=0) # Left panel
        self.main_frame.grid_columnconfigure(1, weight=1) # Video area
        self.main_frame.grid_columnconfigure(2, weight=0) # Right panel
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Left Panel (Annotation Tools)
        self.left_panel = ttk.Frame(self.main_frame, width=150, style='White.TFrame')
        self.left_panel.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        self.left_panel.grid_propagate(False) # Prevent frame from resizing to content

        # Buttons for annotation tools
        self.icons = {}
        self._load_icons()

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

        # Add a separator and zoom controls
        ttk.Separator(self.left_panel, orient='horizontal').pack(fill='x', pady=10, padx=5)
        zoom_frame = ttk.Frame(self.left_panel, style='White.TFrame')
        zoom_frame.pack(fill=tk.X, pady=2)
        ttk.Label(zoom_frame, text="Zoom:", style='White.TLabel').pack(side=tk.LEFT, padx=5)
        zoom_in_button = ttk.Button(zoom_frame, text="+", style='White.TButton', command=self.zoom_in, width=3)
        zoom_in_button.pack(side=tk.LEFT)
        Tooltip(zoom_in_button, "Zoom avant (Ctrl++)")
        zoom_out_button = ttk.Button(zoom_frame, text="-", style='White.TButton', command=self.zoom_out, width=3)
        zoom_out_button.pack(side=tk.LEFT)
        Tooltip(zoom_out_button, "Zoom arrière (Ctrl+-)")


        # Video Display Area
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ttk.Label(self.video_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Display a placeholder image immediately
        self.placeholder_image = Image.new('RGB', (self.current_resolution[0], self.current_resolution[1]), (50, 50, 50)) # Dark grey background
        draw = ImageDraw.Draw(self.placeholder_image)
        text = "Chargement de la caméra..."
        text_color = (200, 200, 200) # Light grey text
        try:
            font = ImageFont.truetype("arial.ttf", 30) # Use a common font
        except IOError:
            font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (self.current_resolution[0] - text_width) // 2
        text_y = (self.current_resolution[1] - text_height) // 2
        draw.text((text_x, text_y), text, font=font, fill=text_color)
        self.current_photo = ImageTk.PhotoImage(self.placeholder_image)
        self.image_label.config(image=self.current_photo)

        self.image_label.bind("<Button-1>", self.on_mouse_down)
        self.image_label.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_label.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.image_label.bind("<Motion>", self.on_mouse_move)
        self.image_label.bind("<MouseWheel>", self.on_mouse_wheel) # For Windows/macOS
        self.image_label.bind("<Button-4>", self.on_mouse_wheel) # For Linux scroll up
        self.image_label.bind("<Button-5>", self.on_mouse_wheel) # For Linux scroll down
        self.image_label.bind("<Button-2>", self.on_pan_start) # Middle mouse button
        self.image_label.bind("<B2-Motion>", self.on_pan_move)
        self.image_label.bind("<ButtonRelease-2>", self.on_pan_end)


        # Camera and PDF Controls
        self.controls_frame = ttk.Frame(self.video_frame)
        self.controls_frame.grid(row=1, column=0, pady=5)

        self.camera_selection_frame = ttk.Frame(self.controls_frame)
        self.camera_selection_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(self.camera_selection_frame, text="Sélectionner Webcam:").pack(side=tk.LEFT, padx=5)
        self.camera_var = tk.StringVar(self)
        self.camera_options = []
        self.camera_menu_placeholder = ttk.Label(self.camera_selection_frame, text="Recherche de caméras en cours...")
        self.camera_menu_placeholder.pack(side=tk.LEFT)
        
        self.pdf_navigation_frame = ttk.Frame(self.controls_frame)
        self.pdf_navigation_frame.pack(side=tk.LEFT, padx=10)
        self.prev_page_button = ttk.Button(self.pdf_navigation_frame, text="<", command=self.prev_pdf_page, width=3)
        self.page_label = ttk.Label(self.pdf_navigation_frame, text="")
        self.next_page_button = ttk.Button(self.pdf_navigation_frame, text=">", command=self.next_pdf_page, width=3)

        self.camera_population_thread = threading.Thread(target=self._initialize_camera, daemon=True)
        self.camera_population_thread.start()

        # Right Panel (Action Buttons)
        self.right_panel = ttk.Frame(self.main_frame, width=150, style='White.TFrame')
        self.right_panel.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        self.right_panel.grid_propagate(False)

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

        # Add logo to the bottom of the right panel
        self.logo_photo = self.icons.get("logo") # Store a reference to prevent garbage collection
        logo_label = ttk.Label(self.right_panel, image=self.logo_photo, background='white')
        logo_label.pack(side=tk.BOTTOM, pady=10)

        self.bind("<Delete>", self.delete_selected_annotation)
        
        # Keyboard Shortcuts
        self.bind("<Control-o>", lambda event: self.open_file())
        self.bind("<Control-f>", lambda event: self.set_tool("freedraw"))
        self.bind("<Control-r>", lambda event: self.set_tool("rectangle"))
        self.bind("<Control-c>", lambda event: self.set_tool("circle"))
        self.bind("<Control-l>", lambda event: self.set_tool("line"))
        self.bind("<Control-t>", lambda event: self.set_tool("text"))
        self.bind("<Control-b>", lambda event: self.set_tool("blur"))
        self.bind("<Control-a>", lambda event: self.set_tool("arrow"))
        self.bind("<Control-h>", lambda event: self.set_tool("highlight"))
        self.bind("<Control-s>", lambda event: self.set_tool("selection"))
        
        self.bind("<Control-Shift-S>", lambda event: self.save_image())
        self.bind("<Control-e>", lambda event: self.clear_all_annotations())
        self.bind("<Control-z>", lambda event: self.undo_last_annotation())
        self.bind("<Control-y>", lambda event: self.redo_last_annotation())
        self.bind("<Control-p>", lambda event: self.open_settings_dialog())
        
        self.bind("<Control-plus>", self.zoom_in)
        self.bind("<Control-equal>", self.zoom_in) # For keyboards where + is Shift+=
        self.bind("<Control-minus>", self.zoom_out)

        self.bind("<Control-k>", lambda event: self.choose_annotation_color())
        self.bind("<Control-i>", lambda event: self.choose_annotation_size())
        self.bind("<Control-j>", lambda event: self.flip_horizontal())
        self.bind("<Control-u>", lambda event: self.flip_vertical())

        self.bind("<Control-question>", lambda event: self.show_help())

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_display()
        if pyi_splash.is_alive():
            pyi_splash.close()

    def _load_icons(self):
        icon_names = {
            "freedraw": "freedraw.png",
            "rectangle": "rectangle.png",
            "circle": "circle.png",
            "line": "line.png",
            "text": "text.png",
            "blur": "blur.png",
            "arrow": "arrow.png",
            "highlight": "highlight.png",
            "color_picker": "color_picker.png",
            "size_picker": "size_picker.png",
            "save": "save.png",
            "clear": "clear.png",
            "undo": "undo.png",
            "redo": "redo.png",
            "settings": "settings.png",
            "logo": "logoVisioDoc3.png",
            "selection": "selection.png",
            "delete": "delete.png",
            "help": "help.png",
            "open_file": "open_file.png",
            "close_file": "close_file.png",
            "flip_horizontal": "flip_horizontal.png",
            "flip_vertical": "flip_vertical.png"
        }
        for name, filename in icon_names.items():
            try:
                path = os.path.join(self.ICON_DIR, filename)
                img = Image.open(path)
                img = img.resize((16, 16), Image.LANCZOS) # Resize icons to 16x16
                self.icons[name] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Warning: Icon file not found: {filename}")
                # Create a simple placeholder image if the icon is not found
                if name == "help":
                    placeholder_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0)) # Transparent background
                    draw = ImageDraw.Draw(placeholder_img)
                    draw.text((0, 0), "?", fill=(0, 0, 0)) # Black question mark
                    self.icons[name] = ImageTk.PhotoImage(placeholder_img)
                else:
                    self.icons[name] = None # Set to None if not found
            except Exception as e:
                print(f"Error loading icon {filename}: {e}")
                if name == "help":
                    placeholder_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0)) # Transparent background
                    draw = ImageDraw.Draw(placeholder_img)
                    draw.text((0, 0), "?", fill=(0, 0, 0)) # Black question mark
                    self.icons[name] = ImageTk.PhotoImage(placeholder_img)
                else:
                    self.icons[name] = None # Set to None if not found
        # Special handling for the logo to make it larger
        try:
            path = os.path.join(self.ICON_DIR, "logoVisioDoc3.png")
            img = Image.open(path)
            # Resize logo to fit the panel width (150px), with some padding
            base_width = 140
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), Image.LANCZOS)
            self.icons["logo"] = ImageTk.PhotoImage(img)
        except FileNotFoundError:
            print(f"Warning: Icon file not found: logoVisioDoc3.png")
            self.icons["logo"] = None

    def show_help(self):
        help_dialog = tk.Toplevel(self)
        help_dialog.title("Manuel d'Utilisateur VisioDoc3")
        help_dialog.transient(self)
        help_dialog.grab_set()

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
        text_widget.config(state="disabled") # Make it read-only
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(help_dialog, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        ttk.Button(help_dialog, text="Fermer", command=help_dialog.destroy).pack(pady=10)

        # Center the dialog
        help_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (help_dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (help_dialog.winfo_height() // 2)
        help_dialog.geometry(f"{help_dialog.winfo_width()}x{help_dialog.winfo_height()}+{x}+{y}")

    def _initialize_camera(
        self,
    ):  # This function is called in a separate thread, so it cannot directly update Tkinter widgets.
        # Try to load cached camera index
        cached_camera_index = self._load_camera_config()
        if cached_camera_index is not None:
            print(f"Attempting to open cached camera {cached_camera_index}...")
            # On Windows, we can't just check if it's open, we need to get the device list first
            if platform.system() == "Windows":
                self.populate_cameras()
                return

            cap = cv2.VideoCapture(cached_camera_index)
            if cap.isOpened():
                print(f"Successfully opened cached camera {cached_camera_index}.")
                self.camera_options.append((f"Webcam {cached_camera_index}", cached_camera_index))
                cap.release()
                self.after(0, lambda: self.update_camera_menu(initial_camera_index=cached_camera_index))
                return
            else:
                print(f"Cached camera {cached_camera_index} not available. Scanning for cameras...")

        # If cached camera fails or not found, proceed with full scan
        self.populate_cameras()

    def _load_camera_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('last_camera_index')
            except json.JSONDecodeError:
                print("Error decoding camera config file.")
        return None

    def _save_camera_config(self, camera_index):
        config = {'last_camera_index': camera_index}
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except IOError as e:
            print(f"Error saving camera config file: {e}")

    def update_camera_menu(self, initial_camera_index=None):
        self.camera_menu_placeholder.pack_forget()

        if self.camera_options:
            # Sort cameras by index to ensure consistent order
            self.camera_options.sort(key=lambda x: x[1])
            
            # Set initial value based on cached or first available
            if initial_camera_index is not None and any(opt[1] == initial_camera_index for opt in self.camera_options):
                self.camera_var.set(f"Webcam {initial_camera_index}")
                selected_index = initial_camera_index
            else:
                self.camera_var.set(self.camera_options[0][0])
                selected_index = self.camera_options[0][1]

            self.camera_menu = ttk.OptionMenu(self.camera_selection_frame, self.camera_var, self.camera_var.get(), *[opt[0] for opt in self.camera_options], style='White.TMenubutton', command=self.select_camera)
            self.camera_menu.pack(side=tk.LEFT)
            Tooltip(self.camera_menu, "Sélectionne la webcam à utiliser")
            self.start_video_stream(selected_index, self.current_resolution[0], self.current_resolution[1])
            self._save_camera_config(selected_index) # Save the successfully opened camera
        else:
            ttk.Label(self.camera_selection_frame, text="Aucune webcam trouvée", style='White.TLabel').pack(side=tk.LEFT)

    def _check_camera(self, index, results_list, initial_camera_found):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            results_list.append((f"Webcam {index}", index))
            if not initial_camera_found[0]:
                self.after(0, lambda: self.start_video_stream(index, self.current_resolution[0], self.current_resolution[1]))
                self.after(0, lambda: self._save_camera_config(index))
                initial_camera_found[0] = True
            cap.release()

    def populate_cameras(self):
        if platform.system() == "Windows" and DSShow is not None:
            try:
                devices = DSShow.get_input_devices()
                for i, device_name in enumerate(devices):
                    self.camera_options.append((device_name, i))
                self.after(0, self.update_camera_menu)
            except Exception as e:
                print(f"Error using pygrabber: {e}")
                # Fallback to the old method if pygrabber fails
                self._populate_cameras_linux()
        else:
            self._populate_cameras_linux()

    def _populate_cameras_linux(self):
        # This function now runs in a separate thread and spawns sub-threads to check cameras in parallel
        threads = []
        found_cameras = []
        initial_camera_found = [False] # Use a mutable list to pass by reference
        for i in range(10): # Check up to 10 cameras
            thread = threading.Thread(target=self._check_camera, args=(i, found_cameras, initial_camera_found), daemon=True)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join() # Wait for all threads to complete

        self.camera_options = found_cameras
        self.after(0, self.update_camera_menu) # Call update_camera_menu without initial_camera_index

    def start_video_stream(self, camera_index, width, height):
        if self.video_stream_thread and self.video_stream_thread.is_alive():
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        
        self.video_stream_thread = VideoStreamThread(camera_index, width, height)
        self.video_stream_thread.start()

    def select_camera(self, camera_name):
        for name, index in self.camera_options:
            if name == camera_name:
                self.start_video_stream(index, self.current_resolution[0], self.current_resolution[1])
                self._save_camera_config(index) # Save selected camera
                break

    def update_display(self):
        if self.file_mode:
            if self.loaded_image:
                self.display_image(self.loaded_image)
        elif self.video_stream_thread and self.video_stream_thread.is_alive():
            frame = self.video_stream_thread.get_frame()
            if frame is not None:
                self.display_image(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        
        self.after(10, self.update_display)

    def display_image(self, pil_image):
        # Create a copy of the image for display purposes
        display_image = pil_image.copy()
        display_image_cv = cv2.cvtColor(np.array(display_image), cv2.COLOR_RGB2BGR)

        # Draw existing annotations on the display frame
        for annotation in self.annotations:
            annotation.draw(display_image_cv)

        # Draw bounding box for selected annotation
        if self.selected_annotation:
            bbox = self.selected_annotation.get_bounding_box()
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[2]), int(bbox[3]))
                cv2.rectangle(display_image_cv, p1, p2, (0, 255, 0), 2, cv2.LINE_AA)
                # Draw resize handles
                handles = self.selected_annotation.get_resize_handles()
                for handle in handles.values():
                    cv2.rectangle(display_image_cv, (int(handle[0])-8, int(handle[1])-8), (int(handle[0])+8, int(handle[1])+8), (0, 255, 0), -1)
        elif self.hovered_annotation:
            bbox = self.hovered_annotation.get_bounding_box()
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[2]), int(bbox[3]))
                cv2.rectangle(display_image_cv, p1, p2, (255, 165, 0), 2, cv2.LINE_AA) # Orange for hover

        # Draw temporary annotation if currently drawing
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
            elif self.current_tool == "freedraw" and self.current_freedraw_points:
                temp_annotation = FreeDrawAnnotation(self.current_freedraw_points, color=(0, 255, 255), thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "blur":
                overlay = display_image_cv.copy()
                x1, y1 = self.start_point
                x2, y2 = self.end_point
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 0), -1)
                alpha = 0.3
                display_image_cv = cv2.addWeighted(overlay, alpha, display_image_cv, 1 - alpha, 0)
            elif self.current_tool == "arrow":
                temp_annotation = ArrowAnnotation(self.start_point, self.end_point, color=(0, 0, 255), thickness=self.current_annotation_thickness)
                temp_annotation.draw(display_image_cv)
            elif self.current_tool == "highlight":
                overlay = display_image_cv.copy()
                x1, y1 = self.start_point
                x2, y2 = self.end_point
                cv2.rectangle(overlay, (x1, y1), (x2, y2), self.current_annotation_color, -1)
                alpha = 0.3
                display_image_cv = cv2.addWeighted(overlay, alpha, display_image_cv, 1 - alpha, 0)

        # Convert the final annotated frame to PIL
        final_annotated_pil = Image.fromarray(cv2.cvtColor(display_image_cv, cv2.COLOR_BGR2RGB))
        original_width, original_height = final_annotated_pil.size

        # Apply zoom
        scaled_width = int(original_width * self.zoom_level)
        scaled_height = int(original_height * self.zoom_level)
        
        if scaled_width <= 0 or scaled_height <= 0:
            return

        scaled_image = final_annotated_pil.resize((scaled_width, scaled_height), Image.LANCZOS)

        # Create the final view canvas
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        final_view = Image.new('RGB', (label_width, label_height), (200, 200, 200))

        # Clamp offsets to valid range
        self.clamp_offsets()

        # Calculate paste position
        paste_x = -int(self.view_offset_x)
        paste_y = -int(self.view_offset_y)
        
        # When zoomed out, the image is smaller than the label. Center it.
        if scaled_width < label_width:
            paste_x = (label_width - scaled_width) // 2
        if scaled_height < label_height:
            paste_y = (label_height - scaled_height) // 2

        final_view.paste(scaled_image, (paste_x, paste_y))

        self.current_photo = ImageTk.PhotoImage(image=final_view)
        self.image_label.config(image=self.current_photo)
        self.pil_image_to_save = final_annotated_pil
        self.view_for_saving = final_view

    def on_closing(self):
        if self.video_stream_thread:
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        self.destroy()

    def choose_annotation_color(self):
        color_code = colorchooser.askcolor(title="Choisir la couleur de l'annotation")
        if color_code[1]: # If a color is selected
            rgb_color = color_code[0] # RGB tuple
            # Convert RGB to BGR for OpenCV
            self.current_annotation_color = (rgb_color[2], rgb_color[1], rgb_color[0])

    def choose_annotation_size(self):
        size_dialog = tk.Toplevel(self, bg='white')
        size_dialog.title("Choisir la taille")
        size_dialog.transient(self)
        size_dialog.grab_set()

        ttk.Label(size_dialog, text="Épaisseur du trait:").pack(pady=5)
        thickness_slider = ttk.Scale(size_dialog, from_=1, to_=50, orient=tk.HORIZONTAL)
        thickness_slider.set(self.current_annotation_thickness)
        thickness_slider.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(size_dialog, text="Taille de la police:").pack(pady=5)
        font_size_slider = ttk.Scale(size_dialog, from_=8, to_=72, orient=tk.HORIZONTAL)
        font_size_slider.set(self.current_font_size)
        font_size_slider.pack(fill=tk.X, padx=10, pady=5)

        def on_ok():
            self.current_annotation_thickness = int(thickness_slider.get())
            self.current_font_size = int(font_size_slider.get())
            size_dialog.destroy()

        ttk.Button(size_dialog, text="OK", command=on_ok).pack(pady=10)

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self.current_freedraw_points = []
        self.entered_text = "" # Reset entered text when tool changes
        if tool_name == "text":
            pass # The text input dialog will be triggered on mouse click for text tool
        elif tool_name == "blur":
            self.start_point = None
            self.end_point = None
        elif tool_name == "arrow":
            self.start_point = None
            self.end_point = None
        elif tool_name == "highlight":
            self.start_point = None
            self.end_point = None
        elif tool_name == "selection":
            self.selected_annotation = None
            self.hovered_annotation = None

    def save_image(self):
        if hasattr(self, 'view_for_saving'):
            img_to_save = self.view_for_saving

            file_path = filedialog.asksaveasfilename(
                filetypes=[("Fichiers PNG", "*.png"), ("Fichiers PDF", "*.pdf")],
                title="Sauvegarder l'image annotée"
            )

            if file_path:
                selected_ext = ".png"
                for desc, pattern in [("Fichiers PNG", "*.png"), ("Fichiers PDF", "*.pdf")]:
                    if file_path.lower().endswith(pattern[1:]):
                        selected_ext = pattern[1:]
                        break
                
                name, ext = os.path.splitext(file_path)
                if not ext or ext.lower() != selected_ext:
                    file_path = name + selected_ext

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                directory, filename = os.path.split(file_path)
                name, ext = os.path.splitext(filename)
                
                final_filename = os.path.join(directory, f"{timestamp}_{name}{ext}")

                try:
                    if ext.lower() == ".pdf":
                        img_to_save.convert('RGB').save(final_filename, "PDF", resolution=100.0)
                    else:
                        img_to_save.save(final_filename)
                    messagebox.showinfo("Sauvegarde", f"Image sauvegardée avec succès :\n{final_filename}")
                except Exception as e:
                    messagebox.showerror("Erreur de Sauvegarde", f"Impossible de sauvegarder l'image :\n{e}")
        else:
            messagebox.showwarning("Avertissement", "Aucune image à sauvegarder.")

    def _convert_event_to_original_coords(self, event):
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        
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

        paste_x = -int(self.view_offset_x)
        paste_y = -int(self.view_offset_y)
        if scaled_width < label_width:
            paste_x = (label_width - scaled_width) // 2
        if scaled_height < label_height:
            paste_y = (label_height - scaled_height) // 2

        scaled_image_x = event.x - paste_x
        scaled_image_y = event.y - paste_y

        original_x = scaled_image_x / self.zoom_level
        original_y = scaled_image_y / self.zoom_level

        return (int(original_x), int(original_y))

    def on_mouse_down(self, event):
        click_point = self._convert_event_to_original_coords(event)

        if self.current_tool == "selection":
            self.resize_handle = None
            if self.selected_annotation:
                handles = self.selected_annotation.get_resize_handles()
                for handle_name, handle_pos in handles.items():
                    # Increase handle click area for usability
                    if abs(handle_pos[0] - click_point[0]) < 15 / self.zoom_level and abs(handle_pos[1] - click_point[1]) < 15 / self.zoom_level:
                        self.resize_handle = handle_name
                        self.initial_drag_point_for_resize = click_point
                        self.drawing = True
                        return

            newly_selected = None
            for annotation in reversed(self.annotations):
                if annotation.is_point_inside(click_point):
                    newly_selected = annotation
                    break
            
            if newly_selected:
                self.selected_annotation = newly_selected
                self.start_point = click_point
                self.drawing = True
            else:
                self.selected_annotation = None
                self.drawing = False

        elif self.current_tool == "text":
            entered_text = self.get_text_input()
            if entered_text:
                self.annotations.append(TextAnnotation(click_point, entered_text, color=self.current_annotation_color, font_size=self.current_font_size))
                self.redo_stack.clear()
                self.set_tool("selection")
        elif self.current_tool != "none":
            self.drawing = True
            self.start_point = click_point
            self.end_point = click_point

    def on_mouse_drag(self, event):
        if not self.drawing:
            return

        current_point = self._convert_event_to_original_coords(event)

        if self.current_tool == "selection" and self.selected_annotation:
            dx = current_point[0] - self.start_point[0]
            dy = current_point[1] - self.start_point[1]
            if self.resize_handle:
                self.selected_annotation.resize(self.resize_handle, current_point, self.initial_drag_point_for_resize)
            else:
                self.selected_annotation.move(dx, dy)
            self.start_point = current_point
        elif self.current_tool != "selection":
            self.end_point = current_point
            if self.current_tool == "freedraw":
                self.current_freedraw_points.append(self.end_point)

    def on_mouse_up(self, event):
        if not self.drawing:
            return

        self.drawing = False
        self.resize_handle = None
        
        if self.current_tool != "selection":
            final_point = self._convert_event_to_original_coords(event)
            self.end_point = final_point

            if self.start_point == self.end_point: # Ignore zero-size shapes
                return

            if self.current_tool == "line":
                self.annotations.append(LineAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "rectangle":
                self.annotations.append(RectangleAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "circle":
                center_x = (self.start_point[0] + self.end_point[0]) // 2
                center_y = (self.start_point[1] + self.end_point[1]) // 2
                radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                if radius > 0:
                    self.annotations.append(CircleAnnotation((center_x, center_y), radius, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "freedraw":
                if self.current_freedraw_points:
                    self.annotations.append(FreeDrawAnnotation(list(self.current_freedraw_points), color=self.current_annotation_color, thickness=self.current_annotation_thickness))
                self.current_freedraw_points = []
            elif self.current_tool == "blur":
                self.annotations.append(BlurAnnotation(self.start_point, self.end_point))
            elif self.current_tool == "arrow":
                self.annotations.append(ArrowAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "highlight":
                self.annotations.append(HighlightAnnotation(self.start_point, self.end_point, color=self.current_annotation_color))
            
            self.redo_stack.clear()
            self.start_point = None
            self.end_point = None

    def on_mouse_move(self, event):
        if self.current_tool == "selection" and not self.drawing:
            mouse_point = self._convert_event_to_original_coords(event)
            self.hovered_annotation = None
            for annotation in reversed(self.annotations):
                if annotation.is_point_inside(mouse_point):
                    self.hovered_annotation = annotation
                    break

    def zoom_in(self, event=None):
        if event is None:
            event = tk.Event()
            event.x = self.image_label.winfo_width() / 2
            event.y = self.image_label.winfo_height() / 2
        self.zoom(1.1, event.x, event.y)

    def zoom_out(self, event=None):
        if event is None:
            event = tk.Event()
            event.x = self.image_label.winfo_width() / 2
            event.y = self.image_label.winfo_height() / 2
        self.zoom(0.9, event.x, event.y)

    def on_mouse_wheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.zoom(0.9, event.x, event.y)
        elif event.num == 4 or event.delta > 0:
            self.zoom(1.1, event.x, event.y)

    def zoom(self, factor, x, y):
        old_zoom_level = self.zoom_level
        new_zoom_level = old_zoom_level * factor
        new_zoom_level = max(0.1, min(new_zoom_level, 10.0))
        self.zoom_level = new_zoom_level

        original_x = (x + self.view_offset_x) / old_zoom_level
        original_y = (y + self.view_offset_y) / old_zoom_level

        self.view_offset_x = (original_x * self.zoom_level) - x
        self.view_offset_y = (original_y * self.zoom_level) - y
        
        self.clamp_offsets()

    def on_pan_start(self, event):
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_pan_move(self, event):
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.view_offset_x -= dx
            self.view_offset_y -= dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.clamp_offsets()

    def on_pan_end(self, event):
        self.is_panning = False

    def clamp_offsets(self):
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

        if scaled_width < label_width:
            self.view_offset_x = (scaled_width - label_width) / 2
        else:
            max_offset_x = scaled_width - label_width
            self.view_offset_x = max(0, min(self.view_offset_x, max_offset_x))

        if scaled_height < label_height:
            self.view_offset_y = (scaled_height - label_height) / 2
        else:
            max_offset_y = scaled_height - label_height
            self.view_offset_y = max(0, min(self.view_offset_y, max_offset_y))

    def get_text_input(self):
        self.entered_text = None # Initialize to None
        self.text_input_dialog = tk.Toplevel(self, bg='white')
        self.text_input_dialog.title("Ajouter du Texte")
        self.text_input_dialog.transient(self) # Make it a transient window of the main app
        self.text_input_dialog.update_idletasks() # Ensure window is drawn
        self.text_input_dialog.grab_set() # Make it modal

        tk.Label(self.text_input_dialog, text="Entrez le texte:").pack(pady=5)
        self.text_entry = ttk.Entry(self.text_input_dialog, width=40)
        self.text_entry.pack(pady=5)
        self.text_entry.focus_set()

        ttk.Button(self.text_input_dialog, text="OK", command=self.process_text_input).pack(pady=5)

        # Center the dialog
        self.text_input_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (self.text_input_dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (self.text_input_dialog.winfo_height() // 2)
        self.text_input_dialog.geometry(f"{self.text_input_dialog.winfo_width()}x{self.text_input_dialog.winfo_height()}+{x}+{y}")

        self.wait_window(self.text_input_dialog) # Wait for the dialog to close
        return self.entered_text # Return the text after the dialog closes

    def process_text_input(self):
        self.entered_text = self.text_entry.get()
        self.text_input_dialog.destroy()

    def clear_all_annotations(self):
        self.annotations.clear()
        self.redo_stack.clear() # Clear redo stack as well
        self.undo_stack.clear() # Clear undo stack as well

    def undo_last_annotation(self):
        if self.annotations:
            last_annotation = self.annotations.pop()
            self.redo_stack.append(last_annotation)
            # No explicit undo_stack needed, annotations list is the source of truth

    def redo_last_annotation(self):
        if self.redo_stack:
            last_redone = self.redo_stack.pop()
            self.annotations.append(last_redone)

    def delete_selected_annotation(self, event=None):
        if self.selected_annotation:
            self.annotations.remove(self.selected_annotation)
            self.selected_annotation = None
            self.hovered_annotation = None
        elif self.hovered_annotation:
            self.annotations.remove(self.hovered_annotation)
            self.hovered_annotation = None

    def open_settings_dialog(self):
        settings_dialog = tk.Toplevel(self, bg='white')
        settings_dialog.title("Paramètres de la Caméra")
        settings_dialog.transient(self)
        settings_dialog.grab_set()

        # Brightness control
        ttk.Label(settings_dialog, text="Luminosité:").pack(pady=5)
        self.brightness_slider = ttk.Scale(settings_dialog, from_=0, to_=255, orient=tk.HORIZONTAL, command=self.set_brightness)
        self.brightness_slider.set(self.video_stream_thread.cap.get(cv2.CAP_PROP_BRIGHTNESS) if self.video_stream_thread and self.video_stream_thread.cap else 128)
        self.brightness_slider.pack(fill=tk.X, padx=10, pady=5)

        # Contrast control
        ttk.Label(settings_dialog, text="Contraste:", background='white', style='White.TLabel').pack(pady=5)
        self.contrast_slider = ttk.Scale(settings_dialog, from_=0, to_=255, orient=tk.HORIZONTAL, style='White.Horizontal.TScale', command=self.set_contrast)
        self.contrast_slider.set(self.video_stream_thread.cap.get(cv2.CAP_PROP_CONTRAST) if self.video_stream_thread and self.video_stream_thread.cap else 128)
        self.contrast_slider.pack(fill=tk.X, padx=10, pady=5)

        # Resolution control
        ttk.Label(settings_dialog, text="Résolution:", style='White.TLabel').pack(pady=5)
        self.resolution_var = tk.StringVar(settings_dialog)
        self.resolutions = ["640x480", "800x600", "1280x720", "1920x1080"] # Common resolutions
        self.resolution_var.set(f"{self.current_resolution[0]}x{self.current_resolution[1]}")
        resolution_menu = ttk.OptionMenu(settings_dialog, self.resolution_var, self.resolution_var.get(), *self.resolutions, command=self.set_resolution)
        resolution_menu.pack(pady=5)

        ttk.Button(settings_dialog, text="Fermer", command=settings_dialog.destroy).pack(pady=10)

    def set_brightness(self, value):
        if self.video_stream_thread and self.video_stream_thread.cap:
            self.video_stream_thread.cap.set(cv2.CAP_PROP_BRIGHTNESS, float(value))

    def set_contrast(self, value):
        if self.video_stream_thread and self.video_stream_thread.cap:
            self.video_stream_thread.cap.set(cv2.CAP_PROP_CONTRAST, float(value))

    def set_resolution(self, resolution_str):
        width, height = map(int, resolution_str.split('x'))
        self.current_resolution = (width, height)
        if self.video_stream_thread:
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
            # Restart the video stream with the new resolution
            self.start_video_stream(self.video_stream_thread.camera_index, width, height)

    def flip_horizontal(self):
        if self.file_mode and self.loaded_image:
            self.loaded_image = self.loaded_image.transpose(Image.FLIP_LEFT_RIGHT)
        elif not self.file_mode and self.video_stream_thread and self.video_stream_thread.is_alive():
            self.video_stream_thread.flip_horizontal()

    def flip_vertical(self):
        if self.file_mode and self.loaded_image:
            self.loaded_image = self.loaded_image.transpose(Image.FLIP_TOP_BOTTOM)
        elif not self.file_mode and self.video_stream_thread and self.video_stream_thread.is_alive():
            self.video_stream_thread.flip_vertical()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("PDF Files", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return

        self.close_file() # Reset state before opening a new file
        self.file_mode = True
        self.camera_selection_frame.pack_forget()

        if file_path.lower().endswith('.pdf'):
            self.pdf_document = fitz.open(file_path)
            self.pdf_pages = [page for page in self.pdf_document]
            self.current_pdf_page = 0
            self.load_pdf_page(self.current_pdf_page)
            self.show_pdf_nav()
        else:
            try:
                self.loaded_image = Image.open(file_path).convert("RGB")
                self.display_image(self.loaded_image)
            except Exception as e:
                messagebox.showerror("Erreur d'ouverture", f"Impossible d'ouvrir le fichier image:\n{e}")
                self.close_file()

    def close_file(self):
        self.file_mode = False
        self.loaded_image = None
        if self.pdf_document:
            self.pdf_document.close()
        self.pdf_document = None
        self.pdf_pages = []
        self.current_pdf_page = 0
        self.hide_pdf_nav()
        self.camera_selection_frame.pack(side=tk.LEFT, padx=10)
        if self.camera_options:
            self.select_camera(self.camera_var.get())

    def load_pdf_page(self, page_number):
        if self.pdf_document and 0 <= page_number < len(self.pdf_pages):
            page = self.pdf_pages[page_number]
            pix = page.get_pixmap()
            self.loaded_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.current_pdf_page = page_number
            self.display_image(self.loaded_image)
            self.page_label.config(text=f"Page {self.current_pdf_page + 1} / {len(self.pdf_pages)}")

    def next_pdf_page(self):
        if self.current_pdf_page < len(self.pdf_pages) - 1:
            self.load_pdf_page(self.current_pdf_page + 1)

    def prev_pdf_page(self):
        if self.current_pdf_page > 0:
            self.load_pdf_page(self.current_pdf_page - 1)

    def show_pdf_nav(self):
        self.prev_page_button.pack(side=tk.LEFT)
        self.page_label.pack(side=tk.LEFT, padx=5)
        self.next_page_button.pack(side=tk.LEFT)

    def hide_pdf_nav(self):
        self.prev_page_button.pack_forget()
        self.page_label.pack_forget()
        self.next_page_button.pack_forget()
