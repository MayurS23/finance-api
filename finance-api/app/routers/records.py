from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin, require_viewer
from app.models import FinancialRecord, TransactionType, User
from app.schemas import PaginatedResponse, RecordCreate, RecordResponse, RecordUpdate

router = APIRouter(prefix="/records", tags=["records"])


# ── Helper ─────────────────────────────────────────────────────────────────────

def _build_filter_query(
    type:      TransactionType | None = None,
    category:  str | None             = None,
    date_from: str | None             = None,
    date_to:   str | None             = None,
):
    query = select(FinancialRecord).where(FinancialRecord.is_deleted.is_(False))
    if type:
        query = query.where(FinancialRecord.type == type)
    if category:
        query = query.where(FinancialRecord.category.ilike(f"%{category}%"))
    if date_from:
        query = query.where(FinancialRecord.date >= date_from)
    if date_to:
        query = query.where(FinancialRecord.date <= date_to)
    return query


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[RecordResponse],
    dependencies=[Depends(require_viewer)],
    summary="List financial records with optional filters",
)
async def list_records(
    type:      TransactionType | None = Query(default=None),
    category:  str | None             = Query(default=None),
    date_from: str | None             = Query(default=None, description="YYYY-MM-DD"),
    date_to:   str | None             = Query(default=None, description="YYYY-MM-DD"),
    page:      int                    = Query(default=1, ge=1),
    page_size: int                    = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RecordResponse]:
    base_q = _build_filter_query(type, category, date_from, date_to)
    total  = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar_one()

    result = await db.execute(
        base_q.order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
              .offset((page - 1) * page_size)
              .limit(page_size)
    )
    records = result.scalars().all()

    return PaginatedResponse(
        items=[RecordResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=-(-total // page_size),
    )


@router.post(
    "",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Create a new financial record (admin only)",
)
async def create_record(
    payload:      RecordCreate,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
) -> RecordResponse:
    record = FinancialRecord(**payload.model_dump(), created_by=current_user.id)
    db.add(record)
    await db.flush()
    return RecordResponse.model_validate(record)


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    dependencies=[Depends(require_viewer)],
    summary="Get a single record by ID",
)
async def get_record(record_id: str, db: AsyncSession = Depends(get_db)) -> RecordResponse:
    record = await _get_active_record(record_id, db)
    return RecordResponse.model_validate(record)


@router.patch(
    "/{record_id}",
    response_model=RecordResponse,
    dependencies=[Depends(require_admin)],
    summary="Update a financial record (admin only)",
)
async def update_record(
    record_id: str,
    payload:   RecordUpdate,
    db:        AsyncSession = Depends(get_db),
) -> RecordResponse:
    record = await _get_active_record(record_id, db)

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    for field, value in updates.items():
        setattr(record, field, value)

    await db.flush()
    return RecordResponse.model_validate(record)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
    summary="Soft-delete a record (admin only)",
)
async def delete_record(record_id: str, db: AsyncSession = Depends(get_db)) -> None:
    record = await _get_active_record(record_id, db)
    record.is_deleted = True


# ── Private helpers ────────────────────────────────────────────────────────────

async def _get_active_record(record_id: str, db: AsyncSession) -> FinancialRecord:
    result = await db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record
