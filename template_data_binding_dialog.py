"""
Диалог привязки шаблона к набору данных (для выбора записей при генерации).
"""
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QVBoxLayout,
)

from services.data_table_service import list_data_tables
from services.template_service import get_template_by_id, load_templates_list, set_template_linked_data_table


class TemplateDataBindingDialog(QDialog):
    """Выбор шаблона и набора данных для привязки."""

    def __init__(self, parent=None, initial_template_id: int | None = None):
        super().__init__(parent)
        self.setWindowTitle("Привязать шаблон к набору данных")
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._template_combo = QComboBox()
        self._template_combo.setMinimumWidth(280)
        form.addRow("Шаблон:", self._template_combo)
        for t in load_templates_list():
            self._template_combo.addItem(t.name, t.id)
        if initial_template_id is not None:
            idx = self._template_combo.findData(initial_template_id)
            if idx >= 0:
                self._template_combo.setCurrentIndex(idx)

        self._table_combo = QComboBox()
        self._table_combo.setMinimumWidth(280)
        self._table_combo.addItem("— не привязывать —", None)
        for dt in list_data_tables():
            self._table_combo.addItem(f"{dt.name} ({dt.code})", dt.id)
        form.addRow("Набор данных:", self._table_combo)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        template_id = self._template_combo.currentData()
        if template_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон.")
            return
        data_table_id = self._table_combo.currentData()
        ok = set_template_linked_data_table(template_id, data_table_id)
        if not ok:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить привязку.")
            return
        template = get_template_by_id(template_id)
        table_name = "не привязан"
        if data_table_id is not None:
            for dt in list_data_tables():
                if dt.id == data_table_id:
                    table_name = dt.name
                    break
        QMessageBox.information(
            self,
            "Готово",
            f"Шаблон «{template.name if template else template_id}» привязан к набору данных: {table_name}.",
        )
        self.accept()
