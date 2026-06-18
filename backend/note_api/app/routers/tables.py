from fastapi import APIRouter, HTTPException

from note_api.app.deps import CurrentAid, DbSession
from note_api.app.schemas import (
    ResultResponse,
    TableCellUpdateRequest,
    TableColDeleteRequest,
    TableColInsertRequest,
    TableGetRequest,
    TableGetResponse,
    TableMutationResponse,
    TablePasteCellRequest,
    TableRowDeleteRequest,
    TableRowInsertRequest,
    TableTitleUpdateRequest,
)
from note_api.app.services import table_service

router = APIRouter(prefix="/table", tags=["table"])


def _raise_if_failed(result: ResultResponse) -> None:
    if not result.result:
        raise HTTPException(status_code=400, detail=result.reason)


@router.post("/get", response_model=TableGetResponse)
def get_table(body: TableGetRequest, aid: CurrentAid, db: DbSession) -> TableGetResponse:
    result = table_service.get_table(db, aid, body.table_id)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/title/update", response_model=TableMutationResponse)
def update_table_title(
    body: TableTitleUpdateRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.update_table_title(db, aid, body.table_id, body.title)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/cells/update", response_model=TableMutationResponse)
def update_table_cell(
    body: TableCellUpdateRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.update_table_cell(
        db,
        aid,
        body.table_id,
        body.x,
        body.y,
        body.cell_type,
        body.input_value,
        body.display_format,
        body.text_align,
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/cells/paste", response_model=TableMutationResponse)
def paste_table_cell(
    body: TablePasteCellRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.paste_table_cell(
        db,
        aid,
        body.table_id,
        body.x,
        body.y,
        body.source_input_value,
        body.source_cell_type,
        body.source_display_format,
        body.source_text_align,
        body.offset_x,
        body.offset_y,
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/rows/insert", response_model=TableMutationResponse)
def insert_table_row(
    body: TableRowInsertRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.insert_table_row(db, aid, body.table_id, body.at_row)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/rows/delete", response_model=TableMutationResponse)
def delete_table_row(
    body: TableRowDeleteRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.delete_table_row(db, aid, body.table_id, body.at_row)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/cols/insert", response_model=TableMutationResponse)
def insert_table_col(
    body: TableColInsertRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.insert_table_col(db, aid, body.table_id, body.at_col)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/cols/delete", response_model=TableMutationResponse)
def delete_table_col(
    body: TableColDeleteRequest, aid: CurrentAid, db: DbSession
) -> TableMutationResponse:
    result = table_service.delete_table_col(db, aid, body.table_id, body.at_col)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result
