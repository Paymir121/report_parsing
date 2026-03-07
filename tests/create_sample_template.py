"""
Создание тестового Word-шаблона .docx с плейсхолдерами Jinja2.
Поля совпадают с тестовыми данными из init_db (Договор оказания услуг).

Запуск из корня проекта:
  python -m tests.create_sample_template
  python tests/create_sample_template.py
"""
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root))

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def create_contract_template(output_path: Path) -> None:
    """Шаблон «Договор оказания услуг» — поля: CLIENT_NAME, CONTRACT_NUMBER, CONTRACT_DATE, CONTRACT_TYPE, AMOUNT."""
    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(12)
    style.font.name = "Times New Roman"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("ДОГОВОР ОКАЗАНИЯ УСЛУГ")
    run.bold = True
    run.font.size = Pt(14)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("№ ")
    p.add_run("{{ CONTRACT_NUMBER }}")
    p.add_run(" от ")
    p.add_run("{{ CONTRACT_DATE }}")
    p.add_run(" г.")

    doc.add_paragraph()
    doc.add_paragraph(
        "Настоящий договор заключён между Исполнителем и Заказчиком в лице "
        "{{ CLIENT_NAME }}, именуемым в дальнейшем «Заказчик»."
    )
    doc.add_paragraph()
    doc.add_paragraph("Тип договора: {{ CONTRACT_TYPE }}.")
    doc.add_paragraph("Сумма договора: {{ AMOUNT }} руб.")
    doc.add_paragraph()
    doc.add_paragraph("Подписи сторон: _______________________  _______________________")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Создан шаблон: {output_path}")


def create_act_template(output_path: Path) -> None:
    """Шаблон «Акт выполненных работ» — поля: ACT_NUMBER, ACT_DATE, CLIENT_NAME, EXECUTOR_NAME, WORK_DESCRIPTION."""
    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(12)
    style.font.name = "Times New Roman"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("АКТ ВЫПОЛНЕННЫХ РАБОТ")
    run.bold = True
    run.font.size = Pt(14)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("№ ")
    p.add_run("{{ ACT_NUMBER }}")
    p.add_run(" от ")
    p.add_run("{{ ACT_DATE }}")

    doc.add_paragraph()
    doc.add_paragraph("Заказчик: {{ CLIENT_NAME }}")
    doc.add_paragraph("Исполнитель: {{ EXECUTOR_NAME }}")
    doc.add_paragraph()
    doc.add_paragraph("Описание выполненных работ: {{ WORK_DESCRIPTION }}")
    doc.add_paragraph()
    doc.add_paragraph("Подписи: _______________________  _______________________")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Создан шаблон: {output_path}")


def main():
    # Каталог tests/fixtures рядом со скриптом
    root = Path(__file__).resolve().parent
    out_dir = root / "fixtures"
    create_contract_template(out_dir / "contract_services.docx")
    create_act_template(out_dir / "act_works.docx")
    print("Готово. Файлы в каталоге tests/fixtures/")
    print("В приложении: «Загрузить шаблон...» → указать один из этих файлов.")


if __name__ == "__main__":
    main()
