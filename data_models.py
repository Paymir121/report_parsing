from typing import Any

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeMeta

from connection import Connection
from orm_models import ORMTableModel, ORMTableColumnModel,  Base

class TableColumnModel:
    def __init__(self,
                 orm_column,
                 rus_name="Пример колонки",
                 type_column="string"
                 ):
        self.orm_column_name = orm_column.name
        self.rus_name = rus_name
        self.orm_column = orm_column
        self.type_column = type_column
        print(f"column_name={self.orm_column_name}, orm_column={orm_column}, rus_name={rus_name} type={type}")

class TableModel:
    def __init__(self, orm_table_data, rus_name="Пример модели"):
        self.connection = Connection()
        self.table_name = orm_table_data.table_name
        self.rus_name = orm_table_data.rus_name
        self.orm_table_data = orm_table_data
        self.columns: list[TableColumnModel] = []
        self.orm_table_column: list[ORMTableColumnModel] = self.connection.session.query(ORMTableColumnModel).filter_by(table_id=self.orm_table_data.id).all()
        print(f"orm_table_column={self.orm_table_column}")
        self.add_column(self.orm_table_column)
        print(f"table_name={self.table_name}, self.orm_table_data={self.orm_table_data}, rus_name={self.rus_name}")
        self.base: DeclarativeMeta = Base
        self.orm_model = self.create_model()
        self.base.metadata.create_all(self.connection.engine)

    def create_model(self):
        dynamic_class = None
        print(f"self.table_name={self.table_name}")
        attributes: dict[str: Column | dict | str] = {
            "__tablename__": self.table_name,
        }
        for column in self.columns:
            print(f"type of column={column.type_column}")
            if column.type_column == "integer":
                attributes[column.orm_column_name] = Column(Integer, nullable=True)
            elif column.type_column == "Pinteger":
                attributes[column.orm_column_name] = Column(Integer, primary_key=True, autoincrement=True)
            else:
                attributes[column.orm_column_name] = Column(String(50), nullable=True)
        table_args: list = []
        attributes['__table_args__'] = tuple(table_args) + ({'extend_existing': True},)
        print(f"attributes={attributes}")
        dynamic_class: type = type(self.table_name, (self.base,), attributes)
        print(f"dynamic_class={dynamic_class}")
        return dynamic_class

    def add_column(self, orm_columns):

        for column in orm_columns:
            self.columns.append(TableColumnModel(
                orm_column=column,
                rus_name=column.rus_name,
                type_column=column.type_column
            ))

    def get_column_by_rus_name(self, rus_name):
        for column in self.columns:
            if column.rus_name == rus_name:
                return column




if __name__ == '__main__':
    connection = Connection()
    tables = connection.session.query(ORMTableModel).all()
    print(f"tables={tables}, len(tables)={len(tables)}")
    for orm_table_data in tables:

        table = TableModel(
            orm_table_data=orm_table_data,
        )
        print(table)
        for column in table.columns:
            print(column.rus_name)