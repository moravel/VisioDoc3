# VisioDoc3

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

VisioDoc3 is an intuitive application designed for real-time video stream visualization from your webcam, with advanced annotation capabilities. Whether you need to highlight details, add notes, or blur sensitive information, VisioDoc3 offers a comprehensive suite of tools to enhance your image capture and manipulation experience.

## Features

*   Real-time webcam feed display.
*   Comprehensive annotation tools:
    *   Freehand drawing
    *   Rectangles
    *   Circles
    *   Lines
    *   Text
    *   Blur zones
    *   Arrows
    *   Highlights
*   Annotation selection, movement, and resizing.
*   Color and thickness customization for annotations.
*   Zoom and pan functionality.
*   Horizontal and vertical image flipping.
*   Ability to open and annotate image files (PNG, JPG, BMP, GIF) and PDF documents.
*   Save annotated images as PNG or PDF.
*   Undo/Redo functionality for annotations.
*   Camera settings control (brightness, contrast, resolution).
*   User-friendly interface with tooltips and keyboard shortcuts.
 
## Hybrid Interface

VisioDoc3 features a modern hybrid interface with a compact sidebar and top toolbar for efficient workspace utilization.

### Interface Layout

- **Top Toolbar** (horizontal menu bar):
  - **Fichier**: Open, Save, Close file, Save, Quit
  - **Annotations**: Drawing tools (freedraw, rectangle, circle, line, text, blur, arrow, highlight, selection)
  - **Affichage**: Zoom controls, Flip, Fullscreen, Settings
  - **Webcam**: Camera selection dropdown (shows available cameras)
  - **Status indicator**: Shows current state at right

- **Left Sidebar** (48px compact icon panel):
  - Drawing tools with tooltips (9 buttons)
  - Color/Size pickers (2 buttons)
  - Actions: Undo, Redo, Save, Clear (4 buttons)
  - Display controls: Flip H/V, Fullscreen, Settings (4 buttons)
  - File controls: Open, Close (2 buttons)

- **Canvas Area**: Central workspace displaying the live webcam feed with overlaid annotations.

![](./screenshots/interface.png)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open file |
| Ctrl+Shift+S | Save image |
| Ctrl+F | Freehand tool |
| Ctrl+R | Rectangle tool |
| Ctrl+C | Circle tool |
| Ctrl+L | Line tool |
| Ctrl+T | Text tool |
| Ctrl+A | Arrow tool |
| Ctrl+H | Highlight tool |
| Ctrl+B | Blur tool |
| Ctrl+S | Selection tool |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| F11 | Toggle fullscreen |

## User Manual

For detailed instructions on how to use VisioDoc3 and its various features, please refer to the [User Manual](MANUAL.md).

## Compilation

For instructions on how to compile VisioDoc3 into an executable for Windows and Linux, please refer to the [Compilation Guide](COMPILATION.md).

### GitHub Actions (Recommended)

Windows executables are automatically built using GitHub Actions. Check the [Actions tab](https://github.com/moravel/VisioDoc3/actions) for builds after each push to the main branch.

## Technologies Used

*   Python
*   Tkinter (for GUI)
*   OpenCV (for video processing and drawing)
*   Pillow (PIL Fork - for image manipulation)
*   PyMuPDF (for PDF handling)
*   PyGrabber (Windows-specific for camera enumeration)
*   PyInstaller (for creating executables)

## License

**This is a copyleft license (GPLv3)** - any derivative works must also be open source under the same license.

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

VisioDoc3 is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
