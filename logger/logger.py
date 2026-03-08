import logging

import os
import time
import traceback

from pathlib import Path, WindowsPath
from typing import Any
import inspect
import psutil

from functools import wraps


class ColoredFormatter(logging.Formatter):
    """Кастомный форматтер с цветами для консоли"""

    # Цвета ANSI
    # TODO Доавить в настройки
    COLORS: dict[str, str] = {
        "COMPLETE": '\033[32m',
        'DEBUG': '\033[35m',
        'INFO': '\033[34m',
        'SUCCESS': '\033[36m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[31m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        # Получаем стандартное форматированное сообщение
        message = super().format(record)
        # Добавляем цвет в зависимости от уровня
        if record.levelname in self.COLORS:
            message = f"{self.COLORS[record.levelname]}{message}{self.COLORS['RESET']}"
        return message


class Logger(logging.Logger):
    """
    Класс Logger для настройки логирования;
    """

    # Добавляем новый уровень логирования SUCCESS (между WARNING и ERROR)
    SUCCESS = 31
    logging.addLevelName(SUCCESS, 'SUCCESS')

    COMPLETE = 32
    logging.addLevelName(COMPLETE, 'COMPLETE')

    def __init__(self, name: str, log_file: str = None):
        """
        Инициализация экземпляра класса Logger;
        """
        super().__init__(name)

        self.log_file = log_file

        self.setLevel(logging.DEBUG)

        # Форматтер для файла (без цветов)
        format_string: str = "%(asctime)s - %(levelname)s - %(message)s"
        file_formatter = logging.Formatter(
            format_string
        )

        if self.log_file is None:
            BASE_DIR: WindowsPath | Path = Path(__file__).resolve().parent.parent
            self.log_file: WindowsPath = BASE_DIR / "logger.log"

        self._clear_log_file()

        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        self.addHandler(file_handler)

        # Обработчик для консоли с цветами
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            "|%(levelname)-8s|%(asctime)s|: %(message)s",
        )
        # TODO Добавить в настройки
        console_handler.setLevel(logging.INFO)

        console_handler.setFormatter(console_formatter)
        self.addHandler(console_handler)
        self.are_functions_logged: bool = False
        self.debug(f"LOG.0: Создан экземпляр класса Logger. {self.are_functions_logged}")

    def _clear_log_file(self):
        """Очищает файл лога при создании экземпляра логгера"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('')  # Просто очищаем файл
            self.debug(f"LOG.INIT: Файл лога очищен при запуске приложения: {self.log_file}")
        except Exception as e:
            self.error(f"LOG.ERROR: Не удалось очистить файл лога: {e}")

    def success(self, msg: str, *args, **kwargs):
        """
        Метод для логирования сообщений с уровнем SUCCESS;
        """
        if self.isEnabledFor(self.SUCCESS):
            self._log(self.SUCCESS, msg, args, **kwargs)

    def complete(self, msg: str, *args, **kwargs):
        """
        Метод для логирования сообщений с уровнем SUCCESS;
        """
        if self.isEnabledFor(self.COMPLETE):
            self._log(self.COMPLETE, msg, args, **kwargs)

    def set_lvl_log(self, lvl_logger: str):

        level_mapping = {
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "CRITICAL": logging.CRITICAL
        }

        new_level = level_mapping.get(lvl_logger, logging.DEBUG)

        self.setLevel(new_level)

        for handler in self.handlers:
            handler.setLevel(new_level)

        # Отдельно настраиваем SQLAlchemy
        sa_log = logging.getLogger("sqlalchemy.engine")
        sa_log.setLevel(new_level)
        for ha in sa_log.handlers:
            ha.setLevel("WARNING")

        self.debug(f"LOG.1: Уровень логгера изменён на {logging.getLevelName(new_level)}")



py_logger: Logger = Logger(__name__)

def error_logger(
    # label: str = None,
    # only_this: bool = None,
):
    """
    Декоратор для логирования выполнения функции, времени выполнения и использования памяти.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:

            # if only_this is not None:
            #     if only_this is False:
            #         return

            """
            if label:
                logger.info(f"1: label = {label}")
            """


            start_time: float | None = None

            """ ====================================================>>> """

            if py_logger.are_functions_logged:
                start_time = time.time()

            try:
                result = func(*args, **kwargs)
                if py_logger.are_functions_logged:
                    func_args: tuple = func.__code__.co_varnames[:func.__code__.co_argcount]
                    class_name: str = args[0].__class__.__name__ if func_args and  func_args[0] == "self" else "None (это функция, а не метод)"
                    end_time = time.time()

                    py_logger.complete(f"LOG.3: time =  {end_time - start_time:.4f} с. | def = {func.__name__} | class = {class_name} | path = {inspect.getfile(func)}")
                else:
                    py_logger.complete(f"LOG.4: def = {func.__name__}")
                return result
            except Exception as err:
                traceback.print_exc()

                py_logger.critical(f"LOG.5: def = {func.__name__}(...) | traceback =\n{traceback.format_exc()}\n| error = {str(err)} | path = {inspect.getfile(func)}")

        return wrapper
    return decorator


@error_logger()
def example_function() -> list:
    """
    Пример функции, которая создает список из 1 000 000 элементов.
    """

    return [i for i in range(10000000)]

if __name__ == "__main__":

    py_logger.info(f"debug")
    py_logger.info(f"info")
    py_logger.warning(f"warning")
    py_logger.error(f"error")
    py_logger.critical(f"critical")
    py_logger.success(f"success")
    py_logger.complete(f"complete")
    example_function()
