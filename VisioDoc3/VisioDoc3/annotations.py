import cv2
import numpy as np
from PIL import ImageDraw, ImageFont # Import for PIL drawing

class Annotation:
    def __init__(self, color, thickness=2):
        self.color = color  # BGR format for OpenCV
        self.thickness = thickness

    def draw(self, frame):
        pass

    def draw_pil(self, draw_obj):
        pass

    def is_point_inside(self, point):
        return False

    def move(self, dx, dy):
        pass

    def get_bounding_box(self):
        return None

    def get_resize_handles(self):
        return {}

    def resize(self, handle, dx, dy):
        pass

class LineAnnotation(Annotation):
    def __init__(self, start_point, end_point, color, thickness=2):
        super().__init__(color, thickness)
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, frame):
        cv2.line(frame, self.start_point, self.end_point, self.color, self.thickness)

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        tolerance = self.thickness + 10
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

class RectangleAnnotation(Annotation):
    def __init__(self, p1, p2, color, thickness=2, filled=False):
        super().__init__(color, thickness)
        self.p1 = p1
        self.p2 = p2
        self.filled = filled

    def draw(self, frame):
        if self.filled:
            cv2.rectangle(frame, self.p1, self.p2, self.color, -1)
        else:
            cv2.rectangle(frame, self.p1, self.p2, self.color, self.thickness)

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        margin = 5
        return min(x1, x2) - margin <= x <= max(x1, x2) + margin and \
               min(y1, y2) - margin <= y <= max(y1, y2) + margin

    def move(self, dx, dy):
        self.p1 = (self.p1[0] + dx, self.p1[1] + dy)
        self.p2 = (self.p2[0] + dx, self.p2[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def get_resize_handles(self):
        x1, y1, x2, y2 = self.get_bounding_box()
        return {
            "top-left": (x1, y1), "top-right": (x2, y1),
            "bottom-left": (x1, y2), "bottom-right": (x2, y2)
        }

    def resize(self, handle, dx, dy):
        x1, y1 = self.p1
        x2, y2 = self.p2

        if handle == "top-left":
            self.p1 = (x1 + dx, y1 + dy)
        elif handle == "top-right":
            self.p1 = (x1, y1 + dy)
            self.p2 = (x2 + dx, y2)
        elif handle == "bottom-left":
            self.p1 = (x1 + dx, y1)
            self.p2 = (x2, y2 + dy)
        elif handle == "bottom-right":
            self.p2 = (x2 + dx, y2 + dy)

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

    def is_point_inside(self, point):
        distance = np.sqrt((point[0] - self.center[0])**2 + (point[1] - self.center[1])**2)
        return distance <= self.radius + 5

    def move(self, dx, dy):
        self.center = (self.center[0] + dx, self.center[1] + dy)

    def get_bounding_box(self):
        x, y = self.center
        return (x - self.radius, y - self.radius, x + self.radius, y + self.radius)

class FreeDrawAnnotation(Annotation):
    def __init__(self, points, color, thickness=2):
        super().__init__(color, thickness)
        self.points = points

    def draw(self, frame):
        for i in range(1, len(self.points)):
            cv2.line(frame, self.points[i-1], self.points[i], self.color, self.thickness)

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
        cv2.putText(frame, self.text, self.position, cv2.FONT_HERSHEY_SIMPLEX, 
                    self.font_size / 20, self.color, 2, cv2.LINE_AA)

    def is_point_inside(self, point):
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x, y = point
        x1, y1 = self.position
        margin = 5
        return x1 - margin <= x <= x1 + text_width + margin and \
               y1 - text_height - margin <= y <= y1 + margin

    def move(self, dx, dy):
        self.position = (self.position[0] + dx, self.position[1] + dy)

    def get_bounding_box(self):
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x1, y1 = self.position
        return (x1, y1 - text_height, x1 + text_width, y1)

class BlurAnnotation(Annotation):
    def __init__(self, p1, p2, blur_strength=25):
        super().__init__((0, 0, 0))
        self.p1 = p1
        self.p2 = p2
        self.blur_strength = blur_strength

    def draw(self, frame):
        x1, y1 = min(self.p1[0], self.p2[0]), min(self.p1[1], self.p2[1])
        x2, y2 = max(self.p1[0], self.p2[0]), max(self.p1[1], self.p2[1])
        h, w, _ = frame.shape
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            roi = frame[y1:y2, x1:x2]
            blurred_roi = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)
            frame[y1:y2, x1:x2] = blurred_roi

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        margin = 5
        return min(x1, x2) - margin <= x <= max(x1, x2) + margin and \
               min(y1, y2) - margin <= y <= max(y1, y2) + margin

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
        self.tip_length = tip_length

    def draw(self, frame):
        cv2.arrowedLine(frame, self.start_point, self.end_point, self.color, self.thickness, tipLength=self.tip_length)

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        tolerance = self.thickness + 10
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
        h, w, _ = frame.shape
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            cv2.rectangle(overlay, (x1, y1), (x2, y2), self.color, -1)
            cv2.addWeighted(overlay, self.opacity, frame, 1 - self.opacity, 0, frame)

    def is_point_inside(self, point):
        x, y = point
        x1, y1 = self.p1
        x2, y2 = self.p2
        margin = 5
        return min(x1, x2) - margin <= x <= max(x1, x2) + margin and \
               min(y1, y2) - margin <= y <= max(y1, y2) + margin

    def move(self, dx, dy):
        self.p1 = (self.p1[0] + dx, self.p1[1] + dy)
        self.p2 = (self.p2[0] + dx, self.p2[1] + dy)

    def get_bounding_box(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))