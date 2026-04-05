from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoginRequest, Token
from app.security import create_access_token, verify_password
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    body: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    email = str(body.email).lower()
    user = user_service.get_by_email(db, email)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    token = create_access_token(str(user.id))
    return Token(access_token=token)
