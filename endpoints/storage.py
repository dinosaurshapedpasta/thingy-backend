from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud, models
from app import schemas

router = APIRouter(prefix="/storage", tags=["storage"])


@router.post("/", response_model=schemas.StoragePointRead)
def create_storage_point(
    storage_point: schemas.StoragePointCreate,
    db: Session = Depends(get_db)
):
    """Create a new storage point (ID assigned automatically by server)."""
    return crud.create_storage_point(db, storage_point)


@router.get("/{id}", response_model=schemas.StoragePointRead)
def get_storage_point(id: str, db: Session = Depends(get_db)):
    """Get details about a storage point."""
    storage_point = crud.get_storage_point(db, id)
    if not storage_point:
        raise HTTPException(status_code=404, detail="Storage point not found")
    return storage_point


@router.patch("/{id}", response_model=schemas.StoragePointRead)
def update_storage_point(
    id: str,
    storage_point_data: schemas.StoragePointCreate,
    db: Session = Depends(get_db)
):
    """Change details about a storage point (ID cannot be changed)."""
    updated_storage_point = crud.update_storage_point(db, id, storage_point_data)
    if not updated_storage_point:
        raise HTTPException(status_code=404, detail="Storage point not found")
    return updated_storage_point


@router.get("/{id}/items", response_model=list[schemas.StorageItemResponse])
def get_storage_items(id: str, db: Session = Depends(get_db)):
    """Get the items currently held by a storage point."""
    # Verify storage point exists
    storage_point = crud.get_storage_point(db, id)
    if not storage_point:
        raise HTTPException(status_code=404, detail="Storage point not found")

    # Get all items in this storage point
    items = db.query(models.ItemsInStorage).filter(
        models.ItemsInStorage.storageID == id
    ).all()

    return [
        {
            "id": item.itemVariantID,
            "quantity": item.quantity
        }
        for item in items
    ]
