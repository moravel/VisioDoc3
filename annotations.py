import cv2
import numpy as np
from PIL import ImageDraw, ImageFont # Import for PIL drawing

# Base class for all annotations
# Classe de base pour toutes les annotations
class Annotation:
    def __init__(self, color, thickness=2):
        """
        Initializes an Annotation object.
        Initialise un objet Annotation.

        Args:
            color (tuple): BGR color tuple (e.g., (0, 0, 255) for red).
                           Tuple de couleur BGR (par exemple, (0, 0, 255) pour le rouge).
            thickness (int): Thickness of the annotation line.
                             Épaisseur de la ligne de l'annotation.
        """
        self.color = color  # BGR format for OpenCV / Format BGR pour OpenCV
        self.thickness = thickness # Épaisseur de l'annotation

    def draw(self, frame):
        """
        Draws the annotation on the given OpenCV frame.
        This method should be overridden by subclasses.
        Dessine l'annotation sur le cadre OpenCV donné.
        Cette méthode doit être surchargée par les sous-classes.
        """
        pass

    def draw_pil(self, draw_obj):
        """
        Draws the annotation using PIL ImageDraw object.
        This method is currently a placeholder and not fully implemented for all annotations.
        Dessine l'annotation à l'aide de l'objet PIL ImageDraw.
        Cette méthode est actuellement un espace réservé et n'est pas entièrement implémentée pour toutes les annotations.
        """
        pass

    def is_point_inside(self, point):
        """
        Checks if a given point is inside the annotation's interactive area.
        This method should be overridden by subclasses.
        Vérifie si un point donné se trouve à l'intérieur de la zone interactive de l'annotation.
        Cette méthode doit être surchargée par les sous-classes.

        Args:
            point (tuple): (x, y) coordinates of the point.
                           Coordonnées (x, y) du point.

        Returns:
            bool: True if the point is inside, False otherwise.
                  Vrai si le point est à l'intérieur, Faux sinon.
        """
        return False

    def move(self, dx, dy):
        """
        Moves the annotation by a given displacement.
        This method should be overridden by subclasses.
        Déplace l'annotation d'un déplacement donné.
        Cette méthode doit être surchargée par les sous-classes.

        Args:
            dx (int): Displacement in x-direction.
                      Déplacement en direction x.
            dy (int): Displacement in y-direction.
                      Déplacement en direction y.
        """
        pass

    def get_bounding_box(self):
        """
        Returns the bounding box of the annotation (x1, y1, x2, y2).
        This method should be overridden by subclasses.
        Retourne la boîte englobante de l'annotation (x1, y1, x2, y2).
        Cette méthode doit être surchargée par les sous-classes.

        Returns:
            tuple: (x1, y1, x2, y2) coordinates of the bounding box, or None.
                   Coordonnées (x1, y1, x2, y2) de la boîte englobante, ou Aucun.
        """
        return None

    def get_resize_handles(self):
        """
        Returns a dictionary of resize handles for the annotation.
        Each handle is a (name, point) tuple.
        This method should be overridden by subclasses.
        Retourne un dictionnaire de poignées de redimensionnement pour l'annotation.
        Chaque poignée est un tuple (nom, point).
        Cette méthode doit être surchargée par les sous-classes.

        Returns:
            dict: Dictionary of handle names to their (x, y) coordinates.
                  Dictionnaire des noms de poignées et de leurs coordonnées (x, y).
        """
        return {}

    def resize(self, handle, current_mouse_point, initial_drag_point):
        """
        Resizes the annotation based on the dragged handle and mouse movement.
        This method should be overridden by subclasses.
        Redimensionne l'annotation en fonction de la poignée glissée et du mouvement de la souris.
        Cette méthode doit être surchargée par les sous-classes.

        Args:
            handle (str): Name of the handle being dragged.
                          Nom de la poignée en cours de glissement.
            current_mouse_point (tuple): Current (x, y) coordinates of the mouse.
                                         Coordonnées (x, y) actuelles de la souris.
            initial_drag_point (tuple): Initial (x, y) coordinates when drag started.
                                        Coordonnées (x, y) initiales au début du glissement.
        """
        pass

