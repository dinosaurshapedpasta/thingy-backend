from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud
from app import schemas
from app.auth import get_current_user as get_authenticated_user

router = APIRouter(prefix="/pickuprequests", tags=["user"])


@router.get("/", response_model=List[schemas.PickupRequest])
def get_pickup_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Get active pickup requests."""
    return crud.get_active_pickup_requests(db)


@router.post("/", response_model=schemas.PickupRequestRead)
def create_pickup_request(
    pickup_request: schemas.PickupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Submit a new pickup request. ONLY AVAILABLE TO MANAGERS"""
    # if not current_user.is_manager:
    #     raise HTTPException(status_code=403, detail="Not authorised")

    return crud.create_pickup_request(db, pickup_request)


@router.delete("/{id}")
def delete_pickup_request(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Delete an active pickup request. ONLY AVAILABLE TO MANAGERS"""
    # if not current_user.is_manager:
    #     raise HTTPException(status_code=403, detail="Not authorised")

    success = crud.delete_pickup_request(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Pickup request not found")

    return {"detail": "Action successful"}


@router.get("/{id}/responses", response_model=List[schemas.PickupResponse])
def get_pickup_request_responses(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Get the responses to a pickup request. ONLY AVAILABLE TO MANAGERS"""
    # if not current_user.is_manager:
    #     raise HTTPException(status_code=403, detail="Not authorised")

    return crud.get_pickup_request_responses(db, id)


@router.post("/{id}/accept")
def accept_pickup_request(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Accept a pickup request. ONLY AVAILABLE TO VOLUNTEERS"""
    success = crud.create_pickup_request_response(
        db, id, current_user.id, 1)
    if not success:
        raise HTTPException(status_code=404, detail="Pickup request not found")

    return {"detail": "Action successful"}


@router.post("/{id}/deny")
def deny_pickup_request(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Deny a pickup request. ONLY AVAILABLE TO VOLUNTEERS"""
    success = crud.create_pickup_request_response(
        db, id, current_user.id, 0)
    if not success:
        raise HTTPException(status_code=404, detail="Pickup request not found")

    return {"detail": "Action successful"}
