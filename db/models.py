"""
Модели БД для приложения Word-шаблонов (Jinja2).
Таблицы: document_templates, template_versions, template_fields, field_values,
data_tables, data_table_columns, data_records, data_record_values, generation_history.
"""
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    file_path = Column(String(1024))
    file_content = Column(LargeBinary)
    store_in_db = Column(Boolean, nullable=False, default=False)
    linked_data_table_id = Column(
        Integer,
        ForeignKey("data_tables.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan", order_by="TemplateField.sort_order")
    generation_history = relationship("GenerationHistory", back_populates="template", passive_deletes=True)
    linked_data_table = relationship("DataTable", back_populates="templates_linked", foreign_keys=[linked_data_table_id])


class TemplateVersion(Base):
    __tablename__ = "template_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("document_templates.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(1024))
    file_content = Column(LargeBinary)
    store_in_db = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    template = relationship("DocumentTemplate", back_populates="versions")

    __table_args__ = (UniqueConstraint("template_id", "version_number", name="uq_template_version"),)


class TemplateField(Base):
    __tablename__ = "template_fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("document_templates.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    field_type = Column(String(50), nullable=False, default="text")
    is_required = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    default_value = Column(Text)
    help_text = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    template = relationship("DocumentTemplate", back_populates="fields")
    values = relationship("FieldValue", back_populates="field", cascade="all, delete-orphan", order_by="FieldValue.sort_order")

    __table_args__ = (UniqueConstraint("template_id", "field_name", name="uq_template_field"),)


class FieldValue(Base):
    __tablename__ = "field_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("template_fields.id", ondelete="CASCADE"), nullable=False)
    value_text = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    field = relationship("TemplateField", back_populates="values")


class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        Integer,
        ForeignKey("document_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    generated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    output_path = Column(String(1024))
    context_snapshot = Column(JSON)  # SQLite и PostgreSQL
    created_by = Column(String(255))

    template = relationship("DocumentTemplate", back_populates="generation_history")


# --- Наборы данных (таблицы/справочники) для импорта из Excel и ручного ввода ---


class DataTable(Base):
    """Набор данных (справочник): например «Клиенты», «Договоры»."""
    __tablename__ = "data_tables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    columns = relationship("DataTableColumn", back_populates="data_table", cascade="all, delete-orphan", order_by="DataTableColumn.sort_order")
    records = relationship("DataRecord", back_populates="data_table", cascade="all, delete-orphan")
    templates_linked = relationship("DocumentTemplate", back_populates="linked_data_table", foreign_keys="DocumentTemplate.linked_data_table_id")


class DataTableColumn(Base):
    """Колонка набора данных: имя поля и отображаемое имя (для маппинга с Excel и UI)."""
    __tablename__ = "data_table_columns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_table_id = Column(Integer, ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    sort_order = Column(Integer, nullable=False, default=0)

    data_table = relationship("DataTable", back_populates="columns")

    __table_args__ = (UniqueConstraint("data_table_id", "field_name", name="uq_data_table_column"),)


class DataRecord(Base):
    """Одна запись в наборе данных (одна строка: клиент, договор и т.д.)."""
    __tablename__ = "data_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_table_id = Column(Integer, ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    data_table = relationship("DataTable", back_populates="records")
    values = relationship("DataRecordValue", back_populates="data_record", cascade="all, delete-orphan")


class DataRecordValue(Base):
    """Значение одного поля записи: field_name -> value_text."""
    __tablename__ = "data_record_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_record_id = Column(Integer, ForeignKey("data_records.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(255), nullable=False)
    value_text = Column(Text, default="")

    data_record = relationship("DataRecord", back_populates="values")

    __table_args__ = (UniqueConstraint("data_record_id", "field_name", name="uq_data_record_value"),)


def create_all_tables(engine):
    """Создать все таблицы в БД."""
    Base.metadata.create_all(bind=engine)
    _ensure_linked_data_table_column(engine)


def _ensure_linked_data_table_column(engine):
    """
    Миграция для существующих БД: добавить колонку linked_data_table_id
    в document_templates, если её нет.
    """
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "document_templates" not in insp.get_table_names():
        return
    cols = [c["name"] for c in insp.get_columns("document_templates")]
    if "linked_data_table_id" in cols:
        return
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE document_templates ADD COLUMN linked_data_table_id INTEGER"))
        conn.commit()
