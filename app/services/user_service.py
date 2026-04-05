from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, User
from app.schemas import UserCreate, UserUpdate
from app.security import hash_password


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


def create_user(db: Session, data: UserCreate) -> User:
    if get_by_email(db, str(data.email)):
        raise ValueError("Email already registered")
    user = User(
        email=str(data.email).lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=Role(data.role.value),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = Role(data.role.value)
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user
