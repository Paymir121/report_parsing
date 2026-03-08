"""
Запуск полной подготовки тестовых данных:
  1) init_db     — создание БД и заполнение тестовыми записями (шаблоны, поля, значения, история)
  2) Шаблоны Word (.docx) в tests/fixtures/
  3) Шаблоны Excel (имя/значение) в tests/fixtures/

Запуск из корня проекта:
  python -m tests.run_all
  python tests/run_all.py
"""
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root))


def main():
    root = Path(__file__).resolve().parent
    if str(root.parent) not in sys.path:
        sys.path.insert(0, str(root.parent))

    print("=== 1. Инициализация БД и заполнение тестовыми данными ===")
    from tests import init_db
    init_db.main()

    print("\n=== 2. Создание шаблонов документов (.docx) ===")
    from tests import create_sample_template
    create_sample_template.main()

    print("\n=== 3. Создание шаблонов Excel (имя / значение) ===")
    from tests import create_sample_excel
    create_sample_excel.main()

    print("\n=== Готово ===")
    print("  БД: word_templates.db (или из DATABASE в .env)")
    print("  Полная очистка БД и перезаполнение: python -m tests.init_db --clear")
    print("")
    print("  Word-шаблоны (только простые поля):")
    print("    tests/fixtures/contract_services.docx   — Договор: CLIENT_NAME, CONTRACT_NUMBER, CONTRACT_DATE, CONTRACT_TYPE, AMOUNT")
    print("    tests/fixtures/act_works.docx          — Акт работ: ACT_NUMBER, ACT_DATE, CLIENT_NAME, EXECUTOR_NAME, WORK_DESCRIPTION")
    print("    tests/fixtures/invoice_simple.docx     — Счёт на оплату: INVOICE_NO, DATE, CUSTOMER, TOTAL")
    print("")
    print("  Word-шаблоны (с таблицами/циклами):")
    print("    tests/fixtures/invoice_loop.docx   — Счёт-фактура: поля + цикл items (NAME, QTY, PRICE)")
    print("    tests/fixtures/mixed_loop.docx     — Акт сдачи-приёмки: поля + цикл works (WORK, AMOUNT)")
    print("    tests/fixtures/delivery_note.docx  — Накладная: поля + цикл goods (NAME, QTY, UNIT)")
    print("    tests/fixtures/project_report.docx — Отчёт по проекту: 3 цикла — participants, milestones, budget_lines")
    print("")
    print("  Excel для простых полей (кнопка «Вставить из Excel»):")
    print("    tests/fixtures/contract_services_values.xlsx")
    print("    tests/fixtures/act_works_values.xlsx")
    print("    tests/fixtures/invoice_simple_values.xlsx")
    print("    tests/fixtures/invoice_loop_values.xlsx")
    print("    tests/fixtures/mixed_loop_values.xlsx")
    print("    tests/fixtures/delivery_note_values.xlsx")
    print("    tests/fixtures/project_report_values.xlsx")
    print("")
    print("  Excel для циклов (вкладка цикла → «Загрузить из Excel»):")
    print("    tests/fixtures/invoice_loop_items.xlsx   ({{NAME}}, {{QTY}}, {{PRICE}})")
    print("    tests/fixtures/mixed_loop_works.xlsx     (WORK, AMOUNT)")
    print("    tests/fixtures/delivery_note_goods.xlsx  (NAME, QTY, UNIT)")
    print("    tests/fixtures/project_report_participants.xlsx  (NAME, ROLE, CONTACT)")
    print("    tests/fixtures/project_report_milestones.xlsx    (MILESTONE, DEADLINE, STATUS)")
    print("    tests/fixtures/project_report_budget_lines.xlsx (DESCRIPTION, AMOUNT, CATEGORY)")
    print("")
    print("  Запуск приложения: python main.py")


if __name__ == "__main__":
    main()
