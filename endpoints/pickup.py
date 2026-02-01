from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud
from app import schemas

router = APIRouter(prefix="/pickup", tags=["pickup"])

@router.get("/{id}", response_model=schemas.PickupPointRead)
def get_pickup_point(id: str, db: Session = Depends(get_db)):
    """Get a pickup point."""
    pickup_point = crud.get_pickup_point(db, id)
    if not pickup_point:
        raise HTTPException(status_code=404, detail="Pickup Point not found")
    return pickup_point


@router.get("/{id}/items")
def get_pickup_point_items(id: str, db: Session = Depends(get_db)):
    """Get the items currently held by a pickup point."""
    pickup_point = crud.get_pickup_point(db, id)
    if not pickup_point:
        raise HTTPException(status_code=404, detail="Pickup Point not found")
    
    items = crud.get_all_items_at_pickup_point(db, id)
    return [{"id": item.itemVariantID, "quantity": item.quantity} for item in items]


@router.patch("/{id}", response_model=schemas.PickupPointRead)
def update_pickup_point(id: str, pickup_point_data: schemas.PickupPointCreate, db: Session = Depends(get_db)):
    """Change details about a pickup point."""
    updated_pickup_point = crud.update_pickup_point(db, id, pickup_point_data)
    if not updated_pickup_point:
        raise HTTPException(status_code=404, detail="Pickup Point not found")
    return updated_pickup_point

@router.post("/", response_model=schemas.PickupPointRead)
def create_pickup_point(pickup_point_data: schemas.PickupPointCreate, db: Session = Depends(get_db)):
    """Create a new Pickup Point. ID is assigned automatically by server."""
    new_pickup_point = crud.create_pickup_point(db, pickup_point_data)
    return new_pickup_point

