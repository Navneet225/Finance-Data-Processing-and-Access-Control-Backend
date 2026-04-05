from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import Role, User
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

AdminUser = Annotated[User, Depends(require_roles(Role.admin))]


@router.get("", response_model=list[UserResponse])
def list_users(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> list[UserResponse]:
    return user_service.list_users(db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(_: AdminUser, db: Annotated[Session, Depends(get_db)], body: UserCreate) -> UserResponse:
    try:
        return user_service.create_user(db, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    _: AdminUser,
    db: Annotated[Session, Depends(get_db)],
    user_id: int,
    body: UserUpdate,
) -> UserResponse:
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.role is None and body.is_active is None and body.full_name is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )
    return user_service.update_user(db, user, body)
