from sqlalchemy import URL, Inspector, create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from logger.logger import py_logger

from db.models import Base
from settings import DATABASES


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
        try:
            db_config = dict(DATABASES) if DATABASES else None
        except Exception:
            db_config = None
        if not db_config or not db_config.get("drivername"):
            db_config = {"drivername": "sqlite", "database": "word_templates.db"}
        self.url_object = URL.create(**db_config)

        kwargs = {"echo": True}
        if db_config.get("drivername", "").startswith("postgresql"):
            kwargs["client_encoding"] = "utf8"
        self.engine: Engine = create_engine(self.url_object, **kwargs)
        try:
            self.connection = self.engine.connect()
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            self.inspector: Inspector | None = inspect(subject=self.engine)
            self.inspector.clear_cache()
            self.connected = True
            py_logger.info(f"Подключение к базе данных прошло успешно")
        except SQLAlchemyError as err:
            py_logger.error(
                f"Не удалось подключиться к базе данных {err}, {err.__cause__}"
            )
            if self.connection:
                self.connection.invalidate()
                self.connection.close()
            self.engine.dispose()
