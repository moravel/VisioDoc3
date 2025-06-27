import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import datetime
import os
import threading
import time
from annotations import LineAnnotation, RectangleAnnotation, CircleAnnotation, FreeDrawAnnotation, TextAnnotation, BlurAnnotation # Import new annotation classes


class VideoStreamThread(threading.Thread):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self._run_flag = True
        self.frame = None
        self.lock = threading.Lock()

    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
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
    def __init__(self):
        super().__init__()
        self.title("VisioDoc3 - Visionneuse de Documents")
        self.geometry("1000x700")

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

        # Main layout
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.main_frame.grid_columnconfigure(0, weight=0) # Left panel
        self.main_frame.grid_columnconfigure(1, weight=1) # Video area
        self.main_frame.grid_columnconfigure(2, weight=0) # Right panel
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Left Panel (Annotation Tools)
        self.left_panel = ttk.Frame(self.main_frame, width=150)
        self.left_panel.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        self.left_panel.grid_propagate(False) # Prevent frame from resizing to content

        # Buttons for annotation tools
        ttk.Button(self.left_panel, text="Sélection", command=lambda: self.set_tool("none")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Dessin Main Levée", command=lambda: self.set_tool("freedraw")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Rectangle", command=lambda: self.set_tool("rectangle")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Cercle", command=lambda: self.set_tool("circle")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Ligne", command=lambda: self.set_tool("line")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Ajouter Texte", command=lambda: self.set_tool("text")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Zone de Flou", command=lambda: self.set_tool("blur")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Flèche", command=lambda: self.set_tool("arrow")).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_panel, text="Surlignage", command=lambda: self.set_tool("highlight")).pack(fill=tk.X, pady=2)

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
            self.start_video_stream(self.camera_options[0][1])
        else:
            ttk.Label(self.camera_selection_frame, text="Aucune webcam trouvée").pack(side=tk.LEFT)

        # Right Panel (Action Buttons)
        self.right_panel = ttk.Frame(self.main_frame, width=150)
        self.right_panel.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        self.right_panel.grid_propagate(False)

        ttk.Button(self.right_panel, text="Sauvegarder", command=self.save_image).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Effacer Tout", command=self.clear_all_annotations).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Annuler (Undo)", command=self.undo_last_annotation).pack(fill=tk.X, pady=2)
        ttk.Button(self.right_panel, text="Rétablir (Redo)", command=self.redo_last_annotation).pack(fill=tk.X, pady=2)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_video_frame()

    def populate_cameras(self):
        # Try to find available cameras
        for i in range(10): # Check up to 10 cameras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.camera_options.append((f"Webcam {i}", i))
                cap.release()
            else:
                break

    def start_video_stream(self, camera_index):
        if self.video_stream_thread and self.video_stream_thread.is_alive():
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        
        self.video_stream_thread = VideoStreamThread(camera_index)
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
                # Convertir l'image OpenCV en format compatible Tkinter
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_image)
                
                # Redimensionner l'image pour qu'elle s'adapte au label
                label_width = self.image_label.winfo_width()
                label_height = self.image_label.winfo_height()

                if label_width > 0 and label_height > 0:
                    img_width, img_height = img.size
                    ratio = min(label_width / img_width, label_height / img_height)
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    img = img.resize((new_width, new_height), Image.LANCZOS)

                # Draw existing annotations on the frame
                for annotation in self.annotations:
                    annotation.draw(frame)

                # Draw temporary annotation if currently drawing
                if self.drawing and self.start_point and self.end_point:
                    if self.current_tool == "line":
                        temp_annotation = LineAnnotation(self.start_point, self.end_point, color=(0, 0, 255), thickness=2)
                        temp_annotation.draw(frame)
                    elif self.current_tool == "rectangle":
                        temp_annotation = RectangleAnnotation(self.start_point, self.end_point, color=(0, 255, 0), thickness=2)
                        temp_annotation.draw(frame)
                    elif self.current_tool == "circle":
                        center_x = (self.start_point[0] + self.end_point[0]) // 2
                        center_y = (self.start_point[1] + self.end_point[1]) // 2
                        radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                        temp_annotation = CircleAnnotation((center_x, center_y), radius, color=(255, 0, 0), thickness=2)
                        temp_annotation.draw(frame)
                    elif self.current_tool == "freedraw" and self.current_freedraw_points:
                        temp_annotation = FreeDrawAnnotation(self.current_freedraw_points, color=(0, 255, 255), thickness=2)
                        temp_annotation.draw(frame)
                    elif self.current_tool == "blur":
                        # Draw a translucent rectangle to indicate the blur area
                        overlay = frame.copy()
                        x1, y1 = self.start_point
                        x2, y2 = self.end_point
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 0), -1) # Blue color, filled
                        alpha = 0.3 # Transparency factor
                        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

                # Convertir l'image OpenCV (avec annotations) en format compatible Tkinter
                rgb_image_annotated = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_annotated = Image.fromarray(rgb_image_annotated)
                
                # Redimensionner l'image pour qu'elle s'adapte au label
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
        
        self.after(10, self.update_video_frame)

    def on_closing(self):
        if self.video_stream_thread:
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        self.destroy()

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

    def save_image(self):
        if self.video_stream_thread and self.video_stream_thread.is_alive():
            frame_to_save = self.video_stream_thread.get_frame()
            if frame_to_save is not None:
                # Convertir l'image OpenCV en format PIL
                img_pil = Image.fromarray(cv2.cvtColor(frame_to_save, cv2.COLOR_BGR2RGB))

                # Dessiner les annotations sur l'image PIL avant de sauvegarder
                for annotation in self.annotations:
                    if isinstance(annotation, BlurAnnotation):
                        x1, y1 = min(annotation.p1[0], annotation.p2[0]), min(annotation.p1[1], annotation.p2[1])
                        x2, y2 = max(annotation.p1[0], annotation.p2[0]), max(annotation.p1[1], annotation.p2[1])
                        
                        # Ensure coordinates are within image boundaries
                        img_width, img_height = img_pil.size
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(img_width, x2)
                        y2 = min(img_height, y2)

                        if x2 > x1 and y2 > y1:
                            # Extract ROI, blur it, and paste back
                            roi = img_pil.crop((x1, y1, x2, y2))
                            blurred_roi = roi.filter(ImageFilter.GaussianBlur(radius=annotation.blur_strength))
                            img_pil.paste(blurred_roi, (x1, y1))
                    else:
                        draw = ImageDraw.Draw(img_pil)
                        annotation.draw_pil(draw)

                # Demander à l'utilisateur le chemin de sauvegarde
                file_path = filedialog.asksaveasfilename(
                    filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")],
                    title="Sauvegarder l'image annotée"
                )

                if file_path:
                    # Determine the intended extension based on the selected filetype
                    # filedialog.asksaveasfilename does not directly return the selected filter,
                    # so we infer it from the file_path and filetypes.
                    selected_ext = ".png" # Default to PNG if no specific extension is found
                    for desc, pattern in [("PNG files", "*.png"), ("PDF files", "*.pdf")]:
                        if file_path.lower().endswith(pattern[1:]): # Check if path ends with .png or .pdf
                            selected_ext = pattern[1:]
                            break
                    
                    # If the user didn't type an extension, or typed a wrong one, append the correct one
                    name, ext = os.path.splitext(file_path)
                    if not ext or ext.lower() != selected_ext:
                        file_path = name + selected_ext

                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    directory, filename = os.path.split(file_path)
                    name, ext = os.path.splitext(filename)
                    
                    final_filename = os.path.join(directory, f"{timestamp}_{name}{ext}")

                    try:
                        if ext.lower() == ".pdf":
                            img_pil.save(final_filename, "PDF", resolution=100.0)
                        elif ext.lower() == ".png":
                            img_pil.save(final_filename)
                        else: # Fallback if something unexpected happens
                            img_pil.save(final_filename, "PNG") # Save as PNG by default
                        messagebox.showinfo("Sauvegarde", f"Image sauvegardée avec succès :\n{final_filename}")
                    except Exception as e:
                        messagebox.showerror("Erreur de Sauvegarde", f"Impossible de sauvegarder l'image :\n{e}")
            else:
                messagebox.showwarning("Avertissement", "Aucune image à sauvegarder.")
        else:
            messagebox.showwarning("Avertissement", "Le flux vidéo n'est pas actif.")

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
                self.annotations.append(TextAnnotation(text_position, entered_text, color=(0, 0, 0), font_size=20))
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

    def on_mouse_drag(self, event):
        if self.drawing and self.current_tool in ["line", "rectangle", "freedraw", "blur"]:
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
                self.annotations.append(LineAnnotation(self.start_point, self.end_point, color=(0, 0, 255), thickness=2))
            elif self.current_tool == "rectangle":
                self.annotations.append(RectangleAnnotation(self.start_point, self.end_point, color=(0, 255, 0), thickness=2))
            elif self.current_tool == "circle":
                center_x = (self.start_point[0] + self.end_point[0]) // 2
                center_y = (self.start_point[1] + self.end_point[1]) // 2
                radius = int(((self.end_point[0] - self.start_point[0])**2 + (self.end_point[1] - self.start_point[1])**2)**0.5 // 2)
                self.annotations.append(CircleAnnotation((center_x, center_y), radius, color=(255, 0, 0), thickness=2))
            elif self.current_tool == "freedraw":
                if self.current_freedraw_points:
                    self.annotations.append(FreeDrawAnnotation(list(self.current_freedraw_points), color=(0, 255, 255), thickness=2))
                self.current_freedraw_points = [] # Reset for next freedraw
            elif self.current_tool == "blur":
                self.annotations.append(BlurAnnotation(self.start_point, self.end_point))
            # Add other tools here
            self.redo_stack.clear() # Clear redo stack on new annotation

            

    

    

    def get_text_input(self):
        self.entered_text = None # Initialize to None
        self.text_input_dialog = tk.Toplevel(self)
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

    def on_closing(self):
        if self.video_stream_thread:
            self.video_stream_thread.stop()
            self.video_stream_thread.join()
        self.destroy()

if __name__ == "__main__":
    app = VisioDoc3()
    app.mainloop()
