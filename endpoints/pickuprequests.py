from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, crud
from app import schemas
from app.auth import get_current_user as get_authenticated_user

router = APIRouter(prefix="/pickuprequests", tags=["pickup"])


@router.get("/", response_model=List[schemas.PickupRequest])
def get_pickup_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Get active pickup requests."""
    requests = crud.get_active_pickup_requests(db)
    return [schemas.PickupRequest(id=r.id, pickupPointID=r.pickupPointID) for r in requests]


@router.post("/")
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


@router.get("/{id}/responses")
def get_pickup_request_responses(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """Get the responses to a pickup request. ONLY AVAILABLE TO MANAGERS"""
    # if not current_user.is_manager:
    #     raise HTTPException(status_code=403, detail="Not authorised")

    responses = crud.get_pickup_request_responses(db, id)
    return [{"userID": r.userID, "response": "accept" if r.result == 1 else "deny"} for r in responses]


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


@router.post("/{id}/execute-routing")
async def execute_routing_endpoint(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """
    Execute the routing algorithm for a pickup request.
    
    This will:
    1. Get all volunteers who accepted and have GPS location
    2. Calculate optimal routes using VSP algorithm
    3. Update volunteer car contents in the database
    
    Returns the computed routes and database changes.
    ONLY AVAILABLE TO MANAGERS.
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can execute routing")
    
    # Check pickup request exists
    from app.database import models
    pickup_request = db.query(models.PickupRequest).filter(
        models.PickupRequest.id == id
    ).first()
    
    if not pickup_request:
        raise HTTPException(status_code=404, detail="Pickup request not found")
    
    from app.services.routing_service import execute_routing
    
    result = await execute_routing(db, id)
    
    if not result:
        raise HTTPException(
            status_code=400, 
            detail="Could not execute routing. Ensure there are volunteers who accepted with GPS locations."
        )
    
    return result


@router.get("/{id}/routing-input", response_model=schemas.RoutingInput)
async def get_routing_input(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    """
    Get the input data for the routing algorithm.
    Calculates real travel times via OpenRouteService.
    
    Returns:
    - distance_matrix: Travel times from each volunteer to each drop-off (minutes)
    - drops_matrix: Travel times between drop-offs (minutes)
    - item_volumes: Volume of each item at pickup
    - car_caps: Each volunteer's car capacity
    - volunteer_ids: IDs of volunteers who accepted with GPS
    - dropoff_ids: All drop-off point IDs
    
    ONLY AVAILABLE TO MANAGERS.
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can access routing data")
    
    from app.services.pickup_service import prepare_routing_input_with_distances
    
    routing_input = await prepare_routing_input_with_distances(db, id)
    if not routing_input:
        raise HTTPException(status_code=400, detail="No accepted volunteers with GPS or pickup request not found")
    
    return routing_input
