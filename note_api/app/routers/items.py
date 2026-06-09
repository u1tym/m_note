from fastapi import APIRouter, HTTPException

from note_api.app.deps import CurrentAid, DbSession
from note_api.app.schemas import ItemsListRequest, ItemsListResponse, ResultResponse
from note_api.app.services import note_service

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/list", response_model=ItemsListResponse)
def list_items(
    body: ItemsListRequest,
    aid: CurrentAid,
    db: DbSession,
) -> ItemsListResponse:
    result = note_service.list_items(db, aid, body.folder_id, body.include_deleted)
    if isinstance(result, ResultResponse):
        raise HTTPException(status_code=400, detail=result.reason)
    return result
