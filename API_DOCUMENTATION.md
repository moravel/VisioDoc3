# VisioDoc3 - OpenAPI Architecture Documentation

## Overview

This documentation describes the OpenAPI 3.0 specifications created for the VisioDoc3 project. Since VisioDoc3 is a desktop application (not a web API), these specifications serve as architectural documentation, modeling the application's internal structure, class hierarchies, and data flows using REST-like patterns for clarity and standardization.

## Files

- **`openapi.yaml`** - Main OpenAPI 3.0 specification documenting all endpoints and paths
- **`components.yaml`** - Reusable component schemas referenced by `openapi.yaml`
- **`API_DOCUMENTATION.md`** - This documentation file

## Architecture Mapping

### Application Structure

The VisioDoc3 application (`visiodoc_app.py`) is modeled as a collection of REST-like resources:

| Application Class/Component | OpenAPI Resource | Description |
|---------------------------|------------------|-------------|
| `VisioDoc3` (main window) | `/application` | Application lifecycle and window management |
| Annotation classes | `/annotations` | Creation, modification, deletion of annotations |
| `VideoStreamThread` | `/videostream` | Camera capture and frame processing |
| File operations | `/file` | Opening, saving, PDF navigation |
| UI tools & state | `/ui` | Tool selection, zoom, pan, display control |
| Configuration | `/config` | Camera settings, brightness, contrast |
| Undo/redo stacks | `/state` | History management |

### Class to Schema Mapping

| Python Class | OpenAPI Schema | File |
|--------------|----------------|------|
| `Annotation` (base) | `Annotation` | components.yaml |
| `LineAnnotation` | `Annotation` (with LineProperties) | components.yaml |
| `RectangleAnnotation` | `Annotation` (with RectangleProperties) | components.yaml |
| `CircleAnnotation` | `Annotation` (with CircleProperties) | components.yaml |
| `FreeDrawAnnotation` | `Annotation` (with FreeDrawProperties) | components.yaml |
| `TextAnnotation` | `Annotation` (with TextProperties) | components.yaml |
| `BlurAnnotation` | `Annotation` (with BlurProperties) | components.yaml |
| `ArrowAnnotation` | `Annotation` (with ArrowProperties) | components.yaml |
| `HighlightAnnotation` | `Annotation` (with HighlightProperties) | components.yaml |
| `VideoStreamThread` | `VideoStreamStatus` | components.yaml |
| `VisioDoc3` (state) | `ApplicationState` | components.yaml |
| Fullscreen control | `FullscreenState` | components.yaml |

## New Features

### Fullscreen Mode (`/application/fullscreen`)
- **Toggle**: `POST` - Switches between normal and fullscreen display
- **Exit**: `DELETE` - Exits fullscreen mode (ESC key equivalent)
- **Keyboard**: `F11` to toggle, `ESC` to exit
- **Implementation**: `toggle_fullscreen()`, `exit_fullscreen()`
- **State**: `is_fullscreen` (bool), `FullscreenState` schema

## Key Design Decisions

### 1. REST-like Modeling of Desktop Operations

Since VisioDoc3 is not a web service, HTTP methods are used to represent operations:

- **GET** = Retrieve state or data
- **POST** = Create or initiate operations  
- **PUT** = Update configuration or settings
- **DELETE** = Remove resources

### 2. Annotation Type Handling

All annotations inherit from a base `Annotation` schema with type-specific properties:

```yaml
Annotation:
  allOf:
    - $ref: "#/components/schemas/AnnotationBase"
    - type: object
      properties:
        properties:
          oneOf:
            - $ref: "#/components/schemas/LineProperties"
            - $ref: "#/components/schemas/RectangleProperties"
            # ... etc
```

This mirrors the Python class hierarchy:

```python
class Annotation:
    def __init__(self, color, thickness):
        # Base class

class LineAnnotation(Annotation):
    def __init__(self, start_point, end_point, color, thickness):
        # Specific properties
```

### 3. Coordinate Systems

Two coordinate systems are documented:

- **Display coordinates**: Relative to the UI label/widget (affected by zoom/pan)
- **Original image coordinates**: Actual pixel coordinates in the source image

The `_convert_event_to_original_coords()` method is represented in the `MouseEvent` schema with conversion notes in descriptions.

### 4. State Management

Undo/redo stacks are modeled as separate from the main annotation list:

