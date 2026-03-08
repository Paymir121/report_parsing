# report_parsing — Word-шаблоны

Десктопное приложение для заполнения Word-документов по шаблонам с полями Jinja2: загрузка шаблона → ввод или подстановка значений (вручную, из Excel или из записей БД) → генерация .docx.

## Возможности

- **Шаблоны .docx** с переменными `{{ поле }}` и циклами Jinja2 (`{% for item in items %} … {% endfor %}`).
- **Простые поля** — одна вкладка «Поля»: таблица полей, кнопка «Вставить из Excel…» (формат: колонки «имя» и «значение»).
- **Циклы (таблицы)** — отдельная вкладка на каждый цикл шаблона: таблица строк, «Загрузить из Excel…», «+ Строка» / «− Строка».
- Автоматическое извлечение полей и циклов из шаблона при регистрации (template_parser).
- **Наборы данных (БД)**: импорт Excel в таблицы, привязка шаблона к набору, выбор записи для подстановки в поля.
- **Генерация** через docxtpl с подстановкой простых полей и циклов; история в БД.
- **Настройки** (QSettings): интерфейс (каталог шаблонов, раскрытие лога, **уровень логирования**), БД (SQLite/PostgreSQL).

## Технологии

- **Python** 3.9+
- **PySide6** — GUI (форма из .ui в рантайме)
- **SQLite** по умолчанию (опционально PostgreSQL), **SQLAlchemy** 2.x
- **python-docx**, **Jinja2**, **docxtpl** — шаблоны Word
- **openpyxl** — чтение Excel

## Установка и запуск

### Клонирование и окружение

```bash
git clone git@github.com:Paymir121/report_parsing.git
cd report_parsing
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
```

### Запуск

```bash
python main.py
```

При первом запуске создаётся база SQLite `word_templates.db` (или путь из `.env` / настроек).

### Тестовые данные (опционально)

```bash
python -m tests.run_all
```

Создаёт БД с тестовыми шаблонами, генерирует .docx и .xlsx в `tests/fixtures/`. Полная очистка БД и перезаполнение: `python -m tests.init_db --clear`.

## Документация

- [Инструкция по применению](docs/ИНСТРУКЦИЯ.md) — сценарии, Excel, наборы данных, настройки.
- [Архитектура проекта](docs/ARCHITECTURE.md) — слои, БД, циклы, сервисы.
- [План реализации](docs/IMPLEMENTATION_PLAN.md) — этапы и текущее состояние.
- [Тесты и фикстуры](tests/README.md) — run_all, init_db, список шаблонов и Excel.

## Конфигурация

- **.env** (опционально): `DATABASE`, `DRIVERNAME`, `TEMPLATES_DIR`, для PostgreSQL — `USERNAME`, `PASSWORD`, `HOST`, `PORT`.
- **Настройки (Сервис → Настройки…)**: сохраняются в QSettings (интерфейс, БД, уровень логирования DEBUG/INFO/WARNING/ERROR/CRITICAL).

## Авторы

- [Nikki Nikonor](https://github.com/Paymir121)
