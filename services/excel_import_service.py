"""
Импорт данных из Excel (.xlsx) в набор данных (data_tables).
Первая строка — заголовки (имена колонок), остальные — записи.
"""
from pathlib import Path
from typing import Any, Dict, List, Tuple

from db.connection import Connection
from db.models import DataRecord, DataRecordValue, DataTable, DataTableColumn
from logger import py_logger

from services.data_table_service import (
    ensure_columns_from_field_names,
    get_columns,
    get_data_table_by_id,
)


def _cell_to_str(cell: Any) -> str:
    """Привести ячейку к строке (числа, даты, None)."""
    if cell is None:
        return ""
    if hasattr(cell, "isoformat"):
        return cell.isoformat()
    if isinstance(cell, (int, float)):
        return str(int(cell)) if isinstance(cell, float) and cell == int(cell) else str(cell)
    return str(cell).strip()


def _normalize_header(header: str) -> str:
    """Нормализовать заголовок в field_name: пробелы -> подчёркивания, без лишних символов."""
    if not header:
        return ""
    s = header.strip().replace(" ", "_").replace("-", "_")
    return "".join(c for c in s if c.isalnum() or c == "_") or header.strip()


def read_excel_headers_and_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Прочитать активный лист Excel: первая строка — заголовки (нормализованные в field_name),
    остальные — строки как словари {field_name: value}.
    Пустые строки пропускаются.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    if ws is None:
        return [], []

    rows = [[_cell_to_str(c) for c in row] for row in ws.iter_rows(values_only=True)]
    if not rows:
        return [], []

    raw_headers = [h for h in rows[0]]
    headers = [_normalize_header(h) for h in raw_headers]
    # Не допускаем пустые имена колонок
    for i, h in enumerate(headers):
        if not h:
            headers[i] = f"col_{i}"

    data_rows: List[Dict[str, str]] = []
    for row in rows[1:]:
        if not row:
            continue
        # Пустая строка — все ячейки пустые
        if all(_cell_to_str(c) == "" for c in row):
            continue
        record = {}
        for col_idx, field_name in enumerate(headers):
            if col_idx < len(row):
                record[field_name] = _cell_to_str(row[col_idx])
            else:
                record[field_name] = ""
        data_rows.append(record)

    return headers, data_rows


def import_excel_into_data_table(
    table_id: int,
    path: Path,
    use_first_row_as_headers: bool = True,
) -> Tuple[int, int, List[str]]:
    """
    Импортировать Excel-файл в набор данных.

    - Если use_first_row_as_headers=True, первая строка — заголовки; колонки создаются/сопоставляются по ним.
    - Каждая следующая строка — новая запись (DataRecord + DataRecordValues).

    Возвращает (rows_created, rows_skipped, errors).
    """
    errors: List[str] = []
    table = get_data_table_by_id(table_id)
    if not table:
        return 0, 0, [f"Набор данных с id={table_id} не найден."]

    path = Path(path)
    if not path.exists():
        return 0, 0, [f"Файл не найден: {path}"]

    try:
        headers, data_rows = read_excel_headers_and_rows(path)
    except Exception as e:
        py_logger.exception("Excel read error: %s", e)
        return 0, 0, [f"Ошибка чтения файла: {e}"]

    if not headers and not data_rows:
        return 0, 0, ["В файле нет данных или заголовков."]

    conn = Connection()
    # Создать колонки по заголовкам, если их ещё нет
    ensure_columns_from_field_names(table_id, headers)

    rows_created = 0
    rows_skipped = 0

    for row_data in data_rows:
        if not row_data:
            rows_skipped += 1
            continue
        try:
            record = DataRecord(data_table_id=table_id)
            conn.session.add(record)
            conn.session.flush()
            for field_name, value in row_data.items():
                if not field_name:
                    continue
                conn.session.add(
                    DataRecordValue(
                        data_record_id=record.id,
                        field_name=field_name,
                        value_text=value or "",
                    )
                )
            rows_created += 1
        except Exception as e:
            rows_skipped += 1
            errors.append(f"Строка {rows_created + rows_skipped + 1}: {e}")
            py_logger.warning("Import row error: %s", e)

    try:
        conn.session.commit()
    except Exception as e:
        conn.session.rollback()
        py_logger.exception("Import commit error: %s", e)
        return rows_created, rows_skipped, errors + [f"Ошибка сохранения: {e}"]

    py_logger.info("Excel import: table_id=%s, created=%s, skipped=%s", table_id, rows_created, rows_skipped)
    return rows_created, rows_skipped, errors