```yaml
HistoryStacks:
  properties:
    undo_stack: [Annotation]
    redo_stack: [Annotation]
```

This mirrors the Python implementation:

```python
self.undo_stack = []  # Stores undone annotations
self.redo_stack = []  # Stores redone annotations
```

## API Paths Summary

### Application Management

- `GET /application` - Get application instance
- `POST /application` - Initialize application
- `POST /application/closing` - Handle window close

### Annotations

- `GET /annotations` - List all annotations
- `POST /annotations` - Create new annotation
- `GET /annotations/{id}` - Get annotation by ID
- `PUT /annotations/{id}` - Update annotation
- `DELETE /annotations/{id}` - Delete annotation
- `POST /annotations/{id}/move` - Move annotation
- `POST /annotations/{id}/resize` - Resize annotation
- `POST /annotations/undo` - Undo last annotation
- `POST /annotations/redo` - Redo last undone annotation
- `DELETE /annotations/clear` - Clear all annotations

### Video Stream

- `GET /videostream` - Get stream status
- `POST /videostream` - Start video stream
- `POST /videostream/stop` - Stop video stream
- `GET /videostream/frame` - Get current frame
- `POST /videostream/flip/horizontal` - Toggle horizontal flip
- `POST /videostream/flip/vertical` - Toggle vertical flip
- `GET /videostream/cameras` - List available cameras
- `POST /videostream/cameras/scan` - Scan for cameras

### File Operations

- `POST /file` - Open image/PDF file
- `POST /file/close` - Close file (return to webcam)
- `POST /file/save` - Save annotated image
- `GET /file/pdf/page` - Get current PDF page
- `GET /file/pdf/page/{number}` - Navigate to PDF page
- `POST /file/pdf/next` - Next PDF page
- `POST /file/pdf/prev` - Previous PDF page

### UI Components

- `PUT /ui/tool` - Set active tool
- `PUT /ui/tool/color` - Set annotation color
- `PUT /ui/tool/size` - Set annotation size/thickness
- `GET /ui/display` - Get display status
- `POST /ui/display/zoom` - Apply zoom
- `POST /ui/display/zoom/in` - Zoom in
- `POST /ui/display/zoom/out` - Zoom out
- `POST /ui/display/reset` - Reset zoom/pan
- `POST /ui/display/pan` - Pan display
- `POST /ui/mouse/click` - Handle mouse click
- `POST /ui/mouse/drag` - Handle mouse drag
- `POST /ui/mouse/release` - Handle mouse release
- `POST /ui/mouse/move` - Handle mouse move

### Configuration

- `GET /config` - Get all configuration
- `GET /config/camera` - Get camera config
- `POST /config/camera/save` - Save camera config
- `PUT /config/brightness` - Set brightness
- `PUT /config/contrast` - Set contrast
- `PUT /config/resolution` - Set resolution

### State Management

- `GET /state` - Get application state
- `GET /state/history` - Get undo/redo stacks

## Data Flow Examples

### Example 1: Creating a Rectangle Annotation

**Python Implementation:**
```python
def on_mouse_up(self, event):
    if self.current_tool == "rectangle":
        self.annotations.append(RectangleAnnotation(
            self.start_point, 
            self.end_point, 
            color=self.current_annotation_color, 
            thickness=self.current_annotation_thickness
        ))
```

**OpenAPI Equivalent:**
```http
POST /annotations
Content-Type: application/json

{
  "type": "rectangle",
  "color": {"b": 255, "g": 0, "r": 0},
  "thickness": 2,
  "properties": {
    "corner1": {"x": 100, "y": 100},
    "corner2": {"x": 200, "y": 200},
    "filled": false
  }
}
```

### Example 2: Undo/Redo Operations

**Python Implementation:**
```python
def undo_last_annotation(self):
    if self.annotations:
        last_annotation = self.annotations.pop()
        self.redo_stack.append(last_annotation)

def redo_last_annotation(self):
    if self.redo_stack:
        last_redone = self.redo_stack.pop()
        self.annotations.append(last_redone)
```

**OpenAPI Equivalent:**
```http
POST /annotations/undo

# Response
{
  "undone": {"id": 5, "type": "rectangle", ...},
  "remaining": 3
}

POST /annotations/redo

# Response
{
  "id": 5,
  "type": "rectangle",
  ...
}
```

### Example 3: Camera Configuration

