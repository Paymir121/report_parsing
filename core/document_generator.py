"""
Генерация итогового .docx по шаблону и контексту через docxtpl.
"""
from pathlib import Path
from typing import Any, Dict, Union

from docxtpl import DocxTemplate

from logger import py_logger


def render_docx(
    template_path_or_bytes: Union[str, Path, bytes],
    context: Dict[str, Any],
    output_path: Union[str, Path],
) -> Path:
    """
    Загрузить шаблон, подставить context, сохранить в output_path.
    template_path_or_bytes: путь к .docx или байты содержимого.
    context: словарь имя_переменной -> значение (строка/число); для вложенных полей
             можно передать вложенные dict (например {"user": {"name": "Иван"}}).
    output_path: куда сохранить итоговый файл.
    Возвращает Path сохранённого файла.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(template_path_or_bytes, bytes):
        import io
        doc = DocxTemplate(io.BytesIO(template_path_or_bytes))
    else:
        doc = DocxTemplate(str(template_path_or_bytes))

    # Контекст только примитивы/вложенные dict — без объектов с методами
    safe_context = {k: _safe_value(v) for k, v in context.items()}
    doc.render(safe_context)
    doc.save(str(output_path))
    py_logger.info("Document saved: %s", output_path)
    return output_path


def _safe_value(v: Any) -> Any:
    """Привести значение к типу, безопасному для Jinja2 (без вызовов)."""
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {k: _safe_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_safe_value(item) for item in v]
    return str(v)
