"""
Создание БД и заполнение тестовыми данными для приложения Word-шаблонов.

Запуск из корня проекта:
  python -m tests.init_db
  python tests/init_db.py

Полная очистка БД и повторное заполнение:
  python -m tests.init_db --clear
  python -m tests.init_db -c
"""
import argparse
import sys
from pathlib import Path

# Чтобы работали импорты при запуске tests/init_db.py из любой директории
if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root))

from db.connection import Connection
from db.models import (
    Base,
    create_all_tables,
    DocumentTemplate,
    TemplateField,
    TemplateLoopBlock,
    TemplateLoopField,
    FieldValue,
    GenerationHistory,
)


def seed_templates(session):
    """Шаблоны документов (только простые поля)."""
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"

    t1 = DocumentTemplate(
        name="Договор оказания услуг",
        code="contract_services",
        description="Типовой договор с полями: клиент, номер, дата.",
        file_path=str(fixtures_dir / "contract_services.docx"),
        store_in_db=False,
    )
    session.add(t1)
    session.flush()

    t2 = DocumentTemplate(
        name="Акт выполненных работ",
        code="act_works",
        description="Акт с реквизитами и подписантами.",
        file_path=str(fixtures_dir / "act_works.docx"),
        store_in_db=False,
    )
    session.add(t2)
    session.flush()

    t3_simple = DocumentTemplate(
        name="Счёт на оплату",
        code="invoice_simple",
        description="Простой счёт без таблицы: номер, дата, заказчик, сумма.",
        file_path=str(fixtures_dir / "invoice_simple.docx"),
        store_in_db=False,
    )
    session.add(t3_simple)
    session.flush()

    return t1.id, t2.id, t3_simple.id


def seed_fields(session, template_id_contract, template_id_act, template_id_invoice_simple):
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

    # Поля для «Счёт на оплату» (простой)
    fields_invoice_simple = [
        ("INVOICE_NO", "Номер счёта", 0, True),
        ("DATE", "Дата счёта", 1, True),
        ("CUSTOMER", "Заказчик", 2, True),
        ("TOTAL", "Сумма к оплате", 3, True),
    ]
    for field_name, display_name, sort_order, is_required in fields_invoice_simple:
        session.add(TemplateField(
            template_id=template_id_invoice_simple,
            field_name=field_name,
            display_name=display_name,
            sort_order=sort_order,
            is_required=is_required,
        ))

    session.flush()


