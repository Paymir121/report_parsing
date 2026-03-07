"""
Создание тестовых Excel-файлов (имя поля / значение) для загрузки в приложение.
Формат: колонки «имя» и «значение» — для режима «Из Excel».

Запуск из корня проекта:
  python -m tests.create_sample_excel
  python tests/create_sample_excel.py
"""
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root))

import openpyxl
from openpyxl.styles import Font


def create_excel_file(path: Path, headers: tuple, rows: list) -> None:
    """Записать в path лист с заголовками и строками."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    if ws is None:
        return
    ws.title = "Данные"
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True)
    for r, row in enumerate(rows, 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    wb.save(str(path))
    print(f"Создан файл: {path}")


def main():
    root = Path(__file__).resolve().parent
    out_dir = root / "fixtures"

    # Договор: поля из contract_services
    create_excel_file(
        out_dir / "contract_services_values.xlsx",
        ("имя", "значение"),
        [
            ("CLIENT_NAME", "ООО Рога и копыта"),
            ("CONTRACT_NUMBER", "1"),
            ("CONTRACT_DATE", "2025-01-15"),
            ("CONTRACT_TYPE", "Разовый"),
            ("AMOUNT", "15000"),
        ],
    )

    # Акт: поля из act_works
    create_excel_file(
        out_dir / "act_works_values.xlsx",
        ("имя", "значение"),
        [
            ("ACT_NUMBER", "АКТ-001"),
            ("ACT_DATE", "2025-02-01"),
            ("CLIENT_NAME", "ООО Рога и копыта"),
            ("EXECUTOR_NAME", "ИП Исполнитель"),
            ("WORK_DESCRIPTION", "Консультационные услуги за январь 2025"),
        ],
    )

    print("Готово. В приложении: режим «Из Excel» → «Загрузить из Excel...» → выбрать файл из tests/fixtures/.")


if __name__ == "__main__":
    main()
