
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()

class ORMTableModel(Base):
    __tablename__ = 'tables'
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False)
    rus_name = Column(String(50), nullable=False)
    columns = relationship("ORMTableColumnModel", back_populates="table")

class ORMTableColumnModel(Base):
    __tablename__ = 'table_columns'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    rus_name = Column(String(50), nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"))
    table = relationship("ORMTableModel", back_populates="columns")
    type_column = Column(String(50), default="string")

if __name__ == '__main__':
    from connection import Connection
    conn = Connection()
    Base.metadata.create_all(
        bind=conn.engine,
    )
