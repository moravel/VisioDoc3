import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import datetime
import os
import threading
import time
from annotations import LineAnnotation, RectangleAnnotation, CircleAnnotation, FreeDrawAnnotation, TextAnnotation, BlurAnnotation, ArrowAnnotation, HighlightAnnotation # Import new annotation classes

ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")


class VideoStreamThread(threading.Thread):
    def __init__(self, camera_index=0, width=1280, height=720):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self._run_flag = True
        self.frame = None
        self.lock = threading.Lock()

    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.cap.isOpened():
            print(f"Error: Could not open video stream for camera {self.camera_index}")
            self._run_flag = False
            return

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            else:
                print("Error: Could not read frame.")
                break
            time.sleep(0.03) # Approx 30 FPS
        self.cap.release()

    def stop(self):
        self._run_flag = False

    def get_frame(self):
        with self.lock:
            return self.frame

    def set_camera(self, index):
        self.stop()
        self.join() # Wait for the old thread to finish
        self.camera_index = index
        self._run_flag = True
        self.start() # Start a new thread for the new camera

class VisioDoc3(tk.Tk):
    ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
    def __init__(self):
        super().__init__()
        self.title("VisioDoc3 - Visionneuse de Documents")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}")
        self.configure(bg='white') # Set main window background to white

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
        ttk.Button(self.left_panel, text="Rectangle", image=self.icons.get("rectangle"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("rectangle")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Cercle", image=self.icons.get("circle"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("circle")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Ligne", image=self.icons.get("line"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("line")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Ajouter Texte", image=self.icons.get("text"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("text")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Zone de Flou", image=self.icons.get("blur"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("blur")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Flèche", image=self.icons.get("arrow"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("arrow")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Surlignage", image=self.icons.get("highlight"), compound=tk.LEFT, style='White.TButton', command=lambda: self.set_tool("highlight")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Choisir Couleur", image=self.icons.get("color_picker"), compound=tk.LEFT, style='White.TButton', command=self.choose_annotation_color).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Choisir Taille", image=self.icons.get("size_picker"), compound=tk.LEFT, style='White.TButton', command=self.choose_annotation_size).pack(fill=tk.X, pady=2)

        # Video Display Area
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ttk.Label(self.video_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.image_label.bind("<Button-1>", self.on_mouse_down)
        self.image_label.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_label.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Camera Selection
        self.camera_selection_frame = ttk.Frame(self.video_frame)
        self.camera_selection_frame.grid(row=1, column=0, pady=5)

        ttk.Label(self.camera_selection_frame, text="Sélectionner Webcam:").pack(side=tk.LEFT, padx=5)

        self.camera_var = tk.StringVar(self)
        self.camera_options = []
        self.populate_cameras()
        
        if self.camera_options:
            self.camera_var.set(self.camera_options[0][0]) # Set initial value
            self.camera_menu = ttk.OptionMenu(self.camera_selection_frame, self.camera_var, self.camera_options[0][0], *[opt[0] for opt in self.camera_options], command=self.select_camera)
            self.camera_menu.pack(side=tk.LEFT)
            self.start_video_stream(self.camera_options[0][1], self.current_resolution[0], self.current_resolution[1])
        else:
            ttk.Label(self.camera_selection_frame, text="Aucune webcam trouvée").pack(side=tk.LEFT)

        # Right Panel (Action Buttons)
        self.right_panel = ttk.Frame(self.main_frame, width=150, style='White.TFrame')
        self.right_panel.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        self.right_panel.grid_propagate(False)

        ttk.Button(self.right_panel, text="Sauvegarder", image=self.icons.get("save"), compound=tk.LEFT, style='White.TButton', command=self.save_image).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Effacer Tout", image=self.icons.get("clear"), compound=tk.LEFT, style='White.TButton', command=self.clear_all_annotations).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Annuler (Undo)", image=self.icons.get("undo"), compound=tk.LEFT, style='White.TButton', command=self.undo_last_annotation).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Rétablir (Redo)", image=self.icons.get("redo"), compound=tk.LEFT, style='White.TButton', command=self.redo_last_annotation).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Paramètres", image=self.icons.get("settings"), compound=tk.LEFT, style='White.TButton', command=self.open_settings_dialog).pack(fill=tk.X, pady=2)

        # Add logo to the bottom of the right panel
        self.logo_photo = self.icons.get("logo") # Store a reference to prevent garbage collection
        logo_label = ttk.Label(self.right_panel, image=self.logo_photo, background='white')
        logo_label.pack(side=tk.BOTTOM, pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_video_frame()

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
        }
        for name, filename in icon_names.items():
            try:
                path = os.path.join(ICON_DIR, filename)
                img = Image.open(path)
                img = img.resize((16, 16), Image.LANCZOS) # Resize icons to 16x16
                self.icons[name] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Warning: Icon file not found: {filename}")
                self.icons[name] = None # Set to None if not found
        # Special handling for the logo to make it larger
        try:
            path = os.path.join(ICON_DIR, "logoVisioDoc3.png")
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

    def populate_cameras(self):
        # Try to find available cameras
        for i in range(10): # Check up to 10 cameras
            print(f"Attempting to open camera {i}...")
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"Successfully opened camera {i}.")
                self.camera_options.append((f"Webcam {i}", i))
                cap.release()
            else:
                print(f"Could not open camera {i}.")
                # If a camera index fails, it doesn't necessarily mean there are no more cameras.
                # Sometimes, higher indices might work even if lower ones don't.
                # So, we continue checking all 10 indices.
                pass

    def start_video_stream(self, camera_index, width, height):
        if self.video_stream_thread and self.video_stream_thread.is_alive():
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        
        self.video_stream_thread = VideoStreamThread(camera_index, width, height)
        self.video_stream_thread.start()

    def select_camera(self, camera_name):
        for name, index in self.camera_options:
            if name == camera_name:
                self.start_video_stream(index)
                break

    def update_video_frame(self):
        if self.video_stream_thread and self.video_stream_thread.is_alive():
            frame = self.video_stream_thread.get_frame()
            if frame is not None:
                # Create a copy of the frame for display purposes
                display_frame = frame.copy()

                

                # Draw existing annotations on the display frame
                for annotation in self.annotations:
                    annotation.draw(display_frame)

                # Draw temporary annotation if currently drawing
                if self.drawing and self.start_point and self.end_point:
                    if self.current_tool == "line":
                        temp_annotation = LineAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness)
                        temp_annotation.draw(display_frame)
                    elif self.current_tool == "rectangle":
                        temp_annotation = RectangleAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness)
                        temp_annotation.draw(display_frame)
                    elif self.current_tool == "circle":
                        center_x = (self.start_point[0] + self.end_point[0]) // 2
                        center_y = (self.start_point[1] + self.end_point[1]) // 2
                        radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                        temp_annotation = CircleAnnotation((center_x, center_y), radius, color=self.current_annotation_color, thickness=self.current_annotation_thickness)
                        print(f"Creating temporary CircleAnnotation with color: {self.current_annotation_color}")
                        temp_annotation.draw(display_frame)
                    elif self.current_tool == "freedraw" and self.current_freedraw_points:
                        temp_annotation = FreeDrawAnnotation(self.current_freedraw_points, color=(0, 255, 255), thickness=self.current_annotation_thickness)
                        temp_annotation.draw(display_frame)
                    elif self.current_tool == "blur":
                        # Draw a translucent rectangle to indicate the blur area
                        overlay = display_frame.copy()
                        x1, y1 = self.start_point
                        x2, y2 = self.end_point
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 0), -1) # Blue color, filled
                        alpha = 0.3 # Transparency factor
                        display_frame = cv2.addWeighted(overlay, alpha, display_frame, 1 - alpha, 0)
                    elif self.current_tool == "arrow":
                        temp_annotation = ArrowAnnotation(self.start_point, self.end_point, color=(0, 0, 255), thickness=self.current_annotation_thickness)
                        temp_annotation.draw(display_frame)
                    elif self.current_tool == "highlight":
                        # Draw a translucent rectangle to indicate the highlight area
                        overlay = display_frame.copy()
                        x1, y1 = self.start_point
                        x2, y2 = self.end_point
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), self.current_annotation_color, -1) # Yellow color, filled
                        alpha = 0.3 # Transparency factor
                        display_frame = cv2.addWeighted(overlay, alpha, display_frame, 1 - alpha, 0)

                # Convert the display frame to Tkinter compatible format
                rgb_image_annotated = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img_annotated = Image.fromarray(rgb_image_annotated)
                
                # Resize the image to fit the label
                label_width = self.image_label.winfo_width()
                label_height = self.image_label.winfo_height()

                if label_width > 0 and label_height > 0:
                    img_width, img_height = img_annotated.size
                    ratio = min(label_width / img_width, label_height / img_height)
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    img_annotated = img_annotated.resize((new_width, new_height), Image.LANCZOS)

                self.current_photo = ImageTk.PhotoImage(image=img_annotated)
                self.image_label.config(image=self.current_photo)
                self.pil_image_to_save = img_annotated
        
        self.after(10, self.update_video_frame)

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

    def save_image(self):
        if self.pil_image_to_save:
            # Récupère l'image actuellement affichée (qui contient déjà les annotations)
            img_to_save = self.pil_image_to_save

            # Demande à l'utilisateur le chemin de sauvegarde
            file_path = filedialog.asksaveasfilename(
                filetypes=[("Fichiers PNG", "*.png"), ("Fichiers PDF", "*.pdf")],
                title="Sauvegarder l'image annotée"
            )

            if file_path:
                # Détermine l'extension souhaitée en fonction du type de fichier sélectionné
                selected_ext = ".png"  # Par défaut, PNG si aucune extension spécifique n'est trouvée
                for desc, pattern in [("Fichiers PNG", "*.png"), ("Fichiers PDF", "*.pdf")]:
                    if file_path.lower().endswith(pattern[1:]):
                        selected_ext = pattern[1:]
                        break
                
                # Si l'utilisateur n'a pas tapé d'extension, ou en a tapé une mauvaise, ajoute la bonne
                name, ext = os.path.splitext(file_path)
                if not ext or ext.lower() != selected_ext:
                    file_path = name + selected_ext

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                directory, filename = os.path.split(file_path)
                name, ext = os.path.splitext(filename)
                
                final_filename = os.path.join(directory, f"{timestamp}_{name}{ext}")

                try:
                    if ext.lower() == ".pdf":
                        img_to_save.save(final_filename, "PDF", resolution=100.0)
                    elif ext.lower() == ".png":
                        img_to_save.save(final_filename)
                    else:  # Repli si quelque chose d'inattendu se produit
                        img_to_save.save(final_filename, "PNG")  # Sauvegarde en PNG par défaut
                    messagebox.showinfo("Sauvegarde", f"Image sauvegardée avec succès :\n{final_filename}")
                except Exception as e:
                    messagebox.showerror("Erreur de Sauvegarde", f"Impossible de sauvegarder l'image :\n{e}")
        else:
            messagebox.showwarning("Avertissement", "Aucune image à sauvegarder.")

    def on_mouse_down(self, event):
        if self.current_tool == "text":
            entered_text = self.get_text_input()
            if entered_text:
                # Get coordinates relative to the original frame size
                original_width = self.video_stream_thread.get_frame().shape[1]
                original_height = self.video_stream_thread.get_frame().shape[0]
                
                label_width = self.image_label.winfo_width()
                label_height = self.image_label.winfo_height()

                # Calculate scaling factor
                scale_x = original_width / label_width
                scale_y = original_height / label_height

                # Adjust for aspect ratio if image is scaled to fit
                img_ratio = original_width / original_height
                label_ratio = label_width / label_height

                if img_ratio > label_ratio: # Image is wider than label, height is scaled to fit
                    scaled_img_width = label_width
                    scaled_img_height = int(label_width / img_ratio)
                    offset_y = (label_height - scaled_img_height) / 2
                    offset_x = 0
                else: # Image is taller than label, width is scaled to fit
                    scaled_img_height = label_height
                    scaled_img_width = int(label_height * img_ratio)
                    offset_x = (label_width - scaled_img_width) / 2
                    offset_y = 0

                # Convert mouse coordinates to original frame coordinates
                text_position = (int((event.x - offset_x) * scale_x), int((event.y - offset_y) * scale_y))
                self.annotations.append(TextAnnotation(text_position, entered_text, color=self.current_annotation_color, font_size=self.current_font_size))
                self.undo_stack.append(self.annotations[:]) # Save state for undo
                self.redo_stack.clear() # Clear redo stack on new annotation
                self.set_tool("none") # Go back to selection tool
        elif self.current_tool != "none":
            self.drawing = True
            # Get coordinates relative to the original frame size
            original_width = self.video_stream_thread.get_frame().shape[1]
            original_height = self.video_stream_thread.get_frame().shape[0]
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            # Calculate scaling factor
            scale_x = original_width / label_width
            scale_y = original_height / label_height

            # Adjust for aspect ratio if image is scaled to fit
            img_ratio = original_width / original_height
            label_ratio = label_width / label_height

            if img_ratio > label_ratio: # Image is wider than label, height is scaled to fit
                scaled_img_width = label_width
                scaled_img_height = int(label_width / img_ratio)
                offset_y = (label_height - scaled_img_height) / 2
                offset_x = 0
            else: # Image is taller than label, width is scaled to fit
                scaled_img_height = label_height
                scaled_img_width = int(label_height * img_ratio)
                offset_x = (label_width - scaled_img_width) / 2
                offset_y = 0

            # Convert mouse coordinates to original frame coordinates
            self.start_point = (int((event.x - offset_x) * scale_x), int((event.y - offset_y) * scale_y))
            self.end_point = self.start_point # For single click tools or initial point
        elif self.current_tool == "blur":
            self.drawing = True
            original_width = self.video_stream_thread.get_frame().shape[1]
            original_height = self.video_stream_thread.get_frame().shape[0]
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            scale_x = original_width / label_width
            scale_y = original_height / label_height

            img_ratio = original_width / original_height
            label_ratio = label_width / label_height

            if img_ratio > label_ratio:
                scaled_img_width = label_width
                scaled_img_height = int(label_width / img_ratio)
                offset_y = (label_height - scaled_img_height) / 2
                offset_x = 0
            else:
                scaled_img_height = label_height
                scaled_img_width = int(label_height * img_ratio)
                offset_x = (label_width - scaled_img_width) / 2
                offset_y = 0

            self.start_point = (int((event.x - offset_x) * scale_x), int((event.y - offset_y) * scale_y))
            self.end_point = self.start_point # Initialize end_point for drag
        elif self.current_tool == "arrow":
            self.drawing = True
            original_width = self.video_stream_thread.get_frame().shape[1]
            original_height = self.video_stream_thread.get_frame().shape[0]
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            scale_x = original_width / label_width
            scale_y = original_height / label_height

            img_ratio = original_width / original_height
            label_ratio = label_width / label_height

            if img_ratio > label_ratio:
                scaled_img_width = label_width
                scaled_img_height = int(label_width / img_ratio)
                offset_y = (label_height - scaled_img_height) / 2
                offset_x = 0
            else:
                scaled_img_height = label_height
                scaled_img_width = int(label_height * img_ratio)
                offset_x = (label_width - scaled_img_width) / 2
                offset_y = 0

            self.start_point = (int((event.x - offset_x) * scale_x), int((event.y - offset_y) * scale_y))
            self.end_point = self.start_point # Initialize end_point for drag
        elif self.current_tool == "highlight":
            self.drawing = True
            original_width = self.video_stream_thread.get_frame().shape[1]
            original_height = self.video_stream_thread.get_frame().shape[0]
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            scale_x = original_width / label_width
            scale_y = original_height / label_height

            img_ratio = original_width / original_height
            label_ratio = label_width / label_height

            if img_ratio > label_ratio:
                scaled_img_width = label_width
                scaled_img_height = int(label_width / img_ratio)
                offset_y = (label_height - scaled_img_height) / 2
                offset_x = 0
            else:
                scaled_img_height = label_height
                scaled_img_width = int(label_height * img_ratio)
                offset_x = (label_width - scaled_img_width) / 2
                offset_y = 0

            self.start_point = (int((event.x - offset_x) * scale_x), int((event.y - offset_y) * scale_y))
            self.end_point = self.start_point # Initialize end_point for drag

    def on_mouse_drag(self, event):
        if self.drawing and self.current_tool in ["line", "rectangle", "freedraw", "blur", "arrow", "highlight"]:
            # Get coordinates relative to the original frame size
            original_width = self.video_stream_thread.get_frame().shape[1]
            original_height = self.video_stream_thread.get_frame().shape[0]
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            # Calculate scaling factor
            scale_x = original_width / label_width
            scale_y = original_height / label_height

            # Adjust for aspect ratio if image is scaled to fit
            img_ratio = original_width / original_height
            label_ratio = label_width / label_height

            if img_ratio > label_ratio: # Image is wider than label, height is scaled to fit
                scaled_img_width = label_width
                scaled_img_height = int(label_width / img_ratio)
                offset_y = (label_height - scaled_img_height) / 2
                offset_x = 0
            else: # Image is taller than label, width is scaled to fit
                scaled_img_height = label_height
                scaled_img_width = int(label_height * img_ratio)
                offset_x = (label_width - scaled_img_width) / 2
                offset_y = 0

            self.end_point = (int((event.x - offset_x) * scale_x), int((event.y - offset_y) * scale_y))

            # For freedraw, add points continuously
            if self.current_tool == "freedraw":
                self.current_freedraw_points.append(self.end_point)

    def on_mouse_up(self, event):
        if self.drawing:
            self.drawing = False
            # Get coordinates relative to the original frame size
            original_width = self.video_stream_thread.get_frame().shape[1]
            original_height = self.video_stream_thread.get_frame().shape[0]
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()

            # Calculate scaling factor
            scale_x = original_width / label_width
            scale_y = original_height / label_height

            # Adjust for aspect ratio if image is scaled to fit
            img_ratio = original_width / original_height
            label_ratio = label_width / label_height

            if img_ratio > label_ratio: # Image is wider than label, height is scaled to fit
                scaled_img_width = label_width
                scaled_img_height = int(label_width / img_ratio)
                offset_y = (label_height - scaled_img_height) / 2
                offset_x = 0
            else: # Image is taller than label, width is scaled to fit
                scaled_img_height = label_height
                scaled_img_width = int(label_height * img_ratio)
                offset_x = (label_width - scaled_img_width) / 2
                offset_y = 0

            final_x = int((event.x - offset_x) * scale_x)
            final_y = int((event.y - offset_y) * scale_y)
            self.end_point = (final_x, final_y)

            if self.current_tool == "line":
                self.annotations.append(LineAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "rectangle":
                self.annotations.append(RectangleAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "circle":
                center_x = (self.start_point[0] + self.end_point[0]) // 2
                center_y = (self.start_point[1] + self.end_point[1]) // 2
                radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                self.annotations.append(CircleAnnotation((center_x, center_y), radius, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
                print(f"Adding CircleAnnotation with color: {self.current_annotation_color}")
            elif self.current_tool == "freedraw":
                if self.current_freedraw_points:
                    self.annotations.append(FreeDrawAnnotation(list(self.current_freedraw_points), color=self.current_annotation_color, thickness=self.current_annotation_thickness))
                self.current_freedraw_points = [] # Reset for next freedraw
            elif self.current_tool == "blur":
                self.annotations.append(BlurAnnotation(self.start_point, self.end_point))
            elif self.current_tool == "arrow":
                self.annotations.append(ArrowAnnotation(self.start_point, self.end_point, color=self.current_annotation_color, thickness=self.current_annotation_thickness))
            elif self.current_tool == "highlight":
                self.annotations.append(HighlightAnnotation(self.start_point, self.end_point, color=self.current_annotation_color))
            # Add other tools here
            self.redo_stack.clear() # Clear redo stack on new annotation

            

    

    

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
        ttk.Label(settings_dialog, text="Contraste:").pack(pady=5)
        self.contrast_slider = ttk.Scale(settings_dialog, from_=0, to_=255, orient=tk.HORIZONTAL, command=self.set_contrast)
        self.contrast_slider.set(self.video_stream_thread.cap.get(cv2.CAP_PROP_CONTRAST) if self.video_stream_thread and self.video_stream_thread.cap else 128)
        self.contrast_slider.pack(fill=tk.X, padx=10, pady=5)

        # Resolution control
        ttk.Label(settings_dialog, text="Résolution:").pack(pady=5)
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

    def on_closing(self):
        if self.video_stream_thread:
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        self.destroy()

if __name__ == "__main__":
    app = VisioDoc3()
    app.mainloop()