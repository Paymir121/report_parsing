# Архитектура проекта report_parsing

Десктопное приложение для заполнения Word-шаблонов (Jinja2) и генерации документов: загрузка шаблона → извлечение полей `{{ FIELD }}` → ввод/выбор значений (вручную или из Excel) → сохранение .docx через docxtpl.

---

## 1. Стек технологий

| Компонент        | Технология                          |
|------------------|-------------------------------------|
| Язык             | Python 3.9+                         |
| UI               | PySide6, Qt Designer (.ui)          |
| БД               | SQLite (по умолчанию), опционально PostgreSQL |
| ORM              | SQLAlchemy 2.x                      |
| Шаблоны Word     | python-docx, Jinja2, docxtpl        |
| Импорт значений  | openpyxl (Excel)                    |
| Конфигурация     | python-dotenv, `settings.py`        |
| Логирование      | Модуль `logger`                     |

---

## 2. Структура каталогов

```
report_parsing/
├── main.py                 # Точка входа: БД, QApplication, MainWindow
├── main_window.py          # Главное окно: загрузка .ui, привязка виджетов, логика UI
├── settings.py              # Конфигурация БД и приложения
├── abstract_dialog.py       # Базовый класс диалогов (если используется)
├── db/
│   ├── connection.py        # Подключение к БД (singleton), Session
│   └── models.py            # SQLAlchemy-модели и create_all_tables
├── core/
│   ├── template_parser.py   # Извлечение переменных из .docx (Jinja2 AST)
│   └── document_generator.py# Рендер .docx по шаблону и контексту (docxtpl)
├── services/
│   ├── template_service.py  # Шаблоны: список, регистрация, поля из файла
│   ├── field_value_service.py # Справочники значений полей (field_values)
│   └── generation_service.py  # Генерация документа и запись в историю
├── ui/
│   ├── main_window.ui       # Макет главного окна (Qt Designer)
│   └── main_window_ui.py     # Сгенерированный Python (опционально, не используется при запуске)
├── logger/
│   └── logger.py            # Настройка логирования
└── tests/
    ├── init_db.py           # Создание таблиц и начальное заполнение
    ├── create_sample_template.py  # Тестовые .docx-шаблоны
    ├── create_sample_excel.py     # Тестовые .xlsx с данными
    └── run_all.py           # Запуск инициализации и фикстур
```

---

## 3. Слои приложения

### 3.1. Точка входа (`main.py`)

- Подключение к БД и создание таблиц (`Connection`, `create_all_tables`).
- Создание `QUiLoader` до `QApplication` (рекомендация для Windows).
- Создание приложения Qt и главного окна с путём к `ui/main_window.ui`.
- Запуск цикла событий.

### 3.2. UI (`main_window.py`, `ui/main_window.ui`)

- **Загрузка интерфейса**: форма загружается из `.ui` в рантайме через `QUiLoader` (без генерации в Python при старте). Путь к файлу считается от каталога `main_window.py`. При ошибке открытия файла используется чтение через `QBuffer` и байты файла.
- **Виджеты**: центральный виджет загруженной формы подменяет central widget главного окна; ссылка на загруженный виджет хранится в `_loaded_ui`. Элементы ищутся по `objectName` через `_find(type_, name)`.
- **Основные элементы**: кнопка загрузки шаблона, комбобокс шаблонов, кнопка «Вставить из Excel», таблица полей (Поле / Значение), кнопка «Сгенерировать документ».
- **Логика**: обновление списка шаблонов, смена шаблона → заполнение таблицы полей и подстановка значений из БД, импорт из Excel (колонки «имя»/«значение»), сбор контекста из таблицы и вызов сервиса генерации с выбором пути сохранения.

### 3.3. Сервисы (`services/`)

- **template_service**: список шаблонов, получение шаблона по id, поля шаблона, парсинг/валидация файла, регистрация нового шаблона с синхронизацией полей из .docx.
- **field_value_service**: получение вариантов значений по `template_id` или по списку `field_id` (таблица `field_values`).
- **generation_service**: получение содержимого шаблона (файл или байты из БД), вызов `render_docx`, запись записи в `generation_history`.

### 3.4. Ядро (`core/`)

- **template_parser**: сбор текста из .docx (параграфы и таблицы), извлечение переменных через Jinja2 AST (`meta.find_undeclared_variables`), валидация синтаксиса. Для MVP учитываются простые подстановки вида `{{ name }}`.
- **document_generator**: загрузка шаблона (путь или байты), приведение контекста к «безопасным» типам для Jinja2, рендер и сохранение через docxtpl.

### 3.5. База данных (`db/`)

- **connection**: синглтон; создание `Engine` и `Session` из настроек в `settings.py` (SQLite по умолчанию, при необходимости PostgreSQL).
- **models**: декларативные модели и создание таблиц.

---

## 4. Модели данных (кратко)

| Таблица              | Назначение |
|----------------------|------------|
| **document_templates** | Шаблоны: имя, code, описание, путь/содержимое файла, флаг хранения в БД. |
| **template_versions**  | Версии шаблона (при необходимости). |
| **template_fields**    | Поля шаблона: field_name, display_name, тип, обязательность, sort_order и т.д. |
| **field_values**       | Справочные значения для полей (для выбора в UI). |
| **generation_history** | История генераций: template_id (nullable, SET NULL при удалении шаблона), путь к файлу, снимок контекста, дата, created_by. |

Связи: шаблон → поля (cascade delete); поле → значения; шаблон → история (passive_deletes). Для SQLite используется тип `JSON` вместо `JSONB`.

---

## 5. Поток данных

1. **Старт**: создание таблиц, загрузка списка шаблонов в комбобокс.
2. **Выбор шаблона**: загрузка полей из БД, заполнение таблицы (Поле / Значение), подстановка значений по умолчанию из `field_values`.
3. **Редактирование**: пользователь меняет значения в таблице и/или подгружает данные из Excel (по колонкам «имя»/«значение»).
4. **Генерация**: сбор контекста из таблицы (имя поля → значение), вызов `generate_document(template_id, context, output_path)` → рендер docxtpl, сохранение .docx и запись в `generation_history`.

---

## 6. Конфигурация

- **settings.py**: выбор БД по переменной окружения `DRIVERNAME` (при `postgresql+psycopg2` — PostgreSQL, иначе SQLite). Для SQLite имя файла задаётся через `DATABASE` (по умолчанию `word_templates.db`). Опционально: `TEMPLATES_DIR`, логирование.
- Переменные окружения через `.env` (python-dotenv).

---

## 7. Зависимости ключевых модулей

- **main_window** → db.connection, db.models (DocumentTemplate), services (template, field_value, generation), logger, settings.
- **services** → db.connection, db.models, core (template_parser, document_generator), logger.
- **core** → python-docx, jinja2, docxtpl (document_generator), logger.

---

## 8. Тесты и фикстуры

- **init_db**: создание таблиц и начальное заполнение (идемпотентность по коду шаблона).
- **create_sample_template**: создание тестовых .docx в `tests/fixtures/`.
- **create_sample_excel**: создание .xlsx с колонками «имя»/«значение» для подстановки в поля.
- **run_all**: последовательный запуск инициализации и создания фикстур.
