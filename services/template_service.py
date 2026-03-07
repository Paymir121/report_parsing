"""
Сервис загрузки шаблонов и извлечения полей.
"""
from pathlib import Path
from typing import List, Optional, Tuple, Union

from db.connection import Connection
from db.models import DocumentTemplate, TemplateField
from core.template_parser import extract_variables_from_docx, validate_template_syntax
from logger import py_logger


def load_templates_list() -> List[DocumentTemplate]:
    """Вернуть список всех шаблонов из БД."""
    conn = Connection()
    return conn.session.query(DocumentTemplate).order_by(DocumentTemplate.name).all()


def get_template_by_id(template_id: int) -> Optional[DocumentTemplate]:
    """Вернуть шаблон по id или None."""
    conn = Connection()
    return conn.session.get(DocumentTemplate, template_id)


def get_template_fields(template_id: int) -> List[TemplateField]:
    """Вернуть поля шаблона (активные, по sort_order)."""
    conn = Connection()
    return (
        conn.session.query(TemplateField)
        .filter_by(template_id=template_id, is_active=True)
        .order_by(TemplateField.sort_order)
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
        variable_names, parse_errors = extract_variables_from_docx(path)
        errors.extend(parse_errors)
        for i, var in enumerate(variable_names):
            f = TemplateField(
                template_id=template.id,
                field_name=var,
                display_name=var.replace("_", " ").title(),
                sort_order=i,
            )
            conn.session.add(f)
    conn.session.commit()
    conn.session.refresh(template)
    py_logger.info("Registered template id=%s code=%s", template.id, code)
    return template, errors
