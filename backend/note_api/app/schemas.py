from typing import Literal

from pydantic import BaseModel, Field

PartsType = Literal["jpeg", "png", "text", "tex", "md", "binary", "url", "action", "table"]


class ResultResponse(BaseModel):
    result: bool
    reason: str | None = None


# --- A-1 ---
class ItemsListRequest(BaseModel):
    folder_id: int | None
    include_deleted: bool


class ParentInfo(BaseModel):
    id: int | None
    name: str | None


class FolderItem(BaseModel):
    id: int
    dorder: int
    name: str
    is_del: bool


class FileItem(BaseModel):
    id: int
    dorder: int
    title: str
    is_del: bool


class ItemsListResponse(BaseModel):
    parent: ParentInfo
    folder: list[FolderItem]
    file: list[FileItem]


# --- A-2 ---
class FileGetRequest(BaseModel):
    file_id: int
    include_deleted: bool = False


class BelongInfo(BaseModel):
    id: int
    name: str


class PartInfo(BaseModel):
    id: int
    dorder: int
    ptype: str
    data: str
    filename: str
    title: str
    is_del: bool
    revisions: list["PartRevisionSummary"] = []


class PartRevisionSummary(BaseModel):
    id: int
    revision_number: int
    filename: str
    ptype: str
    created_at: str


class PartRevisionGetRequest(BaseModel):
    revision_id: int


class PartRevisionGetResponse(BaseModel):
    id: int
    parts_id: int
    revision_number: int
    filename: str
    ptype: str
    data: str
    created_at: str


class FileGetResponse(BaseModel):
    id: int
    belong: BelongInfo
    title: str
    parts: list[PartInfo]


# --- B ---
class FolderCreateRequest(BaseModel):
    parent_id: int | None
    name: str


class FolderIdRequest(BaseModel):
    folder_id: int


class FolderRenameRequest(BaseModel):
    folder_id: int
    name: str


class FolderMoveRequest(BaseModel):
    folder_id: int
    old_parent_id: int | None
    new_parent_id: int | None


class FolderSwapOrderRequest(BaseModel):
    parent_id: int | None
    folder_id_1: int
    folder_id_2: int


# --- C ---
class FileCreateRequest(BaseModel):
    folder_id: int
    title: str


class FileIdRequest(BaseModel):
    file_id: int


class FileRenameRequest(BaseModel):
    file_id: int
    name: str


class FileMoveRequest(BaseModel):
    file_id: int
    old_parent_id: int
    new_parent_id: int


class FileSwapOrderRequest(BaseModel):
    parent_id: int
    file_id_1: int
    file_id_2: int


# --- D ---
class PartCreateRequest(BaseModel):
    file_id: int
    ptype: PartsType = Field(alias="type")
    data: str
    filename: str = ""
    title: str = ""

    model_config = {"populate_by_name": True}


class PartIdRequest(BaseModel):
    parts_id: int


class PartUpdateRequest(BaseModel):
    parts_id: int
    ptype: PartsType = Field(alias="type")
    data: str
    filename: str | None = None
    title: str | None = None

    model_config = {"populate_by_name": True}


class PartSwapOrderRequest(BaseModel):
    file_id: int
    parts_id_1: int
    parts_id_2: int


# --- Table ---
class TableGetRequest(BaseModel):
    table_id: int


class TableCellItem(BaseModel):
    x: int
    y: int
    cell_type: str
    input_value: str
    display_format: str
    display_value: str
    text_align: str


class TableColWidthItem(BaseModel):
    x: int
    width_px: int


class TableGetResponse(BaseModel):
    table_id: int
    title: str
    row_count: int
    col_count: int
    col_widths: list[TableColWidthItem]
    cells: list[TableCellItem]


class TableMutationResponse(BaseModel):
    table_id: int
    title: str
    row_count: int
    col_count: int
    col_widths: list[TableColWidthItem]
    cells: list[TableCellItem]


class TableCellUpdateRequest(BaseModel):
    table_id: int
    x: int
    y: int
    cell_type: str | None = None
    input_value: str | None = None
    display_format: str | None = None
    text_align: str | None = None


class TablePasteCellRequest(BaseModel):
    table_id: int
    x: int
    y: int
    source_input_value: str
    source_cell_type: str
    source_display_format: str
    source_text_align: str = "左寄せ"
    offset_x: int = 0
    offset_y: int = 0


class TableRowInsertRequest(BaseModel):
    table_id: int
    at_row: int


class TableRowDeleteRequest(BaseModel):
    table_id: int
    at_row: int


class TableColInsertRequest(BaseModel):
    table_id: int
    at_col: int


class TableColDeleteRequest(BaseModel):
    table_id: int
    at_col: int


class TableTitleUpdateRequest(BaseModel):
    table_id: int
    title: str


class TableColWidthUpdateRequest(BaseModel):
    table_id: int
    x: int
    width_px: int | None = None
