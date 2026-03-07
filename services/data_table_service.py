"""
Сервис наборов данных (data_tables): CRUD таблиц, колонок, записей и значений.
Используется для импорта из Excel и ручного ввода/редактирования записей.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from db.connection import Connection
from db.models import DataRecord, DataRecordValue, DataTable, DataTableColumn
from logger import py_logger


def list_data_tables() -> List[DataTable]:
    """Вернуть список всех наборов данных."""
    conn = Connection()
    return conn.session.query(DataTable).order_by(DataTable.name).all()


def get_data_table_by_id(table_id: int) -> Optional[DataTable]:
    """Вернуть набор данных по id или None."""
    conn = Connection()
    return conn.session.get(DataTable, table_id)


def get_data_table_by_code(code: str) -> Optional[DataTable]:
    """Вернуть набор данных по коду или None."""
    conn = Connection()
    return conn.session.query(DataTable).filter_by(code=code).first()


def create_data_table(name: str, code: str, description: Optional[str] = None) -> Tuple[Optional[DataTable], List[str]]:
    """
    Создать новый набор данных.
    Возвращает (DataTable, список ошибок).
    """
    errors: List[str] = []
    code = (code or "").strip() or name.replace(" ", "_").lower()
    if not name.strip():
        return None, ["Укажите название набора данных."]
    conn = Connection()
    existing = conn.session.query(DataTable).filter_by(code=code).first()
    if existing:
        return None, [f"Набор данных с кодом «{code}» уже существует."]
    table = DataTable(name=name.strip(), code=code, description=(description or "").strip() or None)
    conn.session.add(table)
    conn.session.commit()
    conn.session.refresh(table)
    py_logger.info("Created data table id=%s code=%s", table.id, code)
    return table, errors


def update_data_table(table_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[DataTable]:
    """Обновить название/описание набора данных."""
    conn = Connection()
    table = conn.session.get(DataTable, table_id)
    if not table:
        return None
    if name is not None:
        table.name = name.strip()
    if description is not None:
        table.description = description.strip() or None
    table.updated_at = datetime.utcnow()
    conn.session.commit()
    conn.session.refresh(table)
    return table


def delete_data_table(table_id: int) -> bool:
    """Удалить набор данных и все записи. Возвращает True при успехе."""
    conn = Connection()
    table = conn.session.get(DataTable, table_id)
    if not table:
        return False
    conn.session.delete(table)
    conn.session.commit()
    py_logger.info("Deleted data table id=%s", table_id)
    return True


def get_columns(table_id: int) -> List[DataTableColumn]:
    """Вернуть колонки набора данных по sort_order."""
    conn = Connection()
    return (
        conn.session.query(DataTableColumn)
        .filter_by(data_table_id=table_id)
        .order_by(DataTableColumn.sort_order)
        .all()
    )


def ensure_columns_from_field_names(table_id: int, field_names: List[str]) -> List[DataTableColumn]:
    """
    Создать колонки для набора данных по списку имён полей (если ещё нет).
    Возвращает актуальный список колонок.
    """
    conn = Connection()
    existing = {c.field_name for c in get_columns(table_id)}
    for i, fn in enumerate(field_names):
        fn = (fn or "").strip()
        if not fn or fn in existing:
            continue
        col = DataTableColumn(
            data_table_id=table_id,
            field_name=fn,
            display_name=fn.replace("_", " ").title(),
            sort_order=i,
        )
        conn.session.add(col)
        existing.add(fn)
    conn.session.commit()
    return get_columns(table_id)


def list_records(table_id: int) -> List[DataRecord]:
    """Вернуть все записи набора данных."""
    conn = Connection()
    return (
        conn.session.query(DataRecord)
        .filter_by(data_table_id=table_id)
        .order_by(DataRecord.id)
        .all()
    )


def get_record_values(record_id: int) -> Dict[str, str]:
    """Вернуть словарь field_name -> value_text для записи."""
    conn = Connection()
    rows = (
        conn.session.query(DataRecordValue)
        .filter_by(data_record_id=record_id)
        .all()
    )
    return {r.field_name: r.value_text or "" for r in rows}


def get_record_with_values(record_id: int) -> Optional[Tuple[DataRecord, Dict[str, str]]]:
    """Вернуть (DataRecord, {field_name: value}) или None."""
    conn = Connection()
    record = conn.session.get(DataRecord, record_id)
    if not record:
        return None
    values = get_record_values(record_id)
    return record, values


def create_record(table_id: int, values: Dict[str, Any]) -> Optional[DataRecord]:
    """
    Создать новую запись в наборе данных с заданными значениями полей.
    values: {field_name: value} (value приводится к строке).
    """
    conn = Connection()
    table = conn.session.get(DataTable, table_id)
    if not table:
        return None
    record = DataRecord(data_table_id=table_id)
    conn.session.add(record)
    conn.session.flush()
    for fn, val in values.items():
        fn = (fn or "").strip()
        if not fn:
            continue
        v = DataRecordValue(data_record_id=record.id, field_name=fn, value_text=_to_str(val))
        conn.session.add(v)
    conn.session.commit()
    conn.session.refresh(record)
    return record


def update_record_values(record_id: int, values: Dict[str, Any]) -> bool:
    """
    Обновить значения полей записи. Переданные ключи перезаписываются;
    ключи, не переданные, не удаляются (для частичного обновления передайте все нужные поля).
    Если нужно заменить все значения — сначала удалить старые и вызвать с полным словарём.
    """
    conn = Connection()
    record = conn.session.get(DataRecord, record_id)
    if not record:
        return False
    existing = {v.field_name: v for v in record.values}
    for fn, val in values.items():
        fn = (fn or "").strip()
        if not fn:
            continue
        if fn in existing:
            existing[fn].value_text = _to_str(val)
        else:
            conn.session.add(DataRecordValue(data_record_id=record_id, field_name=fn, value_text=_to_str(val)))
    record.updated_at = datetime.utcnow()
    conn.session.commit()
    return True


def replace_record_values(record_id: int, values: Dict[str, Any]) -> bool:
    """Полностью заменить значения записи: удалить все старые, записать новые."""
    conn = Connection()
    record = conn.session.get(DataRecord, record_id)
    if not record:
        return False
    for v in list(record.values):
        conn.session.delete(v)
    conn.session.flush()
    for fn, val in values.items():
        fn = (fn or "").strip()
        if not fn:
            continue
        conn.session.add(DataRecordValue(data_record_id=record_id, field_name=fn, value_text=_to_str(val)))
    record.updated_at = datetime.utcnow()
    conn.session.commit()
    return True


def delete_record(record_id: int) -> bool:
    """Удалить запись и все её значения."""
    conn = Connection()
    record = conn.session.get(DataRecord, record_id)
    if not record:
        return False
    conn.session.delete(record)
    conn.session.commit()
    return True


def _to_str(val: Any) -> str:
    """Привести значение к строке для хранения."""
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val).strip()
