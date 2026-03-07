# Архитектура проекта report_parsing

Десктопное приложение для заполнения Word-шаблонов (Jinja2) и генерации документов: загрузка шаблона → извлечение полей `{{ FIELD }}` → ввод/выбор значений (вручную или из Excel) → сохранение .docx через docxtpl. Настройки интерфейса и БД, геометрия и состояние главного окна хранятся в QSettings.

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
| Конфигурация     | python-dotenv, `settings.py`, **QSettings** |
| Логирование      | Модуль `logger`, панель лога в UI   |

---

## 2. Структура каталогов

```
report_parsing/
├── main.py                 # Точка входа: QApplication, QSettings (name/org), load_from_qsettings, БД, MainWindow
├── main_window.py          # Главное окно: .ui, виджеты, лог-панель, геометрия/состояние, меню «Настройки»
├── settings.py             # Конфигурация БД и приложения; load_from_qsettings() — чтение из QSettings
├── settings_dialog.py      # Модальное окно настроек (вкладки «Интерфейс» и «БД»), запись в QSettings
├── abstract_dialog.py      # Базовый класс диалогов (если используется)
├── db/
│   ├── connection.py       # Подключение к БД (singleton), Session
│   └── models.py           # SQLAlchemy-модели и create_all_tables
├── core/
│   ├── template_parser.py  # Извлечение переменных из .docx (Jinja2 AST)
│   └── document_generator.py # Рендер .docx по шаблону и контексту (docxtpl)
├── services/
│   ├── template_service.py # Шаблоны: список, регистрация, поля из файла
│   ├── field_value_service.py # Справочники значений полей (field_values)
│   └── generation_service.py  # Генерация документа и запись в историю
├── ui/
│   ├── main_window.ui      # Макет главного окна (Qt Designer)
│   └── main_window_ui.py   # Сгенерированный Python (опционально, не используется при запуске)
├── logger/
│   └── logger.py           # Настройка логирования
├── docs/
│   ├── ARCHITECTURE.md     # Этот документ
│   └── ИНСТРУКЦИЯ.md       # Инструкция по применению
└── tests/
    ├── init_db.py           # Создание таблиц и начальное заполнение
    ├── create_sample_template.py  # Тестовые .docx-шаблоны
    ├── create_sample_excel.py     # Тестовые .xlsx с данными
    └── run_all.py           # Запуск инициализации и фикстур
```

---

## 3. Слои приложения

### 3.1. Точка входа (`main.py`)

- Создание `QUiLoader` до `QApplication` (рекомендация для Windows).
- `QApplication(sys.argv)`, затем `QCoreApplication.setApplicationName("WordTemplates")` и `setOrganizationName("ReportParsing")` для области хранения QSettings.
- Вызов `settings.load_from_qsettings()` — перечитывает из QSettings настройки БД и каталога шаблонов (при наличии).
- Подключение к БД и создание таблиц (`Connection`, `create_all_tables`) — уже с учётом QSettings.
- Создание главного окна с путём к `ui/main_window.ui`, показ окна, запуск цикла событий.

### 3.2. UI (`main_window.py`, `ui/main_window.ui`)

- **Загрузка интерфейса**: форма загружается из `.ui` в рантайме через `QUiLoader`. Путь к файлу — относительно каталога `main_window.py`. При ошибке открытия QFile используется чтение через `QBuffer` и байты файла. Ссылка на загруженный виджет хранится в `_loaded_ui`; центральный виджет подменяется в главном окне.
- **Виджеты**: элементы ищутся по `objectName` через `_find(type_, name)`. Основные: кнопка загрузки шаблона, комбобокс шаблонов, кнопка «Вставить из Excel», таблица полей (Поле / Значение), кнопка «Сгенерировать документ».
- **Панель лога**: скрываемая/раскрываемая панель снизу окна. `LogSignalBridge` (QObject + Signal(str)) и `QtLogHandler` (logging.Handler) перенаправляют сообщения логгера в `QPlainTextEdit`; при запуске раскрытие панели задаётся настройкой из QSettings («Раскрывать панель лога при запуске»).
- **Геометрия и состояние окна**: при старте из QSettings восстанавливаются `MainWindow/geometry` и `MainWindow/state`; при отсутствии сохранённых данных окно открывается развёрнутым (`WindowMaximized`). При изменении состояния окна (`changeEvent` с `WindowStateChange`) и при закрытии (`closeEvent`) геометрия и состояние сохраняются в QSettings.
- **Меню**: в меню бар добавляется «Сервис» → «Настройки…», открывающее модальный диалог `SettingsDialog`. После принятия диалога обновляется `settings.DEFAULT_TEMPLATES_DIR` из QSettings (каталог шаблонов действует без перезапуска).
- **Логика**: обновление списка шаблонов, смена шаблона → заполнение таблицы полей и подстановка значений из БД, импорт из Excel (колонки «имя»/«значение»), сбор контекста из таблицы и вызов сервиса генерации с выбором пути сохранения.

