from picamera2 import Picamera2, Preview
from datetime import datetime
import time

cam = Picamera2()
camera_config = cam.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
cam.configure(camera_config)
cam.start_preview(Preview.QTGL)
cam.start()

time.sleep(2)

timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
cam.capture_file(f"out/test_{timestamp}.jpg")
