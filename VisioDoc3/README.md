# VisioDoc3 - Visionneuse de Documents

VisioDoc3 est une application de visionneuse de documents en temps réel avec des capacités d'annotation, développée en Python en utilisant Tkinter pour l'interface utilisateur et OpenCV pour le traitement vidéo.

## Fonctionnalités

*   **Flux Vidéo en Temps Réel:** Affiche le flux vidéo d'une webcam connectée.
*   **Sélection de Caméra:** Permet de choisir parmi les caméras disponibles.
*   **Outils d'Annotation:**
    *   Ligne
    *   Rectangle
    *   Cercle
    *   Dessin à main levée
    *   Ajout de texte
    *   Zone de flou
    *   Flèche
    *   Surlignage
*   **Sauvegarde d'Image:** Permet de sauvegarder le cadre actuel avec les annotations sous forme d'image (PNG) ou de PDF.
*   **Annuler/Rétablir:** Fonctionnalités pour annuler et rétablir les dernières annotations.
*   **Effacer Tout:** Supprime toutes les annotations de l'image.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre système :

*   Python 3.x
*   pip (gestionnaire de paquets Python)

## Installation

Suivez ces étapes pour configurer et exécuter le projet :

1.  **Cloner le dépôt (si ce n'est pas déjà fait) :**
    ```bash
    git clone https://github.com/moravel/VisioDoc3.git
    cd VisioDoc3
    ```

2.  **Créer et activer un environnement virtuel :**
    Il est fortement recommandé d'utiliser un environnement virtuel pour gérer les dépendances du projet.

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sous Linux/macOS
    # Pour Windows, utilisez `venv\Scripts\activate`
    ```

3.  **Installer les dépendances :**
    Les dépendances principales sont `opencv-python`, `Pillow` et `tkinter` (généralement inclus avec Python).

    ```bash
    pip install opencv-python Pillow
    ```
    *Note: Tkinter est généralement inclus avec l'installation standard de Python. Si vous rencontrez des problèmes, vous devrez peut-être l'installer séparément en fonction de votre système d'exploitation (par exemple, `sudo apt-get install python3-tk` sur Debian/Ubuntu).*

## Utilisation

Pour démarrer l'application, assurez-vous que votre environnement virtuel est activé, puis exécutez le script `main.py` :

```bash
source venv/bin/activate # Si ce n'est pas déjà fait
python3 main.py
```

L'application devrait se lancer et afficher le flux vidéo de votre webcam par défaut. Vous pouvez sélectionner différentes caméras si plusieurs sont disponibles et utiliser les outils d'annotation sur le panneau de gauche.

## Dépannage

*   **L'application ne démarre pas / Pas de flux vidéo :**
    *   Assurez-vous que votre webcam est correctement connectée et que les pilotes sont à jour.
    *   Vérifiez les permissions d'accès à la caméra pour l'application.
    *   Les messages d'erreur dans la console peuvent indiquer des problèmes avec OpenCV ou l'accès à la caméra.
    *   Si vous avez plusieurs caméras, l'application essaie d'ouvrir la caméra avec l'index 0 par défaut. Vous pouvez essayer de modifier l'index de la caméra dans le code pour tester d'autres caméras.

*   **Problèmes de sauvegarde d'image :**
    *   Assurez-vous que vous avez sélectionné un format de fichier valide (.png ou .pdf).
    *   Vérifiez les permissions d'écriture dans le répertoire de destination.
    *   Si la sauvegarde PDF échoue, assurez-vous que Pillow est correctement installé et qu'il peut gérer la conversion en PDF.

---