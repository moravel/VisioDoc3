# VisioDoc3

## Visionneuse de Documents et Outil d'Annotation

VisioDoc3 est une application Python développée avec Tkinter et OpenCV, conçue pour visualiser des flux de webcam en temps réel et y ajouter des annotations. Elle permet aux utilisateurs de capturer des images, de dessiner diverses formes, d'ajouter du texte, d'appliquer des effets de flou ou de surlignage, et de manipuler la vue avec des fonctionnalités de zoom et de panoramique.

### Fonctionnalités principales :
-   Visualisation en temps réel depuis une webcam.
-   Outils d'annotation : Ligne, Rectangle, Cercle, Dessin à main levée, Texte, Flou, Flèche, Surlignage.
-   Sélection, déplacement et redimensionnement des annotations existantes.
-   Choix de la couleur et de l'épaisseur des annotations.
-   Fonctionnalités de zoom (molette de la souris, boutons +/-) et de panoramique (bouton central de la souris).
-   Sauvegarde des images annotées au format PNG ou PDF.
-   Fonctions Annuler/Rétablir et Effacer tout.
-   Paramètres de la caméra (luminosité, contraste, résolution).

## Compilation

### Compilation pour Linux

Pour compiler l'application en un exécutable autonome pour Linux, assurez-vous d'avoir un environnement Python avec `pyinstaller` installé. Il est recommandé d'utiliser un environnement virtuel.

1.  **Accédez au répertoire racine du projet** (où se trouve le dossier `VisioDoc3`).
2.  **Activez votre environnement virtuel** (si vous en utilisez un) :
    ```bash
    source venv/bin/activate
    ```
3.  **Exécutez la commande PyInstaller suivante** :
    ```bash
    /home/moravel/VisioDoc3/venv/bin/pyinstaller --onefile --windowed --add-data 'VisioDoc3/VisioDoc3/icons:icons' --hidden-import PIL._tkinter_finder VisioDoc3/VisioDoc3/main.py
    ```
    -   `--onefile` : Crée un seul fichier exécutable.
    -   `--windowed` : Empêche l'ouverture d'une console lors de l'exécution de l'application graphique.
    -   `--add-data 'VisioDoc3/VisioDoc3/icons:icons'` : Inclut le répertoire des icônes dans l'exécutable.
    -   `--hidden-import PIL._tkinter_finder` : Assure que le module nécessaire pour l'intégration de Pillow/Tkinter est inclus.
    -   `VisioDoc3/VisioDoc3/main.py` : Le chemin vers le script principal de l'application.

L'exécutable sera généré dans le répertoire `dist/`.

### Compilation pour Windows

La compilation croisée pour Windows depuis Linux n'est pas toujours fiable. Pour obtenir un exécutable Windows stable, il est fortement recommandé d'effectuer la compilation sur une machine Windows.

1.  **Copiez le dossier `VisioDoc3`** sur votre machine Windows.
2.  **Assurez-vous d'avoir Python et PyInstaller installés** sur cette machine. Il est recommandé d'utiliser un environnement virtuel.
3.  **Ouvrez une invite de commande (CMD) ou PowerShell** dans le répertoire racine du projet (où se trouve le dossier `VisioDoc3`).
4.  **Activez votre environnement virtuel** (si vous en utilisez un) :
    ```cmd
    venv\Scripts\activate
    ```
5.  **Exécutez la commande PyInstaller suivante** :
    ```cmd
    pyinstaller --onefile --windowed --add-data "VisioDoc3\VisioDoc3\icons;icons" --hidden-import PIL._tkinter_finder VisioDoc3\VisioDoc3\main.py
    ```
    -   Notez l'utilisation des doubles barres obliques inverses (`\`) pour les chemins sous Windows.
    -   `--add-data "VisioDoc3\VisioDoc3\icons;icons"` : Inclut le répertoire des icônes.

L'exécutable sera généré dans le répertoire `dist/` de votre projet Windows.

