# Тесты и тестовые данные

## Полная подготовка одной командой

```bash
python -m tests.run_all
```

Скрипт **run_all** по очереди выполняет:

1. **init_db** — создание БД (таблицы) и заполнение тестовыми шаблонами, полями, циклами, значениями и историей.
2. **create_sample_template** — создание Word-шаблонов (.docx) в `tests/fixtures/`.
3. **create_sample_excel** — создание Excel-файлов в `tests/fixtures/` для простых полей (имя/значение) и для данных циклов.

После этого можно запускать приложение и использовать файлы из `tests/fixtures/`.

---

## Полная очистка БД

Чтобы удалить все данные и заново заполнить БД тестовыми шаблонами:

```bash
python -m tests.init_db --clear
```

или кратко:

```bash
python -m tests.init_db -c
```

---

## Отдельные шаги

### Подготовка БД

```bash
python -m tests.init_db
```

Создаёт таблицы и заполняет шаблонами: три простых (Договор, Акт, Счёт на оплату), четыре с циклами (Счёт-фактура, Акт сдачи-приёмки, Накладная, Отчёт по проекту с тремя циклами), поля, блоки циклов, история.

### Word-шаблоны (.docx)

```bash
python -m tests.create_sample_template
```

В `tests/fixtures/` создаются:

**Простые поля (одна вкладка «Поля»):**

- **contract_services.docx** — Договор: CLIENT_NAME, CONTRACT_NUMBER, CONTRACT_DATE, CONTRACT_TYPE, AMOUNT
- **act_works.docx** — Акт: ACT_NUMBER, ACT_DATE, CLIENT_NAME, EXECUTOR_NAME, WORK_DESCRIPTION
- **invoice_simple.docx** — Счёт на оплату: INVOICE_NO, DATE, CUSTOMER, TOTAL

**С циклами (вкладка «Поля» + вкладки циклов):**

- **invoice_loop.docx** — Счёт-фактура: поля + цикл items (NAME, QTY, PRICE)
- **mixed_loop.docx** — Акт сдачи-приёмки: поля + цикл works (WORK, AMOUNT)
- **delivery_note.docx** — Накладная: поля + цикл goods (NAME, QTY, UNIT)
- **project_report.docx** — Отчёт по проекту: поля + три цикла (participants, milestones, budget_lines)

### Excel для подстановки

```bash
python -m tests.create_sample_excel
```

**Для простых полей (вкладка «Поля» → «Вставить из Excel…»):**  
Файлы с колонками **«имя»** и **«значение»**:

- contract_services_values.xlsx, act_works_values.xlsx, invoice_simple_values.xlsx
- invoice_loop_values.xlsx, mixed_loop_values.xlsx, delivery_note_values.xlsx, project_report_values.xlsx

**Для циклов (вкладка цикла → «Загрузить из Excel…»):**  
Заголовки = имена полей цикла:

- invoice_loop_items.xlsx (NAME, QTY, PRICE)
- mixed_loop_works.xlsx (WORK, AMOUNT)
- delivery_note_goods.xlsx (NAME, QTY, UNIT)
- project_report_participants.xlsx, project_report_milestones.xlsx, project_report_budget_lines.xlsx

---

## Полный цикл тестирования

1. `python -m tests.run_all` — БД, .docx и .xlsx в `tests/fixtures/`.
2. `python main.py` — запуск приложения: выбор шаблона из списка (или загрузка из `tests/fixtures/`), при необходимости загрузка значений из Excel (простые поля — файлы *_values.xlsx; циклы — соответствующие файлы по вкладкам), генерация документа.
