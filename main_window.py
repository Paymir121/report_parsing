"""
Главное окно приложения Word-шаблонов.
Интерфейс загружается из .ui файла в рантайме (QUiLoader), без генерации в Python.
"""
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QFile, QIODevice, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from db.connection import Connection
from db.models import DocumentTemplate
from logger import py_logger
import settings as st
from services.template_service import load_templates_list, register_template, get_template_fields
from services.field_value_service import get_values_by_template_id
from services.generation_service import generate_document


class MainWindow(QMainWindow):
    _tables_combobox = None
    _data_tables = None
    _current_fields = None  # список (field_name, display_name) для строк таблицы
    _load_excel_btn = None

    def __init__(self, ui_file_name: str = "ui/main_window.ui", ui_loader=None):
        super().__init__()
        self._tables_combobox = None
        self._data_tables = None
        self._current_fields = []
        self._load_excel_btn = None
        loader = ui_loader if ui_loader is not None else QUiLoader()

        ui_path = Path(ui_file_name)
        if not ui_path.is_absolute():
            base = Path(__file__).resolve().parent
            ui_path = (base / ui_file_name).resolve()
        if not ui_path.exists():
            py_logger.warning("UI file not found: %s", ui_path)
            self.window = QWidget(self)
            self.setCentralWidget(self.window)
            self.setWindowTitle("Word-шаблоны")
            self._setup_stub_ui()
            self.connection = Connection()
            return

        ui_file = QFile(str(ui_path))
        if ui_file.open(QIODevice.ReadOnly):
            device = ui_file
        else:
            ui_file.close()
            try:
                data = ui_path.read_bytes()
            except OSError as e:
                py_logger.error("Cannot read UI file %s: %s", ui_path, e)
                sys.exit(-1)
            device = QBuffer(QByteArray(data))
            if not device.open(QIODevice.ReadOnly):
                py_logger.error("Cannot open UI buffer")
                sys.exit(-1)

        loaded = loader.load(device, None)
        if hasattr(device, "close"):
            device.close()

        if not loaded:
            py_logger.error("QUiLoader: %s", loader.errorString())
            sys.exit(-1)

        # Ссылку храним до изъятия виджетов, иначе C++ объект может быть удалён
        self._loaded_ui = loaded
        cw = loaded.centralWidget()
        mb = loaded.menuBar()
        sb = loaded.statusBar()
        self.setCentralWidget(cw)
        if mb is not None:
            self.setMenuBar(mb)
        if sb is not None:
            self.setStatusBar(sb)
        self.window = self.centralWidget()
        self.connection = Connection()
        self._bind_ui()
        self.setWindowTitle("Word-шаблоны")
        py_logger.info("MainWindow initialized (Word templates)")

    def _setup_stub_ui(self):
        """Минимальный UI, если .ui файл не найден."""
        from PySide6.QtWidgets import QLabel, QVBoxLayout
        layout = QVBoxLayout(self.window)
        layout.addWidget(QLabel("Файл ui/main_window.ui не найден.\nШаблоны: см. БД document_templates."))

    def _find(self, type_, name):
        """Виджет по имени в центральном виджете."""
        if self.window is None:
            return None
        return self.window.findChild(type_, name)

    def _bind_ui(self):
        """Привязка виджетов из загруженного .ui к логике."""
        self._tables_combobox = self._find(QComboBox, "tables_combobox")
        if self._tables_combobox is not None:
            self._refresh_templates_combo()
            self._tables_combobox.currentIndexChanged.connect(self._on_template_changed)

        add_file_btn = self._find(QPushButton, "add_file_pushbutton")
        if add_file_btn is not None:
            add_file_btn.clicked.connect(self._on_add_template)

        export_btn = self._find(QPushButton, "export_pushbutton")
        if export_btn is not None:
            export_btn.clicked.connect(self._on_generate)

        self._data_tables = self._find(QTableWidget, "data_tables")
        if self._data_tables is not None:
            self._data_tables.horizontalHeader().setStretchLastSection(True)

        self._load_excel_btn = self._find(QPushButton, "load_excel_pushbutton")
        if self._load_excel_btn is not None:
            self._load_excel_btn.clicked.connect(self._on_load_from_excel)

    def _on_load_from_excel(self):
        """Загрузить значения из Excel (колонки: имя поля, значение) и подставить в таблицу."""
        if not self._current_fields:
            QMessageBox.warning(
                self,
                "Загрузка из Excel",
                "Сначала выберите шаблон.",
            )
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл Excel",
            "",
            "Excel (*.xlsx *.xls);;All (*.*)",
        )
        if not path:
            return
        try:
            data = self._read_name_value_excel(path)
        except Exception as e:
            py_logger.error("Excel read: %s", e)
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось прочитать файл:\n{e}",
            )
            return
        if not data:
            QMessageBox.warning(
                self,
                "Загрузка из Excel",
                "В файле не найдено колонок «имя» и «значение» (или «name» и «value»).",
            )
            return
        self._apply_values_to_table(data)
        QMessageBox.information(
            self,
            "Загрузка из Excel",
            f"Подставлено значений: {len(data)}.",
        )

    def _cell_to_str(self, c) -> str:
        """Ячейка в строку (числа, даты, None)."""
        if c is None:
            return ""
        if hasattr(c, "isoformat"):
            return c.isoformat()
        if isinstance(c, (int, float)):
            return str(int(c)) if isinstance(c, float) and c == int(c) else str(c)
        return str(c).strip()

    def _read_name_value_excel(self, path: str) -> dict:
        """
        Прочитать Excel: две колонки — имя поля и значение.
        Поддерживаются заголовки: имя/name/поле, значение/value.
        Возвращает словарь {имя_поля: значение} (ключи в верхнем регистре).
        """
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        if ws is None:
            return {}
        rows = [[self._cell_to_str(c) for c in row] for row in ws.iter_rows(values_only=True)]
        if not rows:
            return {}
        first = [c.lower().strip() for c in rows[0] if c]
        name_col = value_col = None
        for col, header in enumerate(rows[0]):
            h = (header or "").strip().lower()
            if h in ("имя", "name", "поле", "field"):
                name_col = col
            elif h in ("значение", "value"):
                value_col = col
        has_header = name_col is not None and value_col is not None
        if name_col is None or value_col is None:
            name_col, value_col = 0, 1
        data = {}
        for row in rows[1:] if has_header and len(rows) > 1 else rows:
            if not row or name_col >= len(row):
                continue
            name = self._cell_to_str(row[name_col]).strip()
            if not name:
                continue
            value = self._cell_to_str(row[value_col]) if value_col < len(row) else ""
            data[name.upper()] = value
        return data

    def _apply_values_to_table(self, data: dict):
        """Подставить словарь data (имя_поля -> значение) в ячейки таблицы."""
        if self._data_tables is None or not self._current_fields:
            return
        # Сопоставление без учёта регистра: ключ в data уже upper(), ищем по field_name
        data_upper = {k.upper(): v for k, v in data.items()}
        applied = 0
        for row in range(self._data_tables.rowCount()):
            if row >= len(self._current_fields):
                break
            field_name, _ = self._current_fields[row]
            key = field_name.upper()
            value = data_upper.get(key) or data.get(field_name) or ""
            w = self._data_tables.cellWidget(row, 1)
            if w is None:
                continue
            if isinstance(w, QComboBox):
                idx = w.findData(value)
                if idx >= 0:
                    w.setCurrentIndex(idx)
                    applied += 1
                else:
                    idx = w.findText(value)
                    if idx >= 0:
                        w.setCurrentIndex(idx)
                        applied += 1
                    else:
                        w.setCurrentIndex(0)
            elif isinstance(w, QLineEdit):
                w.setText(value)
                applied += 1

    def _refresh_templates_combo(self):
        if self._tables_combobox is None:
            return
        self._tables_combobox.clear()
        self._tables_combobox.addItem(st.AUX.NOT_CHOOSED_ITEM)
        try:
            for t in load_templates_list():
                self._tables_combobox.addItem(t.name, t.id)
        except Exception as e:
            py_logger.error("Load templates: %s", e)

    def _on_template_changed(self, index: int):
        if index <= 0:
            self._current_fields = []
            if self._data_tables is not None:
                self._data_tables.setRowCount(0)
            if self._load_excel_btn is not None:
                self._load_excel_btn.setEnabled(False)
            return
        if self._tables_combobox is None:
            return
        template_id = self._tables_combobox.currentData()
        if template_id is None:
            return
        py_logger.info("Template selected: id=%s", template_id)
        self._fill_fields_table(template_id)
        if self._load_excel_btn is not None:
            self._load_excel_btn.setEnabled(True)

    def _fill_fields_table(self, template_id: int):
        """Заполнить таблицу полей и виджетами ввода/выбора значения."""
        if self._data_tables is None:
            return
        fields = get_template_fields(template_id)
        values_by_field = get_values_by_template_id(template_id)
        self._current_fields = [(f.field_name, f.display_name or f.field_name) for f in fields]
        self._data_tables.setRowCount(len(fields))
        for row, f in enumerate(fields):
            name_item = QTableWidgetItem(f.display_name or f.field_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self._data_tables.setItem(row, 0, name_item)
            field_values = values_by_field.get(f.id, [])
            if field_values:
                combo = QComboBox()
                combo.addItem(st.AUX.NOT_CHOOSED_ITEM, None)
                for v in field_values:
                    combo.addItem(v.value_text, v.value_text)
                default = next((v for v in field_values if v.is_default), None)
                if default:
                    combo.setCurrentIndex(combo.findData(default.value_text))
                else:
                    combo.setCurrentIndex(0)
                self._data_tables.setCellWidget(row, 1, combo)
            else:
                line = QLineEdit()
                if f.default_value:
                    line.setPlaceholderText(f.default_value)
                self._data_tables.setCellWidget(row, 1, line)

    def _on_add_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл шаблона .docx",
            st.DEFAULT_TEMPLATES_DIR or "",
            "Word (*.docx);;All (*.*)",
        )
        if not path:
            return
        path = Path(path)
        name = path.stem.replace("_", " ").strip() or "Шаблон"
        code = path.stem.replace(" ", "_").strip() or "template"
        template, errors = register_template(
            name=name,
            code=code,
            file_path=str(path),
            sync_fields_from_file=True,
        )
        if errors:
            QMessageBox.warning(self, "Ошибка загрузки шаблона", "\n".join(errors))
            return
        if template:
            self._refresh_templates_combo()
            QMessageBox.information(
                self,
                "Шаблон загружен",
                f"Добавлен шаблон «{template.name}» с полями из файла.",
            )

    def _on_generate(self):
        if self._tables_combobox is None:
            return
        template_id = self._tables_combobox.currentData()
        if template_id is None or self._tables_combobox.currentIndex() <= 0:
            QMessageBox.warning(
                self,
                "Генерация",
                "Выберите шаблон.",
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить документ",
            "",
            "Word (*.docx);;All (*.*)",
        )
        if not path:
            return
        if not path.lower().endswith(".docx"):
            path = path + ".docx"
        context = self._collect_context_from_table()
        try:
            generate_document(template_id, context, path)
            QMessageBox.information(
                self,
                "Генерация",
                f"Документ сохранён:\n{path}",
            )
        except Exception as e:
            py_logger.error("Generate: %s", e)
            QMessageBox.critical(
                self,
                "Ошибка",
                str(e),
            )

    def _collect_context_from_table(self) -> dict:
        """Собрать из таблицы полей словарь field_name -> value для подстановки в шаблон."""
        context = {}
        if self._data_tables is None or not self._current_fields:
            return context
        for row in range(self._data_tables.rowCount()):
            if row >= len(self._current_fields):
                break
            field_name, _ = self._current_fields[row]
            w = self._data_tables.cellWidget(row, 1)
            val = ""
            if w is not None:
                if isinstance(w, QComboBox):
                    v = w.currentData()
                    if v is not None:
                        val = v if isinstance(v, str) else str(v)
                elif isinstance(w, QLineEdit):
                    val = w.text().strip()
            context[field_name] = val
        return context
