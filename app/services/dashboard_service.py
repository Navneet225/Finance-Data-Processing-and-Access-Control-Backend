from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import EntryType
from app.schemas import CategoryTotal, DashboardSummary, DashboardTrends, TrendPoint
from app.services import record_service


def start_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def start_of_month(d: date) -> date:
    return date(d.year, d.month, 1)


def build_summary(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> DashboardSummary:
    total_income, total_expense, record_count = record_service.aggregate_for_dashboard(
        db, date_from=date_from, date_to=date_to
    )
    cats = record_service.category_totals(db, date_from=date_from, date_to=date_to)
    by_category = [
        CategoryTotal(
            category=c,
            income=i,
            expense=e,
            net=i - e,
        )
        for c, i, e in cats
    ]
    return DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        by_category=by_category,
        record_count=record_count,
    )


def build_trends(
    db: Session,
    *,
    granularity: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> DashboardTrends:
    records = record_service.iter_records_for_trends(db, date_from=date_from, date_to=date_to)
    bucket: dict[date, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal(0), "expense": Decimal(0)}
    )
    for r in records:
        if granularity == "week":
            key = start_of_week(r.entry_date)
        else:
            key = start_of_month(r.entry_date)
        if r.type == EntryType.income:
            bucket[key]["income"] += Decimal(str(r.amount))
        else:
            bucket[key]["expense"] += Decimal(str(r.amount))
    points = [
        TrendPoint(
            period_start=k,
            income=v["income"],
            expense=v["expense"],
            net=v["income"] - v["expense"],
        )
        for k, v in sorted(bucket.items(), key=lambda x: x[0])
    ]
    return DashboardTrends(granularity=granularity, points=points)
