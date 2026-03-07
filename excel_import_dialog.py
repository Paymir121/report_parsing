"""
Диалог импорта данных из Excel в набор данных (БД).
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from logger import py_logger
from services.data_table_service import create_data_table, list_data_tables
from services.excel_import_service import import_excel_into_data_table


class ExcelImportDialog(QDialog):
    """Диалог: выбор набора данных, выбор файла .xlsx, импорт в БД."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Импорт из Excel в БД")
        self._layout = QVBoxLayout(self)

        form = QFormLayout()
        self._combo = QComboBox()
        self._combo.setMinimumWidth(280)
        form.addRow("Набор данных:", self._combo)

        btn_create = QPushButton("Создать новый набор…")
        btn_create.clicked.connect(self._on_create_table)
        form.addRow("", btn_create)

        self._file_btn = QPushButton("Выбрать файл .xlsx…")
        self._file_path: Path | None = None
        self._file_btn.clicked.connect(self._on_choose_file)
        form.addRow("Файл:", self._file_btn)

        self._layout.addLayout(form)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_import)
        self._buttons.rejected.connect(self.reject)
        self._layout.addWidget(self._buttons)

        self._refresh_combo()

    def _refresh_combo(self):
        self._combo.clear()
        self._combo.addItem("— выберите набор данных —", None)
        for t in list_data_tables():
            self._combo.addItem(f"{t.name} ({t.code})", t.id)

    def _on_create_table(self):
        name, ok = QInputDialog.getText(self, "Новый набор данных", "Название:")
        if not ok or not name.strip():
            return
        code = name.replace(" ", "_").lower()
        table, errs = create_data_table(name.strip(), code)
        if errs:
            QMessageBox.warning(self, "Ошибка", "\n".join(errs))
            return
        self._refresh_combo()
        idx = self._combo.findData(table.id)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        QMessageBox.information(self, "Готово", f"Создан набор данных «{table.name}».")

    def _on_choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл Excel",
            "",
            "Excel (*.xlsx *.xls);;All (*.*)",
        )
        if path:
            self._file_path = Path(path)
            self._file_btn.setText(self._file_path.name)

    def _on_import(self):
        table_id = self._combo.currentData()
        if table_id is None:
            QMessageBox.warning(
                self,
                "Импорт",
                "Выберите набор данных.",
            )
            return
        if not self._file_path or not self._file_path.exists():
            QMessageBox.warning(
                self,
                "Импорт",
                "Выберите файл Excel.",
            )
            return
        try:
            created, skipped, errors = import_excel_into_data_table(table_id, self._file_path)
        except Exception as e:
            py_logger.exception("Import: %s", e)
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        msg = f"Импортировано записей: {created}."
        if skipped:
            msg += f" Пропущено строк: {skipped}."
        if errors:
            msg += "\nОшибки:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n… и ещё {len(errors) - 10}."
        QMessageBox.information(self, "Импорт", msg)
        self.accept()
