# VisioDoc3 - Compilation Guide

This guide provides instructions on how to compile the VisioDoc3 application into a standalone executable for both Windows and Linux using PyInstaller.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.x**: It is recommended to use Python 3.8 or newer.
*   **pip**: Python's package installer (usually comes with Python).
*   **Git**: For cloning the repository.

## Setting up the Environment

It's highly recommended to use a virtual environment to manage project dependencies.

1.  **Navigate to the project directory:**
    ```bash
    cd /home/moravel/VisioDoc3
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   **On Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **On Windows (Command Prompt):**
        ```bash
        venv\Scripts\activate.bat
        ```
    *   **On Windows (PowerShell):**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```

4.  **Install dependencies:**
    ```bash
    pip install opencv-python Pillow PyMuPDF PyInstaller numpy
    ```
    *   **For Windows only**: You will also need `pygrabber`.
        ```bash
        pip install pygrabber
        ```
        Note: `pygrabber` might require additional system dependencies like Microsoft Visual C++ Redistributable.

## Compiling for Windows

1.  **Ensure your virtual environment is activated.**
2.  **Run PyInstaller with the spec file:**
    The project includes a `VisioDoc3.spec` file which configures PyInstaller for correct packaging, including handling icons and data files.
    ```bash
    pyinstaller VisioDoc3.spec
    ```
3.  **Find the executable:**
    After successful compilation, the executable will be located in the `dist/VisioDoc3` directory within your project folder.

## Compiling for Linux

1.  **Ensure your virtual environment is activated.**
2.  **Run PyInstaller with the spec file:**
    ```bash
    pyinstaller VisioDoc3.spec
    ```
3.  **Find the executable:**
    After successful compilation, the executable will be located in the `dist/VisioDoc3` directory within your project folder.

### Important Notes for Linux:

*   **OpenCV Dependencies**: On some Linux distributions, you might need to install additional system libraries for OpenCV to function correctly, such as `libgl1-mesa-glx` or `libsm6`, `libxext6`, `libxrender1`. You can usually install them using your distribution's package manager (e.g., `sudo apt-get install libgl1-mesa-glx libsm6 libxext6 libxrender1` on Debian/Ubuntu).
*   **Tkinter**: Tkinter is usually included with Python installations. If you encounter issues, ensure your Python installation includes Tkinter support.