# Line annotation class
# Classe d'annotation de ligne
class LineAnnotation(Annotation):
    def __init__(self, start_point, end_point, color, thickness=2):
        """
        Initializes a LineAnnotation object.
        Initialise un objet LineAnnotation.

        Args:
            start_point (tuple): (x, y) coordinates of the line's start point.
                                 Coordonnées (x, y) du point de départ de la ligne.
            end_point (tuple): (x, y) coordinates of the line's end point.
                               Coordonnées (x, y) du point de fin de la ligne.
            color (tuple): BGR color tuple.
                           Tuple de couleur BGR.
            thickness (int): Thickness of the line.
                             Épaisseur de la ligne.
        """
        super().__init__(color, thickness)
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, frame):
        """
        Draws the line on the OpenCV frame.
        Dessine la ligne sur le cadre OpenCV.
        """
        cv2.line(frame, self.start_point, self.end_point, self.color, self.thickness)

    def is_point_inside(self, point):
        """
        Checks if a point is near the line segment.
        Vérifie si un point est proche du segment de ligne.
        """
        x, y = point
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        tolerance = self.thickness + 10 # Add tolerance for easier selection / Ajoute une tolérance pour une sélection plus facile
        
        # Check if point is within the bounding box of the line segment with tolerance
        # Vérifie si le point est dans la boîte englobante du segment de ligne avec tolérance
        if not (min(x1, x2) - tolerance <= x <= max(x1, x2) + tolerance and 
                min(y1, y2) - tolerance <= y <= max(y1, y2) + tolerance):
            return False
        
        # Calculate distance from point to line segment
        # Calcule la distance du point au segment de ligne
        denominator = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        if denominator < 1e-6: # Handle case where line is a single point or very short
                               # Gère le cas où la ligne est un point unique ou très courte
            return np.sqrt((x - x1)**2 + (y - y1)**2) <= tolerance
        
        distance = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / denominator
        return distance <= tolerance

    def move(self, dx, dy):
        """
        Moves the line by updating its start and end points.
        Déplace la ligne en mettant à jour ses points de début et de fin.
        """
        self.start_point = (int(self.start_point[0] + dx), int(self.start_point[1] + dy))
        self.end_point = (int(self.end_point[0] + dx), int(self.end_point[1] + dy))

    def get_bounding_box(self):
        """
        Returns the bounding box of the line.
        Retourne la boîte englobante de la ligne.
        """
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def get_resize_handles(self):
        """
        Returns resize handles at the start and end points of the line.
        Retourne les poignées de redimensionnement aux points de début et de fin de la ligne.
        """
        return {"start": self.start_point, "end": self.end_point}

    def resize(self, handle, current_mouse_point, initial_drag_point):
        """
        Resizes the line by moving either the start or end point.
        Redimensionne la ligne en déplaçant le point de début ou de fin.
        """
        if handle == "start":
            self.start_point = current_mouse_point
        elif handle == "end":
            self.end_point = current_mouse_point

