# Video stream handling module for OpenCV camera capture
# Module de gestion de flux vidéo pour la capture de caméra OpenCV
import threading
import cv2
import time
import platform


# Thread-based video stream for non-blocking camera capture
# Flux vidéo basé sur thread pour une capture de caméra sans blocage
class VideoStreamThread(threading.Thread):
    # Initializes the video stream thread with camera settings
    # Initialise le thread de flux vidéo avec les paramètres de la caméra
    def __init__(self, camera_index=0, width=1280, height=720):
        super().__init__()
        self.camera_index = (
            camera_index  # Index of the camera device / Index du périphérique caméra
        )
        self.width = width  # Frame width in pixels / Largeur de la trame en pixels
        self.height = height  # Frame height in pixels / Hauteur de la trame en pixels
        self.cap = None  # OpenCV VideoCapture object / Objet VideoCapture OpenCV
        self._run_flag = True  # Controls the main capture loop / Contrôle la boucle principale de capture
        self.frame = None  # Latest captured frame / Dernière trame capturée
        self.lock = (
            threading.Lock()
        )  # Thread lock for frame access / Verrou de thread pour l'accès à la trame
        self.flip_h = False  # Horizontal flip state / État de retournement horizontal
        self.flip_v = False  # Vertical flip state / État de retournement vertical

        # Performance optimization
        # Optimisation des performances
        self._target_interval = (
            0.033  # ~30 FPS target / Cible d'environ 30 images par seconde
        )
        self._last_frame_time = 0  # Timestamp for frame timing / Horodatage pour la synchronisation des trames

    # Main thread execution - opens camera and captures frames
    # Exécution principale du thread - ouvre la caméra et capture les trames
    def run(self):
        if platform.system() == "Windows":
            # Use DirectShow backend for Windows compatibility
            # Utilise le backend DirectShow pour la compatibilité Windows
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            # Use default backend for other platforms
            # Utilise le backend par défaut pour les autres plateformes
            self.cap = cv2.VideoCapture(self.camera_index)

        # Set the desired frame dimensions
        # Définit les dimensions souhaitées de la trame
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Check if camera opened successfully
        # Vérifie si la caméra s'est ouverte avec succès
        if not self.cap.isOpened():
            print(f"Error: Could not open video stream for camera {self.camera_index}")
            self._run_flag = False
            return

        self._last_frame_time = time.perf_counter()

        # Main capture loop
        # Boucle principale de capture
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    # Apply horizontal flip if enabled
                    # Applique le retournement horizontal si activé
                    if self.flip_h:
                        frame = cv2.flip(frame, 1)
                    # Apply vertical flip if enabled
                    # Applique le retournement vertical si activé
                    if self.flip_v:
                        frame = cv2.flip(frame, 0)
                    self.frame = frame
            else:
                break

            # Adaptive timing based on actual frame rate
            # Temporisation adaptative basée sur le taux de trames réel
            elapsed = time.perf_counter() - self._last_frame_time
            sleep_time = max(0, self._target_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._last_frame_time = time.perf_counter()

        # Release the camera when done
        # Libère la caméra à la fin
        self.cap.release()

    # Stops the video stream thread gracefully
    # Arrête le thread de flux vidéo de manière appropriée
    def stop(self):
        self._run_flag = False

    # Returns the most recent captured frame
    # Retourne la trame capturée le plus récemment
    def get_frame(self):
        with self.lock:
            return self.frame

    # Switches to a different camera by index
    # Change pour une caméra différente par index
    def set_camera(self, index):
        self.stop()
        self.join()
        self.camera_index = index
        self._run_flag = True
        self.start()

    # Toggles horizontal flip of the video stream
    # Active/désactive le retournement horizontal du flux vidéo
    def flip_horizontal(self):
        with self.lock:
            self.flip_h = not self.flip_h

    # Toggles vertical flip of the video stream
    # Active/désactive le retournement vertical du flux vidéo
    def flip_vertical(self):
        with self.lock:
            self.flip_v = not self.flip_v
