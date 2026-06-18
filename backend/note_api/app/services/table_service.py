from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from note_api.app.models import NoteTable, Part, TableCell
from note_api.app.schemas import (
    ResultResponse,
    TableCellItem,
    TableGetResponse,
    TableMutationResponse,
)
from note_api.app.table_engine import (
    DEFAULT_TEXT_ALIGN,
    CellData,
    TableData,
    adjust_formulas_for_col_delete,
    adjust_formulas_for_row_delete,
    rebuild_cell_map,
    recalculate_display_values,
    shift_cell_references,
    shift_cells_for_col_insert,
    shift_cells_for_row_insert,
    validate_cell_type,
    validate_display_format,
    validate_text_align,
)


def _fail(reason: str) -> ResultResponse:
    return ResultResponse(result=False, reason=reason)


def _ok() -> ResultResponse:
    return ResultResponse(result=True, reason=None)


def create_table_for_part(db: Session, aid: int) -> NoteTable:
    table = NoteTable(aid=aid, row_count=5, col_count=5)
    db.add(table)
    db.flush()
    return table


def validate_table_part_data(db: Session, aid: int, data: str) -> ResultResponse | None:
    if not data.strip().isdigit():
        return _fail("table パーツの data には table ID を指定してください")
    table_id = int(data.strip())
    table = db.scalar(
        select(NoteTable).where(NoteTable.id == table_id, NoteTable.aid == aid)
    )
    if table is None:
        return _fail("指定された表が見つかりません")
    return None


def _get_table_or_none(db: Session, aid: int, table_id: int) -> NoteTable | None:
    return db.scalar(
        select(NoteTable).where(NoteTable.id == table_id, NoteTable.aid == aid)
    )


def _load_table_data(db: Session, table: NoteTable) -> TableData:
    rows = db.scalars(select(TableCell).where(TableCell.table_id == table.id)).all()
    cells: dict[tuple[int, int], CellData] = {}
    for row in rows:
        cells[(row.x, row.y)] = CellData(
            x=row.x,
            y=row.y,
            cell_type=row.cell_type,
            input_value=row.input_value,
            display_format=row.display_format,
            display_value=row.display_value,
            text_align=row.text_align,
        )
    return TableData(row_count=table.row_count, col_count=table.col_count, cells=cells)


def _cells_to_items(cells: dict[tuple[int, int], CellData]) -> list[TableCellItem]:
    return [
        TableCellItem(
            x=cell.x,
            y=cell.y,
            cell_type=cell.cell_type,
            input_value=cell.input_value,
            display_format=cell.display_format,
            display_value=cell.display_value,
            text_align=cell.text_align,
        )
        for cell in sorted(cells.values(), key=lambda c: (c.y, c.x))
    ]


def _persist_table_data(db: Session, table_id: int, table_data: TableData) -> None:
    db.execute(delete(TableCell).where(TableCell.table_id == table_id))
    for cell in table_data.cells.values():
        db.add(
            TableCell(
                table_id=table_id,
                x=cell.x,
                y=cell.y,
                cell_type=cell.cell_type,
                input_value=cell.input_value,
                display_format=cell.display_format,
                display_value=cell.display_value,
                text_align=cell.text_align,
            )
        )


def _build_response(table: NoteTable, table_data: TableData) -> TableMutationResponse:
    return TableMutationResponse(
        table_id=table.id,
        title=table.title,
        row_count=table_data.row_count,
        col_count=table_data.col_count,
        cells=_cells_to_items(table_data.cells),
    )


def get_table(
    db: Session, aid: int, table_id: int
) -> TableGetResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")
    table_data = _load_table_data(db, table)
    return TableGetResponse(
        table_id=table.id,
        title=table.title,
        row_count=table_data.row_count,
        col_count=table_data.col_count,
        cells=_cells_to_items(table_data.cells),
    )


def update_table_title(
    db: Session, aid: int, table_id: int, title: str
) -> TableMutationResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")

    table.title = title
    table_data = _load_table_data(db, table)
    db.commit()
    return _build_response(table, table_data)


