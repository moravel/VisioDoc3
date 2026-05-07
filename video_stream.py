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
        
        # Performance optimization
        self._target_interval = 0.033  # ~30 FPS target
        self._last_frame_time = 0

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

        self._last_frame_time = time.perf_counter()
        
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    if self.flip_h:
                        frame = cv2.flip(frame, 1)
                    if self.flip_v:
                        frame = cv2.flip(frame, 0)
                    # Don't copy the frame - just use it directly
                    self.frame = frame
            else:
                break
            
            # Adaptive timing based on actual frame rate
            elapsed = time.perf_counter() - self._last_frame_time
            sleep_time = max(0, self._target_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._last_frame_time = time.perf_counter()
        
        self.cap.release()

    def stop(self):
        self._run_flag = False

    def get_frame(self):
        with self.lock:
            return self.frame

    def set_camera(self, index):
        self.stop()
        self.join()
        self.camera_index = index
        self._run_flag = True
        self.start()

    def flip_horizontal(self):
        with self.lock:
            self.flip_h = not self.flip_h

    def flip_vertical(self):
        with self.lock:
            self.flip_v = not self.flip_v
