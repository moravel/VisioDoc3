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

    def resize(self, handle, current_mouse_point, initial_drag_point):
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
        denominator = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        if denominator < 1e-6: # Handle case where line is a single point or very short
            return np.sqrt((x - x1)**2 + (y - y1)**2) <= tolerance
        distance = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / denominator
        return distance <= tolerance

    def move(self, dx, dy):
        self.start_point = (int(self.start_point[0] + dx), int(self.start_point[1] + dy))
        self.end_point = (int(self.end_point[0] + dx), int(self.end_point[1] + dy))

    def get_bounding_box(self):
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def get_resize_handles(self):
        return {"start": self.start_point, "end": self.end_point}

    def resize(self, handle, current_mouse_point, initial_drag_point):
        if handle == "start":
            self.start_point = current_mouse_point
        elif handle == "end":
            self.end_point = current_mouse_point

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
        self.p1 = (int(self.p1[0] + dx), int(self.p1[1] + dy))
        self.p2 = (int(self.p2[0] + dx), int(self.p2[1] + dy))

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

    def resize(self, handle, current_mouse_point, initial_drag_point):
        # Determine the fixed point (opposite corner) based on the handle being dragged
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
            return # Should not happen

        # Update p1 and p2 based on the fixed point and current mouse position
        new_x1 = min(fixed_point[0], current_mouse_point[0])
        new_y1 = min(fixed_point[1], current_mouse_point[1])
        new_x2 = max(fixed_point[0], current_mouse_point[0])
        new_y2 = max(fixed_point[1], current_mouse_point[1])

        self.p1 = (int(new_x1), int(new_y1))
        self.p2 = (int(new_x2), int(new_y2))

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
        self.center = (int(self.center[0] + dx), int(self.center[1] + dy))

    def get_bounding_box(self):
        x, y = self.center
        return (x - self.radius, y - self.radius, x + self.radius, y + self.radius)

    def get_resize_handles(self):
        x, y = self.center
        r = self.radius
        # Define handles at cardinal points and corners of the bounding box
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
        # The new radius is the distance from the center to the current mouse position.
        new_radius = np.sqrt((current_mouse_point[0] - self.center[0])**2 + (current_mouse_point[1] - self.center[1])**2)
        self.radius = int(new_radius)


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
        self.points = [(int(p[0] + dx), int(p[1] + dy)) for p in self.points]

    def get_bounding_box(self):
        if not self.points:
            return None
        x_coords = [p[0] for p in self.points]
        y_coords = [p[1] for p in self.points]
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def get_resize_handles(self):
        x1, y1, x2, y2 = self.get_bounding_box()
        return {
            "top-left": (x1, y1), "top-right": (x2, y1),
            "bottom-left": (x1, y2), "bottom-right": (x2, y2)
        }

    def resize(self, handle, current_mouse_point, initial_drag_point):
        x1, y1, x2, y2 = self.get_bounding_box()
        orig_w = x2 - x1
        orig_h = y2 - y1

        if orig_w == 0 or orig_h == 0: # Avoid division by zero
            return

        # Determine the fixed point (opposite corner) based on the handle being dragged
        if handle == "top-left":
            fixed_x, fixed_y = x2, y2
        elif handle == "top-right":
            fixed_x, fixed_y = x1, y2
        elif handle == "bottom-left":
            fixed_x, fixed_y = x2, y1
        elif handle == "bottom-right":
            fixed_x, fixed_y = x1, y1
        else:
            return # Should not happen

        # Calculate new bounding box based on fixed point and current mouse position
        new_x1 = min(fixed_x, current_mouse_point[0])
        new_y1 = min(fixed_y, current_mouse_point[1])
        new_x2 = max(fixed_x, current_mouse_point[0])
        new_y2 = max(fixed_y, current_mouse_point[1])

        new_w = max(1, new_x2 - new_x1)
        new_h = max(1, new_y2 - new_y1)

        scale_x = new_w / orig_w
        scale_y = new_h / orig_h

        # Apply scaling and translation to all points
        new_points = []
        for p_x, p_y in self.points:
            # Translate point relative to the fixed point
            translated_x = p_x - fixed_x
            translated_y = p_y - fixed_y

            # Scale
            scaled_x = translated_x * scale_x
            scaled_y = translated_y * scale_y

            # Translate back from the fixed point to the new position
            new_points.append((int(scaled_x + fixed_x), int(scaled_y + fixed_y)))
        self.points = new_points

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
        self.position = (int(self.position[0] + dx), int(self.position[1] + dy))

    def get_bounding_box(self):
        text_width = len(self.text) * self.font_size // 2
        text_height = self.font_size
        x1, y1 = self.position
        return (x1, y1 - text_height, x1 + text_width, y1)

    def get_resize_handles(self):
        x1, y1, x2, y2 = self.get_bounding_box()
        return {"size": (x2, y2)}

    def resize(self, handle, current_mouse_point, initial_drag_point):
        if handle == "size":
            # Calculate the change in distance from the initial drag point
            initial_distance = np.sqrt((initial_drag_point[0] - self.position[0])**2 + (initial_drag_point[1] - self.position[1])**2)
            current_distance = np.sqrt((current_mouse_point[0] - self.position[0])**2 + (current_mouse_point[1] - self.position[1])**2)

            if initial_distance > 0:
                scale_factor = current_distance / initial_distance
                self.font_size = max(8, int(self.font_size * scale_factor))

class BlurAnnotation(RectangleAnnotation):
    def __init__(self, p1, p2, blur_strength=25):
        super().__init__(p1, p2, (0,0,0))
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

class ArrowAnnotation(LineAnnotation):
    def __init__(self, start_point, end_point, color=(0, 0, 255), thickness=2, tip_length=0.3):
        super().__init__(start_point, end_point, color, thickness)
        self.tip_length = tip_length

    def draw(self, frame):
        cv2.arrowedLine(frame, self.start_point, self.end_point, self.color, self.thickness, tipLength=self.tip_length)

class HighlightAnnotation(RectangleAnnotation):
    def __init__(self, p1, p2, color=(255, 255, 0), opacity=0.3):
        super().__init__(p1, p2, color)
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