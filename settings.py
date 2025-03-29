import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_DJANGO", "key does not exist")

if os.getenv("DRIVERNAME") == "postgresql+psycopg2":

        DATABASES: dict = {
                "drivername": os.getenv("DRIVERNAME","postgresql+psycopg2"),
                "username": os.getenv("USERNAME", "postgres"),
                "password": os.getenv("PASSWORD","456852"),
                "host": os.getenv("HOST", "localhost"),
                "database": os.getenv("DATABASE", "test_db"),
                "port": int(os.getenv("PORT", "5432")),
            }
        print(f"DATABASES {DATABASES}")
elif os.getenv("DRIVERNAME") == "sqlite":
        DATABASES: dict = {
                "drivername": os.getenv("DRIVERNAME","sqlite"),
                "database": os.getenv("DATABASE", "example.db"),
            }

class AUX:
    NOT_CHOOSED_ITEM: str = "<-не выбран->"