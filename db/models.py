"""
Модели БД для приложения Word-шаблонов (Jinja2).
Таблицы: document_templates, template_versions, template_fields, field_values, generation_history.
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
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan", order_by="TemplateField.sort_order")
    generation_history = relationship("GenerationHistory", back_populates="template", passive_deletes=True)


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


def create_all_tables(engine):
    """Создать все таблицы в БД."""
    Base.metadata.create_all(bind=engine)
