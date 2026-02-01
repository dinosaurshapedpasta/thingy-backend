from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud
from app import schemas

router = APIRouter(prefix="/item", tags=["item"])

@router.post("/", response_model=schemas.ItemVariantRead)
def create_item(item_data: schemas.ItemVariantCreate, db: Session = Depends(get_db)):
    """Create a new type of item. ID is assigned automatically by server."""
    new_item = crud.create_item_variant(db, item_data)
    return new_item

@router.get("/{id}", response_model=schemas.ItemVariantRead)
def get_item(id: str, db: Session = Depends(get_db)):
    """Get details about an item."""
    item = crud.get_item_variant(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.patch("/{id}", response_model=schemas.ItemVariantRead)
def update_item(id: str, item_data: schemas.ItemVariantCreate, db: Session = Depends(get_db)):
    """Change details about an item."""
    updated_item = crud.update_item_variant(db, id, item_data)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item
    