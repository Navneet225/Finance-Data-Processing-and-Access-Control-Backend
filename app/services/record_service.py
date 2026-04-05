from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import EntryType, FinancialRecord
from app.schemas import FinancialRecordCreate, FinancialRecordUpdate


def _not_deleted():
    return FinancialRecord.deleted_at.is_(None)


def get_record(db: Session, record_id: int) -> FinancialRecord | None:
    return db.scalars(select(FinancialRecord).where(FinancialRecord.id == record_id, _not_deleted())).first()


def list_records(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    entry_type: EntryType | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[FinancialRecord], int]:
    q = select(FinancialRecord).where(_not_deleted())
    if date_from is not None:
        q = q.where(FinancialRecord.entry_date >= date_from)
    if date_to is not None:
        q = q.where(FinancialRecord.entry_date <= date_to)
    if category:
        q = q.where(FinancialRecord.category.ilike(category.strip()))
    if entry_type is not None:
        q = q.where(FinancialRecord.type == entry_type)
    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.where(
            or_(
                FinancialRecord.notes.ilike(term),
                FinancialRecord.category.ilike(term),
            )
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = db.scalar(count_q) or 0

    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size
    q = q.order_by(FinancialRecord.entry_date.desc(), FinancialRecord.id.desc()).offset(offset).limit(page_size)
    items = list(db.scalars(q).all())
    return items, total


def create_record(db: Session, data: FinancialRecordCreate, created_by_id: int | None) -> FinancialRecord:
    rec = FinancialRecord(
        amount=data.amount,
        type=EntryType(data.type.value),
        category=data.category.strip(),
        entry_date=data.entry_date,
        notes=data.notes,
        created_by_id=created_by_id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def update_record(db: Session, rec: FinancialRecord, data: FinancialRecordUpdate) -> FinancialRecord:
    from datetime import datetime, timezone

    if data.amount is not None:
        rec.amount = data.amount
    if data.type is not None:
        rec.type = EntryType(data.type.value)
    if data.category is not None:
        rec.category = data.category.strip()
    if data.entry_date is not None:
        rec.entry_date = data.entry_date
    if data.notes is not None:
        rec.notes = data.notes
    rec.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rec)
    return rec


def soft_delete_record(db: Session, rec: FinancialRecord) -> None:
    from datetime import datetime, timezone

    rec.deleted_at = datetime.now(timezone.utc)
    db.commit()


def _filter_conds(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list:
    conds = [_not_deleted()]
    if date_from is not None:
        conds.append(FinancialRecord.entry_date >= date_from)
    if date_to is not None:
        conds.append(FinancialRecord.entry_date <= date_to)
    return conds


def aggregate_for_dashboard(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[Decimal, Decimal, int]:
    conds = _filter_conds(date_from=date_from, date_to=date_to)
    income = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            *conds,
            FinancialRecord.type == EntryType.income,
        )
    )
    expense = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            *conds,
            FinancialRecord.type == EntryType.expense,
        )
    )
    count = db.scalar(select(func.count()).select_from(FinancialRecord).where(*conds)) or 0
    return Decimal(str(income or 0)), Decimal(str(expense or 0)), int(count)


def category_totals(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[tuple[str, Decimal, Decimal]]:
    q = select(FinancialRecord).where(_not_deleted())
    if date_from is not None:
        q = q.where(FinancialRecord.entry_date >= date_from)
    if date_to is not None:
        q = q.where(FinancialRecord.entry_date <= date_to)

    rows = list(db.scalars(q).all())
    from collections import defaultdict

    acc: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal(0), "expense": Decimal(0)})
    for r in rows:
        if r.type == EntryType.income:
            acc[r.category]["income"] += Decimal(str(r.amount))
        else:
            acc[r.category]["expense"] += Decimal(str(r.amount))
    out: list[tuple[str, Decimal, Decimal]] = []
    for cat, v in sorted(acc.items()):
        out.append((cat, v["income"], v["expense"]))
    return out


def iter_records_for_trends(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[FinancialRecord]:
    q = select(FinancialRecord).where(_not_deleted())
    if date_from is not None:
        q = q.where(FinancialRecord.entry_date >= date_from)
    if date_to is not None:
        q = q.where(FinancialRecord.entry_date <= date_to)
    q = q.order_by(FinancialRecord.entry_date)
    return list(db.scalars(q).all())


def recent_records(db: Session, limit: int = 10) -> list[FinancialRecord]:
    limit = min(max(1, limit), 50)
    q = (
        select(FinancialRecord)
        .where(_not_deleted())
        .order_by(FinancialRecord.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(q).all())