# Rectangle annotation class
# Classe d'annotation de rectangle
class RectangleAnnotation(Annotation):
    def __init__(self, p1, p2, color, thickness=2, filled=False):
        """
        Initializes a RectangleAnnotation object.
        Initialise un objet RectangleAnnotation.

        Args:
            p1 (tuple): (x, y) coordinates of the first corner.
                        Coordonnées (x, y) du premier coin.
            p2 (tuple): (x, y) coordinates of the second corner.
                        Coordonnées (x, y) du deuxième coin.
            color (tuple): BGR color tuple.
                           Tuple de couleur BGR.
            thickness (int): Thickness of the rectangle border. Use -1 for filled.
                             Épaisseur de la bordure du rectangle. Utilisez -1 pour rempli.
            filled (bool): If True, the rectangle will be filled.
                           Si Vrai, le rectangle sera rempli.
        """
        super().__init__(color, thickness)
        self.p1 = p1
        self.p2 = p2
        self.filled = filled

    def draw(self, frame):
        """
        Draws the rectangle on the OpenCV frame.
        Dessine le rectangle sur le cadre OpenCV.
        """
        if self.filled:
            cv2.rectangle(frame, self.p1, self.p2, self.color, -1) # -1 for filled rectangle / -1 pour un rectangle rempli
        else:
            cv2.rectangle(frame, self.p1, self.p2, self.color, self.thickness)

    def is_point_inside(self, point):
        """
        Checks if a point is inside or near the rectangle's bounding box.
        Vérifie si un point est à l'intérieur ou près de la boîte englobante du rectangle.
        """
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        margin = 5 # Add a small margin for easier selection / Ajoute une petite marge pour une sélection plus facile
        return min(x1, x2) - margin <= x <= max(x1, x2) + margin and \
               min(y1, y2) - margin <= y <= max(y1, y2) + margin

    def move(self, dx, dy):
        """
        Moves the rectangle by updating its two corner points.
        Déplace le rectangle en mettant à jour ses deux points d'angle.
        """
        self.p1 = (int(self.p1[0] + dx), int(self.p1[1] + dy))
        self.p2 = (int(self.p2[0] + dx), int(self.p2[1] + dy))

    def get_bounding_box(self):
        """
        Returns the bounding box of the rectangle.
        Retourne la boîte englobante du rectangle.
        """
        x1, y1 = self.p1
        x2, y2 = self.p2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def get_resize_handles(self):
        """
        Returns resize handles at the four corners of the rectangle's bounding box.
        Retourne les poignées de redimensionnement aux quatre coins de la boîte englobante du rectangle.
        """
        x1, y1, x2, y2 = self.get_bounding_box()
        return {
            "top-left": (x1, y1), "top-right": (x2, y1),
            "bottom-left": (x1, y2), "bottom-right": (x2, y2)
        }

    def resize(self, handle, current_mouse_point, initial_drag_point):
        """
        Resizes the rectangle by moving one corner while keeping the opposite fixed.
        Redimensionne le rectangle en déplaçant un coin tout en gardant l'opposé fixe.
        """
        # Determine the fixed point (opposite corner) based on the handle being dragged
        # Détermine le point fixe (coin opposé) en fonction de la poignée glissée
        x1_orig, y1_orig = self.p1
        x2_orig, y2_orig = self.p2

        if handle == "top-left":
            fixed_point = (x2_orig, y2_orig)
        elif handle == "top-right":
            fixed_point = (x1_orig, y2_orig)
        elif handle == "bottom-left":
            fixed_point = (x2_orig, y1_orig)
        elif handle == "bottom-right":
            fixed_point = (x1_orig, y1_orig)
        else:
            return # Should not happen / Ne devrait pas arriver

        # Update p1 and p2 based on the fixed point and current mouse position
        # Met à jour p1 et p2 en fonction du point fixe et de la position actuelle de la souris
        new_x1 = min(fixed_point[0], current_mouse_point[0])
        new_y1 = min(fixed_point[1], current_mouse_point[1])
        new_x2 = max(fixed_point[0], current_mouse_point[0])
        new_y2 = max(fixed_point[1], current_mouse_point[1])

        self.p1 = (int(new_x1), int(new_y1))
        self.p2 = (int(new_x2), int(new_y2))

