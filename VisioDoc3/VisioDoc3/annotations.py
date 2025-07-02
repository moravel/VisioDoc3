import cv2
import numpy as np
from PIL import ImageDraw, ImageFont # Import for PIL drawing

class Annotation:
    def __init__(self, color, thickness=2):
        self.color = color  # BGR format for OpenCV
        self.thickness = thickness

    def draw(self, frame):
        # This method will be overridden by specific annotation types for OpenCV
        pass

    def draw_pil(self, draw_obj):
        # This method will be overridden by specific annotation types for PIL
        pass

    def is_point_inside(self, point):
        # This method will be overridden by specific annotation types
        return False

    def move(self, dx, dy):
        # This method will be overridden by specific annotation types
        pass

    def get_bounding_box(self):
        # This method will be overridden by specific annotation types
        return None

class LineAnnotation(Annotation):
    def __init__(self, start_point, end_point, color, thickness=2):
        super().__init__(color, thickness)
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, frame):
        cv2.line(frame, self.start_point, self.end_point, self.color, self.thickness)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0]) # Convert BGR to RGB
        draw_obj.line([self.start_point, self.end_point], fill=pil_color, width=self.thickness)

    def is_point_inside(self, point):
        # Check if the point is close to the line segment
        x, y = point
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        
        # A small tolerance for clicking near the line
        tolerance = self.thickness + 5 

        # Check if the point is within the bounding box of the line segment
        if not (min(x1, x2) - tolerance <= x <= max(x1, x2) + tolerance and 
                min(y1, y2) - tolerance <= y <= max(y1, y2) + tolerance):
            return False

        # Calculate the distance from the point to the line
        # Using the formula for the distance from a point to a line
        try:
            distance = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
            return distance <= tolerance
        except ZeroDivisionError: # Handle vertical or horizontal lines
            return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)

    def move(self, dx, dy):
        self.start_point = (self.start_point[0] + dx, self.start_point[1] + dy)
        self.end_point = (self.end_point[0] + dx, self.end_point[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

class RectangleAnnotation(Annotation):
    def __init__(self, p1, p2, color, thickness=2, filled=False):
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

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)

    def move(self, dx, dy):
        self.p1 = (self.p1[0] + dx, self.p1[1] + dy)
        self.p2 = (self.p2[0] + dx, self.p2[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

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

    def is_point_inside(self, point):
        distance = np.sqrt((point[0] - self.center[0])**2 + (point[1] - self.center[1])**2)
        return distance <= self.radius

    def move(self, dx, dy):
        self.center = (self.center[0] + dx, self.center[1] + dy)

    def get_bounding_box(self):
        x, y = self.center
        return (x - self.radius, y - self.radius, x + self.radius, y + self.radius)

class FreeDrawAnnotation(Annotation):
    def __init__(self, points, color, thickness=2):
        super().__init__(color, thickness)
        self.points = points # List of (x, y) tuples

    def draw(self, frame):
        for i in range(1, len(self.points)):
            cv2.line(frame, self.points[i-1], self.points[i], self.color, self.thickness)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0])
        draw_obj.line(self.points, fill=pil_color, width=self.thickness, joint="curve")

    def is_point_inside(self, point):
        for i in range(len(self.points) - 1):
            line_segment = LineAnnotation(self.points[i], self.points[i+1], self.color, self.thickness)
            if line_segment.is_point_inside(point):
                return True
        return False

    def move(self, dx, dy):
        self.points = [(p[0] + dx, p[1] + dy) for p in self.points]

    def get_bounding_box(self):
        if not self.points:
            return None
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

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
        try:
            font = ImageFont.truetype("arial.ttf", self.font_size)
        except IOError:
            font = ImageFont.load_default()
            font = font.font_variant(size=self.font_size)
        
        pil_color = (self.color[2], self.color[1], self.color[0])
        draw_obj.text(self.position, self.text, font=font, fill=pil_color)

    def is_point_inside(self, point):
        # Approximate bounding box for the text
        # This is a simplification, a more accurate method would use font metrics
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x, y = point
        x1, y1 = self.position
        return x1 <= x <= x1 + text_width and y1 - text_height <= y <= y1

    def move(self, dx, dy):
        self.position = (self.position[0] + dx, self.position[1] + dy)

    def get_bounding_box(self):
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x1, y1 = self.position
        return (x1, y1 - text_height, x1 + text_width, y1)

class BlurAnnotation(Annotation):
    def __init__(self, p1, p2, blur_strength=25):
        super().__init__((0, 0, 0)) # Color and thickness are not relevant for blur, but base class requires it
        self.p1 = p1
        self.p2 = p2
        self.blur_strength = blur_strength

    def draw(self, frame):
        x1, y1 = min(self.p1[0], self.p2[0]), min(self.p1[1], self.p2[1])
        x2, y2 = max(self.p1[0], self.p2[0]), max(self.p1[1], self.p2[1])

        # Ensure coordinates are within frame boundaries
        h, w, _ = frame.shape
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        if x2 > x1 and y2 > y1:
            roi = frame[y1:y2, x1:x2]
            blurred_roi = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)
            frame[y1:y2, x1:x2] = blurred_roi

    def draw_pil(self, draw_obj):
        # PIL drawing for blur is more complex as it requires image manipulation
        # rather than just drawing on a Draw object. This method will be handled
        # by directly manipulating the PIL Image object in main.py before passing
        # it to ImageDraw.Draw.
        pass

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)

    def move(self, dx, dy):
        self.p1 = (self.p1[0] + dx, self.p1[1] + dy)
        self.p2 = (self.p2[0] + dx, self.p2[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

class ArrowAnnotation(Annotation):
    def __init__(self, start_point, end_point, color=(0, 0, 255), thickness=2, tip_length=0.3):
        super().__init__(color, thickness)
        self.start_point = start_point
        self.end_point = end_point
        self.tip_length = tip_length # Relative to arrow length

    def draw(self, frame):
        cv2.arrowedLine(frame, self.start_point, self.end_point, self.color, self.thickness, tipLength=self.tip_length)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0])
        draw_obj.line([self.start_point, self.end_point], fill=pil_color, width=self.thickness)

        # Calculate arrowhead points for PIL
        # This is a simplified arrow head, can be improved for better aesthetics
        angle = np.arctan2(self.end_point[1] - self.start_point[1], self.end_point[0] - self.start_point[0])
        arrow_size = self.thickness * 5 # Adjust arrow head size based on thickness

        # Points for the arrowhead
        p1 = (self.end_point[0] - arrow_size * np.cos(angle - np.pi / 6),
              self.end_point[1] - arrow_size * np.sin(angle - np.pi / 6))
        p2 = (self.end_point[0] - arrow_size * np.cos(angle + np.pi / 6),
              self.end_point[1] - arrow_size * np.sin(angle + np.pi / 6))

        draw_obj.line([self.end_point, p1], fill=pil_color, width=self.thickness)
        draw_obj.line([self.end_point, p2], fill=pil_color, width=self.thickness)

    def is_point_inside(self, point):
        # Same logic as LineAnnotation
        x, y = point
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        
        tolerance = self.thickness + 5 

        if not (min(x1, x2) - tolerance <= x <= max(x1, x2) + tolerance and 
                min(y1, y2) - tolerance <= y <= max(y1, y2) + tolerance):
            return False

        try:
            distance = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
            return distance <= tolerance
        except ZeroDivisionError:
            return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)

    def move(self, dx, dy):
        self.start_point = (self.start_point[0] + dx, self.start_point[1] + dy)
        self.end_point = (self.end_point[0] + dx, self.end_point[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

class HighlightAnnotation(Annotation):
    def __init__(self, p1, p2, color=(255, 255, 0), opacity=0.3):
        super().__init__(color)
        self.p1 = p1
        self.p2 = p2
        self.opacity = opacity

    def draw(self, frame):
        overlay = frame.copy()
        x1, y1 = min(self.p1[0], self.p2[0]), min(self.p1[1], self.p2[1])
        x2, y2 = max(self.p1[0], self.p2[0]), max(self.p1[1], self.p2[1])

        # Ensure coordinates are within frame boundaries
        h, w, _ = frame.shape
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        if x2 > x1 and y2 > y1:
            cv2.rectangle(overlay, (x1, y1), (x2, y2), self.color, -1)
            cv2.addWeighted(overlay, self.opacity, frame, 1 - self.opacity, 0, frame)

    def draw_pil(self, draw_obj):
        pil_color = (self.color[2], self.color[1], self.color[0], int(self.opacity * 255)) # RGBA
        draw_obj.rectangle([self.p1, self.p2], fill=pil_color)

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)

    def move(self, dx, dy):
        self.p1 = (self.p1[0] + dx, self.p1[1] + dy)
        self.p2 = (self.p2[0] + dx, self.p2[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))