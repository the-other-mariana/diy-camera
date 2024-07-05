from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QDir, QTimer, QThread, QMetaObject, pyqtSlot
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QApplication, QWidget
from picamera2.previews.qt import QGlPicamera2
from picamera2 import Picamera2
from datetime import datetime, timedelta
from gpiozero import Button
from DoublyLinkedList import Node, DoublyLinkedList
import RPi.GPIO as GPIO
import time
import sys
import os
import PyQt5.QtCore

OUT_PATH = "/home/pi/Documents/github/diy-camera/out"

WINDOW_WIDTH = 480
WINDOW_HEIGHT = 320

CAMERA_STILL_WIDTH = 1920
CAMERA_STILL_HEIGHT = 1280

# UI
WINDOW1_BUTTON_HEIGHT = 30

# pin number is pin number, not gpio
CAPTURE_BUTTON_GPIO_PIN = 36
# move left right up down button pins
BUTTON_PINS = [12, 16, 18, 32]

MAIN_STYLE = "background-color: black; color: white;"
FOCUSED_BUTTON_STYLE = """
                            QPushButton:focus {
                                color: white;
                                background-color: black;
                                border: 3px solid white;
                                font-weight: bold;
                            }
                        """
log_file = open("/home/pi/main.log", 'a')
class Window1(QtWidgets.QWidget):
    def set_up_camera(self):
        self.camera = Picamera2()
        self.camera_config = self.camera.create_still_configuration(main={"size": (CAMERA_STILL_WIDTH, CAMERA_STILL_HEIGHT)}, lores={"size": (CAMERA_STILL_WIDTH, CAMERA_STILL_HEIGHT)}, display="lores")
        #self.camera_config = self.camera.create_preview_configuration()
        self.camera.configure(self.camera_config)

    def capture_file_request(self):
        #timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        utc_now = datetime.utcnow()
        offset_hours = -6
        my_datetime = utc_now + timedelta(hours=offset_hours)
        timestamp = my_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{OUT_PATH}/img_{timestamp}.jpg"
        self.camera.capture_file(filename, signal_function=self.qpicamera2.signal_done)
        self.main_window.dll.push(filename)

        self.picture_taken_widget.setVisible(True)
        QMetaObject.invokeMethod(self,"start_timer", Qt.QueuedConnection)

    @pyqtSlot()     
    def start_timer(self):
        self.timer=QTimer()
        self.timer.timeout.connect(self.hide_picture_taken_widget)
        self.timer.start(300)

    def hide_picture_taken_widget(self):
        self.picture_taken_widget.setVisible(False)

    def on_capture_button(self):
        self.capture_button.setEnabled(False)
        self.capture_file_request()

    def capture_done(self, job):
        result = self.camera.wait(job)
        self.capture_button.setEnabled(True)
        
    def on_phys_button(self, channel):
        print("click")
        self.capture_file_request()

    def set_up_attributes(self):
        self.qpicamera2 =QGlPicamera2(self.camera, width=640, height=480, keep_ar=False)
        self.capture_button = QPushButton("Capture")
        self.qpicamera2.done_signal.connect(self.capture_done)
        self.capture_button.clicked.connect(self.on_capture_button)
        self.capture_button.setStyleSheet(FOCUSED_BUTTON_STYLE)

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(CAPTURE_BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(CAPTURE_BUTTON_GPIO_PIN, GPIO.FALLING, callback=self.on_phys_button, bouncetime=300)

        self.camera.start()

    def move_focus_callback_window1(self, pin):
        button_index = BUTTON_PINS.index(pin)

        if button_index == 0:
            # left button is clicked
            if self.current_button > 0:
                self.current_button -= 1
        if button_index == 1:
            # right button is clicked
            if self.current_button < len(self.move_focus_button_list) - 1:
                self.current_button += 1
        if button_index == 2:
            # ok button is clicked
            focused_button = QApplication.focusWidget()
            focused_button.click()
        self.move_focus_button_list[self.current_button].setFocus()

    def __init__(self, stacked_widget, main_window):
        super(Window1, self).__init__()

        self.main_window = main_window
        self.set_up_camera()
        self.set_up_attributes()

        self.go_to_window2_button = QtWidgets.QPushButton('Camera Roll')
        self.go_to_window2_button.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))
        self.go_to_window2_button.setStyleSheet(FOCUSED_BUTTON_STYLE)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.go_to_window2_button)

        self.move_focus_button_list = []
        self.current_button = 0
        self.move_focus_button_list.append(self.capture_button)
        self.move_focus_button_list.append(self.go_to_window2_button)
        self.move_focus_button_list[self.current_button].setFocus()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.qpicamera2)
        main_layout.addLayout(button_layout)

        self.picture_taken_widget = QtWidgets.QLabel(self.qpicamera2)
        self.picture_taken_widget.setGeometry(self.rect())
        self.picture_taken_widget.setStyleSheet("background-color: rgba(0, 0, 0, 255);")
        self.picture_taken_widget.setVisible(False)


        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

    def handleButton(self):
        sender_button = self.sender()
        if sender_button:
            print(f'Button "{sender_button.text()}" clicked!')

