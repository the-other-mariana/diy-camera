from picamera2 import Picamera2, Preview
from datetime import datetime
from gpiozero import Button
from tkinter import Button as TkButton, Tk, Label, PhotoImage
import time

class CameraSystem:
    def __init__(self):
        self.camera = None
        self.set_up()
    def set_up(self):
        self.camera = Picamera2()
        camera_config = self.camera.create_preview_configuration()
        self.camera.configure(camera_config)
        #self.camera.start_preview(Preview.QTGL)
        #self.camera.start()
    def show_menu(self):
        print("pressed button")
    def start(self):
        self.camera.start_preview(Preview.QTGL)
        self.camera.start()
        root = Tk()
        root.title("Digital Camera")
        btn = TkButton(root, text="Button", command=self.show_menu())
        btn.pack()
        try: 
            root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.camera.stop_preview()
            self.camera.close()

def main():
    s = CameraSystem()
    s.start()
if __name__ == "__main__":
    main()
