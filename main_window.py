import sys


from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow, QWidget, QTableWidgetItem, QFileDialog, QTableWidget, QPushButton, QComboBox, \
    QLineEdit
from connection import Connection
import pandas as pd
from orm_models import ExampleModel
import settings as st


class MainWindow(QMainWindow):

    def __init__(self, ui_file_name):
        super().__init__()
        loader: QUiLoader = QUiLoader()
        ui_file: QFile = QFile(ui_file_name)
        self.window: QWidget = loader.load(ui_file, self)
        ui_file.close()
        self.connection: Connection = Connection()

        if not self.window:
            print(loader.errorString())
            sys.exit(-1)
        self.window.show()
        print("MainWindow.__init__")
        self.data_table: QTableWidget = self.window.data_tables
        self.export_pushbutton: QPushButton = self.window.export_pushbutton
        self.add_file_pushbutton: QPushButton = self.window.add_file_pushbutton

        self.export_pushbutton.clicked.connect(self.create_relationships_column)
        self.add_file_pushbutton.clicked.connect(self.open_file_dialog)

        self.data_table.setRowCount(3)
        self.chose_file = None
        self.chose_file = pd.read_excel("example.xlsx")
        self.add_export_column_name()
        self.add_orm_column_name()



    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt)", options=options)
        print(f"open_file_dialog file_name=", file_path)
        self.chose_file = pd.read_excel(file_path)
        self.add_export_column_name()



    def add_orm_column_name(self):
        print(f"1: add_orm_column_name")
        columns = ExampleModel.__table__.columns
        for row_index, column in enumerate(columns[1:4]):
            print(f"2: column={column}")
            self.data_table.setItem(row_index, 0, QTableWidgetItem(column.name))
            line_edit: QLineEdit = QLineEdit()
            self.data_table.setCellWidget(row_index, 2, line_edit)
            line_edit.setText("=value")

    def add_export_column_name(self):
        print(f"3: pars_export_file")
        for row_index in range(self.data_table.rowCount()):
            combo_box = QComboBox()
            combo_box.addItems(self.chose_file.iloc[0].to_dict().keys())
            combo_box.addItem(st.AUX.NOT_CHOOSED_ITEM)
            combo_box.setCurrentIndex(combo_box.findText(st.AUX.NOT_CHOOSED_ITEM))
            self.data_table.setCellWidget(row_index, 1, combo_box)

    def create_relationships_column(self):
        print(f"5:export_data_to_db")
        relationships_column_name: list[dict] = []
        for i in range(self.data_table.rowCount()):
            column_name_in_orm = self.data_table.item(i, 0).text()
            column_name_in_file = self.data_table.cellWidget(i, 1).currentText()
            modification_data: str = self.data_table.cellWidget(i, 2).text()
            if column_name_in_file == st.AUX.NOT_CHOOSED_ITEM:
                print(f"6: {column_name_in_orm}={column_name_in_file}")
                # return
            print(f"6: {column_name_in_orm}={column_name_in_file}")
            relationship_column: dict = {
                "column_name_in_orm": column_name_in_orm,
                "column_name_in_file": column_name_in_file,
                "modification_data": modification_data
            }
            relationships_column_name.append( relationship_column )
        print(f"7: relationship_column_name={relationships_column_name}")
        self.export_data_to_db(relationships_column_name)

    def export_data_to_db(self, relationships_column_name: list[dict]):
        print(f"8: export_data_to_db")
        for index, row in self.chose_file.iterrows():
            if row.isnull().all():  # Проверка, пустая ли вся строка
                break  # Выйти из цикла, если встретилась пустая строка
            data: dict = {}
            for relationship in relationships_column_name:
                column_in_orm = relationship["column_name_in_orm"]
                column_in_file = relationship["column_name_in_file"]
                if column_in_file == st.AUX.NOT_CHOOSED_ITEM:
                    continue
                modification_data = relationship["modification_data"]
                value = row[column_in_file]
                # new_value = eval(f"{modification_data}")
                new_value = value
                data[column_in_orm] = new_value
            print(f"9: data={data}")
            orm_object: ExampleModel = ExampleModel(**data)
            self.connection.session.add(orm_object)
        # self.connection.session.commit()
