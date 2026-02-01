from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud
from app import schemas

router = APIRouter(prefix="/dropoff", tags=["dropoff"])


@router.post("/", response_model=schemas.DropOffPointRead)
def create_dropoff_point(
    dropoff_point: schemas.DropOffPointCreate,
    db: Session = Depends(get_db)
):
    """Create a new drop off point (ID assigned automatically by server)."""
    return crud.create_drop_off_point(db, dropoff_point)


@router.get("/{id}", response_model=schemas.DropOffPointRead)
def get_dropoff_point(id: str, db: Session = Depends(get_db)):
    """Get details about a drop off point."""
    dropoff_point = crud.get_drop_off_point(db, id)
    if not dropoff_point:
        raise HTTPException(status_code=404, detail="Drop off point not found")
    return dropoff_point


@router.patch("/{id}", response_model=schemas.DropOffPointRead)
def update_dropoff_point(
    id: str,
    dropoff_point_data: schemas.DropOffPointCreate,
    db: Session = Depends(get_db)
):
    """Change details about a drop off point (ID cannot be changed)."""
    updated_dropoff_point = crud.update_drop_off_point(db, id, dropoff_point_data)
    if not updated_dropoff_point:
        raise HTTPException(status_code=404, detail="Drop off point not found")
    return updated_dropoff_point