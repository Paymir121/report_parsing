"""
Модальное окно настроек приложения (интерфейс и БД).
Все значения хранятся в QSettings.
"""
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def _settings() -> QSettings:
    return QSettings()


class SettingsDialog(QDialog):
    """Диалог настроек: вкладки «Интерфейс» и «БД», сохранение в QSettings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_interface_tab(), "Интерфейс")
        self._tabs.addTab(self._build_database_tab(), "БД")
        layout.addWidget(self._tabs)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self._load_values()

    LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def _build_interface_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._log_expanded = QCheckBox("Раскрывать панель лога при запуске")
        self._log_expanded.setToolTip("Иначе панель лога будет свёрнута при старте")
        form.addRow(self._log_expanded)

        self._log_level = QComboBox()
        for lvl in self.LOG_LEVELS:
            self._log_level.addItem(lvl, lvl)
        self._log_level.setToolTip("Уровень детализации лога (DEBUG — максимум, CRITICAL — только критические ошибки)")
        form.addRow("Уровень логирования:", self._log_level)

        self._templates_dir = QLineEdit()
        self._templates_dir.setPlaceholderText("Пусто — без начальной папки")
        browse = QPushButton("Обзор…")
        browse.clicked.connect(self._browse_templates_dir)
        row_layout = QHBoxLayout()
        row_layout.addWidget(self._templates_dir)
        row_layout.addWidget(browse)
        form.addRow("Каталог шаблонов по умолчанию:", row_layout)

        return w

    def _build_database_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Изменения БД применяются после перезапуска приложения."))

        group = QGroupBox("Подключение")
        form = QFormLayout(group)
        self._db_driver = QComboBox()
        self._db_driver.addItem("SQLite", "sqlite")
        self._db_driver.addItem("PostgreSQL", "postgresql+psycopg2")
        self._db_driver.currentIndexChanged.connect(self._on_driver_changed)
        form.addRow("Тип БД:", self._db_driver)

        self._sqlite_path = QLineEdit()
        self._sqlite_path.setPlaceholderText("word_templates.db")
        row_sqlite = QHBoxLayout()
        row_sqlite.addWidget(self._sqlite_path)
        browse_db = QPushButton("Обзор…")
        browse_db.clicked.connect(self._browse_sqlite)
        row_sqlite.addWidget(browse_db)
        form.addRow("Файл SQLite:", row_sqlite)

        self._pg_host = QLineEdit()
        self._pg_host.setPlaceholderText("localhost")
        form.addRow("PostgreSQL — хост:", self._pg_host)
        self._pg_port = QSpinBox()
        self._pg_port.setRange(1, 65535)
        self._pg_port.setValue(5432)
        form.addRow("Порт:", self._pg_port)
        self._pg_database = QLineEdit()
        self._pg_database.setPlaceholderText("test_db")
        form.addRow("Имя БД:", self._pg_database)
        self._pg_user = QLineEdit()
        self._pg_user.setPlaceholderText("postgres")
        form.addRow("Пользователь:", self._pg_user)
        self._pg_password = QLineEdit()
        self._pg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._pg_password.setPlaceholderText("—")
        form.addRow("Пароль:", self._pg_password)

        self._db_sqlite_widgets = [self._sqlite_path]
        self._db_pg_widgets = [
            self._pg_host,
            self._pg_port,
            self._pg_database,
            self._pg_user,
            self._pg_password,
        ]
        layout.addWidget(group)
        return w

    def _on_driver_changed(self, index: int):
        is_sqlite = self._db_driver.currentData() == "sqlite"
        for w in self._db_sqlite_widgets:
            w.setEnabled(is_sqlite)
        for w in self._db_pg_widgets:
            w.setEnabled(not is_sqlite)

    def _browse_templates_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Каталог шаблонов по умолчанию")
        if path:
            self._templates_dir.setText(path)

    def _browse_sqlite(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Файл базы SQLite", "", "SQLite (*.db);;All (*.*)"
        )
        if path:
            self._sqlite_path.setText(path)

    def _load_values(self):
        s = _settings()
        # Интерфейс
        self._log_expanded.setChecked(
            s.value("Interface/LogExpandedAtStartup", False, type=bool)
        )
        log_level = s.value("Interface/LogLevel", "INFO", type=str)
        idx = self._log_level.findData(log_level)
        if idx >= 0:
            self._log_level.setCurrentIndex(idx)
        else:
            self._log_level.setCurrentIndex(self._log_level.findData("INFO"))
        self._templates_dir.setText(s.value("Interface/TemplatesDir", "", type=str))

        # БД
        drv = s.value("Database/Driver", "sqlite", type=str)
        idx = self._db_driver.findData(drv)
        if idx >= 0:
            self._db_driver.setCurrentIndex(idx)
        self._sqlite_path.setText(s.value("Database/SqlitePath", "word_templates.db", type=str))
        self._pg_host.setText(s.value("Database/PgHost", "localhost", type=str))
        self._pg_port.setValue(s.value("Database/PgPort", 5432, type=int))
        self._pg_database.setText(s.value("Database/PgDatabase", "test_db", type=str))
        self._pg_user.setText(s.value("Database/PgUser", "postgres", type=str))
        self._pg_password.setText(s.value("Database/PgPassword", "", type=str))
        self._on_driver_changed(self._db_driver.currentIndex())

    def _on_accept(self):
        s = _settings()
        s.setValue("Interface/LogExpandedAtStartup", self._log_expanded.isChecked())
        log_level = self._log_level.currentData() or "INFO"
        s.setValue("Interface/LogLevel", log_level)
        s.setValue("Interface/TemplatesDir", self._templates_dir.text().strip())
        _apply_log_level(log_level)
        s.setValue("Database/Driver", self._db_driver.currentData())
        s.setValue("Database/SqlitePath", self._sqlite_path.text().strip() or "word_templates.db")
        s.setValue("Database/PgHost", self._pg_host.text().strip() or "localhost")
        s.setValue("Database/PgPort", self._pg_port.value())
        s.setValue("Database/PgDatabase", self._pg_database.text().strip() or "test_db")
        s.setValue("Database/PgUser", self._pg_user.text().strip() or "postgres")
        s.setValue("Database/PgPassword", self._pg_password.text())
        s.sync()
        self.accept()


def get_settings_interface_log_expanded() -> bool:
    """Читает из QSettings: раскрывать ли панель лога при запуске."""
    return QSettings().value("Interface/LogExpandedAtStartup", False, type=bool)


def get_settings_interface_log_level() -> str:
    """Читает из QSettings уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
    return QSettings().value("Interface/LogLevel", "INFO", type=str) or "INFO"


def _apply_log_level(level: str) -> None:
    """Применить уровень логирования к глобальному логгеру (вызов после сохранения настроек)."""
    try:
        from logger import py_logger
        if hasattr(py_logger, "set_lvl_log"):
            py_logger.set_lvl_log(level)
    except Exception:
        pass


def apply_log_level_from_settings() -> None:
    """Прочитать уровень логирования из QSettings и применить при загрузке приложения."""
    level = get_settings_interface_log_level()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        level = "INFO"
    _apply_log_level(level)


def get_settings_interface_templates_dir() -> str:
    """Читает из QSettings: каталог шаблонов по умолчанию."""
    return QSettings().value("Interface/TemplatesDir", "", type=str) or ""
