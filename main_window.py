import sys

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow, QWidget, QComboBox, QTableWidget, QPushButton
from connection import Connection
from orm_models import OrmTable
from models import Table, Column


class MainWindow(QMainWindow):

    def __init__(self, ui_file_name):
        super().__init__()
        loader: QUiLoader = QUiLoader()
        ui_file: QFile = QFile(ui_file_name)
        self.window: QWidget = loader.load(ui_file, self)
        ui_file.close()
        self.connection = Connection()
        orm_tables: list[OrmTable] = self.connection.session.query(OrmTable).filter().all()
        self.tables: list[Table] = [Table(
            name=table.name,
            columns=[Column(name=column.name, orm_model=column) for column in table.columns],
            orm_model=table)
            for table in orm_tables
        ]
        self.tables_combobox: QComboBox = self.window.tables_combobox
        self.add_file_push_button: QPushButton = self.window.add_file_pushbutton
        self.data_tables: QTableWidget = self.window.data_tables
        self.add_tables_name_to_combobox()

        self.add_file_push_button.clicked.connect(self.get_export_file)
        self.tables_combobox.currentTextChanged.connect(self.table_name_chose)


        if not self.window:
            print(loader.errorString())
            sys.exit(-1)
        self.window.show()

    def add_tables_name_to_combobox(self):
        for table in self.tables:
            self.tables_combobox.addItem(table.name)

    def table_name_chose(self, table_name: str):
        pass

    def get_export_file(self):
        pass

    def pars_export_file(self, file):
        pass
