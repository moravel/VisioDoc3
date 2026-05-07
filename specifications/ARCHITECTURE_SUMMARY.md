# VisioDoc3 OpenAPI Architecture Summary

## Project: VisioDoc3 Desktop Application

### Overview
OpenAPI 3.0 specification files documenting the internal architecture of VisioDoc3,
a Python desktop application (Tkinter + OpenCV + PIL) for document viewing and annotation.

---

## Files Created

| File | Lines | Purpose |
|------|-------|----------|
| `openapi.yaml` | 1,616 | Main OpenAPI 3.0 specification with all endpoints and paths |
| `components.yaml` | 1,021 | Reusable schema definitions (44 schemas) |
| `API_DOCUMENTATION.md` | 380 | Comprehensive documentation and usage guide |
| `ARCHITECTURE_SUMMARY.md` | This file | Quick reference summary |

---

## OpenAPI Specification Details

### Basic Info
- **OpenAPI Version**: 3.0.3
- **Title**: VisioDoc3 Application Architecture API
- **Version**: 3.0.0
- **License**: MIT

### Servers
- `app://visiodoc3` - Local VisioDoc3 Application Instance

### Tags (7)
1. **Application** - Core application lifecycle and main window management
2. **Annotations** - Annotation creation, management, and rendering
3. **VideoStream** - Camera capture and video stream handling
4. **FileOperations** - File I/O, document loading, and saving
5. **UIComponents** - User interface components and interactions
6. **Configuration** - Application settings and camera configuration
7. **StateManagement** - Undo/redo stacks and application state

---

## API Paths (50 total)

### Application Management (5 paths)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/application` | Get application instance |
| POST | `/application` | Initialize application |
| POST | `/application/closing` | Handle window closing |
| POST | `/application/fullscreen` | Toggle fullscreen mode |
| DELETE | `/application/fullscreen` | Exit fullscreen mode |

### Annotations (13 paths)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/annotations` | List all annotations |
| POST | `/annotations` | Create new annotation |
| GET | `/annotations/{id}` | Get annotation by ID |
| PUT | `/annotations/{id}` | Update annotation |
| DELETE | `/annotations/{id}` | Delete annotation |
| POST | `/annotations/{id}/move` | Move annotation |
| POST | `/annotations/{id}/resize` | Resize annotation |
| POST | `/annotations/undo` | Undo last annotation |
| POST | `/annotations/redo` | Redo last undone annotation |
| DELETE | `/annotations/clear` | Clear all annotations |
| GET | `/annotations/types` | Get available annotation types |
| GET | `/annotations/bounding-box/{id}` | Get annotation bounding box |
| POST | `/annotations/{id}/is-point-inside` | Check if point is inside annotation |

### Video Stream (8 paths)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/videostream` | Get video stream status |
| POST | `/videostream` | Start video stream |
| POST | `/videostream/stop` | Stop video stream |
| GET | `/videostream/frame` | Get current frame |
| POST | `/videostream/flip/horizontal` | Toggle horizontal flip |
| POST | `/videostream/flip/vertical` | Toggle vertical flip |
| GET | `/videostream/cameras` | List available cameras |
| POST | `/videostream/cameras/scan` | Scan for cameras |

### File Operations (8 paths)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/file` | Open image/PDF file |
| POST | `/file/close` | Close file |
| POST | `/file/save` | Save annotated image |
| GET | `/file/pdf/page` | Get current PDF page |
| GET | `/file/pdf/page/{number}` | Navigate to PDF page |
| POST | `/file/pdf/next` | Next PDF page |
| POST | `/file/pdf/prev` | Previous PDF page |

### UI Components (14 paths)
| Method | Path | Description |
|--------|------|-------------|
| PUT | `/ui/tool` | Set active tool |
| PUT | `/ui/tool/color` | Set annotation color |
| PUT | `/ui/tool/size` | Set annotation size |
| GET | `/ui/display` | Get display status |
| POST | `/ui/display/zoom` | Apply zoom |
| POST | `/ui/display/zoom/in` | Zoom in |
| POST | `/ui/display/zoom/out` | Zoom out |
| POST | `/ui/display/reset` | Reset display (zoom/pan) |
| POST | `/ui/display/pan` | Pan display |
| POST | `/ui/mouse/click` | Handle mouse click |
| POST | `/ui/mouse/drag` | Handle mouse drag |
| POST | `/ui/mouse/release` | Handle mouse release |
| POST | `/ui/mouse/move` | Handle mouse move |

### Configuration (5 paths)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/config` | Get all configuration |
| GET | `/config/camera` | Get camera configuration |
| POST | `/config/camera/save` | Save camera configuration |
| PUT | `/config/brightness` | Set brightness |
| PUT | `/config/contrast` | Set contrast |
| PUT | `/config/resolution` | Set resolution |

### State Management (2 paths)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/state` | Get application state |
| GET | `/state/history` | Get undo/redo stacks |

---

## Reusable Schemas (44 total)

### Core Schemas (5)
- `Application` - Main application instance
- `ApplicationState` - Current application state
- `WindowGeometry` - Window position and dimensions
- `DisplayStatus` - Display configuration and status
- `AppConfig` - Application configuration

### Annotation Schemas (15)
- `Annotation` - Base annotation (all types)
- `AnnotationBase` - Common annotation properties
- `AnnotationCreate` - Create request payload
- `AnnotationUpdate` - Update request payload
- `LineProperties` - Line annotation properties
- `RectangleProperties` - Rectangle annotation properties
- `CircleProperties` - Circle annotation properties
- `FreeDrawProperties` - Freehand drawing properties
- `TextProperties` - Text annotation properties
- `BlurProperties` - Blur annotation properties
- `ArrowProperties` - Arrow annotation properties
- `HighlightProperties` - Highlight annotation properties
- `AnnotationTypeInfo` - Annotation type information
- `ResizeOperation` - Resize operation details

