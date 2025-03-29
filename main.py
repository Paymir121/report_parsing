from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
import sys

def run():
    loader: QUiLoader = QUiLoader()
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(ui_file_name="main_window.ui")
    sys.exit(app.exec())


if __name__ == '__main__':
    run()