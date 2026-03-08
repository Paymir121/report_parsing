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
        py_logger.info("Template content: id=%s, source=db (bytes, len=%s)", template.id, len(template.file_content or b""))
        return template.file_content
    if template.file_path and Path(template.file_path).exists():
        py_logger.info("Template content: id=%s, source=file path=%s", template.id, template.file_path)
        return Path(template.file_path)
    py_logger.error("Template unavailable: id=%s, file_path=%s, store_in_db=%s", template.id, template.file_path, template.store_in_db)
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

    # Подробное логирование для отладки вставки полей
    _log_generation_start(template_id, template, content, output_path, context)

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


def _log_generation_start(
    template_id: int,
    template: DocumentTemplate,
    content: Union[bytes, Path],
    output_path: Path,
    context: Dict[str, Any],
) -> None:
    """Логировать: какой шаблон читается, куда сохраняется, сколько полей передаётся."""
    if isinstance(content, Path):
        doc_read_from = str(content)
        doc_read_kind = "файл"
    else:
        doc_read_from = f"БД (байты, {len(content)} байт)"
        doc_read_kind = "БД"
    py_logger.info(
        "========== Генерация документа ========== Читается шаблон: id=%s, name=%s, code=%s | источник: %s",
        template_id, template.name, template.code, doc_read_from,
    )
    py_logger.info("Шаблон загружен из: %s", doc_read_kind)
    py_logger.info("Результат будет сохранён в документ: %s", output_path)

    simple = {k: v for k, v in context.items() if not isinstance(v, (list, tuple))}
    loops = {k: v for k, v in context.items() if isinstance(v, (list, tuple))}
    py_logger.info(
        "Передано полей в контекст: %s простых, %s циклов (всего ключей: %s)",
        len(simple), len(loops), len(context),
    )
    for key, val in simple.items():
        py_logger.info("  [поле] %s = %r", key, val)
    for key, rows in loops.items():
        py_logger.info("  [цикл] %s: строк=%s", key, len(rows))
        for i, row in enumerate(rows):
            py_logger.info("    строка %s: %s", i + 1, row)
