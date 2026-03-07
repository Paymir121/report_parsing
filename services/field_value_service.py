"""
Сервис получения значений полей для шаблона (справочник field_values).
"""
from typing import Dict, List

from db.connection import Connection
from db.models import FieldValue, TemplateField


def get_values_by_template_id(template_id: int) -> Dict[int, List[FieldValue]]:
    """
    Вернуть для каждого поля шаблона список вариантов значений.
    Ключ — field_id, значение — список FieldValue (по sort_order).
    """
    conn = Connection()
    fields = (
        conn.session.query(TemplateField)
        .filter_by(template_id=template_id, is_active=True)
        .order_by(TemplateField.sort_order)
        .all()
    )
    result: Dict[int, List[FieldValue]] = {}
    for f in fields:
        values = (
            conn.session.query(FieldValue)
            .filter_by(field_id=f.id)
            .order_by(FieldValue.sort_order)
            .all()
        )
        result[f.id] = list(values)
    return result


def get_values_by_field_ids(field_ids: List[int]) -> Dict[int, List[FieldValue]]:
    """Вернуть варианты значений по списку field_id."""
    conn = Connection()
    result: Dict[int, List[FieldValue]] = {fid: [] for fid in field_ids}
    rows = (
        conn.session.query(FieldValue)
        .filter(FieldValue.field_id.in_(field_ids))
        .order_by(FieldValue.sort_order)
        .all()
    )
    for r in rows:
        result[r.field_id].append(r)
    return result
