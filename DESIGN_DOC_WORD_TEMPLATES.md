# Проект Word-шаблонов (Jinja2): исправленная архитектура и план

Исправленная и расширенная версия архитектурного документа. Контекст скелета — **PROJECT_REPORT.md**.

---

## 1. Краткое понимание задачи

- **Вход:** .docx как Jinja2-шаблон с плейсхолдерами `{{FIELD}}`.
- **Данные:** значения для подстановки в PostgreSQL; у каждого шаблона свой **фиксированный** набор полей.
- **Действия:** загрузка шаблона → извлечение полей → получение значений из БД → выбор пользователем → генерация итогового .docx.
- **Дополнительно:** версионирование шаблонов, история генерации; значения могут быть как справочником вариантов, так и привязаны к сущностям/записям (учёт во второй фазе).
- **Стек:** Python 3.9, PySide6, PostgreSQL, SQLAlchemy 2.x.

---

## 2. Исправленная архитектура приложения

### 2.1. Слои

- **UI (PySide6):** выбор шаблона, отображение полей, выбор значений, кнопка «Сгенерировать». Без парсинга и рендера.
- **Сервисы (services/):** template_service, field_value_service (или работа с data_sets позже), generation_service. Оркестрируют core и db.
- **Ядро (core/):** template_parser (извлечение переменных через Jinja2 AST), document_generator (рендер через **docxtpl**, не ручной python-docx).
- **БД (db/):** connection, models; репозитории при необходимости.

### 2.2. Где что используется

| Задача | Инструмент | Обоснование |
|--------|------------|-------------|
| Чтение структуры .docx при извлечении переменных | **python-docx** | Обход параграфов/таблиц/ячеек, сборка текста для передачи в Jinja2 AST. |
| Извлечение имён переменных из шаблона | **Jinja2 AST** (Environment.parse + обход узлов) | Безопасно, без выполнения; корректно обрабатывает `{{ name }}`, `{{ user.name }}` и т.д. Regex — только как запасной вариант для MVP. |
| Рендер шаблона (подстановка значений в .docx) | **docxtpl** | Готовый рендер Jinja2 внутри docx: корректная работа с runs, таблицами, циклами. python-docx сам по себе не подставляет Jinja2 — пришлось бы вручную дробить/склеивать XML runs, легко сломать. |
| Генерация итогового файла | **docxtpl** (DocxTemplate) | Единственная точка, где создаётся итоговый документ. |

**Почему python-docx недостаточен для рендера:** в .docx один «кусок» текста может быть разбит на несколько `<w:t>` (runs). Подстановка `{{ CLIENT_NAME }}` может разорвать run или оставить пустые runs. docxtpl решает эту задачу (merge runs, подстановка в правильные места). Самостоятельная реализация — трудоёмко и хрупко.

---

## 3. Исправленная архитектура БД

### 3.1. Исправление generation_history.template_id

**Ошибка в черновике:** `template_id INTEGER NOT NULL REFERENCES ... ON DELETE SET NULL` — противоречие: NOT NULL не позволяет NULL, а ON DELETE SET NULL при удалении шаблона подставит NULL.

**Варианты:**

- **A)** `template_id INTEGER NULL REFERENCES document_templates(id) ON DELETE SET NULL` — история сохраняется при удалении шаблона; в записи просто не будет ссылки на шаблон. Для отчётов и аудита так корректно.
- **B)** `template_id INTEGER NOT NULL REFERENCES document_templates(id) ON DELETE RESTRICT` — запретить удаление шаблона, пока есть записи истории.

**Рекомендация:** вариант **A**. История генерации ценна и при удалённом шаблоне; context_snapshot (JSONB) всё равно хранит, что подставляли. Используем **nullable template_id** и **ON DELETE SET NULL**.

### 3.2. Ключевые сущности и связи

| Таблица | Назначение |
|---------|------------|
| **document_templates** | Шаблон: метаданные, file_path и/или file_content, store_in_db. |
| **template_versions** | Версии одного шаблона (file_path/file_content, version_number). |
| **template_fields** | Поля шаблона: template_id, field_name, display_name, **field_type**, **is_required**, **is_active**, **default_value**, **help_text**, **sort_order**. |
| **field_values** | Справочник вариантов значений по полю: field_id, value_text, sort_order, is_default. |
| **generation_history** | История: **template_id NULL**, generated_at, output_path, context_snapshot JSONB, created_by. |

Опционально (после MVP): **data_sets** (именованный набор данных для генерации) и **data_set_values** (field_id, data_set_id, value_text) — если значения должны принадлежать «записи»/сущности.

### 3.3. Расширенное описание template_fields

Добавляемые атрибуты:

| Поле | Тип | Назначение |
|------|-----|------------|
| field_type | VARCHAR(50) | `text`, `number`, `date` — для UI и валидации (MVP: в основном text). |
| is_required | BOOLEAN | Обязательность при генерации. |
| is_active | BOOLEAN | Поле участвует в шаблоне (при расхождении с парсером можно деактивировать). |
| default_value | TEXT | Значение по умолчанию для подстановки. |
| help_text | TEXT | Подсказка в UI. |
| sort_order | INTEGER | Уже было; порядок отображения в форме. |

