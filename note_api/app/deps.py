from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from note_api.app.config import get_settings
from note_api.app.database import get_db
from note_api.app.models import Account
from note_api.app.security.jwt_verifier import JWTVerifier

settings = get_settings()
jwt_verifier = JWTVerifier(
    secret_key=settings.secret_key,
    algorithm=settings.algorithm,
    cookie_name=settings.cookie_name,
)
require_jwt = jwt_verifier.dependency()


def get_current_aid(
    claims: Annotated[dict, Depends(require_jwt)],
    db: Annotated[Session, Depends(get_db)],
) -> int:
    username = jwt_verifier.get_username(claims)
    account = db.scalar(
        select(Account).where(Account.username == username, Account.is_deleted.is_(False))
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが見つかりません",
        )
    return account.id


CurrentAid = Annotated[int, Depends(get_current_aid)]
DbSession = Annotated[Session, Depends(get_db)]
