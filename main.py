import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from db.connection import Connection
from db.models import create_all_tables
from logger import py_logger
from main_window import MainWindow
import settings as st


def run():
    loader = QUiLoader()
    app = QApplication(sys.argv)
    QCoreApplication.setApplicationName("WordTemplates")
    QCoreApplication.setOrganizationName("ReportParsing")
    st.load_from_qsettings()
    try:
        conn = Connection()
        create_all_tables(conn.engine)
    except Exception as e:
        py_logger.error(e)
    window = MainWindow(ui_file_name="ui/main_window.ui", ui_loader=loader)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    py_logger.info("Start program")
    run()
