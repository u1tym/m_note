from fastapi import APIRouter, HTTPException

from note_api.app.deps import CurrentAid, DbSession
from note_api.app.schemas import (
    FileCreateRequest,
    FileGetRequest,
    FileGetResponse,
    FileIdRequest,
    FileMoveRequest,
    FileRenameRequest,
    FileSwapOrderRequest,
    ResultResponse,
)
from note_api.app.services import note_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/get", response_model=FileGetResponse)
def get_file(body: FileGetRequest, aid: CurrentAid, db: DbSession) -> FileGetResponse:
    result = note_service.get_file_detail(db, aid, body.file_id, body.include_deleted)
    if isinstance(result, ResultResponse):
        raise HTTPException(status_code=404, detail=result.reason)
    return result


@router.post("/create", response_model=ResultResponse)
def create_file(body: FileCreateRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.create_file(db, aid, body.folder_id, body.title)


@router.post("/delete", response_model=ResultResponse)
def delete_file(body: FileIdRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.delete_file(db, aid, body.file_id)


@router.post("/undelete", response_model=ResultResponse)
def undelete_file(body: FileIdRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.undelete_file(db, aid, body.file_id)


@router.post("/rename", response_model=ResultResponse)
def rename_file(body: FileRenameRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.rename_file(db, aid, body.file_id, body.name)


@router.post("/move", response_model=ResultResponse)
def move_file(body: FileMoveRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.move_file(
        db, aid, body.file_id, body.old_parent_id, body.new_parent_id
    )


@router.post("/swap-order", response_model=ResultResponse)
def swap_file_order(body: FileSwapOrderRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.swap_file_order(
        db, aid, body.parent_id, body.file_id_1, body.file_id_2
    )
