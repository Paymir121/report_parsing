# Тесты и тестовые данные

## Полная подготовка одной командой

```bash
python -m tests.run_all
```

Скрипт **run_all** по очереди выполняет:

1. **init_db** — создание БД (таблицы) и заполнение тестовыми шаблонами, полями, значениями и историей.
2. **create_sample_template** — создание Word-шаблонов (.docx) в `tests/fixtures/`.
3. **create_sample_excel** — создание Excel-файлов (имя/значение) в `tests/fixtures/` для режима «Из Excel».

После этого можно запускать приложение и использовать файлы из `tests/fixtures/`.

---

## Отдельные шаги

### Подготовка БД

```bash
python -m tests.init_db
```

Создаёт таблицы и заполняет двумя шаблонами («Договор оказания услуг», «Акт выполненных работ») с полями и вариантами значений.

### Word-шаблоны (.docx)

```bash
python -m tests.create_sample_template
```

В `tests/fixtures/` создаются:

- **contract_services.docx** — договор: `{{ CLIENT_NAME }}`, `{{ CONTRACT_NUMBER }}`, `{{ CONTRACT_DATE }}`, `{{ CONTRACT_TYPE }}`, `{{ AMOUNT }}`
- **act_works.docx** — акт: `{{ ACT_NUMBER }}`, `{{ ACT_DATE }}`, `{{ CLIENT_NAME }}`, `{{ EXECUTOR_NAME }}`, `{{ WORK_DESCRIPTION }}`

### Excel для подстановки (имя / значение)

```bash
python -m tests.create_sample_excel
```

В `tests/fixtures/` создаются:

- **contract_services_values.xlsx** — строки имя/значение для полей договора.
- **act_works_values.xlsx** — строки имя/значение для полей акта.

В приложении: режим «Из Excel» → «Загрузить из Excel...» → выбрать один из этих файлов.

---

## Полный цикл тестирования

1. `python -m tests.run_all` — БД, .docx и .xlsx в `tests/fixtures/`.
2. `python main.py` — запуск приложения, загрузка шаблона из `tests/fixtures/`, при необходимости загрузка значений из Excel и генерация документа.