### 3.4. Сравнение вариантов хранения данных для подстановки

| Подход | Описание | Плюсы | Минусы |
|--------|----------|--------|--------|
| **Только справочник (field_values)** | Один field_id → несколько вариантов (value_text); пользователь выбирает один на поле. | Просто, достаточно для «выбери из списка». | Нет привязки «этот набор значений — одна сущность/договор/клиент». |
| **Записи/наборы (data_sets + record_values)** | Сущность «набор данных» (например, «Договор №1»); у набора — свои значения по полям. | Удобно для повторной генерации одного и того же набора; значения принадлежат записи. | Сложнее модель и UI; избыточно, если всегда выбирают значения «на лету». |
| **Гибрид** | field_values — справочник вариантов; опционально data_sets + data_set_values — сохранённые наборы. | Справочник для выбора + возможность сохранить выбранное как «набор» и подставлять его позже. | Две модели использования. |

**Рекомендация для кейса:**  
- **MVP:** только **field_values** как справочник. Контекст генерации — словарь из UI (field_name → value), без сущности «набор».  
- **После MVP:** при появлении требования «значения принадлежат сущности» / «сохранить этот набор» ввести **data_sets** (name, template_id, created_at) и **data_set_values** (data_set_id, field_id, value_text). Тогда field_value_service сможет отдавать либо варианты из field_values, либо значения из выбранного data_set.

Сущность «набор данных для генерации» в MVP **не вводим** — отложить до явного требования.

### 3.5. Финальная схема таблиц (DDL)

```sql
-- Шаблоны документов
CREATE TABLE document_templates (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    file_path       VARCHAR(1024),
    file_content    BYTEA,
    store_in_db     BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Версии шаблона
CREATE TABLE template_versions (
    id              SERIAL PRIMARY KEY,
    template_id     INTEGER NOT NULL REFERENCES document_templates(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    file_path       VARCHAR(1024),
    file_content    BYTEA,
    store_in_db     BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(template_id, version_number)
);

-- Поля шаблона (расширенные атрибуты)
CREATE TABLE template_fields (
    id              SERIAL PRIMARY KEY,
    template_id     INTEGER NOT NULL REFERENCES document_templates(id) ON DELETE CASCADE,
    field_name      VARCHAR(255) NOT NULL,
    display_name    VARCHAR(255),
    field_type      VARCHAR(50) NOT NULL DEFAULT 'text',
    is_required     BOOLEAN NOT NULL DEFAULT false,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    default_value   TEXT,
    help_text       TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(template_id, field_name)
);

-- Справочник значений по полям
CREATE TABLE field_values (
    id              SERIAL PRIMARY KEY,
    field_id        INTEGER NOT NULL REFERENCES template_fields(id) ON DELETE CASCADE,
    value_text      TEXT NOT NULL,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- История генерации (template_id nullable + ON DELETE SET NULL)
CREATE TABLE generation_history (
    id              SERIAL PRIMARY KEY,
    template_id     INTEGER NULL REFERENCES document_templates(id) ON DELETE SET NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    output_path     VARCHAR(1024),
    context_snapshot JSONB,
    created_by      VARCHAR(255)
);

CREATE INDEX idx_template_fields_template_id ON template_fields(template_id);
CREATE INDEX idx_field_values_field_id ON field_values(field_id);
CREATE INDEX idx_generation_history_template_id ON generation_history(template_id);
CREATE INDEX idx_generation_history_generated_at ON generation_history(generated_at);
```

---

## 4. Ограничения шаблонного синтаксиса

### 4.1. MVP — разрешено

- Только подстановки вида **`{{ variable_name }}`**.
- `variable_name` — идентификатор (буквы, цифры, подчёркивание). Точечная нотация для одного уровня (`{{ user.name }}`) допустима при извлечении через AST; в контексте передаём плоский ключ или вложенный dict по соглашению.

### 4.2. MVP — запрещено

- **`{% ... %}`** (for, if, macro, block и т.д.) — не поддерживаем в MVP; валидация должна помечать шаблон как «не поддерживается» или предупреждать.
- Вызовы вида **`{{ func() }}`**, **`{{ value \| filter }}`** с аргументами — запрещены (риск выполнения кода).
- Любые вызовы и фильтры, кроме безопасных (например, `| default` без вызова) — отключить в Environment или не допускать при разборе AST.

### 4.3. Позже (после MVP)

- **`{% for item in list %}`** в таблицах docx — при использовании docxtpl часто уже поддерживается; включить после стабилизации MVP.
- Ограниченный набор фильтров (например, `default`, `upper`) через whitelist в Jinja2 Environment.

### 4.4. Валидация

- При загрузке/обновлении шаблона: собрать текст из docx, вызвать `Environment.parse(template_string)`.
- Обход AST: если встречается узел не из whitelist (например, Call, Filter), считать шаблон невалидным для MVP и возвращать ошибку или список «запрещённых конструкций».
- Список имён переменных извлекать только из узлов типа `Name` (и точечный доступ при необходимости).