def update_table_cell(
    db: Session,
    aid: int,
    table_id: int,
    x: int,
    y: int,
    cell_type: str | None,
    input_value: str | None,
    display_format: str | None,
    text_align: str | None,
) -> TableMutationResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")
    if x < 1 or y < 1 or x > table.col_count or y > table.row_count:
        return _fail("セル位置が表の範囲外です")

    table_data = _load_table_data(db, table)
    key = (x, y)
    existing = table_data.cells.get(key)

    resolved_type = cell_type or (existing.cell_type if existing else "string")
    resolved_input = input_value if input_value is not None else (existing.input_value if existing else "")
    resolved_format = (
        display_format
        if display_format is not None
        else (existing.display_format if existing else "")
    )
    resolved_align = (
        text_align
        if text_align is not None
        else (existing.text_align if existing else DEFAULT_TEXT_ALIGN)
    )

    if not resolved_input.strip():
        if key in table_data.cells:
            del table_data.cells[key]
    else:
        if not validate_cell_type(resolved_type):
            return _fail("セル型が不正です")
        if not validate_display_format(resolved_type, resolved_format):
            return _fail("表示形式が不正です")
        if not validate_text_align(resolved_align):
            return _fail("表示位置が不正です")

        table_data.cells[key] = CellData(
            x=x,
            y=y,
            cell_type=resolved_type,
            input_value=resolved_input,
            display_format=resolved_format,
            text_align=resolved_align,
        )

    recalculate_display_values(table_data)
    _persist_table_data(db, table.id, table_data)
    db.commit()
    return _build_response(table, table_data)


def insert_table_row(
    db: Session, aid: int, table_id: int, at_row: int
) -> TableMutationResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")
    if at_row < 1 or at_row > table.row_count + 1:
        return _fail("行位置が不正です")

    table.row_count += 1
    table_data = _load_table_data(db, table)
    shift_cells_for_row_insert(table_data.cells, at_row)
    table_data.cells = rebuild_cell_map(table_data.cells)
    table_data.row_count = table.row_count
    recalculate_display_values(table_data)
    _persist_table_data(db, table.id, table_data)
    db.commit()
    return _build_response(table, table_data)


def delete_table_row(
    db: Session, aid: int, table_id: int, at_row: int
) -> TableMutationResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")
    if at_row < 1 or at_row > table.row_count:
        return _fail("行位置が不正です")
    if table.row_count <= 1:
        return _fail("これ以上行を削除できません")

    table.row_count -= 1
    table_data = _load_table_data(db, table)
    adjust_formulas_for_row_delete(table_data.cells, at_row)
    table_data.cells = rebuild_cell_map(table_data.cells)
    table_data.row_count = table.row_count
    recalculate_display_values(table_data)
    _persist_table_data(db, table.id, table_data)
    db.commit()
    return _build_response(table, table_data)


def insert_table_col(
    db: Session, aid: int, table_id: int, at_col: int
) -> TableMutationResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")
    if at_col < 1 or at_col > table.col_count + 1:
        return _fail("列位置が不正です")

    table.col_count += 1
    table_data = _load_table_data(db, table)
    shift_cells_for_col_insert(table_data.cells, at_col)
    table_data.cells = rebuild_cell_map(table_data.cells)
    table_data.col_count = table.col_count
    recalculate_display_values(table_data)
    _persist_table_data(db, table.id, table_data)
    db.commit()
    return _build_response(table, table_data)


def delete_table_col(
    db: Session, aid: int, table_id: int, at_col: int
) -> TableMutationResponse | ResultResponse:
    table = _get_table_or_none(db, aid, table_id)
    if table is None:
        return _fail("指定された表が見つかりません")
    if at_col < 1 or at_col > table.col_count:
        return _fail("列位置が不正です")
    if table.col_count <= 1:
        return _fail("これ以上列を削除できません")

    table.col_count -= 1
    table_data = _load_table_data(db, table)
    adjust_formulas_for_col_delete(table_data.cells, at_col)
    table_data.cells = rebuild_cell_map(table_data.cells)
    table_data.col_count = table.col_count
    recalculate_display_values(table_data)
    _persist_table_data(db, table.id, table_data)
    db.commit()
    return _build_response(table, table_data)


def paste_table_cell(
    db: Session,
    aid: int,
    table_id: int,
    x: int,
    y: int,
    source_input_value: str,
    source_cell_type: str,
    source_display_format: str,
    source_text_align: str,
    offset_x: int,
    offset_y: int,
) -> TableMutationResponse | ResultResponse:
    adjusted_input = shift_cell_references(source_input_value, offset_x, offset_y)
    return update_table_cell(
        db,
        aid,
        table_id,
        x,
        y,
        source_cell_type,
        adjusted_input,
        source_display_format,
        source_text_align,
    )


def delete_table_for_part(db: Session, aid: int, part: Part) -> None:
    if part.ptype != "table" or not part.data.strip().isdigit():
        return
    table_id = int(part.data.strip())
    table = _get_table_or_none(db, aid, table_id)
    if table is not None:
        db.delete(table)
