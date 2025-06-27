import cv2
import numpy as np
from PIL import ImageDraw, ImageFont # Import for PIL drawing

class Annotation:
    def __init__(self, color=(0, 0, 255), thickness=2):
        self.color = color  # BGR format for OpenCV
        self.thickness = thickness

    def draw(self, frame):
        # This method will be overridden by specific annotation types for OpenCV
        pass

    def draw_pil(self, draw_obj):
        # This method will be overridden by specific annotation types for PIL
        pass

class LineAnnotation(Annotation):
    def __init__(self, start_point, end_point, color=(0, 0, 255), thickness=2):
        super().__init__(color, thickness)
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, frame):
        cv2.line(frame, self.start_point, self.end_point, self.color, self.thickness)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0]) # Convert BGR to RGB
        draw_obj.line([self.start_point, self.end_point], fill=pil_color, width=self.thickness)

class RectangleAnnotation(Annotation):
    def __init__(self, p1, p2, color=(0, 0, 255), thickness=2, filled=False):
        super().__init__(color, thickness)
        self.p1 = p1
        self.p2 = p2
        self.filled = filled

    def draw(self, frame):
        if self.filled:
            cv2.rectangle(frame, self.p1, self.p2, self.color, -1) # -1 for filled
        else:
            cv2.rectangle(frame, self.p1, self.p2, self.color, self.thickness)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0]) # Convert BGR to RGB
        if self.filled:
            draw_obj.rectangle([self.p1, self.p2], fill=pil_color)
        else:
            draw_obj.rectangle([self.p1, self.p2], outline=pil_color, width=self.thickness)

class CircleAnnotation(Annotation):
    def __init__(self, center, radius, color=(0, 0, 255), thickness=2, filled=False):
        super().__init__(color, thickness)
        self.center = center
        self.radius = radius
        self.filled = filled

    def draw(self, frame):
        if self.filled:
            cv2.circle(frame, self.center, self.radius, self.color, -1)
        else:
            cv2.circle(frame, self.center, self.radius, self.color, self.thickness)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0])
        bbox = [self.center[0] - self.radius, self.center[1] - self.radius, 
                self.center[0] + self.radius, self.center[1] + self.radius]
        if self.filled:
            draw_obj.ellipse(bbox, fill=pil_color)
        else:
            draw_obj.ellipse(bbox, outline=pil_color, width=self.thickness)

class FreeDrawAnnotation(Annotation):
    def __init__(self, points, color=(0, 0, 255), thickness=2):
        super().__init__(color, thickness)
        self.points = points # List of (x, y) tuples

    def draw(self, frame):
        for i in range(1, len(self.points)):
            cv2.line(frame, self.points[i-1], self.points[i], self.color, self.thickness)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0])
        draw_obj.line(self.points, fill=pil_color, width=self.thickness, joint="curve")

class TextAnnotation(Annotation):
    def __init__(self, position, text, font_size=20, color=(0, 0, 255)):
        super().__init__(color)
        self.position = position
        self.text = text
        self.font_size = font_size

    def draw(self, frame):
        # For OpenCV, we need to use a font that OpenCV can handle, or draw pixel by pixel
        # For simplicity, let's use cv2.putText for now, which uses a limited set of fonts
        cv2.putText(frame, self.text, self.position, cv2.FONT_HERSHEY_SIMPLEX, 
                    self.font_size / 20, self.color, 2, cv2.LINE_AA)

    def draw_pil(self, draw_obj):
        font = ImageFont.load_default()
        pil_color = (self.color[2], self.color[1], self.color[0])
        draw_obj.text(self.position, self.text, font=font, fill=pil_color)