"""
Создание БД и заполнение тестовыми данными для приложения Word-шаблонов.
Запуск из корня проекта:
  python -m tests.init_db
  или
  python tests/init_db.py
"""
import sys
from pathlib import Path

# Чтобы работали импорты при запуске tests/init_db.py из любой директории
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root))

from db.connection import Connection
from db.models import (
    create_all_tables,
    DocumentTemplate,
    TemplateField,
    FieldValue,
    GenerationHistory,
)


def seed_templates(session):
    """Шаблоны документов."""
    t1 = DocumentTemplate(
        name="Договор оказания услуг",
        code="contract_services",
        description="Типовой договор с полями: клиент, номер, дата.",
        file_path=None,  # можно подставить путь к тестовому .docx
        store_in_db=False,
    )
    session.add(t1)
    session.flush()

    t2 = DocumentTemplate(
        name="Акт выполненных работ",
        code="act_works",
        description="Акт с реквизитами и подписантами.",
        file_path=None,
        store_in_db=False,
    )
    session.add(t2)
    session.flush()

    return t1.id, t2.id


def seed_fields(session, template_id_contract, template_id_act):
    """Поля шаблонов и варианты значений."""
    # Поля для «Договор»
    fields_contract = [
        ("CLIENT_NAME", "Наименование клиента", 0, True),
        ("CONTRACT_NUMBER", "Номер договора", 1, True),
        ("CONTRACT_DATE", "Дата договора", 2, True),
        ("CONTRACT_TYPE", "Тип договора", 3, False),
        ("AMOUNT", "Сумма", 4, False),
    ]
    field_ids_contract = []
    for field_name, display_name, sort_order, is_required in fields_contract:
        f = TemplateField(
            template_id=template_id_contract,
            field_name=field_name,
            display_name=display_name,
            sort_order=sort_order,
            is_required=is_required,
        )
        session.add(f)
        session.flush()
        field_ids_contract.append((f.id, field_name))

    # Значения для поля «Тип договора»
    for i, (text, is_def) in enumerate([("Разовый", True), ("Рамочный", False), ("Подписка", False)]):
        session.add(
            FieldValue(
                field_id=field_ids_contract[3][0],  # CONTRACT_TYPE
                value_text=text,
                sort_order=i,
                is_default=is_def,
            )
        )

    # Поля для «Акт»
    fields_act = [
        ("ACT_NUMBER", "Номер акта", 0, True),
        ("ACT_DATE", "Дата акта", 1, True),
        ("CLIENT_NAME", "Заказчик", 2, True),
        ("EXECUTOR_NAME", "Исполнитель", 3, True),
        ("WORK_DESCRIPTION", "Описание работ", 4, False),
    ]
    for field_name, display_name, sort_order, is_required in fields_act:
        f = TemplateField(
            template_id=template_id_act,
            field_name=field_name,
            display_name=display_name,
            sort_order=sort_order,
            is_required=is_required,
        )
        session.add(f)

    session.flush()


def seed_history(session, template_id_contract):
    """Пара записей истории генерации."""
    session.add(
        GenerationHistory(
            template_id=template_id_contract,
            output_path="/tmp/contract_001.docx",
            context_snapshot={"CLIENT_NAME": "ООО Рога и копыта", "CONTRACT_NUMBER": "1", "CONTRACT_DATE": "2025-01-15"},
            created_by="init_db",
        )
    )
    session.add(
        GenerationHistory(
            template_id=template_id_contract,
            output_path="/tmp/contract_002.docx",
            context_snapshot={"CLIENT_NAME": "ИП Иванов", "CONTRACT_NUMBER": "2", "CONTRACT_DATE": "2025-02-01"},
            created_by="init_db",
        )
    )


def main():
    print("Создание БД и таблиц...")
    conn = Connection()
    create_all_tables(conn.engine)
    print("Таблицы созданы.")

    session = conn.session
    existing = session.query(DocumentTemplate).filter_by(code="contract_services").first()
    if existing:
        print("Тестовые данные уже есть (шаблон contract_services найден), пропуск заполнения.")
        return

    print("Заполнение тестовыми данными...")
    tid1, tid2 = seed_templates(session)
    seed_fields(session, tid1, tid2)
    seed_history(session, tid1)

    session.commit()
    print("Готово. Добавлено:")
    print("  - 2 шаблона (Договор оказания услуг, Акт выполненных работ)")
    print("  - поля и варианты значений для типа договора")
    print("  - 2 записи в истории генерации")


if __name__ == "__main__":
    main()
