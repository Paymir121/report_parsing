"""
Сервис генерации документа по шаблону и контексту, запись в историю.
"""
from pathlib import Path
from typing import Any, Dict, Optional, Union

from db.connection import Connection
from db.models import DocumentTemplate, GenerationHistory
from core.document_generator import render_docx
from logger import py_logger


def get_template_content(template: DocumentTemplate) -> Union[bytes, Path]:
    """Вернуть содержимое шаблона: путь к файлу или байты из БД."""
    if template.store_in_db and template.file_content:
        return template.file_content
    if template.file_path and Path(template.file_path).exists():
        return Path(template.file_path)
    raise FileNotFoundError(f"Шаблон недоступен: id={template.id}")


def generate_document(
    template_id: int,
    context: Dict[str, Any],
    output_path: Union[str, Path],
    created_by: Optional[str] = None,
) -> Path:
    """
    Сгенерировать документ по шаблону и контексту, сохранить и записать в историю.
    context: словарь имя_поля -> значение (как в шаблоне).
    Возвращает Path сохранённого файла.
    """
    conn = Connection()
    template = conn.session.get(DocumentTemplate, template_id)
    if not template:
        raise ValueError(f"Шаблон не найден: id={template_id}")

    content = get_template_content(template)
    output_path = Path(output_path)
    render_docx(content, context, output_path)

    history = GenerationHistory(
        template_id=template_id,
        output_path=str(output_path),
        context_snapshot=context,
        created_by=created_by,
    )
    conn.session.add(history)
    conn.session.commit()
    py_logger.info("Generated doc: %s (history id=%s)", output_path, history.id)
    return output_path
