from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import Role, User
from app.schemas import DashboardSummary, DashboardTrends, EntryTypeEnum, RecentActivityItem
from app.services import dashboard_service, record_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DashboardUser = Annotated[User, Depends(require_roles(Role.viewer, Role.analyst, Role.admin))]


@router.get("/summary", response_model=DashboardSummary)
def summary(
    _: DashboardUser,
    db: Annotated[Session, Depends(get_db)],
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
) -> DashboardSummary:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be on or before date_to",
        )
    return dashboard_service.build_summary(db, date_from=date_from, date_to=date_to)


@router.get("/trends", response_model=DashboardTrends)
def trends(
    _: DashboardUser,
    db: Annotated[Session, Depends(get_db)],
    granularity: Literal["week", "month"] = Query("month", description="Bucket size for trend series"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
) -> DashboardTrends:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be on or before date_to",
        )
    return dashboard_service.build_trends(
        db,
        granularity=granularity,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/recent", response_model=list[RecentActivityItem])
def recent(
    _: DashboardUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
) -> list[RecentActivityItem]:
    rows = record_service.recent_records(db, limit=limit)
    return [
        RecentActivityItem(
            id=r.id,
            amount=r.amount,
            type=EntryTypeEnum(r.type.value),
            category=r.category,
            entry_date=r.entry_date,
            notes=r.notes,
            created_at=r.created_at,
        )
        for r in rows
    ]
