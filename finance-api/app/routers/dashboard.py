from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_analyst, require_viewer
from app.models import FinancialRecord, TransactionType
from app.schemas import CategoryTotal, DashboardSummary, MonthlyTrend, RecordResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    dependencies=[Depends(require_analyst)],
    summary="Full dashboard summary — totals, trends, recent activity (analyst+ only)",
)
async def get_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    # ── Pull all active records ────────────────────────────────────────────────
    result = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.is_deleted.is_(False))
        .order_by(FinancialRecord.date.desc())
    )
    records = result.scalars().all()

    # ── Aggregate totals ───────────────────────────────────────────────────────
    total_income   = sum(r.amount for r in records if r.type == TransactionType.income)
    total_expenses = sum(r.amount for r in records if r.type == TransactionType.expense)
    net_balance    = total_income - total_expenses

    # ── Category totals ────────────────────────────────────────────────────────
    cat_map: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for r in records:
        cat_map[r.category]["total"] += r.amount
        cat_map[r.category]["count"] += 1

    category_totals = [
        CategoryTotal(category=cat, total=round(data["total"], 2), count=data["count"])
        for cat, data in sorted(cat_map.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    # ── Monthly trends ─────────────────────────────────────────────────────────
    month_map: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for r in records:
        month = r.date[:7]   # YYYY-MM
        if r.type == TransactionType.income:
            month_map[month]["income"] += r.amount
        else:
            month_map[month]["expense"] += r.amount

    monthly_trends = [
        MonthlyTrend(
            month=month,
            income=round(data["income"], 2),
            expense=round(data["expense"], 2),
            net=round(data["income"] - data["expense"], 2),
        )
        for month, data in sorted(month_map.items(), reverse=True)
    ]

    # ── Recent activity (last 10) ──────────────────────────────────────────────
    recent = records[:10]

    return DashboardSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_balance=round(net_balance, 2),
        record_count=len(records),
        category_totals=category_totals,
        monthly_trends=monthly_trends,
        recent_activity=[RecordResponse.model_validate(r) for r in recent],
    )


@router.get(
    "/totals",
    dependencies=[Depends(require_viewer)],
    summary="Quick income / expense / net totals (viewer+)",
)
async def get_totals(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Lightweight endpoint — returns just the three headline numbers.
    Suitable for a quick balance widget on the dashboard header.
    """
    income_q  = select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
        FinancialRecord.is_deleted.is_(False),
        FinancialRecord.type == TransactionType.income,
    )
    expense_q = select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
        FinancialRecord.is_deleted.is_(False),
        FinancialRecord.type == TransactionType.expense,
    )

    total_income   = (await db.execute(income_q)).scalar_one()
    total_expenses = (await db.execute(expense_q)).scalar_one()

    return {
        "total_income":   round(float(total_income), 2),
        "total_expenses": round(float(total_expenses), 2),
        "net_balance":    round(float(total_income) - float(total_expenses), 2),
    }


@router.get(
    "/categories",
    response_model=list[CategoryTotal],
    dependencies=[Depends(require_analyst)],
    summary="Category-wise totals (analyst+ only)",
)
async def get_categories(
    type: TransactionType | None = Query(default=None, description="Filter by income or expense"),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryTotal]:
    query = select(
        FinancialRecord.category,
        func.sum(FinancialRecord.amount).label("total"),
        func.count(FinancialRecord.id).label("count"),
    ).where(FinancialRecord.is_deleted.is_(False))

    if type:
        query = query.where(FinancialRecord.type == type)

    query = query.group_by(FinancialRecord.category).order_by(func.sum(FinancialRecord.amount).desc())

    result = await db.execute(query)
    rows   = result.all()

    return [
        CategoryTotal(category=row.category, total=round(float(row.total), 2), count=row.count)
        for row in rows
    ]


@router.get(
    "/trends",
    response_model=list[MonthlyTrend],
    dependencies=[Depends(require_analyst)],
    summary="Monthly income vs expense trends (analyst+ only)",
)
async def get_trends(
    months: int = Query(default=12, ge=1, le=24, description="Number of months to include"),
    db: AsyncSession = Depends(get_db),
) -> list[MonthlyTrend]:
    result = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.is_deleted.is_(False))
        .order_by(FinancialRecord.date.desc())
    )
    records = result.scalars().all()

    month_map: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for r in records:
        month = r.date[:7]
        if r.type == TransactionType.income:
            month_map[month]["income"] += r.amount
        else:
            month_map[month]["expense"] += r.amount

    sorted_months = sorted(month_map.keys(), reverse=True)[:months]

    return [
        MonthlyTrend(
            month=month,
            income=round(month_map[month]["income"], 2),
            expense=round(month_map[month]["expense"], 2),
            net=round(month_map[month]["income"] - month_map[month]["expense"], 2),
        )
        for month in sorted_months
    ]
