from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QApplication, QWidget
from picamera2.previews.qt import QGlPicamera2
from picamera2 import Picamera2
from datetime import datetime
from gpiozero import Button
import time

class CameraSystem:
    def __init__(self):
        self.camera = None
        self.camera_config = None
        self.qpicamera2 = None
        self.app = None
        self.capture_button = None
        self.window = None
        self.layout_v = None
        self.set_up()
    def set_up(self):
        self.camera = Picamera2()
        self.camera_config = self.camera.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
        #self.camera_config = self.camera.create_preview_configuration()
        self.camera.configure(self.camera_config)
    def on_capture_button(self):
        self.capture_button.setEnabled(False)
        cfg = self.camera.create_still_configuration()
        timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.camera.capture_file(f"out/img_{timestamp}.jpg", signal_function=self.qpicamera2.signal_done)
        #self.camera.switch_mode_and_capture_file(cfg, f"out/test_{timestamp}.jpg", signal_function=self.qpicamera2.signal_done)
    def capture_done(self, job):
        result = self.camera.wait(job)
        self.capture_button.setEnabled(True)
        
    def start(self):
        self.app = QApplication([])
        self.qpicamera2 =QGlPicamera2(self.camera, width=800, height=600, keep_ar=False)
        self.capture_button = QPushButton("Capture")
        self.window = QWidget()
        self.qpicamera2.done_signal.connect(self.capture_done)
        self.capture_button.clicked.connect(self.on_capture_button)

        self.layout_v = QVBoxLayout()
        self.layout_v.addWidget(self.qpicamera2)
        self.layout_v.addWidget(self.capture_button)

        self.window.setWindowTitle("Camera System")
        self.window.resize(640, 480)
        self.window.setLayout(self.layout_v)

        self.camera.start()
        self.window.show()
        self.app.exec()
def main():
    s = CameraSystem()
    s.start()
if __name__ == "__main__":
    main()
