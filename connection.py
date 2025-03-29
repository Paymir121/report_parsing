from sqlalchemy import create_engine, Inspector, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from sqlalchemy import URL

from orm_models import Base
from settings import DATABASES
from logger import py_logger


class Connection:
    """Класс 'Connection' обеспечивает подключение к базам данных и представляет собой =СИНГЛТОН= (singleton)"""

    _instance = None
    connected: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Connection, cls).__new__(cls)
        return cls._instance


    def __init__(
        self,
    ):
        self.base: Base = Base
        if self.connected:
            return
        self.connected: bool = False
        db_config: dict = {
            "drivername": "postgresql+psycopg2",
            "username": "postgres",
            "password": "456852",
            "host": "localhost",
            "database": "test_db",
            "port": 5432,
        }
        # self.url_object: URL = URL.create(**DATABASES)
        self.url_object: URL = URL.create(**db_config)

        self.engine: Engine = create_engine(
            self.url_object,
            echo=True,
            client_encoding="utf8",
        )
        try:
            self.connection = self.engine.connect()
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            self.inspector: Inspector | None = inspect(subject=self.engine)
            self.inspector.clear_cache()
            self.connected = True
            py_logger.info(f"Подключение к базе данных прошло успешно")
        except SQLAlchemyError as err:
            py_logger.error(f"Не удалось подключиться к базе данных {err}, {err.__cause__}")
            if self.connection:
                self.connection.invalidate()
                self.connection.close()
            self.engine.dispose()

