"""
Auction Endpoints

Handles the volunteer auction system for pickup requests.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.auth import get_current_user as get_authenticated_user
from app.services import auction_service

router = APIRouter(prefix="/auction", tags=["auction"])


@router.post("/", response_model=schemas.AuctionRead)
def create_auction(
    auction_data: schemas.AuctionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Create a new auction for a pickup request.
    This starts the 60-second bidding window.
    ONLY AVAILABLE TO MANAGERS.
    """
    # Check if user is a manager (userType == 1)
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can create auctions")
    
    # Check if pickup request exists
    from app.database import models
    pickup_request = db.query(models.PickupRequest).filter(
        models.PickupRequest.id == auction_data.pickupRequestID
    ).first()
    
    if not pickup_request:
        raise HTTPException(status_code=404, detail="Pickup request not found")
    
    # Check if there's already an active auction for this request
    existing = auction_service.get_auction_by_pickup_request(db, auction_data.pickupRequestID)
    if existing:
        raise HTTPException(status_code=400, detail="An auction already exists for this pickup request")
    
    auction = auction_service.create_auction(db, auction_data.pickupRequestID)
    return auction


@router.get("/", response_model=List[schemas.AuctionRead])
def get_active_auctions(
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """Get all active auctions that volunteers can bid on."""
    auctions = auction_service.get_active_auctions(db)
    return auctions


@router.get("/{auction_id}", response_model=schemas.AuctionRead)
def get_auction(
    auction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """Get details about a specific auction."""
    auction = auction_service.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


@router.post("/{auction_id}/bid", response_model=schemas.AuctionBidRead)
def submit_bid(
    auction_id: str,
    bid_data: schemas.AuctionBidCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Submit a bid to an auction.
    Volunteers respond with Y/N and their GPS location.
    """
    # Check if user is a volunteer (userType == 0)
    if current_user.userType != 0:
        raise HTTPException(status_code=403, detail="Only volunteers can submit bids")
    
    # Require location if accepting
    if bid_data.accepted and (bid_data.latitude is None or bid_data.longitude is None):
        raise HTTPException(status_code=400, detail="GPS location required when accepting")
    
    bid = auction_service.submit_bid(
        db=db,
        auction_id=auction_id,
        user_id=current_user.id,
        accepted=bid_data.accepted,
        latitude=bid_data.latitude,
        longitude=bid_data.longitude
    )
    
    if not bid:
        raise HTTPException(status_code=400, detail="Cannot submit bid - auction may be closed")
    
    return bid


@router.get("/{auction_id}/bids", response_model=List[schemas.AuctionBidRead])
def get_auction_bids(
    auction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Get all bids for an auction.
    ONLY AVAILABLE TO MANAGERS.
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can view all bids")
    
    auction = auction_service.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    bids = auction_service.get_auction_bids(db, auction_id)
    return bids


@router.post("/{auction_id}/process", response_model=schemas.AuctionResult)
async def process_auction(
    auction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Process an auction and determine the winner.
    This calculates travel times, scores volunteers, and selects the best one.
    ONLY AVAILABLE TO MANAGERS.
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can process auctions")
    
    auction = auction_service.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "active":
        raise HTTPException(status_code=400, detail=f"Auction is already {auction.status}")
    
    result = await auction_service.process_auction(db, auction_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to process auction")
    
    return result


@router.get("/{auction_id}/routing-input", response_model=schemas.RoutingInput)
async def get_routing_input(
    auction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Get the input data for the routing algorithm.
    Calculates real travel times via OpenRouteService.
    Only available after auction is completed.
    
    Returns:
    - distance_matrix: Travel times from winner to each drop-off (minutes)
    - drops_matrix: Travel times between drop-offs (minutes)
    - item_volumes: Volume of each item at pickup
    - car_caps: Winner's car capacity
    - volunteer_ids: Winner's ID
    - dropoff_ids: All drop-off point IDs
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can access routing data")
    
    routing_input = await auction_service.prepare_routing_input_with_distances(db, auction_id)
    if not routing_input:
        raise HTTPException(status_code=400, detail="Auction not completed or no data available")
    
    return routing_input


@router.post("/{auction_id}/close")
def close_auction(
    auction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Manually close an auction without selecting a winner.
    ONLY AVAILABLE TO MANAGERS.
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can close auctions")
    
    auction = auction_service.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "active":
        raise HTTPException(status_code=400, detail=f"Auction is already {auction.status}")
    
    from app.database import models
    auction.status = "closed"
    db.commit()
    
    return {"code": 200, "message": "Auction closed successfully"}


@router.post("/{auction_id}/execute-routing")
async def execute_routing_endpoint(
    auction_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user)
):
    """
    Execute the routing algorithm for an auction.
    
    This will:
    1. Get all available volunteers and dropoff points
    2. Calculate optimal routes using VSP algorithm
    3. Update volunteer car contents in the database
    
    Returns the computed routes and database changes.
    ONLY AVAILABLE TO MANAGERS.
    """
    if current_user.userType != 1:
        raise HTTPException(status_code=403, detail="Only managers can execute routing")
    
    auction = auction_service.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    from app.services.routing_service import execute_routing
    
    result = await execute_routing(db, auction_id)
    
    if not result:
        raise HTTPException(
            status_code=400, 
            detail="Could not execute routing. Ensure there are accepted bids and valid data."
        )
    
    return result

