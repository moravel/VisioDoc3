import threading
import cv2
import time
import platform

class VideoStreamThread(threading.Thread):
    def __init__(self, camera_index=0, width=1280, height=720):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self._run_flag = True
        self.frame = None
        self.lock = threading.Lock()
        self.flip_h = False
        self.flip_v = False

    def run(self):
        if platform.system() == "Windows":
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.cap.isOpened():
            print(f"Error: Could not open video stream for camera {self.camera_index}")
            self._run_flag = False
            return

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    if self.flip_h:
                        frame = cv2.flip(frame, 1)
                    if self.flip_v:
                        frame = cv2.flip(frame, 0)
                    self.frame = frame.copy()
            else:
                print("Error: Could not read frame.")
                break
            time.sleep(0.03)  # Approx 30 FPS
        self.cap.release()

    def stop(self):
        self._run_flag = False

    def get_frame(self):
        with self.lock:
            return self.frame

    def set_camera(self, index):
        self.stop()
        self.join() # Wait for the old thread to finish
        self.camera_index = index
        self._run_flag = True
        self.start() # Start a new thread for the new camera

    def flip_horizontal(self):
        with self.lock:
            self.flip_h = not self.flip_h

    def flip_vertical(self):
        with self.lock:
            self.flip_v = not self.flip_v