class Window2(QtWidgets.QWidget):
    def __init__(self, stacked_widget, main_window):
        super(Window2, self).__init__()
       
        self.current_button = 0
        self.move_focus_button_list = []

        self.main_window = main_window
        self.image_label = QtWidgets.QLabel()
        self.load_images_from_folder(OUT_PATH)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.image_label)
        button_layout = QtWidgets.QHBoxLayout()

        back_button = QtWidgets.QPushButton(f'<-')
        back_button.clicked.connect(self.on_back)
        button_layout.addWidget(back_button)
        self.move_focus_button_list.append(back_button)

        upload_button = QtWidgets.QPushButton(f'Upload')
        upload_button.clicked.connect(self.on_upload)
        button_layout.addWidget(upload_button)
        self.move_focus_button_list.append(upload_button)

        next_button = QtWidgets.QPushButton(f'->')
        next_button.clicked.connect(self.on_next)
        button_layout.addWidget(next_button)
        self.move_focus_button_list.append(next_button)

        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.clicked.connect(self.on_delete)
        button_layout.addWidget(delete_button)
        self.move_focus_button_list.append(delete_button)

        self.button = QtWidgets.QPushButton('Camera')
        self.button.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        button_layout.addWidget(self.button)
        self.move_focus_button_list.append(self.button)

        stacked_widget.currentChanged.connect(self.handle_active_window)

        main_layout.addLayout(button_layout)

        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        for button in self.move_focus_button_list:
            button.setStyleSheet(FOCUSED_BUTTON_STYLE)
        self.move_focus_button_list[self.current_button].setFocus()
        
        print(f'main window {main_window.dll.size}')

    def move_focus_callback_window2(self, pin):
        button_index = BUTTON_PINS.index(pin)

        if button_index == 0:
            # left button is clicked
            if self.current_button > 0:
                self.current_button -= 1
        if button_index == 1:
            # right button is clicked
            if self.current_button < len(self.move_focus_button_list) - 1:
                self.current_button += 1
        if button_index == 2:
            # ok button is clicked
            focused_button = QApplication.focusWidget()
            focused_button.click()
        self.move_focus_button_list[self.current_button].setFocus()


    def handle_active_window(self, index):
        self.main_window.current_window = index
        print(f'window: {self.main_window.current_window}')
        if index == 1:
            if self.main_window.dll != None:
                image_files = self.get_image_files_only(OUT_PATH)
                if self.main_window.dll.size < len(image_files):
                    for new_file in image_files[self.main_window.dll.size:]:
                        self.main_window.dll.push(new_file)
                self.current_node = self.main_window.dll.tail
                self.show_image(self.current_node.data)

    def load_images_from_folder(self, folder_path):
        self.image_files = self.get_image_files_and_dll(folder_path)
        if self.image_files:
            self.show_image(self.main_window.dll.tail.data)
            self.current_node = self.main_window.dll.tail
            print(self.current_node.data)

    def get_image_files_only(self, folder_path):
        dir = QDir(folder_path)
        dir.setNameFilters(['*.jpg', '*.png', '*.jpeg'])
        image_files = [f.filePath() for f in dir.entryInfoList() if f.isFile()]
        return image_files

    def get_image_files_and_dll(self, folder_path):
        image_files = []
        #self.dll = DoublyLinkedList() 

        dir = QDir(folder_path)
        dir.setNameFilters(['*.jpg', '*.png', '*.jpeg'])
        for file_info in dir.entryInfoList():
            if file_info.isFile():
                image_files.append(file_info.filePath())
                self.main_window.dll.push(file_info.filePath())
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

        self.main_window.dll.delete_node(node_to_delete)
        if self.current_node != None:
            self.show_image(self.current_node.data)
        try:
            os.remove(node_to_delete.data)
        except FileNotFoundError:
            print(f"[ERROR] File {node_to_delete.data} not found. Couldn't delete.")
        except Exception as e:
            print(f"[ERROR] Couldnt't delete file {node_to_delete.data}: {e}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.stacked_widget = QtWidgets.QStackedWidget(self)
        self.setStyleSheet(MAIN_STYLE)
        self.dll = DoublyLinkedList()
        self.current_window = 0

        self.window1 = Window1(self.stacked_widget, self)
        self.window2 = Window2(self.stacked_widget, self)

        GPIO.setmode(GPIO.BOARD)

        for pin in BUTTON_PINS:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.move_focus_callback, bouncetime=300)


        self.stacked_widget.addWidget(self.window1)
        self.stacked_widget.addWidget(self.window2)

        #central_widget = QtWidgets.QWidget()
        #central_widget.setLayout(layout)
        self.setCentralWidget(self.stacked_widget)
        #self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        

    def move_focus_callback(self, pin):
        if self.current_window == 0:
            self.window1.move_focus_callback_window1(pin)
        if self.current_window == 1:
            self.window2.move_focus_callback_window2(pin)

class CameraSystem:
    def __init__(self):
        self.window = None

    def start(self): 
        print(os.environ, file=log_file)
        print(os.getcwd(), file=log_file)
        log_file.flush()
        self.app = QApplication([])
        self.window = QWidget()

        self.window = MainWindow()
        self.window.show()
        sys.exit(self.app.exec())
        log_file.close()
        sys.stdout.flush()
        sys.stderr.flush()

def main():
    s = CameraSystem()
    s.start()

if __name__ == "__main__":
    main()
