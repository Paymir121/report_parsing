from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
import sys
from orm_models import create_table_in_db
from file_db_example import fill_example_tables_in_db
from logger import py_logger

def run():
    loader: QUiLoader = QUiLoader()
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(ui_file_name="main_window.ui")
    sys.exit(app.exec())


if __name__ == '__main__':
    py_logger.info("Start program")
    try:
        create_table_in_db()
        # fill_example_tables_in_db()
    except Exception as e:
        py_logger.error(e)
    run()