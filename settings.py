import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_DJANGO", "key does not exist")

# По умолчанию — SQLite (без установки PostgreSQL)
if os.getenv("DRIVERNAME") == "postgresql+psycopg2":
    DATABASES: dict = {
        "drivername": os.getenv("DRIVERNAME", "postgresql+psycopg2"),
        "username": os.getenv("USERNAME", "postgres"),
        "password": os.getenv("PASSWORD", "456852"),
        "host": os.getenv("HOST", "localhost"),
        "database": os.getenv("DATABASE", "test_db"),
        "port": int(os.getenv("PORT", "5432")),
    }
else:
    # SQLite: файл в корне проекта или из env
    _db_name = os.getenv("DATABASE", "word_templates.db")
    if not _db_name.endswith(".db"):
        _db_name = _db_name + ".db"
    DATABASES: dict = {
        "drivername": "sqlite",
        "database": _db_name,
    }

logging_to_file: bool = True
logging_level: str = "ERROR"

# Каталог шаблонов по умолчанию (для Word-шаблонов)
DEFAULT_TEMPLATES_DIR: str = os.getenv("TEMPLATES_DIR", "")


class AUX:
    NOT_CHOOSED_ITEM: str = "<-не выбран->"
