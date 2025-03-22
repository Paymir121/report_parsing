import sys

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow, QWidget


class MainWindow(QMainWindow):

    def __init__(self, ui_file_name):
        super().__init__()
        loader: QUiLoader = QUiLoader()
        ui_file: QFile = QFile(ui_file_name)
        self.window: QWidget = loader.load(ui_file, self)
        ui_file.close()
        if not self.window:
            print(loader.errorString())
            sys.exit(-1)
        self.window.show()