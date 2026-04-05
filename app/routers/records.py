from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import EntryType, Role, User
from app.schemas import EntryTypeEnum, FinancialRecordCreate, FinancialRecordResponse, FinancialRecordUpdate, PaginatedRecords
from app.services import record_service

router = APIRouter(prefix="/records", tags=["records"])

AnalystOrAdmin = Annotated[User, Depends(require_roles(Role.analyst, Role.admin))]
AdminOnly = Annotated[User, Depends(require_roles(Role.admin))]


@router.get("", response_model=PaginatedRecords)
def list_records(
    _: AnalystOrAdmin,
    db: Annotated[Session, Depends(get_db)],
    date_from: date | None = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="Inclusive end date (YYYY-MM-DD)"),
    category: str | None = Query(None),
    record_type: EntryTypeEnum | None = Query(None, alias="type"),
    q: str | None = Query(None, description="Search notes and category (case-insensitive)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedRecords:
    et: EntryType | None = EntryType(record_type.value) if record_type else None
    items, total = record_service.list_records(
        db,
        date_from=date_from,
        date_to=date_to,
        category=category,
        entry_type=et,
        search=q,
        page=page,
        page_size=page_size,
    )
    return PaginatedRecords(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    user: AdminOnly,
    db: Annotated[Session, Depends(get_db)],
    body: FinancialRecordCreate,
) -> FinancialRecordResponse:
    return record_service.create_record(db, body, created_by_id=user.id)


@router.get("/{record_id}", response_model=FinancialRecordResponse)
def get_record(
    _: AnalystOrAdmin,
    db: Annotated[Session, Depends(get_db)],
    record_id: int,
) -> FinancialRecordResponse:
    rec = record_service.get_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return rec


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
def update_record(
    _: AdminOnly,
    db: Annotated[Session, Depends(get_db)],
    record_id: int,
    body: FinancialRecordUpdate,
) -> FinancialRecordResponse:
    rec = record_service.get_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if all(
        getattr(body, f) is None
        for f in ("amount", "type", "category", "entry_date", "notes")
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )
    return record_service.update_record(db, rec, body)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    _: AdminOnly,
    db: Annotated[Session, Depends(get_db)],
    record_id: int,
) -> None:
    rec = record_service.get_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    record_service.soft_delete_record(db, rec)
