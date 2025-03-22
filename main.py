from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
import sys

def run():
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(ui_file_name="logger.ui")
    sys.exit(app.exec())


if __name__ == '__main__':
    run()