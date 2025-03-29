import sys

import pandas as pd
from pandas import DataFrame
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

import settings as st
from connection import Connection
from data_models import TableColumnModel, TableModel
from logger import py_logger
from orm_models import ORMTableColumnModel, ORMTableModel


class MainWindow(QMainWindow):

    def __init__(self, ui_file_name: str):
        super().__init__()
        loader: QUiLoader = QUiLoader()
        ui_file: QFile = QFile(ui_file_name)
        self.window: QWidget = loader.load(ui_file, self)
        ui_file.close()
        self.connection: Connection = Connection()

        if not self.window:
            py_logger.info(loader.errorString())
            sys.exit(-1)
        self.window.show()
        py_logger.info("1: MainWindow.__init__")
        self.all_tables = self.connection.session.query(ORMTableModel).all()
        self.chose_table: TableModel = TableModel(self.all_tables[0])
        self.tables_combobox: QComboBox = self.window.tables_combobox
        self.data_table: QTableWidget = self.window.data_tables
        self.export_pushbutton: QPushButton = self.window.export_pushbutton
        self.add_file_pushbutton: QPushButton = self.window.add_file_pushbutton
        self.records_table: QTableWidget = self.window.records_table

        self.tables_combobox.addItem(st.AUX.NOT_CHOOSED_ITEM)
        self.tables_combobox.addItems([table.rus_name for table in self.all_tables])

        self.export_pushbutton.clicked.connect(self.create_relationships_column)
        self.add_file_pushbutton.clicked.connect(self.open_file_dialog)
        self.tables_combobox.currentTextChanged.connect(self.change_table)

        self.chose_file: DataFrame = pd.read_excel("example.xlsx")
        self.add_export_column_name()

    def change_table(self, selected_text: str) -> None:
        py_logger.info(f"2: change_table selected_text={selected_text}")
        if selected_text == st.AUX.NOT_CHOOSED_ITEM:
            return
        for table in self.all_tables:
            if table.rus_name == selected_text:
                self.chose_table = TableModel(table)
                self.data_table.setRowCount(len(self.chose_table.columns))
                self.add_orm_column_name()
                self.fill_records_table()
                break

    def fill_records_table(self):
        py_logger.info(f"3: fill_records_table")
        self.clear_records_table()
        records = self.connection.session.query(self.chose_table.orm_model).all()
        self.records_table.setRowCount(len(records))
        self.records_table.setColumnCount(len(self.chose_table.columns))
        headers_table: list[str] = [
            column.rus_name for column in self.chose_table.columns
        ]
        self.records_table.setHorizontalHeaderLabels(headers_table)

        for row_index, record in enumerate(records):
            for column_index, column in enumerate(self.chose_table.columns):
                data: str = getattr(record, column.orm_column_name)
                item_table_widget: QTableWidgetItem = QTableWidgetItem(str(data))
                self.records_table.setItem(row_index, column_index, item_table_widget)

    def clear_records_table(self):
        py_logger.info(f"4: clear_records_table")
        self.records_table.setRowCount(0)
        self.records_table.setColumnCount(0)
        self.records_table.setHorizontalHeaderLabels([])
        self.records_table.clearContents()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "All Files (*);;Text Files (*.txt)",
            options=options,
        )
        py_logger.info(f"5: open_file_dialog file_name=", file_path)
        self.chose_file = pd.read_excel(file_path)
        self.add_export_column_name()

    def add_orm_column_name(self) -> None:
        py_logger.info(f"6: add_orm_column_name")
        columns: list[TableColumnModel] = self.chose_table.columns
        for row_index, column in enumerate(columns):
            py_logger.info(f"7: column={column}")
            orm_column_name_item: QTableWidgetItem = QTableWidgetItem(column.rus_name)
            self.data_table.setItem(row_index, 0, orm_column_name_item)
            if column.type_column == "Pinteger":
                modification_line_edit: QLineEdit = QLineEdit()
                pk_line_edit: QLineEdit = QLineEdit()
                pk_line_edit.setText("PK")
                self.data_table.setCellWidget(row_index, 1, pk_line_edit)
                self.data_table.setCellWidget(row_index, 2, modification_line_edit)
                modification_line_edit.setReadOnly(True)
                pk_line_edit.setReadOnly(True)
            else:
                modification_line_edit: QLineEdit = QLineEdit()
                combo_box: QComboBox = self.create_combo_box_with_exel_columns()
                modification_line_edit.setText("=value")
                self.data_table.setCellWidget(row_index, 1, combo_box)
                self.data_table.setCellWidget(row_index, 2, modification_line_edit)

            orm_column_name_item.setFlags(
                orm_column_name_item.flags() & ~Qt.ItemIsEditable
            )

    def create_combo_box_with_exel_columns(self) -> QComboBox:
        combo_box = QComboBox()
        combo_box.addItems(self.chose_file.iloc[0].to_dict().keys())
        combo_box.addItem(st.AUX.NOT_CHOOSED_ITEM)
        combo_box.setCurrentIndex(combo_box.findText(st.AUX.NOT_CHOOSED_ITEM))
        return combo_box

    def add_export_column_name(self) -> None:
        py_logger.info(f"7: pars_export_file")
        for row_index in range(self.data_table.rowCount()):
            combo_box = self.create_combo_box_with_exel_columns()
            self.data_table.setCellWidget(row_index, 1, combo_box)
        self.add_orm_column_name()

    def create_relationships_column(self) -> None:
        py_logger.info(f"8:export_data_to_db")
        relationships_column_name: list[dict] = []
        for i in range(self.data_table.rowCount()):
            column_name_in_orm = self.data_table.item(i, 0).text()
            if isinstance(self.data_table.cellWidget(i, 1), QLineEdit):
                continue
            column_name_in_file = self.data_table.cellWidget(i, 1).currentText()
            modification_data: str = self.data_table.cellWidget(i, 2).text()
            if column_name_in_file == st.AUX.NOT_CHOOSED_ITEM:
                py_logger.info(f"9: {column_name_in_orm}={column_name_in_file}")
                # return
            py_logger.info(f"10: {column_name_in_orm}={column_name_in_file}")
            relationship_column: dict = {
                "column_name_in_orm": column_name_in_orm,
                "column_name_in_file": column_name_in_file,
                "modification_data": modification_data,
            }
            relationships_column_name.append(relationship_column)
        py_logger.info(f"11: relationship_column_name={relationships_column_name}")
        self.export_data_to_db(relationships_column_name)

    def export_data_to_db(self, relationships_column_name: list[dict]) -> None:
        py_logger.info(f"12: export_data_to_db")
        for index, row in self.chose_file.iterrows():
            if row.isnull().all():  # Проверка, пустая ли вся строка
                break  # Выйти из цикла, если встретилась пустая строка
            data: dict = {}
            for relationship in relationships_column_name:
                column_in_orm = self.chose_table.get_column_by_rus_name(
                    relationship["column_name_in_orm"]
                ).orm_column_name

                column_in_file = relationship["column_name_in_file"]
                if column_in_file == st.AUX.NOT_CHOOSED_ITEM:
                    continue
                modification_data = relationship["modification_data"]
                value = row[column_in_file]
                # new_value = eval(f"{modification_data}")
                new_value = value
                data[column_in_orm] = new_value
            py_logger.info(f"13: data={data}")
            orm_object = self.chose_table.orm_model(**data)
            self.connection.session.add(orm_object)
            py_logger.info(f"14: orm_object={orm_object}")
        self.connection.session.commit()
        self.fill_records_table()