# Circle annotation class
# Classe d'annotation de cercle
class CircleAnnotation(Annotation):
    def __init__(self, center, radius, color=(0, 0, 255), thickness=2, filled=False):
        """
        Initializes a CircleAnnotation object.
        Initialise un objet CircleAnnotation.

        Args:
            center (tuple): (x, y) coordinates of the circle's center.
                            Coordonnées (x, y) du centre du cercle.
            radius (int): Radius of the circle.
                          Rayon du cercle.
            color (tuple): BGR color tuple.
                           Tuple de couleur BGR.
            thickness (int): Thickness of the circle border. Use -1 for filled.
                             Épaisseur de la bordure du cercle. Utilisez -1 pour rempli.
            filled (bool): If True, the circle will be filled.
                           Si Vrai, le cercle sera rempli.
        """
        super().__init__(color, thickness)
        self.center = center
        self.radius = radius
        self.filled = filled

    def draw(self, frame):
        """
        Draws the circle on the OpenCV frame.
        Dessine le cercle sur le cadre OpenCV.
        """
        if self.filled:
            cv2.circle(frame, self.center, self.radius, self.color, -1) # -1 for filled circle / -1 pour un cercle rempli
        else:
            cv2.circle(frame, self.center, self.radius, self.color, self.thickness)

    def is_point_inside(self, point):
        """
        Checks if a point is inside or near the circle.
        Vérifie si un point est à l'intérieur ou près du cercle.
        """
        distance = np.sqrt((point[0] - self.center[0])**2 + (point[1] - self.center[1])**2)
        return distance <= self.radius + 5 # Add tolerance for easier selection / Ajoute une tolérance pour une sélection plus facile

    def move(self, dx, dy):
        """
        Moves the circle by updating its center point.
        Déplace le cercle en mettant à jour son point central.
        """
        self.center = (int(self.center[0] + dx), int(self.center[1] + dy))

    def get_bounding_box(self):
        """
        Returns the bounding box of the circle.
        Retourne la boîte englobante du cercle.
        """
        x, y = self.center
        return (x - self.radius, y - self.radius, x + self.radius, y + self.radius)

    def get_resize_handles(self):
        """
        Returns resize handles at cardinal points and corners of the bounding box.
        Retourne les poignées de redimensionnement aux points cardinaux et aux coins de la boîte englobante.
        """
        x, y = self.center
        r = self.radius
        return {
            "top": (x, y - r),
            "bottom": (x, y + r),
            "left": (x - r, y),
            "right": (x + r, y),
            "top-left": (x - r, y - r),
            "top-right": (x + r, y - r),
            "bottom-left": (x - r, y + r),
            "bottom-right": (x + r, y + r)
        }

    def resize(self, handle, current_mouse_point, initial_drag_point):
        """
        Resizes the circle by adjusting its radius based on the mouse position relative to the center.
        Redimensionne le cercle en ajustant son rayon en fonction de la position de la souris par rapport au centre.
        """
        # The new radius is the distance from the center to the current mouse position.
        # Le nouveau rayon est la distance du centre à la position actuelle de la souris.
        new_radius = np.sqrt((current_mouse_point[0] - self.center[0])**2 + (current_mouse_point[1] - self.center[1])**2)
        self.radius = int(new_radius)

