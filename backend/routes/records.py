from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from db import get_db
from models.record import Record
from models.user import User
from schemas.record import RecordCreate, RecordUpdate, RecordOut
from dependencies.auth import get_current_user, require_admin, require_analyst_or_admin

router = APIRouter(prefix="/records", tags=["Records"])


def _active_records(db: Session):
    """
    Base query that always excludes soft-deleted records.
    All read and write routes should use this instead of db.query(Record) directly
    to ensure deleted records are never returned or modified.
    """
    return db.query(Record).filter(Record.is_deleted == False)  # noqa: E712


@router.post("", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    record = Record(
        user_id=current_user.id,
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=List[RecordOut])
def list_records(
    type: Optional[str] = Query(None, description="Filter by type: income or expense"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter records from this date"),
    end_date: Optional[date] = Query(None, description="Filter records up to this date"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    query = _active_records(db)

    if type:
        query = query.filter(Record.type == type)
    if category:
        query = query.filter(Record.category.ilike(f"%{category}%"))
    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)

    return query.order_by(Record.date.desc()).offset(skip).limit(limit).all()


@router.get("/{record_id}", response_model=RecordOut)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    record = _active_records(db).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.patch(
    "/{record_id}",
    response_model=RecordOut,
    summary="Partially update a record",
    description="""
Update **one or more fields** of an existing financial record.

**Rules:**
- At least one field must be provided — empty body `{}` returns `422`
- Only send the fields you want to change
- `amount` must be greater than zero if provided
- `category` cannot be empty or whitespace if provided

**Examples:**

Update only amount:
```json
{ "amount": 75000.00 }
```

Update category and type:
```json
{ "category": "Bonus", "type": "income" }
```
""",
)
def update_record(
    record_id: int,
    data: RecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    record = _active_records(db).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a record (Admin only)",
    description="""
Marks the record as deleted — it is **no longer returned** by any list or get endpoints.

The record data is **preserved in the database** for audit purposes.
This is intentional: financial data should never be permanently erased unilaterally.
""",
)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    record = _active_records(db).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Soft delete: set is_deleted flag rather than removing the row
    record.is_deleted = True
    db.commit()
