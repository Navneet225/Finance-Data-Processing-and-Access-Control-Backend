import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Role, User
from app.security import hash_password


def seed_initial_admin() -> None:
    """Create a default admin if the database has no users (local dev convenience)."""
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").lower()
    password = os.getenv("SEED_ADMIN_PASSWORD", "Admin12345!")
    db = SessionLocal()
    try:
        if db.scalars(select(User).limit(1)).first():
            return
        user = User(
            email=email,
            full_name="System Admin",
            hashed_password=hash_password(password),
            role=Role.admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