# Freehand drawing annotation class
# Classe d'annotation de dessin à main levée
class FreeDrawAnnotation(Annotation):
    def __init__(self, points, color, thickness=2):
        """
        Initializes a FreeDrawAnnotation object.
        Initialise un objet FreeDrawAnnotation.

        Args:
            points (list): List of (x, y) tuples representing the drawn path.
                           Liste de tuples (x, y) représentant le chemin dessiné.
            color (tuple): BGR color tuple.
                           Tuple de couleur BGR.
            thickness (int): Thickness of the drawn line.
                             Épaisseur de la ligne dessinée.
        """
        super().__init__(color, thickness)
        self.points = points

    def draw(self, frame):
        """
        Draws the freehand path by connecting all points with lines.
        Dessine le chemin à main levée en connectant tous les points avec des lignes.
        """
        for i in range(1, len(self.points)):
            cv2.line(frame, self.points[i-1], self.points[i], self.color, self.thickness)

    def is_point_inside(self, point):
        """
        Checks if a point is near any segment of the freehand drawing.
        Vérifie si un point est proche d'un segment du dessin à main levée.
        """
        for i in range(len(self.points) - 1):
            line_segment = LineAnnotation(self.points[i], self.points[i+1], self.color, self.thickness)
            if line_segment.is_point_inside(point):
                return True
        return False

    def move(self, dx, dy):
        """
        Moves the freehand drawing by translating all its points.
        Déplace le dessin à main levée en translatant tous ses points.
        """
        self.points = [(int(p[0] + dx), int(p[1] + dy)) for p in self.points]

    def get_bounding_box(self):
        """
        Returns the bounding box of the freehand drawing.
        Retourne la boîte englobante du dessin à main levée.
        """
        if not self.points:
            return None
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def get_resize_handles(self):
        """
        Returns resize handles at the corners of the freehand drawing's bounding box.
        Retourne les poignées de redimensionnement aux coins de la boîte englobante du dessin à main levée.
        """
        x1, y1, x2, y2 = self.get_bounding_box()
        return {
            "top-left": (x1, y1), "top-right": (x2, y1),
            "bottom-left": (x1, y2), "bottom-right": (x2, y2)
        }

    def resize(self, handle, current_mouse_point, initial_drag_point):
        """
        Resizes the freehand drawing by scaling all its points relative to a fixed corner.
        Redimensionne le dessin à main levée en mettant à l'échelle tous ses points par rapport à un coin fixe.
        """
        x1, y1, x2, y2 = self.get_bounding_box()
        orig_w = x2 - x1
        orig_h = y2 - y1

        if orig_w == 0 or orig_h == 0: # Avoid division by zero for very thin or flat drawings
                                       # Évite la division par zéro pour les dessins très fins ou plats
            return

        # Determine the fixed point (opposite corner) based on the handle being dragged
        # Détermine le point fixe (coin opposé) en fonction de la poignée glissée
        if handle == "top-left":
            fixed_x, fixed_y = x2, y2
        elif handle == "top-right":
            fixed_x, fixed_y = x1, y2
        elif handle == "bottom-left":
            fixed_x, fixed_y = x2, y1
        elif handle == "bottom-right":
            fixed_x, fixed_y = x1, y1
        else:
            return # Should not happen / Ne devrait pas arriver

        # Calculate new bounding box based on fixed point and current mouse position
        # Calcule la nouvelle boîte englobante en fonction du point fixe et de la position actuelle de la souris
        new_x1 = min(fixed_x, current_mouse_point[0])
        new_y1 = min(fixed_y, current_mouse_point[1])
        new_x2 = max(fixed_x, current_mouse_point[0])
        new_y2 = max(fixed_y, current_mouse_point[1])

        new_w = max(1, new_x2 - new_x1) # Ensure minimum width/height of 1 to avoid division by zero
        new_h = max(1, new_y2 - new_y1) # Assure une largeur/hauteur minimale de 1 pour éviter la division par zéro

        scale_x = new_w / orig_w
        scale_y = new_h / orig_h

        # Apply scaling and translation to all points
        # Applique la mise à l'échelle et la translation à tous les points
        new_points = []
        for p_x, p_y in self.points:
            # Translate point relative to the fixed point
            # Translate le point par rapport au point fixe
            translated_x = p_x - fixed_x
            translated_y = p_y - fixed_y

            # Scale
            # Mise à l'échelle
            scaled_x = translated_x * scale_x
            scaled_y = translated_y * scale_y

            # Translate back from the fixed point to the new position
            # Translate de nouveau du point fixe à la nouvelle position
            new_points.append((int(scaled_x + fixed_x), int(scaled_y + fixed_y)))
        self.points = new_points