### 3.3. Сервисы (`services/`)

- **template_service**: список шаблонов, получение шаблона по id, поля шаблона, парсинг/валидация файла, регистрация нового шаблона с синхронизацией полей из .docx.
- **field_value_service**: получение вариантов значений по `template_id` или по списку `field_id` (таблица `field_values`).
- **generation_service**: получение содержимого шаблона (файл или байты из БД), вызов `render_docx`, запись записи в `generation_history`.

### 3.4. Ядро (`core/`)

- **template_parser**: сбор текста из .docx (параграфы и таблицы), извлечение переменных через Jinja2 AST (`meta.find_undeclared_variables`), валидация синтаксиса. Для MVP учитываются простые подстановки вида `{{ name }}`.
- **document_generator**: загрузка шаблона (путь или байты), приведение контекста к «безопасным» типам для Jinja2, рендер и сохранение через docxtpl.

### 3.5. База данных (`db/`)

- **connection**: синглтон; создание `Engine` и `Session` из настроек в `settings.py` (SQLite по умолчанию, при необходимости PostgreSQL). Настройки при старте могут быть переопределены из QSettings через `load_from_qsettings()`.
- **models**: декларативные модели и создание таблиц.

### 3.6. Окно настроек (`settings_dialog.py`)

- **SettingsDialog**: модальный диалог с вкладками «Интерфейс» и «БД». Все значения читаются и записываются в QSettings (ключи `Interface/*`, `Database/*`).
- **Интерфейс**: «Раскрывать панель лога при запуске», «Каталог шаблонов по умолчанию» (с кнопкой «Обзор»).
- **БД**: тип БД (SQLite / PostgreSQL); для SQLite — путь к файлу; для PostgreSQL — хост, порт, имя БД, пользователь, пароль. Изменения БД применяются после перезапуска приложения.

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

- **QSettings**: область задаётся через `QCoreApplication.setApplicationName("WordTemplates")` и `setOrganizationName("ReportParsing")`. В QSettings хранятся: геометрия и состояние главного окна (`MainWindow/geometry`, `MainWindow/state`); настройки интерфейса (`Interface/LogExpandedAtStartup`, `Interface/TemplatesDir`); настройки БД (`Database/Driver`, `Database/SqlitePath`, `Database/PgHost` и др.). При старте вызывается `settings.load_from_qsettings()` — при наличии сохранённых значений переопределяются `DATABASES` и `DEFAULT_TEMPLATES_DIR`.
- **settings.py**: значения по умолчанию — из переменных окружения (`.env`, python-dotenv): `DRIVERNAME`, `DATABASE`, `TEMPLATES_DIR` и для PostgreSQL — `USERNAME`, `PASSWORD`, `HOST`, `PORT`. Функция `load_from_qsettings()` перечитывает настройки из QSettings после создания QApplication.

---

## 7. Зависимости ключевых модулей

- **main** → PySide6 (QApplication, QCoreApplication), settings (load_from_qsettings), db.connection, db.models (create_all_tables), main_window.
- **main_window** → db.connection, db.models (DocumentTemplate), services (template, field_value, generation), logger, settings, settings_dialog (SettingsDialog, get_settings_interface_*).
- **settings_dialog** → PySide6 (QDialog, QSettings, виджеты вкладок).
- **services** → db.connection, db.models, core (template_parser, document_generator), logger.
- **core** → python-docx, jinja2, docxtpl (document_generator), logger.

---

## 8. Тесты и фикстуры

- **init_db**: создание таблиц и начальное заполнение (идемпотентность по коду шаблона).
- **create_sample_template**: создание тестовых .docx в `tests/fixtures/`.
- **create_sample_excel**: создание .xlsx с колонками «имя»/«значение» для подстановки в поля.
- **run_all**: последовательный запуск инициализации и создания фикстур.