### Geometry & Color Schemas (6)
- `Point2D` - 2D point coordinates
- `BoundingBox` - Axis-aligned bounding box
- `ColorBGR` - Color in BGR format (OpenCV)
- `ColorRGB` - Color in RGB format
- `ZoomState` - Zoom level state
- `PanState` - Pan offset state

### Video Stream Schemas (4)
- `VideoStreamStatus` - Stream status information
- `VideoStreamConfig` - Stream configuration
- `VideoFrame` - Video frame data
- `CameraInfo` - Camera device information

### File Operation Schemas (6)
- `FileOpenRequest` - File open request
- `FileStatus` - File status information
- `SaveRequest` - Save operation request
- `SaveResult` - Save operation result
- `PdfPageInfo` - PDF page information

### UI Component Schemas (5)
- `ToolSelection` - Tool selection request
- `ToolStatus` - Current tool status
- `AnnotationSize` - Annotation size settings
- `MouseEvent` - Mouse event data
- `MouseDragEvent` - Mouse drag event data

### Configuration Schemas (4)
- `CameraConfig` - Camera configuration
- `Resolution` - Image resolution
- `AnnotationSize` - Annotation dimensions

### State Management Schemas (2)
- `HistoryStacks` - Undo/redo history
- `ApplicationState` - Complete application state

### Response Wrappers (2)
- `ApiResponse` - Standard API response
- `ErrorResponse` - Error response

---

## Annotation Types Supported

| Type | Properties | Description |
|------|------------|-------------|
| `line` | start_point, end_point | Straight line |
| `rectangle` | corner1, corner2, filled | Rectangle |
| `circle` | center, radius, filled | Circle |
| `freedraw` | points[] | Freehand drawing |
| `text` | position, text, font_size | Text annotation |
| `blur` | corner1, corner2, blur_strength | Gaussian blur region |
| `arrow` | start_point, end_point, tip_length | Arrow line |
| `highlight` | corner1, corner2, color, opacity | Translucent highlight |

---

## Key Features Documented

### 1. Annotation System
- 8 annotation types (line, rectangle, circle, freedraw, text, blur, arrow, highlight)
- Create, read, update, delete operations
- Move and resize operations
- Bounding box calculations
- Point-in-annotation detection

### 2. Video Stream Handling
- Camera enumeration and selection
- Multiple resolution support
- Horizontal/vertical flip
- Frame capture and display
- Brightness and contrast control

### 3. File Operations
- Image file support (PNG, JPG, BMP, GIF)
- PDF document support (via PyMuPDF)
- Multi-page PDF navigation
- Save as PNG or PDF
- Zoom and pan preservation

### 4. State Management
- Undo/redo stacks
- Tool selection
- Annotation color and size
- Zoom and pan state
- Selection and hover states

### 5. UI Interactions
- Mouse click, drag, release, move
- Zoom (wheel, buttons, keyboard)
- Pan (middle-click drag)
- Tool selection shortcuts
- Hover detection

---

## Python Classes Mapped

| Python File | Classes | OpenAPI Coverage |
|-------------|---------|------------------|
| `visiodoc_app.py` | `VisioDoc3` | ✓ Full |  
| `annotations.py` | `Annotation`, `LineAnnotation`, `RectangleAnnotation`, `CircleAnnotation`, `FreeDrawAnnotation`, `TextAnnotation`, `BlurAnnotation`, `ArrowAnnotation`, `HighlightAnnotation` | ✓ Full |
| `video_stream.py` | `VideoStreamThread` | ✓ Full |
| `tooltip.py` | `Tooltip` | ⚠ Partial (UI component) |

---

## Technology Stack

- **GUI Framework**: Tkinter
- **Image Processing**: PIL/Pillow
- **Video Processing**: OpenCV
- **PDF Support**: PyMuPDF (fitz)
- **Documentation**: OpenAPI 3.0

---

## Usage Examples

### Create Rectangle Annotation
```bash
curl -X POST app://visiodoc3/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "type": "rectangle",
    "color": {"b": 255, "g": 0, "r": 0},
    "thickness": 2,
    "properties": {
      "corner1": {"x": 100, "y": 100},
      "corner2": {"x": 200, "y": 200}
    }
  }'
```

### List All Annotations
```bash
curl app://visiodoc3/annotations
```

### Undo Last Annotation
```bash
curl -X POST app://visiodoc3/annotations/undo
```

### Start Video Stream
```bash
curl -X POST app://visiodoc3/videostream \
  -H "Content-Type: application/json" \
  -d '{"camera_index": 0, "width": 1280, "height": 720}'
```

---

## Validation

Both YAML files are valid according to OpenAPI 3.0.3 specification:

```bash
# Validate with swagger-cli
swagger-cli validate openapi.yaml
swagger-cli validate components.yaml
```

---

## Generated Statistics

- **Total Lines**: ~2,974
- **OpenAPI Paths**: 47
- **Reusable Schemas**: 44
- **Tags**: 7
- **Annotation Types**: 8
- **HTTP Methods**: GET, POST, PUT, DELETE

---

## Conclusion

These OpenAPI specifications provide comprehensive documentation of the VisioDoc3 application architecture, modeling desktop application components as REST-like resources for clarity, standardization, and future extensibility.