# Text annotation class
# Classe d'annotation de texte
class TextAnnotation(Annotation):
    def __init__(self, position, text, font_size=20, color=(0, 0, 255)):
        """
        Initializes a TextAnnotation object.
        Initialise un objet TextAnnotation.

        Args:
            position (tuple): (x, y) coordinates of the text's bottom-left corner.
                              Coordonnées (x, y) du coin inférieur gauche du texte.
            text (str): The text content.
                        Le contenu du texte.
            font_size (int): Font size of the text.
                             Taille de la police du texte.
            color (tuple): BGR color tuple.
                           Tuple de couleur BGR.
        """
        super().__init__(color)
        self.position = position
        self.text = text
        self.font_size = font_size

    def draw(self, frame):
        """
        Draws the text on the OpenCV frame.
        Dessine le texte sur le cadre OpenCV.
        """
        # font_size / 20 is a heuristic to convert font_size to OpenCV's fontScale
        # font_size / 20 est une heuristique pour convertir la taille de police en fontScale d'OpenCV
        cv2.putText(frame, self.text, self.position, cv2.FONT_HERSHEY_SIMPLEX, 
                    self.font_size / 20, self.color, 2, cv2.LINE_AA)

    def is_point_inside(self, point):
        """
        Checks if a point is inside or near the text's bounding box.
        Vérifie si un point est à l'intérieur ou près de la boîte englobante du texte.
        """
        # Estimate text width and height for hit testing
        # Estime la largeur et la hauteur du texte pour le test de collision
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x, y = point
        x1, y1 = self.position
        margin = 5 # Add a small margin for easier selection / Ajoute une petite marge pour une sélection plus facile
        return x1 - margin <= x <= x1 + text_width + margin and \
               y1 - text_height - margin <= y <= y1 + margin

    def move(self, dx, dy):
        """
        Moves the text by updating its position.
        Déplace le texte en mettant à jour sa position.
        """
        self.position = (int(self.position[0] + dx), int(self.position[1] + dy))

    def get_bounding_box(self):
        """
        Returns the bounding box of the text.
        Retourne la boîte englobante du texte.
        """
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x1, y1 = self.position
        # Bounding box is from (x1, y1 - text_height) to (x1 + text_width, y1)
        # La boîte englobante va de (x1, y1 - text_height) à (x1 + text_width, y1)
        return (x1, y1 - text_height, x1 + text_width, y1)

    def get_resize_handles(self):
        """
        Returns a single resize handle for text (typically at the bottom-right).
        Retourne une seule poignée de redimensionnement pour le texte (généralement en bas à droite).
        """
        x1, y1, x2, y2 = self.get_bounding_box()
        return {"size": (x2, y2)}

    def resize(self, handle, current_mouse_point, initial_drag_point):
        """
        Resizes the text by adjusting its font size based on mouse movement.
        Redimensionne le texte en ajustant sa taille de police en fonction du mouvement de la souris.
        """
        if handle == "size":
            # Calculate the change in distance from the initial drag point to the text's origin
            # Calcule le changement de distance entre le point de glissement initial et l'origine du texte
            initial_distance = np.sqrt((initial_drag_point[0] - self.position[0])**2 + (initial_drag_point[1] - self.position[1])**2)
            current_distance = np.sqrt((current_mouse_point[0] - self.position[0])**2 + (current_mouse_point[1] - self.position[1])**2)

            if initial_distance > 0:
                scale_factor = current_distance / initial_distance
                # Ensure font size doesn't go below a minimum
                # S'assure que la taille de police ne descend pas en dessous d'un minimum
                self.font_size = max(8, int(self.font_size * scale_factor))

# Blur annotation class (inherits from RectangleAnnotation)
# Classe d'annotation de flou (hérite de RectangleAnnotation)
class BlurAnnotation(RectangleAnnotation):
    def __init__(self, p1, p2, blur_strength=25):
        """
        Initializes a BlurAnnotation object.
        Initialise un objet BlurAnnotation.

        Args:
            p1 (tuple): (x, y) coordinates of the first corner of the blur area.
                        Coordonnées (x, y) du premier coin de la zone de flou.
            p2 (tuple): (x, y) coordinates of the second corner of the blur area.
                        Coordonnées (x, y) du deuxième coin de la zone de flou.
            blur_strength (int): Strength of the Gaussian blur (must be odd).
                                 Force du flou gaussien (doit être impair).
        """
        super().__init__(p1, p2, (0,0,0)) # Color is irrelevant for blur, set to black / La couleur est sans importance pour le flou, mise à noir
        self.blur_strength = blur_strength

    def draw(self, frame):
        """
        Applies a Gaussian blur to the rectangular region of interest.
        Applique un flou gaussien à la région d'intérêt rectangulaire.
        """
        # Ensure points are ordered for ROI extraction
        # S'assure que les points sont ordonnés pour l'extraction de la ROI
        x1, y1 = min(self.p1[0], self.p2[0]), min(self.p1[1], self.p2[1])
        x2, y2 = max(self.p1[0], self.p2[0]), max(self.p1[1], self.p2[1])
        
        h, w, _ = frame.shape
        # Clamp coordinates to frame boundaries
        # Clampe les coordonnées aux limites du cadre
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        
        if x2 > x1 and y2 > y1: # Ensure valid region / S'assure d'une région valide
            roi = frame[y1:y2, x1:x2]
            # Ensure blur_strength is odd for GaussianBlur kernel size
            # S'assure que blur_strength est impair pour la taille du noyau de GaussianBlur
            kernel_size = self.blur_strength if self.blur_strength % 2 == 1 else self.blur_strength + 1
            blurred_roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
            frame[y1:y2, x1:x2] = blurred_roi

