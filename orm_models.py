
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()

class ORMExampleModel(Base):
    __tablename__ = 'example_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    column_example1 = Column(String(50), nullable=False)
    column_example2 = Column(String(50), nullable=False)
    column_example3 = Column(String(50), nullable=True)

class TableModel:
    def __init__(self, orm_model, rus_name="Пример модели"):
        self.table_name = orm_model.__tablename__
        self.rus_name = rus_name
        self.orm_model = orm_model
        self.columns: list[TableColumnModel] = []
        self.add_column(orm_model.__table__.columns)
        print(f"table_name={self.table_name}, orm_model={self.orm_model}, rus_name={self.rus_name}")

    def add_column(self, orm_columns):
        for column in orm_columns:
            self.columns.append(TableColumnModel(orm_column=column))

    def get_column_by_rus_name(self, rus_name):
        for column in self.columns:
            if column.rus_name == rus_name:
                return column


class TableColumnModel:
    def __init__(self, orm_column, rus_name="Пример колонки"):
        self.orm_column_name = orm_column.name
        self.rus_name = rus_name
        self.orm_column = orm_column
        print(f"column_name={self.orm_column_name}, orm_column={orm_column}, rus_name={rus_name}")

if __name__ == '__main__':
    # from connection import Connection
    # conn = Connection()
    # Base.metadata.create_all(
    #     bind=conn.engine,
    # )
    table = TableModel(ORMExampleModel)
    print(table)