def seed_loop_templates(session):
    """
    Два шаблона с циклами:
    - invoice_loop: простые поля + цикл items (NAME, QTY, PRICE)
    - mixed_loop:   простые поля + цикл works (WORK, AMOUNT)
    Соответствуют файлам tests/fixtures/invoice_loop.docx и mixed_loop.docx.
    """
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"

    t3 = DocumentTemplate(
        name="Счёт-фактура с позициями",
        code="invoice_loop",
        description="Простые поля + цикл по позициям (items).",
        file_path=str(fixtures_dir / "invoice_loop.docx"),
        store_in_db=False,
    )
    session.add(t3)
    session.flush()

    for i, (fname, dname) in enumerate([
        ("INVOICE_NUMBER", "Номер счёта"),
        ("INVOICE_DATE", "Дата счёта"),
        ("CLIENT_NAME", "Покупатель"),
    ]):
        session.add(TemplateField(
            template_id=t3.id, field_name=fname, display_name=dname,
            sort_order=i, is_required=True,
        ))

    block_items = TemplateLoopBlock(
        template_id=t3.id, loop_var="items", item_var="item",
        label="items", sort_order=0,
    )
    session.add(block_items)
    session.flush()
    for j, (fname, dname) in enumerate([
        ("NAME", "Наименование"), ("QTY", "Кол-во"), ("PRICE", "Цена"),
    ]):
        session.add(TemplateLoopField(
            loop_block_id=block_items.id, field_name=fname,
            display_name=dname, sort_order=j,
        ))

    t4 = DocumentTemplate(
        name="Акт сдачи-приёмки (смешанный)",
        code="mixed_loop",
        description="Простые поля (исполнитель, дата) + цикл по работам (works).",
        file_path=str(fixtures_dir / "mixed_loop.docx"),
        store_in_db=False,
    )
    session.add(t4)
    session.flush()

    for i, (fname, dname) in enumerate([
        ("EXECUTOR", "Исполнитель"),
        ("CONTRACT_DATE", "Дата"),
    ]):
        session.add(TemplateField(
            template_id=t4.id, field_name=fname, display_name=dname,
            sort_order=i, is_required=True,
        ))

    block_works = TemplateLoopBlock(
        template_id=t4.id, loop_var="works", item_var="row",
        label="works", sort_order=0,
    )
    session.add(block_works)
    session.flush()
    for j, (fname, dname) in enumerate([
        ("WORK", "Наименование работы"), ("AMOUNT", "Сумма, руб."),
    ]):
        session.add(TemplateLoopField(
            loop_block_id=block_works.id, field_name=fname,
            display_name=dname, sort_order=j,
        ))

    # Накладная: простые поля + цикл goods (NAME, QTY, UNIT)
    t5 = DocumentTemplate(
        name="Накладная",
        code="delivery_note",
        description="Простые поля (получатель, дата) + цикл по товарам (goods).",
        file_path=str(fixtures_dir / "delivery_note.docx"),
        store_in_db=False,
    )
    session.add(t5)
    session.flush()
    for i, (fname, dname) in enumerate([
        ("CONSIGNEE", "Получатель"),
        ("DELIVERY_DATE", "Дата отгрузки"),
    ]):
        session.add(TemplateField(
            template_id=t5.id, field_name=fname, display_name=dname,
            sort_order=i, is_required=True,
        ))
    block_goods = TemplateLoopBlock(
        template_id=t5.id, loop_var="goods", item_var="item",
        label="goods", sort_order=0,
    )
    session.add(block_goods)
    session.flush()
    for j, (fname, dname) in enumerate([
        ("NAME", "Наименование"), ("QTY", "Количество"), ("UNIT", "Ед. изм."),
    ]):
        session.add(TemplateLoopField(
            loop_block_id=block_goods.id, field_name=fname,
            display_name=dname, sort_order=j,
        ))

    # Отчёт по проекту: 3 различных цикла в одном документе
    t6 = DocumentTemplate(
        name="Отчёт по проекту",
        code="project_report",
        description="Простые поля + 3 таблицы: участники, этапы, бюджет.",
        file_path=str(fixtures_dir / "project_report.docx"),
        store_in_db=False,
    )
    session.add(t6)
    session.flush()
    for i, (fname, dname) in enumerate([
        ("PROJECT_NAME", "Название проекта"),
        ("REPORT_DATE", "Дата отчёта"),
        ("AUTHOR", "Автор отчёта"),
    ]):
        session.add(TemplateField(
            template_id=t6.id, field_name=fname, display_name=dname,
            sort_order=i, is_required=True,
        ))
    # Цикл 1: участники (participants)
    block_participants = TemplateLoopBlock(
        template_id=t6.id, loop_var="participants", item_var="item",
        label="participants", sort_order=0,
    )
    session.add(block_participants)
    session.flush()
    for j, (fname, dname) in enumerate([
        ("NAME", "ФИО"), ("ROLE", "Роль"), ("CONTACT", "Контакт"),
    ]):
        session.add(TemplateLoopField(
            loop_block_id=block_participants.id, field_name=fname,
            display_name=dname, sort_order=j,
        ))
    # Цикл 2: этапы (milestones)
    block_milestones = TemplateLoopBlock(
        template_id=t6.id, loop_var="milestones", item_var="m",
        label="milestones", sort_order=1,
    )
    session.add(block_milestones)
    session.flush()
    for j, (fname, dname) in enumerate([
        ("MILESTONE", "Этап"), ("DEADLINE", "Срок"), ("STATUS", "Статус"),
    ]):
        session.add(TemplateLoopField(
            loop_block_id=block_milestones.id, field_name=fname,
            display_name=dname, sort_order=j,
        ))
    # Цикл 3: бюджет (budget_lines)
    block_budget = TemplateLoopBlock(
        template_id=t6.id, loop_var="budget_lines", item_var="line",
        label="budget_lines", sort_order=2,
    )
    session.add(block_budget)
    session.flush()
    for j, (fname, dname) in enumerate([
        ("DESCRIPTION", "Статья"), ("AMOUNT", "Сумма, руб."), ("CATEGORY", "Категория"),
    ]):
        session.add(TemplateLoopField(
            loop_block_id=block_budget.id, field_name=fname,
            display_name=dname, sort_order=j,
        ))

    session.flush()
    return t3.id, t4.id, t5.id, t6.id


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


def clear_database(engine):
    """Полностью очистить БД: удалить все таблицы."""
    from sqlalchemy import inspect
    insp = inspect(engine)
    existing = insp.get_table_names()
    if not existing:
        print("БД пуста, очистка не требуется.")
        return
    Base.metadata.drop_all(bind=engine)
    print("БД полностью очищена (все таблицы удалены).")


def main():
    parser = argparse.ArgumentParser(
        description="Инициализация БД и заполнение тестовыми шаблонами/полями."
    )
    parser.add_argument(
        "-c", "--clear",
        action="store_true",
        help="Полностью очистить БД (удалить все таблицы) и заново создать структуру и данные.",
    )
    args = parser.parse_args()

    conn = Connection()
    engine = conn.engine

    if args.clear:
        print("=== Очистка БД ===")
        clear_database(engine)
        print("")

    print("Создание БД и таблиц...")
    create_all_tables(engine)
    print("Таблицы созданы.")

    session = conn.session
    if not args.clear:
        existing = session.query(DocumentTemplate).filter_by(code="contract_services").first()
        if existing:
            print("Тестовые данные уже есть (шаблон contract_services найден), пропуск заполнения.")
            print("Для полной перезаписи запустите: python -m tests.init_db --clear")
            return

    has_simple = session.query(DocumentTemplate).filter_by(code="contract_services").first()
    has_loop = session.query(DocumentTemplate).filter_by(code="invoice_loop").first()

    if not has_simple:
        print("Заполнение простых шаблонов...")
        tid1, tid2, tid3_simple = seed_templates(session)
        seed_fields(session, tid1, tid2, tid3_simple)
        seed_history(session, tid1)
        session.commit()
        print("  Добавлено: 3 простых шаблона (договор, акт, счёт), поля, история генерации.")
    else:
        print("Простые шаблоны уже есть (contract_services найден), пропуск.")

    if not has_loop:
        print("Заполнение шаблонов с циклами...")
        seed_loop_templates(session)
        session.commit()
        print("  Добавлено: invoice_loop, mixed_loop, delivery_note, project_report (3 цикла) + LoopBlock/LoopField.")
    else:
        print("Шаблоны с циклами уже есть (invoice_loop найден), пропуск.")

    print("Готово.")


if __name__ == "__main__":
    main()
