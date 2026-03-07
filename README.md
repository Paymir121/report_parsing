# report_parsing — Word-шаблоны

Десктопное приложение для заполнения Word-документов по шаблонам с полями Jinja2: загрузка шаблона → ввод или подстановка значений (вручную или из Excel) → генерация .docx.

## Возможности

- Загрузка шаблона .docx с переменными вида `{{ имя_поля }}`
- Автоматическое извлечение полей из шаблона и сохранение в БД
- Редактирование значений полей в таблице
- Импорт значений из Excel (две колонки: имя поля и значение)
- Генерация итогового документа с подстановкой значений (docxtpl)

## Технологии

- **Python** 3.9+
- **PySide6** — графический интерфейс (форма из .ui в рантайме)
- **SQLite** по умолчанию (опционально PostgreSQL)
- **SQLAlchemy** 2.x — работа с БД
- **python-docx**, **Jinja2**, **docxtpl** — шаблоны Word
- **openpyxl** — чтение Excel

## Установка и запуск

### Клонирование

```bash
git clone git@github.com:Paymir121/report_parsing.git
cd report_parsing
```

### Виртуальное окружение

**Windows (PowerShell):**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Зависимости

```bash
pip install -r requirements.txt
```

### Запуск

```bash
python main.py
```

При первом запуске создаётся база SQLite `word_templates.db` (или путь из переменной окружения `DATABASE`).

## Документация

- [Инструкция по применению](docs/ИНСТРУКЦИЯ.md) — как пользоваться приложением
- [Архитектура проекта](docs/ARCHITECTURE.md) — структура кода и слои

## Конфигурация

- Файл `.env` в корне проекта (опционально).
- **DATABASE** — имя файла БД для SQLite (по умолчанию `word_templates.db`).
- **DRIVERNAME** — при значении `postgresql+psycopg2` используется PostgreSQL (нужны `USERNAME`, `PASSWORD`, `HOST`, `DATABASE`, `PORT`).
- **TEMPLATES_DIR** — начальная папка при выборе файла шаблона.

## Авторы

- [Nikki Nikonor](https://github.com/Paymir121)