# Arrow annotation class (inherits from LineAnnotation)
# Classe d'annotation de flèche (hérite de LineAnnotation)
class ArrowAnnotation(LineAnnotation):
    def __init__(self, start_point, end_point, color=(0, 0, 255), thickness=2, tip_length=0.3):
        """
        Initializes an ArrowAnnotation object.
        Initialise un objet ArrowAnnotation.

        Args:
            start_point (tuple): (x, y) coordinates of the arrow's tail.
                                 Coordonnées (x, y) de la queue de la flèche.
            end_point (tuple): (x, y) coordinates of the arrow's tip.
                               Coordonnées (x, y) de la pointe de la flèche.
            color (tuple): BGR color tuple.
                           Tuple de couleur BGR.
            thickness (int): Thickness of the arrow line.
                             Épaisseur de la ligne de la flèche.
            tip_length (float): Length of the arrow tip relative to the line length (0.0 to 1.0).
                                Longueur de la pointe de la flèche par rapport à la longueur de la ligne (0.0 à 1.0).
        """
        super().__init__(start_point, end_point, color, thickness)
        self.tip_length = tip_length

    def draw(self, frame):
        """
        Draws the arrow on the OpenCV frame.
        Dessine la flèche sur le cadre OpenCV.
        """
        cv2.arrowedLine(frame, self.start_point, self.end_point, self.color, self.thickness, tipLength=self.tip_length)

# Highlight annotation class (inherits from RectangleAnnotation)
# Classe d'annotation de surlignage (hérite de RectangleAnnotation)
class HighlightAnnotation(RectangleAnnotation):
    def __init__(self, p1, p2, color=(255, 255, 0), opacity=0.3):
        """
        Initializes a HighlightAnnotation object.
        Initialise un objet HighlightAnnotation.

        Args:
            p1 (tuple): (x, y) coordinates of the first corner of the highlight area.
                        Coordonnées (x, y) du premier coin de la zone de surlignage.
            p2 (tuple): (x, y) coordinates of the second corner of the highlight area.
                        Coordonnées (x, y) du deuxième coin de la zone de surlignage.
            color (tuple): BGR color tuple for the highlight.
                           Tuple de couleur BGR.
            opacity (float): Opacity of the highlight (0.0 to 1.0).
                             Opacité du surlignage (0.0 à 1.0).
        """
        super().__init__(p1, p2, color)
        self.opacity = opacity

    def draw(self, frame):
        """
        Draws a translucent highlight rectangle on the OpenCV frame.
        Dessine un rectangle de surlignage translucide sur le cadre OpenCV.
        """
        overlay = frame.copy() # Create a copy to draw the highlight on / Crée une copie pour dessiner le surlignage
        
        # Ensure points are ordered for rectangle drawing
        # S'assure que les points sont ordonnés pour le dessin du rectangle
        x1, y1 = min(self.p1[0], self.p2[0]), min(self.p1[1], self.p2[1])
        x2, y2 = max(self.p1[0], self.p2[0]), max(self.p1[1], self.p2[1])
        
        h, w, _ = frame.shape
        # Clamp coordinates to frame boundaries
        # Clampe les coordonnées aux limites du cadre
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        
        if x2 > x1 and y2 > y1: # Ensure valid region / S'assure d'une région valide
            cv2.rectangle(overlay, (x1, y1), (x2, y2), self.color, -1) # Draw filled rectangle on overlay / Dessine un rectangle rempli sur la superposition
            # Blend the overlay with the original frame based on opacity
            # Mélange la superposition avec le cadre original en fonction de l'opacité
            cv2.addWeighted(overlay, self.opacity, frame, 1 - self.opacity, 0, frame)