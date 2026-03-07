import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_DJANGO", "key does not exist")


def _default_databases() -> dict:
    """Настройки БД по умолчанию (env / константы)."""
    if os.getenv("DRIVERNAME") == "postgresql+psycopg2":
        return {
            "drivername": os.getenv("DRIVERNAME", "postgresql+psycopg2"),
            "username": os.getenv("USERNAME", "postgres"),
            "password": os.getenv("PASSWORD", "456852"),
            "host": os.getenv("HOST", "localhost"),
            "database": os.getenv("DATABASE", "test_db"),
            "port": int(os.getenv("PORT", "5432")),
        }
    _db_name = os.getenv("DATABASE", "word_templates.db")
    if not _db_name.endswith(".db"):
        _db_name = _db_name + ".db"
    return {"drivername": "sqlite", "database": _db_name}


DATABASES: dict = _default_databases()

logging_to_file: bool = True
logging_level: str = "ERROR"

# Каталог шаблонов по умолчанию (для Word-шаблонов)
DEFAULT_TEMPLATES_DIR: str = os.getenv("TEMPLATES_DIR", "")


def load_from_qsettings():
    """
    Перечитать настройки из QSettings (вызывать после QApplication и setApplicationName/setOrganizationName).
    Обновляет DATABASES и DEFAULT_TEMPLATES_DIR.
    """
    global DATABASES, DEFAULT_TEMPLATES_DIR
    try:
        from PySide6.QtCore import QSettings
    except ImportError:
        return
    s = QSettings()
    templates_dir = s.value("Interface/TemplatesDir", "", type=str) or ""
    if templates_dir:
        DEFAULT_TEMPLATES_DIR = templates_dir
    drv = s.value("Database/Driver", "sqlite", type=str)
    if drv == "postgresql+psycopg2":
        DATABASES = {
            "drivername": "postgresql+psycopg2",
            "username": s.value("Database/PgUser", "postgres", type=str) or "postgres",
            "password": s.value("Database/PgPassword", "", type=str),
            "host": s.value("Database/PgHost", "localhost", type=str) or "localhost",
            "database": s.value("Database/PgDatabase", "test_db", type=str) or "test_db",
            "port": int(s.value("Database/PgPort", 5432, type=int)),
        }
    else:
        db_path = s.value("Database/SqlitePath", "word_templates.db", type=str) or "word_templates.db"
        if not db_path.endswith(".db"):
            db_path = db_path + ".db"
        DATABASES = {"drivername": "sqlite", "database": db_path}


class AUX:
    NOT_CHOOSED_ITEM: str = "<-не выбран->"