---

## 5. План разработки по этапам

- **Этап 1 — Подготовка базы:** структура каталогов, requirements (python-docx, jinja2, docxtpl), сохранение connection/settings/logger, отключение старых импортов Excel.
- **Этап 2 — Модели БД:** SQLAlchemy-модели под все таблицы, create_all.
- **Этап 3 — Работа с шаблонами:** загрузка .docx, извлечение переменных через Jinja2 AST, валидация; генерация через docxtpl.
- **Этап 4 — Сервисы:** template_service, field_value_service, generation_service.
- **Этап 5 — UI:** main_window под шаблоны/поля/генерацию.
- **Этап 6 — Запуск MVP:** сценарий «один шаблон → поля → выбор значений → генерация», ручная проверка.

---

## 6. Адаптация скелета и новая структура каталогов

**Переиспользовать:** `db/connection.py` (подключение к PostgreSQL), `settings.py`, `logger/`, каркас `main.py`, каталог `ui/`.

**Изменить:** `main.py` — создание новых таблиц (models), убрать импорт file_db_example и orm_models Excel; `db/connection.py` — импорт Base из новых models.

**Удалить/не использовать:** старые `db/orm_models.py` (Excel), `db/data_models.py` (динамические таблицы Excel); логику main_window под Excel.

**Новая структура:**

```
report_parsing/
├── main.py
├── main_window.py
├── settings.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── template_parser.py    # извлечение переменных через Jinja2 AST
│   └── document_generator.py # docxtpl: рендер + сохранение
├── db/
│   ├── __init__.py
│   ├── connection.py
│   └── models.py             # DocumentTemplate, TemplateField, FieldValue, GenerationHistory, TemplateVersion
├── services/
│   ├── __init__.py
│   ├── template_service.py
│   ├── field_value_service.py
│   └── generation_service.py
├── ui/
│   └── main_window.ui
└── logger/
```

Отдельный модуль **jinja_render** не нужен: рендер целиком в **document_generator** через docxtpl.

---

## 7. Основные риски и снижение

| Риск | Снижение |
|------|----------|
| Изменение набора полей в шаблоне | Парсинг при открытии/обновлении; сверка с template_fields; обновление полей или is_active. |
| Выполнение кода в Jinja2 | Строго контролируемый контекст (dict примитивов); извлечение переменных только через AST, без render. |
| Повреждённый docx | Открытие через python-docx/docxtpl; при исключении — не сохранять, сообщение пользователю. |
| Большие файлы в БД | Лимит размера; по умолчанию file_path. |
| Расхождение полей БД и файла | Кнопка «Обновить поля из шаблона»; предупреждение при расхождении. |

---

## 8. Контекст скелета

См. **PROJECT_REPORT.md**: структура main.py, main_window.py, db/, ui/, logger/; ранее Excel → маппинг → PostgreSQL. Переиспользуем connection, settings, logger, каркас main и ui; модели и экран заменяем на Word-шаблоны.

---

## 9. Этап 6 — Запуск MVP и проверка

### Что уже должно работать

- Запуск приложения: `python main.py` (PostgreSQL должен быть доступен, БД `test_db` создана).
- При старте создаются таблицы: `document_templates`, `template_versions`, `template_fields`, `field_values`, `generation_history`.
- Главное окно: список шаблонов в комбобоксе (пока пустой), кнопки «Загрузить шаблон...» и «Сгенерировать документ».
- **Загрузить шаблон:** выбор .docx → валидация и парсинг полей через Jinja2 AST → запись в БД (имя/код из имени файла), поля заполняются из шаблона.
- **Сгенерировать:** выбор шаблона и путь сохранения → вызов docxtpl с контекстом (пока пустой) → сохранение файла и запись в `generation_history`.

### Как протестировать вручную

1. Запустить PostgreSQL, создать БД `test_db`, при необходимости поправить `settings.py` / `.env`.
2. `pip install -r requirements.txt` (добавлены python-docx, jinja2, docxtpl).
3. `python main.py` — должно открыться окно.
4. Нажать «Загрузить шаблон...», выбрать .docx с плейсхолдерами `{{ FIELD }}`. После успешной загрузки шаблон появится в списке.
5. Выбрать шаблон, нажать «Сгенерировать документ», указать путь — должен создаться .docx (переменные останутся пустыми, пока не реализована форма полей).

### Ограничения MVP

- Форма «поле → значение» не реализована: контекст при генерации пустой. Следующий шаг — при выборе шаблона строить форму по `template_fields` и `field_values` и передавать выбранные значения в `generate_document`.
- Версионирование шаблонов (таблица `template_versions`) и хранение файла в БД не используются в UI.
- Старый макет `ui/main_window.ui` (Excel) сохранён: виджеты `tables_combobox`, `add_file_pushbutton`, `export_pushbutton` переиспользуются под новый сценарий.
