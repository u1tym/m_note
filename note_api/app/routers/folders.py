from fastapi import APIRouter

from note_api.app.deps import CurrentAid, DbSession
from note_api.app.schemas import (
    FolderCreateRequest,
    FolderIdRequest,
    FolderMoveRequest,
    FolderRenameRequest,
    FolderSwapOrderRequest,
    ResultResponse,
)
from note_api.app.services import note_service

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("/create", response_model=ResultResponse)
def create_folder(body: FolderCreateRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.create_folder(db, aid, body.parent_id, body.name)


@router.post("/delete", response_model=ResultResponse)
def delete_folder(body: FolderIdRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.delete_folder(db, aid, body.folder_id)


@router.post("/undelete", response_model=ResultResponse)
def undelete_folder(body: FolderIdRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.undelete_folder(db, aid, body.folder_id)


@router.post("/rename", response_model=ResultResponse)
def rename_folder(body: FolderRenameRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.rename_folder(db, aid, body.folder_id, body.name)


@router.post("/move", response_model=ResultResponse)
def move_folder(body: FolderMoveRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.move_folder(
        db, aid, body.folder_id, body.old_parent_id, body.new_parent_id
    )


@router.post("/swap-order", response_model=ResultResponse)
def swap_folder_order(
    body: FolderSwapOrderRequest,
    aid: CurrentAid,
    db: DbSession,
) -> ResultResponse:
    return note_service.swap_folder_order(
        db, aid, body.parent_id, body.folder_id_1, body.folder_id_2
    )
