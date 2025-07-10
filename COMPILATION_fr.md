# VisioDoc3 - Guide de Compilation

Ce guide fournit des instructions sur la façon de compiler l'application VisioDoc3 en un exécutable autonome pour Windows et Linux à l'aide de PyInstaller.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés :

*   **Python 3.x** : Il est recommandé d'utiliser Python 3.8 ou une version plus récente.
*   **pip** : Le gestionnaire de paquets de Python (généralement fourni avec Python).
*   **Git** : Pour cloner le dépôt.

## Configuration de l'environnement

Il est fortement recommandé d'utiliser un environnement virtuel pour gérer les dépendances du projet.

1.  **Naviguez vers le répertoire du projet :**
    ```bash
    cd /home/moravel/VisioDoc3
    ```

2.  **Créez un environnement virtuel :**
    ```bash
    python3 -m venv venv
    ```

3.  **Activez l'environnement virtuel :**
    *   **Sous Linux/macOS :**
        ```bash
        source venv/bin/activate
        ```
    *   **Sous Windows (Invite de commandes) :**
        ```bash
        venv\Scripts\activate.bat
        ```
    *   **Sous Windows (PowerShell) :**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```

4.  **Installez les dépendances :**
    ```bash
    pip install opencv-python Pillow PyMuPDF PyInstaller numpy
    ```
    *   **Pour Windows uniquement** : Vous aurez également besoin de `pygrabber`.
        ```bash
        pip install pygrabber
        ```
        Remarque : `pygrabber` peut nécessiter des dépendances système supplémentaires comme le redistribuable Microsoft Visual C++.

## Compilation pour Windows

1.  **Assurez-vous que votre environnement virtuel est activé.**
2.  **Exécutez PyInstaller avec le fichier de spécification :**
    Le projet inclut un fichier `VisioDoc3.spec` qui configure PyInstaller pour un empaquetage correct, y compris la gestion des icônes et des fichiers de données.
    ```bash
    pyinstaller VisioDoc3.spec
    ```
3.  **Trouvez l'exécutable :**
    Après une compilation réussie, l'exécutable se trouvera dans le répertoire `dist/VisioDoc3` de votre dossier de projet.

## Compilation pour Linux

1.  **Assurez-vous que votre environnement virtuel est activé.**
2.  **Exécutez PyInstaller avec le fichier de spécification :**
    ```bash
    pyinstaller VisioDoc3.spec
    ```
3.  **Trouvez l'exécutable :**
    Après une compilation réussie, l'exécutable se trouvera dans le répertoire `dist/VisioDoc3` de votre dossier de projet.

### Notes importantes pour Linux :

*   **Dépendances OpenCV** : Sur certaines distributions Linux, vous devrez peut-être installer des bibliothèques système supplémentaires pour qu'OpenCV fonctionne correctement, telles que `libgl1-mesa-glx` ou `libsm6`, `libxext6`, `libxrender1`. Vous pouvez généralement les installer à l'aide du gestionnaire de paquets de votre distribution (par exemple, `sudo apt-get install libgl1-mesa-glx libsm6 libxext6 libxrender1` sur Debian/Ubuntu).
*   **Tkinter** : Tkinter est généralement inclus avec les installations Python. Si vous rencontrez des problèmes, assurez-vous que votre installation Python inclut le support de Tkinter.
