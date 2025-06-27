# VisioDoc3

VisioDoc3 is a Python application for webcam-based document viewing and annotation. It allows users to draw various shapes (lines, rectangles, circles, freehand), add text, and save the annotated images as PNGs or PDFs.

## Features

*   Real-time webcam feed display.
*   Annotation tools:
    *   Line
    *   Rectangle
    *   Circle
    *   Freehand drawing
    *   Text annotation
*   Undo/Redo functionality for annotations.
*   Save annotated images as PNG or PDF.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd VisioDoc3
    ```
    (Replace `<repository_url>` with the actual URL of your repository.)

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install opencv-python-headless Pillow
    ```
    *(Note: `opencv-python-headless` is recommended for server environments or if you don't need the full OpenCV GUI features. If you encounter issues, you might try `pip install opencv-python` instead.)*

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Using Annotation Tools:**
    *   Select a tool from the left panel (e.g., "Rectangle", "Ajouter Texte").
    *   Click and drag (for shapes) or click (for text) on the video feed to apply annotations.
    *   Use "Annuler" (Undo) and "Rétablir" (Redo) buttons to manage annotations.

3.  **Saving Images:**
    *   Click the "Sauvegarder" (Save) button.
    *   Choose the desired file type (PNG or PDF) and location.

## Troubleshooting

*   **Camera not found:** Ensure your webcam is connected and not in use by other applications. You might need to adjust the `camera_index` in `main.py` if you have multiple cameras.
*   **Text input dialog not working:** This issue has been addressed in recent updates. Ensure your local repository is up to date.

---
