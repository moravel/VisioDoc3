import threading
import cv2
import time
import platform

# Thread for handling video stream capture from a webcam.
# Fil pour la gestion de la capture de flux vidéo à partir d'une webcam.
class VideoStreamThread(threading.Thread):
    def __init__(self, camera_index=0, width=1280, height=720):
        """
        Initializes the VideoStreamThread.
        Initialise le VideoStreamThread.

        Args:
            camera_index (int): Index of the camera to open (e.g., 0 for default).
                                Indice de la caméra à ouvrir (par exemple, 0 pour la valeur par défaut).
            width (int): Desired frame width.
                         Largeur de cadre souhaitée.
            height (int): Desired frame height.
                          Hauteur de cadre souhaitée.
        """
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None  # OpenCV VideoCapture object / Objet VideoCapture d'OpenCV
        self._run_flag = True  # Flag to control the thread's main loop / Drapeau pour contrôler la boucle principale du fil
        self.frame = None  # Stores the latest captured frame / Stocke le dernier cadre capturé
        self.lock = threading.Lock()  # Lock for thread-safe access to self.frame / Verrou pour un accès thread-safe à self.frame
        self.flip_h = False  # Flag for horizontal flip / Drapeau pour le retournement horizontal
        self.flip_v = False  # Flag for vertical flip / Drapeau pour le retournement vertical

    def run(self):
        """
        The main method executed when the thread starts.
        It continuously captures frames from the camera.
        La méthode principale exécutée lorsque le fil démarre.
        Elle capture continuellement des cadres de la caméra.
        """
        # Use CAP_DSHOW on Windows for better camera compatibility
        # Utilise CAP_DSHOW sous Windows pour une meilleure compatibilité de la caméra
        if platform.system() == "Windows":
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
        
        # Set desired frame resolution
        # Définit la résolution de cadre souhaitée
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Check if camera opened successfully
        # Vérifie si la caméra s'est ouverte avec succès
        if not self.cap.isOpened():
            print(f"Error: Could not open video stream for camera {self.camera_index}")
            self._run_flag = False # Stop the thread if camera cannot be opened / Arrête le fil si la caméra ne peut pas être ouverte
            return

        # Main loop for capturing frames
        # Boucle principale pour la capture de cadres
        while self._run_flag:
            ret, frame = self.cap.read() # Read a frame from the camera / Lit un cadre de la caméra
            if ret: # If frame was read successfully / Si le cadre a été lu avec succès
                with self.lock: # Acquire lock before accessing shared resources / Acquiert le verrou avant d'accéder aux ressources partagées
                    # Apply horizontal and/or vertical flip if enabled
                    # Applique le retournement horizontal et/ou vertical si activé
                    if self.flip_h:
                        frame = cv2.flip(frame, 1)
                    if self.flip_v:
                        frame = cv2.flip(frame, 0)
                    self.frame = frame.copy() # Store a copy of the frame / Stocke une copie du cadre
            else:
                print("Error: Could not read frame.")
                break # Exit loop on error / Quitte la boucle en cas d'erreur
            time.sleep(0.03)  # Introduce a small delay to control frame rate (approx 30 FPS)
                              # Introduit un petit délai pour contrôler la fréquence d'images (environ 30 FPS)
        self.cap.release() # Release the camera resource when the thread stops / Libère la ressource de la caméra lorsque le fil s'arrête

    def stop(self):
        """
        Sets the internal flag to stop the video stream thread.
        Définit le drapeau interne pour arrêter le fil du flux vidéo.
        """
        self._run_flag = False

    def get_frame(self):
        """
        Returns the latest captured frame in a thread-safe manner.
        Retourne le dernier cadre capturé de manière thread-safe.

        Returns:
            numpy.ndarray: The latest video frame, or None if no frame is available.
                           Le dernier cadre vidéo, ou Aucun si aucun cadre n'est disponible.
        """
        with self.lock:
            return self.frame

    def set_camera(self, index):
        """
        Stops the current video stream and starts a new one with the specified camera index.
        Arrête le flux vidéo actuel et en démarre un nouveau avec l'indice de caméra spécifié.

        Args:
            index (int): The index of the new camera to use.
                         L'indice de la nouvelle caméra à utiliser.
        """
        self.stop() # Stop the current thread / Arrête le fil actuel
        self.join() # Wait for the old thread to finish its execution / Attend que l'ancien fil termine son exécution
        self.camera_index = index # Update camera index / Met à jour l'indice de la caméra
        self._run_flag = True # Reset run flag for the new thread / Réinitialise le drapeau d'exécution pour le nouveau fil
        self.start() # Start a new thread for the new camera / Démarre un nouveau fil pour la nouvelle caméra

    def flip_horizontal(self):
        """
        Toggles horizontal flipping of the video stream.
        Bascule le retournement horizontal du flux vidéo.
        """
        with self.lock:
            self.flip_h = not self.flip_h

    def flip_vertical(self):
        """
        Toggles vertical flipping of the video stream.
        Bascule le retournement vertical du flux vidéo.
        """
        with self.lock:
            self.flip_v = not self.flip_v