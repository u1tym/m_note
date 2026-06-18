from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from note_api.app.database import Base

PARTS_TYPES = ("jpeg", "png", "text", "tex", "md", "binary", "url", "action", "table")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    session_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_access: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    random_number: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Folder(Base):
    __tablename__ = "folder"
    __table_args__ = (
        UniqueConstraint("aid", "parent", "deleted_number", "name", name="uq_note_folder_name"),
        UniqueConstraint("aid", "parent", "dorder", name="uq_note_folder_dorder"),
        {"schema": "note"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aid: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    parent: Mapped[int | None] = mapped_column(Integer, ForeignKey("note.folder.id"), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    dorder: Mapped[int] = mapped_column(Integer, nullable=False)
    deleted_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class File(Base):
    __tablename__ = "file"
    __table_args__ = (
        UniqueConstraint("aid", "belong", "deleted_number", "title", name="uq_note_file_title"),
        UniqueConstraint("aid", "belong", "dorder", name="uq_note_file_dorder"),
        {"schema": "note"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aid: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    belong: Mapped[int] = mapped_column(Integer, ForeignKey("note.folder.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    dorder: Mapped[int] = mapped_column(Integer, nullable=False)
    deleted_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Part(Base):
    __tablename__ = "parts"
    __table_args__ = (
        UniqueConstraint("aid", "file", "dorder", name="uq_note_parts_dorder"),
        {"schema": "note"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aid: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    file: Mapped[int] = mapped_column(Integer, ForeignKey("note.file.id"), nullable=False)
    dorder: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ptype: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False, default="")


class PartRevision(Base):
    __tablename__ = "parts_revision"
    __table_args__ = (
        UniqueConstraint("parts_id", "revision_number", name="uq_note_parts_revision_number"),
        {"schema": "note"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aid: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    parts_id: Mapped[int] = mapped_column(Integer, ForeignKey("note.parts.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ptype: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class NoteTable(Base):
    __tablename__ = "table"
    __table_args__ = {"schema": "note"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aid: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    col_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")


class TableCell(Base):
    __tablename__ = "table_cell"
    __table_args__ = (
        UniqueConstraint("table_id", "x", "y", name="uq_note_table_cell_position"),
        {"schema": "note"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("note.table.id", ondelete="CASCADE"), nullable=False
    )
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    cell_type: Mapped[str] = mapped_column(Text, nullable=False)
    input_value: Mapped[str] = mapped_column(Text, nullable=False)
    display_format: Mapped[str] = mapped_column(Text, nullable=False, default="")
    display_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text_align: Mapped[str] = mapped_column(Text, nullable=False, default="左寄せ")
