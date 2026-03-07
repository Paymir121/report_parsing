import sys

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from db.connection import Connection
from db.models import create_all_tables
from logger import py_logger
from main_window import MainWindow


def run():
    # QUiLoader создаётся до QApplication (рекомендуется на Windows)
    loader = QUiLoader()
    app = QApplication(sys.argv)
    window = MainWindow(ui_file_name="ui/main_window.ui", ui_loader=loader)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    py_logger.info("Start program")
    try:
        conn = Connection()
        create_all_tables(conn.engine)
    except Exception as e:
        py_logger.error(e)
    run()
