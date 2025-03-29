
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()

class ExampleModel(Base):
    __tablename__ = 'example_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    column_example1 = Column(String(50), nullable=False)
    column_example2 = Column(String(50), nullable=False)
    column_example3 = Column(String(50), nullable=True)


if __name__ == '__main__':
    from connection import Connection
    conn = Connection()
    Base.metadata.create_all(
        bind=conn.engine,
    )
