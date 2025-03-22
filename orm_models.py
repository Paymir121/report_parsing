
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()


class OrmTable(Base):
    __tablename__ = 'orm_tables'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    columns = relationship('OrmColumn', back_populates='table', cascade="all, delete-orphan")

class OrmColumn(Base):
    __tablename__ = 'orm_columns'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    table_id = Column(Integer, ForeignKey('orm_tables.id'), nullable=False)
    table = relationship('OrmTable', back_populates='columns')

if __name__ == '__main__':
    from connection import Connection
    conn = Connection()

    Base.metadata.create_all(
        bind=conn.engine,
    )
