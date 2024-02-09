from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QApplication, QWidget
from picamera2.previews.qt import QGlPicamera2
from picamera2 import Picamera2
from datetime import datetime
from gpiozero import Button
from DoublyLinkedList import Node, DoublyLinkedList
import RPi.GPIO as GPIO
import time
import sys

class Window1(QtWidgets.QWidget):
    def __init__(self, stacked_widget, picameraView):
        super(Window1, self).__init__()

        self.label = QtWidgets.QLabel("Welcome to Window 1")
        self.label.setAlignment(Qt.AlignCenter)

        button_layout = QtWidgets.QHBoxLayout()

        for i in range(1, 5):
            button = QtWidgets.QPushButton(f'Button {i}')
            button.clicked.connect(self.handleButton)
            button_layout.addWidget(button)

        self.go_to_window2_button = QtWidgets.QPushButton('Go To Window 2')
        self.go_to_window2_button.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(picameraView)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.go_to_window2_button)

        self.setFixedSize(640, 480)

    def handleButton(self):
        sender_button = self.sender()
        if sender_button:
            print(f'Button "{sender_button.text()}" clicked!')

class Window2(QtWidgets.QWidget):
    def __init__(self, stacked_widget):
        super(Window2, self).__init__()

        self.image_label = QtWidgets.QLabel()
        self.load_images_from_folder("out")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.image_label)
        button_layout = QtWidgets.QHBoxLayout()

        back_button = QtWidgets.QPushButton(f'<-')
        back_button.clicked.connect(self.on_back)
        button_layout.addWidget(back_button)

        upload_button = QtWidgets.QPushButton(f'Upload')
        upload_button.clicked.connect(self.on_upload)
        button_layout.addWidget(upload_button)

        next_button = QtWidgets.QPushButton(f'->')
        next_button.clicked.connect(self.on_next)
        button_layout.addWidget(next_button)

        delete_button = QtWidgets.QPushButton(f'Trash')
        delete_button.clicked.connect(self.on_delete)
        button_layout.addWidget(delete_button)

        self.button = QtWidgets.QPushButton('Camera')
        self.button.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        button_layout.addWidget(self.button)

        main_layout.addLayout(button_layout)

        self.setFixedSize(640, 480)

    def load_images_from_folder(self, folder_path):
        self.image_files = self.get_image_files(folder_path)
        if self.image_files:
            #self.show_image(self.image_files[-1])
            self.show_image(self.dll.tail.data)
            self.current_node = self.dll.tail
            print(self.current_node.data)

    def get_image_files(self, folder_path):
        image_files = []
        self.dll = DoublyLinkedList() 

        dir = QDir(folder_path)
        dir.setNameFilters(['*.jpg', '*.png', '*.jpeg'])
        for file_info in dir.entryInfoList():
            if file_info.isFile():
                image_files.append(file_info.filePath())
                self.dll.push(file_info.filePath())

        return image_files
    
    def show_image(self, image_path):
        pixmap = QtGui.QPixmap(image_path)
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)

    def show_no_image(self):
        self.image_label.setText("No Images")

    def on_back(self):
        print("back")
        if self.current_node != None and self.current_node.prev != None:
            self.current_node = self.current_node.prev
            self.show_image(self.current_node.data)

    def on_next(self):
        print("next")
        if self.current_node != None and self.current_node.next != None:
            self.current_node = self.current_node.next
            self.show_image(self.current_node.data)

    def on_upload(self):
        print("upload")

    def on_delete(self):
        node_to_delete = self.current_node
        if self.current_node.prev != None:
            self.current_node = self.current_node.prev
        else: 
            # we want to delete the first element
            if self.current_node.next != None:
                # its the only case where the user will see the next after deletion
                self.current_node = self.current_node.next
            else:
                # case: the node has no prev and no next (one picture only)
                # dll will handle refs
                self.current_node = None
                self.show_no_image()

        self.dll.delete_node(node_to_delete)
        if self.current_node != None:
            self.show_image(self.current_node.data)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, picameraView):
        super(MainWindow, self).__init__()

        self.stacked_widget = QtWidgets.QStackedWidget(self)

        self.window1 = Window1(self.stacked_widget, picameraView)
        self.window2 = Window2(self.stacked_widget)

        self.stacked_widget.addWidget(self.window1)
        self.stacked_widget.addWidget(self.window2)

        #central_widget = QtWidgets.QWidget()
        #central_widget.setLayout(layout)
        self.setCentralWidget(self.stacked_widget)
        self.resize(640, 480)

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

    def capture_file_request(self):
        timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.camera.capture_file(f"out/img_{timestamp}.jpg", signal_function=self.qpicamera2.signal_done)

    def on_capture_button(self):
        self.capture_button.setEnabled(False)
        self.capture_file_request()

    def capture_done(self, job):
        result = self.camera.wait(job)
        self.capture_button.setEnabled(True)
        
    def on_phys_button(self, channel):
        print("click")
        self.capture_file_request()

    def start(self):
        self.app = QApplication(sys.argv)
        self.qpicamera2 =QGlPicamera2(self.camera, width=800, height=600, keep_ar=False)
        self.capture_button = QPushButton("Capture")
        self.window = QWidget()
        self.qpicamera2.done_signal.connect(self.capture_done)
        self.capture_button.clicked.connect(self.on_capture_button)

        self.layout_v = QVBoxLayout()
        self.layout_v.addWidget(self.qpicamera2)
        self.layout_v.addWidget(self.capture_button)

        #self.window.setWindowTitle("Camera System")
        #self.window.resize(640, 480)
        #self.window.setLayout(self.layout_v)

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(7, GPIO.FALLING, callback=self.on_phys_button, bouncetime=300)

        self.camera.start()
        self.window = MainWindow(self.qpicamera2)
        self.window.resize(640, 480)
        self.window.show()
        sys.exit(self.app.exec())


def main():
    s = CameraSystem()
    s.start()

if __name__ == "__main__":
    main()
