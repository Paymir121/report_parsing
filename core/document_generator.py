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
        template_source = f"байты из БД ({len(template_path_or_bytes)} байт)"
        import io
        doc = DocxTemplate(io.BytesIO(template_path_or_bytes))
    else:
        template_source = str(template_path_or_bytes)
        doc = DocxTemplate(template_source)

    py_logger.info(
        "---------- render_docx: чтение шаблона ---------- Читается документ-шаблон: %s",
        template_source,
    )
    py_logger.info(
        "Вставляется в документ (файл результата): %s",
        output_path,
    )

    # Контекст: ключи — строки, значения — примитивы/вложенные dict/list (docxtpl/Jinja2)
    safe_context = {str(k): _safe_value(v) for k, v in context.items()}
    _log_fields_being_inserted(safe_context)

    doc.render(safe_context)

    # Проверка: какие переменные шаблона не были подставлены (остались в документе)
    try:
        undeclared = doc.get_undeclared_template_variables(context=safe_context)
        if undeclared:
            py_logger.warning(
                "render_docx: НЕ ПОДСТАВЛЕНЫ (переменные есть в шаблоне, но не в контексте): %s",
                sorted(undeclared),
            )
            py_logger.info(
                "Всего не подставлено переменных: %s",
                len(undeclared),
            )
        else:
            py_logger.info("render_docx: все переменные шаблона подставлены из контекста.")
    except Exception as e:
        py_logger.debug("render_docx: get_undeclared_template_variables: %s", e)

    doc.save(str(output_path))
    py_logger.info(
        "---------- render_docx: готово ---------- Документ сохранён: %s",
        output_path,
    )
    return output_path


def _log_fields_being_inserted(ctx: dict) -> None:
    """Подробно залогировать: какие поля с какими значениями вставляются в документ."""
    simple = {k: v for k, v in ctx.items() if not isinstance(v, (list, tuple))}
    loops = {k: v for k, v in ctx.items() if isinstance(v, (list, tuple))}
    py_logger.info(
        "Подставляемые поля (прочитано из контекста): простых=%s, циклов=%s",
        len(simple), len(loops),
    )
    for key, val in simple.items():
        py_logger.info("  Поле «%s» = %r", key, val)
    for key, rows in loops.items():
        py_logger.info("  Цикл «%s»: строк=%s", key, len(rows))
        for i, row in enumerate(rows):
            if isinstance(row, dict):
                py_logger.info("    [%s] %s", i + 1, row)
            else:
                py_logger.info("    [%s] %r", i + 1, row)


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
