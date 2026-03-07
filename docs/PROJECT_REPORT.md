# Подробный отчёт по проекту report_parsing

*Отчёт обновлён под текущую структуру репозитория (пакеты db/, ui/, logger/).*

## 1. Обзор проекта

**report_parsing** — десктопное приложение на Python для импорта данных из Excel-отчётов в базу данных PostgreSQL. Пользователь выбирает целевую таблицу, загружает Excel-файл, сопоставляет колонки файла с колонками таблицы в БД и выполняет экспорт записей.

| Параметр | Значение |
|----------|----------|
| Язык | Python 3.9 |
| Интерфейс | PySide6 (Qt) |
| БД | PostgreSQL 13.10 |
| ORM | SQLAlchemy 2.x |
| Автор | [Nikki Nikonor](https://github.com/Paymir121) |

---

## 2. Структура проекта (актуальная)

```
report_parsing/
├── main.py                 # Точка входа приложения
├── main_window.py          # Логика главного окна (маппинг, экспорт)
├── settings.py             # Конфигурация (dotenv, логирование)
├── requirements.txt       # Зависимости
├── README.md               # Инструкция по запуску
├── PROJECT_REPORT.md       # Этот отчёт
├── db/                     # Пакет работы с БД
│   ├── __init__.py
│   ├── connection.py       # Подключение к PostgreSQL (singleton)
│   ├── data_models.py      # Динамические модели таблиц из метаданных
│   └── orm_models.py       # Мета-таблицы tables, table_columns (см. разд. 7)
├── ui/                     # Ресурсы интерфейса
│   ├── __init__.py
│   └── main_window.ui      # Описание UI (Qt Designer)
└── logger/                 # Пакет логирования
    ├── __init__.py
    ├── logger.py           # Logger, ColoredFormatter, py_logger, уровни SUCCESS/COMPLETE
    └── logger_view.py      # Окно просмотра логов
```

---

## 3. Зависимости (requirements.txt)

| Пакет | Назначение |
|-------|------------|
| pg8000, psycopg2 | Драйверы PostgreSQL (pg8000 — кроссплатформенно, psycopg2 — для Windows) |
| PySide6, PySide6_Addons, PySide6_Essentials, shiboken6 | GUI на Qt 6 |
| SQLAlchemy, sqlalchemy-json | ORM и работа с БД |
| pandas, openpyxl | Чтение Excel |
| python-dotenv | Переменные окружения |
| python-dateutil, scramp | Вспомогательные зависимости PySide6 |
| black, isort | Форматирование и сортировка импортов |

---

## 4. Архитектура и модули

### 4.1. Точка входа — `main.py`

- Импортирует `create_table_in_db` из `db.orm_models`, `MainWindow` из `main_window`, UI из `ui/main_window.ui`.
- Создаёт мета-таблицы в БД: `create_table_in_db()`.
- Опционально: раскомментировать `fill_example_tables_in_db()` (импорт из `file_db_example`) для первичного заполнения из `example.json`.
- Запускает Qt-приложение и загружает `MainWindow(ui_file_name="ui/main_window.ui")`.

**Важно:** без предварительного заполнения мета-таблиц (скрипт заполнения или вызов `fill_example_tables_in_db()`) в БД не будет описаний целевых таблиц.

### 4.2. Подключение к БД — `db/connection.py`

- Класс **Connection** реализован как **singleton**.
- Импортирует `Base` из `orm_models` (внутри пакета `db`), использует `settings.DATABASES` в коде, но фактически подключение строится из захардкоженного `db_config`.
- Параметры подключения заданы в коде (postgresql+psycopg2, localhost, test_db и т.д.); использование `settings.DATABASES` закомментировано.

### 4.3. Метаданные таблиц — `db/orm_models.py`

- **ORMTableModel** — таблица `tables`: `id`, `table_name`, `rus_name`; связь с колонками.
- **ORMTableColumnModel** — таблица `table_columns`: `id`, `name`, `rus_name`, `table_id`, `type_column` (например, `Pinteger`, `integer`, `string`).
- `create_table_in_db()` создаёт в БД эти две мета-таблицы.
- Импортируется как `db.orm_models` из корня и как `orm_models` внутри пакета `db`.

### 4.4. Динамические модели — `db/data_models.py`

- **TableColumnModel** — обёртка над колонкой: `orm_column_name`, `rus_name`, `type_column`.
- **TableModel** — по записи из `tables` и связанным `table_columns` строит **динамическую** SQLAlchemy-модель и создаёт соответствующую таблицу в БД.
- Поддерживаемые типы колонок: `Pinteger` (PK, autoincrement), `integer`, по умолчанию — `String(50)`.
- Импортирует `Connection`, `Base`, `ORMTableColumnModel`, `ORMTableModel` из пакета `db` (относительно: `connection`, `orm_models`).

### 4.5. Заполнение метаданных — `file_db_example.py`

- В текущей структуре файл в корне не обнаружен; в `main.py` по-прежнему есть импорт `fill_example_tables_in_db` из `file_db_example`.
- По смыслу: читает `example.json`, заполняет `tables` и `table_columns`. Запуск один раз до использования приложения (или вызов из `main.py`).

### 4.6. Конфигурация — `settings.py`

- Загружает переменные из `.env`.
- Определяет `DATABASES` в зависимости от `DRIVERNAME` (postgresql+psycopg2 или sqlite).
- Настройки логирования: `logging_to_file`, `logging_level`.
- Класс **AUX**: константа `NOT_CHOOSED_ITEM` для UI («<-не выбран->»).

### 4.7. Логирование — пакет `logger/`

- **logger/logger.py** — кастомный **Logger**: цветной вывод в консоль (ColoredFormatter), запись в файл `logger.log`, уровни SUCCESS и COMPLETE, опция `are_functions_logged`, декоратор для замера времени и памяти; экспортирует `py_logger`. Использует `logger.memory_info` (модуль `Memory`).
- **logger/logger_view.py** — окно просмотра логов (PySide6), использует `logger.logger.py_logger`.
- В корневых модулях импорт: `from logger import py_logger` — для работы пакета в `logger/__init__.py` должен быть реэкспорт `py_logger` из `logger.logger`.

### 4.8. Главное окно — `main_window.py`

- Загружает UI из переданного файла (при запуске — `ui/main_window.ui`) через **QUiLoader**.
- Использует `db.connection.Connection`, `db.data_models`, `db.orm_models.ORMTableModel`.
- **Элементы:** выпадающий список таблиц (`tables_combobox`), кнопка выбора файла (`add_file_pushbutton`), таблица маппинга колонок БД ↔ Excel (`data_tables`), таблица записей из БД (`records_table`), кнопка экспорта (`export_pushbutton`).
- При старте по умолчанию загружается **example.xlsx** из текущей директории. При отсутствии файла запуск приведёт к ошибке.
- Пользователь может выбрать таблицу, загрузить другой Excel-файл, сопоставить колонки и нажать «Добавить запис в БД» (опечатка в UI: «запис»).
- Экспорт: по выбранным соответствиям данные из DataFrame вставляются в выбранную таблицу через динамическую ORM-модель, затем вызывается `fill_records_table()`.

---

## 5. Формат example.json

- Файл может храниться в корне проекта (при использовании скрипта заполнения мета-таблиц).
- Корневой ключ **tables** — массив таблиц.
- Каждая таблица: **table_name**, **rus_name**, **columns**.
- Колонка: **name**, **rus_name**, **type** (`Pinteger` | `integer` | `string` и т.д.).

Типичные примеры таблиц: **users**, **posts**, **videocards** с колонками и русскими подписями.

---

## 6. Сценарий работы

1. Убедиться, что PostgreSQL запущен, создана БД `test_db`; при необходимости скорректировать параметры в `db/connection.py` или использовать `settings.DATABASES`.
2. Создать виртуальное окружение, установить зависимости: `pip install -r requirements.txt`.
3. Убедиться, что в БД есть мета-таблицы и их описание (при наличии скрипта заполнения — один раз запустить его или вызвать `fill_example_tables_in_db()` из `main.py`).
4. Положить в корень проекта файл **example.xlsx** (или изменить в `main_window.py` путь по умолчанию).
5. Запустить приложение из корня: `python main.py`.
6. В приложении: выбрать таблицу, при необходимости загрузить другой Excel-файл, сопоставить колонки и выполнить экспорт.

---

## 7. Замечания и рекомендации

### Текущее состояние репозитория

| Что проверено | Статус |
|---------------|--------|
| Файл `db/orm_models.py` | В репозитории может отсутствовать; без него импорты `db.orm_models` и `from orm_models import ...` внутри `db/` не сработают. |
| Файл `file_db_example.py` | В корне не найден; в `main.py` есть импорт `fill_example_tables_in_db` из него. |
| Файл `example.json` | В корне не найден; нужен для скрипта заполнения мета-таблиц. |
| Пакет `logger` | Импорт `from logger import py_logger` требует реэкспорта в `logger/__init__.py` (например, `from logger.logger import py_logger`). |
| Модуль `logger.memory_info` | Импортируется в `logger/logger.py`; при отсутствии файла `logger/memory_info.py` запуск логгера приведёт к ошибке. |

### Рекомендации по коду и конфигурации

| Проблема | Где | Рекомендация |
|----------|-----|--------------|
| Параметры БД захардкожены | `db/connection.py` | Использовать `settings.DATABASES` и `.env` для хоста, пароля, имени БД. |
| При старте требуется example.xlsx | `main_window.py` | Не загружать файл по умолчанию или проверять существование и показывать пустую таблицу маппинга. |
| Опечатка в README | README.md | «examlpe.json» → «example.json». |
| Опечатка в UI | ui/main_window.ui | «Добавить запис в БД» → «Добавить запись в БД». |
| Логирование с py_logger.info в циклах | `main_window.py`, `db/data_models.py` | При большом числе строк/колонок снизить уровень детализации или вынести в debug. |
| Модификация данных из ячейки «Модификация» | `main_window.py` | Сейчас значение не используется (закомментирован eval), new_value = value. При необходимости реализовать безопасное преобразование. |
| Пустые строки в Excel | `main_window.py` | В `export_data_to_db` выход из цикла при первой полностью пустой строке — поведение разумное; можно документировать. |

---

## 8. Краткое резюме

Проект реализует связку **Excel → маппинг колонок в GUI → PostgreSQL** с хранением метаданных целевых таблиц в БД и динамической генерацией SQLAlchemy-моделей. Структура обновлена: пакеты **db/** (подключение, ORM, динамические модели), **ui/** (файлы Qt UI), **logger/** (расширенное логирование с цветным выводом и окном просмотра). Для стабильного запуска необходимо наличие `db/orm_models.py`, при необходимости — скрипта заполнения мета-таблиц и `example.json`, а также корректный реэкспорт `py_logger` в `logger/__init__.py`. Для продакшена целесообразно вынести настройки БД в конфигурацию, убрать зависимость от жёстко заданного Excel при старте и исправить опечатки в документации и интерфейсе.