**Python Implementation:**
```python
def set_brightness(self, value):
    if self.video_stream_thread and self.video_stream_thread.cap:
        self.video_stream_thread.cap.set(cv2.CAP_PROP_BRIGHTNESS, float(value))
```

**OpenAPI Equivalent:**
```http
PUT /config/brightness
Content-Type: application/json

{
  "value": 128
}
```

## Schema Details

### Color Handling

OpenCV uses BGR format while PIL uses RGB. The schemas document both:

```yaml
ColorBGR:
  properties:
    b: {type: integer, minimum: 0, maximum: 255}
    g: {type: integer, minimum: 0, maximum: 255}
    r: {type: integer, minimum: 0, maximum: 255}

ColorRGB:
  properties:
    r: {type: integer, minimum: 0, maximum: 255}
    g: {type: integer, minimum: 0, maximum: 255}
    b: {type: integer, minimum: 0, maximum: 255}
```

### Blur Annotation Special Case

The `BlurAnnotation` uses Gaussian blur with odd kernel sizes:

```yaml
BlurProperties:
  properties:
    blur_strength:
      type: integer
      minimum: 1
      maximum: 99
      default: 25
      description: Must be odd for Gaussian blur
```

Python implementation:
```python
kernel_size = self.blur_strength if self.blur_strength % 2 == 1 else self.blur_strength + 1
blurred_roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
```

## Usage with Code Generation

These OpenAPI specifications can be used to:

1. **Generate API documentation** using tools like Swagger UI or Redoc
2. **Generate client SDKs** in various languages
3. **Validate API implementations** against the specification
4. **Document internal architecture** for developers

### Example: Generate HTML Documentation

```bash
# Using Swagger UI
docker run -p 8080:8080 -e SWAGGER_JSON=/api/openapi.yaml -v $(pwd):/api swaggerapi/swagger-ui
```

## Validation

The YAML files conform to OpenAPI 3.0.3 specification and can be validated using:

```bash
# Install swagger-cli
npm install -g @apidevtools/swagger-cli

# Validate
swagger-cli validate openapi.yaml
swagger-cli validate components.yaml
```

## Relationship to Source Code

### File Structure

```
VisioDoc3/
├── main.py                          # Entry point
├── visiodoc_app.py                  # Main application class
├── annotations.py                   # Annotation classes
├── video_stream.py                  # VideoStreamThread class
├── tooltip.py                       # Tooltip class
├── openapi.yaml                     # OpenAPI specification (this file)
├── components.yaml                  # Reusable schemas
└── API_DOCUMENTATION.md            # This file
```

### Key Methods Mapped to Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `VisioDoc3.__init__()` | `POST /application` | Initialize application |
| `VisioDoc3.on_closing()` | `POST /application/closing` | Handle window close |
| `VisioDoc3.set_tool()` | `PUT /ui/tool` | Change active tool |
| `VisioDoc3.create_annotation()` | `POST /annotations` | Create annotation |
| `VisioDoc3.undo_last_annotation()` | `POST /annotations/undo` | Undo annotation |
| `VideoStreamThread.run()` | `POST /videostream` | Start video stream |
| `VideoStreamThread.flip_horizontal()` | `POST /videostream/flip/horizontal` | Toggle flip |
| `VisioDoc3.open_file()` | `POST /file` | Open file |
| `VisioDoc3.save_image()` | `POST /file/save` | Save file |
| `VisioDoc3.set_brightness()` | `PUT /config/brightness` | Set brightness |

## Conclusion

This OpenAPI documentation provides a standardized way to understand the VisioDoc3 architecture, even though it's a desktop application. By modeling internal classes and methods as REST-like resources, we create:

1. **Clear structure**: Understand components and their relationships
2. **Standardized documentation**: Use industry-standard OpenAPI format
3. **Future extensibility**: Could be adapted for web API if needed
4. **Better communication**: Common language for developers and stakeholders

The specifications accurately reflect the Python implementation while providing the benefits of formal API documentation.
### New Features in Current Implementation

#### 1. Fullscreen Mode
- **Endpoint**: `POST /application/fullscreen` (toggle), `DELETE /application/fullscreen` (exit)
- **Keyboard Shortcut**: `F11` to toggle, `ESC` to exit
- **Implementation**: `toggle_fullscreen()`, `exit_fullscreen()` methods
- **State**: `is_fullscreen` boolean, `FullscreenState` schema

### Conclusion

This OpenAPI documentation provides a standardized way to understand the VisioDoc3 architecture.
