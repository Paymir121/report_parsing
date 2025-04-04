from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from logger import py_logger

Base = declarative_base()


class ORMTableModel(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False, unique=True)
    rus_name = Column(String(50), nullable=False)
    columns = relationship("ORMTableColumnModel", back_populates="table")


class ORMTableColumnModel(Base):
    __tablename__ = "table_columns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    rus_name = Column(String(50), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"))
    table = relationship("ORMTableModel", back_populates="columns")
    type_column = Column(String(50), default="string")


def create_table_in_db():
    from connection import Connection

    conn = Connection()
    Base.metadata.create_all(
        bind=conn.engine,
    )


if __name__ == "__main__":
    create_table_in_db()
