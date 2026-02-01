from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud
from app import schemas
from app.auth import get_current_user as get_authenticated_user

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me", response_model=schemas.UserRead)
def get_current_user(current_user = Depends(get_authenticated_user)):
    """
    Get details about yourself.

    Requires X-API-Key header for authentication.
    The API key is hashed and matched against the apiKeys table.
    """
    return current_user


@router.patch("/me", response_model=schemas.UserRead)
def update_current_user(
    user_data: schemas.UserCreate,
    current_user = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Change details about yourself.

    Requires X-API-Key header for authentication.
    Updates user details (ID is ignored).
    """
    updated_user = crud.update_user(db, current_user.id, user_data)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update user")
    return updated_user


@router.post("/me/location")
def update_user_location(
    location: dict,
    current_user = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Send a user's own location. Called when requests from managers are accepted for pathfinding.

    Requires X-API-Key header for authentication.
    """
    # TODO: Update user's location
    # TODO: Trigger pathfinding logic if needed
    return {"message": "Location updated", "user_id": current_user.id}


@router.get("/{id}", response_model=schemas.UserRead)
def get_user(id: str, db: Session = Depends(get_db)):
    """Get details about a user (no authentication required)."""
    user = crud.get_user(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{id}", response_model=schemas.UserRead)
def update_user(id: str, user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Change details about a user (no authentication required)."""
    updated_user = crud.update_user(db, id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.get("/{id}/items")
def get_user_items(id: str, db: Session = Depends(get_db)):
    """Get the items currently held by a user."""
    user = crud.get_user(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    items = crud.get_all_items_in_car(db, id)
    return [{"id": item.itemVariantID, "quantity": item.quantity} for item in items]


@router.patch("/{userID}/items/{itemID}")
def set_user_item_quantity(
    userID: str,
    itemID: str,
    data: dict,
    db: Session = Depends(get_db)
):
    """Set the quantity of an item in a user's car."""
    user = crud.get_user(db, userID)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    quantity = data.get("quantity", 0)
    result = crud.update_items_in_car(db, userID, itemID, quantity)
    if not result:
        # Create new record if it doesn't exist
        crud.create_items_in_car(db, schemas.ItemsInCarCreate(
            userID=userID,
            itemVariantID=itemID,
            quantity=quantity
        ))
    
    return {"code": 200, "message": "Action carried out successfully."}
