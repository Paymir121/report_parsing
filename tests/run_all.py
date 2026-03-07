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
    print("  Word-шаблоны: tests/fixtures/contract_services.docx, act_works.docx")
    print("  Excel для подстановки: tests/fixtures/contract_services_values.xlsx, act_works_values.xlsx")
    print("  Запуск приложения: python main.py")


if __name__ == "__main__":
    main()
