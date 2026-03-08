"""
Сервис загрузки шаблонов и извлечения полей.
"""
from pathlib import Path
from typing import List, Optional, Tuple, Union

from db.connection import Connection
from db.models import DataTable, DocumentTemplate, TemplateField, TemplateLoopBlock, TemplateLoopField
from core.template_parser import extract_variables_from_docx, extract_template_structure, validate_template_syntax
from logger import py_logger


def load_templates_list() -> List[DocumentTemplate]:
    """Вернуть список всех шаблонов из БД."""
    conn = Connection()
    return conn.session.query(DocumentTemplate).order_by(DocumentTemplate.name).all()


def get_template_by_id(template_id: int) -> Optional[DocumentTemplate]:
    """Вернуть шаблон по id или None."""
    conn = Connection()
    return conn.session.get(DocumentTemplate, template_id)


def get_template_linked_data_table(template_id: int) -> Optional[DataTable]:
    """Вернуть привязанный набор данных для шаблона или None."""
    conn = Connection()
    template = conn.session.get(DocumentTemplate, template_id)
    if not template or not template.linked_data_table_id:
        return None
    return conn.session.get(DataTable, template.linked_data_table_id)


def set_template_linked_data_table(template_id: int, data_table_id: Optional[int]) -> bool:
    """Установить или сбросить привязку шаблона к набору данных. Возвращает True при успехе."""
    conn = Connection()
    template = conn.session.get(DocumentTemplate, template_id)
    if not template:
        return False
    template.linked_data_table_id = data_table_id
    conn.session.commit()
    return True


def get_template_fields(template_id: int) -> List[TemplateField]:
    """Вернуть поля шаблона (активные, по sort_order)."""
    conn = Connection()
    return (
        conn.session.query(TemplateField)
        .filter_by(template_id=template_id, is_active=True)
        .order_by(TemplateField.sort_order)
        .all()
    )


def get_template_loop_blocks(template_id: int) -> List[TemplateLoopBlock]:
    conn = Connection()
    return (
        conn.session.query(TemplateLoopBlock)
        .filter_by(template_id=template_id)
        .order_by(TemplateLoopBlock.sort_order)
        .all()
    )


def parse_template_file(path: Union[str, Path]) -> Tuple[List[str], List[str]]:
    """Извлечь переменные из файла шаблона. Возвращает (имена переменных, ошибки)."""
    return extract_variables_from_docx(Path(path) if isinstance(path, str) else path)


def validate_template(path_or_stream) -> Tuple[bool, List[str]]:
    """Проверить синтаксис шаблона. Возвращает (ok, ошибки)."""
    return validate_template_syntax(path_or_stream)


def register_template(
    name: str,
    code: str,
    file_path: str,
    description: Optional[str] = None,
    sync_fields_from_file: bool = True,
) -> Tuple[Optional[DocumentTemplate], List[str]]:
    """
    Зарегистрировать новый шаблон в БД и при необходимости заполнить поля из файла.
    file_path: путь к .docx.
    Возвращает (шаблон, список ошибок).
    """
    errors: List[str] = []
    path = Path(file_path)
    if not path.exists():
        return None, [f"Файл не найден: {file_path}"]

    ok, errs = validate_template(path)
    if not ok:
        errors.extend(errs)
        return None, errors

    conn = Connection()
    existing = conn.session.query(DocumentTemplate).filter_by(code=code).first()
    if existing:
        return None, [f"Шаблон с кодом '{code}' уже существует."]

    template = DocumentTemplate(
        name=name,
        code=code,
        file_path=str(path.absolute()),
        store_in_db=False,
        description=description or "",
    )
    conn.session.add(template)
    conn.session.flush()

    if sync_fields_from_file:
        structure = extract_template_structure(path)
        errors.extend(structure.errors)
        for i, var in enumerate(structure.simple_fields):
            conn.session.add(TemplateField(
                template_id=template.id,
                field_name=var,
                display_name=var.replace("_", " ").title(),
                sort_order=i,
            ))
        for b_idx, lb in enumerate(structure.loop_blocks):
            block = TemplateLoopBlock(
                template_id=template.id,
                loop_var=lb.loop_var,
                item_var=lb.item_var,
                label=lb.loop_var,
                sort_order=b_idx,
            )
            conn.session.add(block)
            conn.session.flush()
            for f_idx, field_name in enumerate(lb.fields):
                conn.session.add(TemplateLoopField(
                    loop_block_id=block.id,
                    field_name=field_name,
                    display_name=field_name.replace("_", " ").title(),
                    sort_order=f_idx,
                ))
    conn.session.commit()
    conn.session.refresh(template)
    py_logger.info("Registered template id=%s code=%s", template.id, code)
    return template, errors
