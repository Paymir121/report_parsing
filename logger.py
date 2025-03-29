import logging
from pathlib import Path, WindowsPath

import settings as st


class Logger(logging.Logger):
    """
    Класс Logger для настройки логирования;
    """

    def __init__(self, name: str, log_file: str = None) -> None:
        """
        Инициализация экземпляра класса Logger;
        """

        super().__init__(name)

        self.log_file = log_file

        formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        if self.log_file is None:
            self.log_file: WindowsPath = (
                Path(__file__).resolve().parent.parent / "logger.log"
            )
        if st.logging_to_file:
            file_handler: logging.FileHandler = logging.FileHandler(
                self.log_file, mode="a"
            )
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)
        self.setLevel(logging.getLevelName(st.logging_level))
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)


py_logger: Logger = Logger(__name__)
