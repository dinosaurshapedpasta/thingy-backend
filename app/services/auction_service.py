"""
Auction Service Module

Handles the auction logic for selecting the best volunteer for a pickup request.

Flow:
1. Create auction when pickup request is issued
2. Collect volunteer responses (Y/N + GPS) within 60 seconds
3. Calculate travel times via Maps API
4. Score volunteers based on time, capacity, and karma
5. Select winner and prepare routing data
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.database import models
from app import schemas
from app.services.maps_service import calculate_distance_matrix


# Auction configuration
AUCTION_DURATION_SECONDS = 60

# Scoring weights
WEIGHT_TIME = 0.6       # Lower travel time = better
WEIGHT_CAPACITY = 0.25  # More capacity = better
WEIGHT_KARMA = 0.15     # Higher karma = better


def create_auction(db: Session, pickup_request_id: str) -> models.Auction:
    """Create a new auction for a pickup request."""
    now = datetime.utcnow()
    auction = models.Auction(
        id=str(uuid.uuid4()),
        pickupRequestID=pickup_request_id,
        status="active",
        createdAt=now,
        expiresAt=now + timedelta(seconds=AUCTION_DURATION_SECONDS),
        winnerUserID=None
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction


def get_auction(db: Session, auction_id: str) -> Optional[models.Auction]:
    """Get an auction by ID."""
    return db.query(models.Auction).filter(models.Auction.id == auction_id).first()


def get_auction_by_pickup_request(db: Session, pickup_request_id: str) -> Optional[models.Auction]:
    """Get the active auction for a pickup request."""
    return db.query(models.Auction).filter(
        models.Auction.pickupRequestID == pickup_request_id,
        models.Auction.status == "active"
    ).first()


def get_active_auctions(db: Session) -> List[models.Auction]:
    """Get all active auctions."""
    return db.query(models.Auction).filter(models.Auction.status == "active").all()


def submit_bid(
    db: Session,
    auction_id: str,
    user_id: str,
    accepted: bool,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Optional[models.AuctionBid]:
    """Submit a volunteer's bid to an auction."""
    auction = get_auction(db, auction_id)
    if not auction or auction.status != "active":
        return None
    
    # Check if auction has expired
    if datetime.utcnow() > auction.expiresAt:
        return None
    
    # Check if user already bid
    existing_bid = db.query(models.AuctionBid).filter(
        models.AuctionBid.auctionID == auction_id,
        models.AuctionBid.userID == user_id
    ).first()
    
    if existing_bid:
        # Update existing bid
        existing_bid.accepted = 1 if accepted else 0
        existing_bid.latitude = latitude
        existing_bid.longitude = longitude
        existing_bid.createdAt = datetime.utcnow()
        db.commit()
        db.refresh(existing_bid)
        return existing_bid
    
    # Create new bid
    bid = models.AuctionBid(
        auctionID=auction_id,
        userID=user_id,
        accepted=1 if accepted else 0,
        latitude=latitude,
        longitude=longitude,
        estimatedTime=None,
        score=None,
        createdAt=datetime.utcnow()
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def get_auction_bids(db: Session, auction_id: str) -> List[models.AuctionBid]:
    """Get all bids for an auction."""
    return db.query(models.AuctionBid).filter(
        models.AuctionBid.auctionID == auction_id
    ).all()


def get_accepted_bids(db: Session, auction_id: str) -> List[models.AuctionBid]:
    """Get all accepted (Y) bids for an auction."""
    return db.query(models.AuctionBid).filter(
        models.AuctionBid.auctionID == auction_id,
        models.AuctionBid.accepted == 1
    ).all()


def calculate_volunteer_score(
    travel_time: float,
    max_travel_time: float,
    car_capacity: float,
    max_capacity: float,
    karma: int,
    max_karma: int
) -> float:
    """
    Calculate a volunteer's score based on multiple factors.
    Higher score = better candidate.
    
    Factors:
    - Travel time (lower is better)
    - Car capacity (higher is better)
    - Karma (higher is better)
    """
    # Normalize values to 0-1 range
    time_score = 1 - (travel_time / max_travel_time) if max_travel_time > 0 else 0
    capacity_score = car_capacity / max_capacity if max_capacity > 0 else 0
    karma_score = karma / max_karma if max_karma > 0 else 0
    
    # Weighted combination
    final_score = (
        WEIGHT_TIME * time_score +
        WEIGHT_CAPACITY * capacity_score +
        WEIGHT_KARMA * karma_score
    )
    
    return final_score


async def process_auction(db: Session, auction_id: str) -> Optional[schemas.AuctionResult]:
    """
    Process an auction after the bidding period ends.
    
    1. Get all accepted bids
    2. Calculate travel times via Maps API
    3. Score each volunteer
    4. Select the winner
    5. Return routing data
    """
    auction = get_auction(db, auction_id)
    if not auction:
        return None
    
    # Get all accepted bids
    accepted_bids = get_accepted_bids(db, auction_id)
    if not accepted_bids:
        # No volunteers accepted, close auction
        auction.status = "closed"
        db.commit()
        return schemas.AuctionResult(
            auctionID=auction_id,
            winnerUserID=None,
            bids=[]
        )
    
    # Get pickup point location
    pickup_request = db.query(models.PickupRequest).filter(
        models.PickupRequest.id == auction.pickupRequestID
    ).first()
    
    if not pickup_request:
        return None
    
    pickup_point = db.query(models.PickupPoint).filter(
        models.PickupPoint.id == pickup_request.pickupPointID
    ).first()
    
    if not pickup_point:
        return None
    
    # Parse pickup point location (stored as "lat,lng" string)
    from app.services.maps_service import parse_location_string
    pickup_location = parse_location_string(pickup_point.location)
    if not pickup_location:
        print(f"Error parsing pickup location: {pickup_point.location}")
        pickup_location = (51.5074, -0.1278)  # Default to London
    
    # Get volunteer locations and user data
    volunteer_data = []
    for bid in accepted_bids:
        user = db.query(models.User).filter(models.User.id == bid.userID).first()
        if user and bid.latitude and bid.longitude:
            volunteer_data.append({
                "bid": bid,
                "user": user,
                "location": (bid.latitude, bid.longitude)
            })
    
    if not volunteer_data:
        auction.status = "closed"
        db.commit()
        return schemas.AuctionResult(
            auctionID=auction_id,
            winnerUserID=None,
            bids=[]
        )
    
    # Calculate travel times using Maps API
    origins = [v["location"] for v in volunteer_data]
    destinations = [pickup_location]  # Parsed pickup point location
    
    try:
        distance_matrix = await calculate_distance_matrix(origins, destinations)
    except Exception as e:
        print(f"Error calculating distances: {e}")
        # Fallback: use placeholder times
        distance_matrix = [[10.0] for _ in origins]  # 10 minutes default
    
    # Extract travel times and calculate scores
    max_time = max(row[0] for row in distance_matrix) if distance_matrix else 1
    max_capacity = max(v["user"].maxVolume for v in volunteer_data)
    max_karma = max(v["user"].karma for v in volunteer_data)
    
    best_score = -1
    winner = None
    
    for i, vol in enumerate(volunteer_data):
        travel_time = distance_matrix[i][0] if i < len(distance_matrix) else 10.0
        
        score = calculate_volunteer_score(
            travel_time=travel_time,
            max_travel_time=max_time,
            car_capacity=vol["user"].maxVolume,
            max_capacity=max_capacity,
            karma=vol["user"].karma,
            max_karma=max_karma
        )
        
        # Update bid with calculated values
        vol["bid"].estimatedTime = travel_time
        vol["bid"].score = score
        
        if score > best_score:
            best_score = score
            winner = vol
    
    # Update auction with winner
    if winner:
        auction.winnerUserID = winner["user"].id
        auction.status = "completed"
    else:
        auction.status = "closed"
    
    db.commit()
    
    # Prepare result
    bids_read = [
        schemas.AuctionBidRead(
            auctionID=b["bid"].auctionID,
            userID=b["bid"].userID,
            accepted=b["bid"].accepted,
            latitude=b["bid"].latitude,
            longitude=b["bid"].longitude,
            estimatedTime=b["bid"].estimatedTime,
            score=b["bid"].score,
            createdAt=b["bid"].createdAt
        )
        for b in volunteer_data
    ]
    
    return schemas.AuctionResult(
        auctionID=auction_id,
        winnerUserID=winner["user"].id if winner else None,
        bids=bids_read
    )


def prepare_routing_input(
    db: Session,
    auction_id: str
) -> Optional[schemas.RoutingInput]:
    """
    Prepare the input data for the routing algorithm (without real distance calculations).
    
    Returns:
    - distance_matrix: All available volunteers to all drop-off points (placeholder values)
    - drops_matrix: Distances between all drop-off points (placeholder values)
    - item_volumes: Volume of each item at the pickup point
    - car_caps: Capacity of each available volunteer's car
    - volunteer_ids: List of all available volunteer IDs
    - dropoff_ids: List of all drop-off point IDs
    """
    auction = get_auction(db, auction_id)
    if not auction:
        return None
    
    # Get ALL accepted bids (available volunteers)
    accepted_bids = db.query(models.AuctionBid).filter(
        models.AuctionBid.auctionID == auction_id,
        models.AuctionBid.accepted == True
    ).all()
    
    if not accepted_bids:
        return None
    
    # Get volunteer info for all accepted bids
    volunteers = []
    for bid in accepted_bids:
        if bid.latitude and bid.longitude:
            user = db.query(models.User).filter(
                models.User.id == bid.userID
            ).first()
            if user:
                volunteers.append(user)
    
    if not volunteers:
        return None
    
    # Get all drop-off points with their locations
    dropoff_points = db.query(models.DropOffPoint).all()
    
    if not dropoff_points:
        return schemas.RoutingInput(
            distance_matrix=[],
            drops_matrix=[],
            item_volumes=[],
            car_caps=[v.maxVolume for v in volunteers],
            volunteer_ids=[v.id for v in volunteers],
            dropoff_ids=[]
        )
    
    # Parse drop-off locations
    from app.services.maps_service import parse_location_string
    valid_dropoffs = []
    for dp in dropoff_points:
        loc = parse_location_string(dp.location)
        if loc:
            valid_dropoffs.append(dp)
    
    # Get item volumes from pickup point
    pickup_request = db.query(models.PickupRequest).filter(
        models.PickupRequest.id == auction.pickupRequestID
    ).first()
    
    item_volumes = []
    if pickup_request:
        items_at_pickup = db.query(models.ItemsAtPickupPoint).filter(
            models.ItemsAtPickupPoint.pickupPointID == pickup_request.pickupPointID
        ).all()
        
        for item_record in items_at_pickup:
            item = db.query(models.ItemVariant).filter(
                models.ItemVariant.id == item_record.itemVariantID
            ).first()
            if item:
                # Add volume for each unit of the item
                for _ in range(item_record.quantity):
                    item_volumes.append(item.volume)
    
    # Build distance matrices (placeholder values - use prepare_routing_input_with_distances for real values)
    num_dropoffs = len(valid_dropoffs)
    num_volunteers = len(volunteers)
    
    # Distance matrix: [N volunteers] x [N dropoffs] - placeholder travel times
    distance_matrix = [[0.0 for _ in range(num_dropoffs)] for _ in range(num_volunteers)]
    
    # Drops matrix: [N dropoffs] x [N dropoffs] - placeholder travel times
    drops_matrix = [[0.0 for _ in range(num_dropoffs)] for _ in range(num_dropoffs)]
    
    dropoff_ids = [dp.id for dp in valid_dropoffs]
    
    # Get item_id from the pickup request items (use first item variant as the main item)
    item_id = ""
    if pickup_request:
        first_item = db.query(models.ItemsAtPickupPoint).filter(
            models.ItemsAtPickupPoint.pickupPointID == pickup_request.pickupPointID
        ).first()
        if first_item:
            item_id = first_item.itemVariantID
    
    # Car contents - initially empty for each volunteer (placeholder)
    # Each car has a vector of 0s representing no items currently loaded
    num_item_types = len(set([iap.itemVariantID for iap in db.query(models.ItemsAtPickupPoint).filter(
        models.ItemsAtPickupPoint.pickupPointID == pickup_request.pickupPointID
    ).all()])) if pickup_request else 0
    car_contents = [[0.0 for _ in range(num_item_types)] for _ in volunteers]
    
    return schemas.RoutingInput(
        distance_matrix=distance_matrix,
        drops_matrix=drops_matrix,
        item_volumes=item_volumes,
        car_caps=[v.maxVolume for v in volunteers],
        volunteer_ids=[v.id for v in volunteers],
        dropoff_ids=dropoff_ids,
        car_contents=car_contents,
        item_id=item_id
    )


async def prepare_routing_input_with_distances(
    db: Session,
    auction_id: str
) -> Optional[schemas.RoutingInput]:
    """
    Prepare routing input with REAL distances calculated via OpenRouteService.
    
    Returns:
    - distance_matrix: Travel times from EACH available volunteer to all drop-off points (in minutes)
    - drops_matrix: Travel times between all drop-off points (in minutes)
    - item_volumes: Volume of each item at the pickup point
    - car_caps: Capacity of each available volunteer's car
    - volunteer_ids: List of all available volunteer IDs
    - dropoff_ids: List of all drop-off point IDs
    """
    auction = get_auction(db, auction_id)
    if not auction:
        return None
    
    # Get ALL accepted bids (available volunteers)
    accepted_bids = db.query(models.AuctionBid).filter(
        models.AuctionBid.auctionID == auction_id,
        models.AuctionBid.accepted == True
    ).all()
    
    if not accepted_bids:
        return None
    
    # Get volunteer info and locations for all accepted bids
    volunteers = []
    volunteer_locations = []
    
    for bid in accepted_bids:
        if bid.latitude and bid.longitude:
            user = db.query(models.User).filter(
                models.User.id == bid.userID
            ).first()
            if user:
                volunteers.append(user)
                volunteer_locations.append((bid.latitude, bid.longitude))
    
    if not volunteers:
        return None
    
    # Get all drop-off points with their locations
    dropoff_points = db.query(models.DropOffPoint).all()
    
    if not dropoff_points:
        return schemas.RoutingInput(
            distance_matrix=[],
            drops_matrix=[],
            item_volumes=[],
            car_caps=[v.maxVolume for v in volunteers],
            volunteer_ids=[v.id for v in volunteers],
            dropoff_ids=[]
        )
    
    # Parse drop-off locations
    from app.services.maps_service import parse_location_string
    dropoff_locations = []
    valid_dropoffs = []
    for dp in dropoff_points:
        loc = parse_location_string(dp.location)
        if loc:
            dropoff_locations.append(loc)
            valid_dropoffs.append(dp)
    
    if not dropoff_locations:
        return schemas.RoutingInput(
            distance_matrix=[],
            drops_matrix=[],
            item_volumes=[],
            car_caps=[v.maxVolume for v in volunteers],
            volunteer_ids=[v.id for v in volunteers],
            dropoff_ids=[]
        )
    
    # Get item volumes from pickup point
    pickup_request = db.query(models.PickupRequest).filter(
        models.PickupRequest.id == auction.pickupRequestID
    ).first()
    
    item_volumes = []
    if pickup_request:
        items_at_pickup = db.query(models.ItemsAtPickupPoint).filter(
            models.ItemsAtPickupPoint.pickupPointID == pickup_request.pickupPointID
        ).all()
        
        for item_record in items_at_pickup:
            item = db.query(models.ItemVariant).filter(
                models.ItemVariant.id == item_record.itemVariantID
            ).first()
            if item:
                for _ in range(item_record.quantity):
                    item_volumes.append(item.volume)
    
    # Calculate REAL distances using OpenRouteService
    try:
        # Distance from EACH volunteer to each dropoff
        distance_matrix = await calculate_distance_matrix(
            origins=volunteer_locations,
            destinations=dropoff_locations
        )
    except Exception as e:
        print(f"Error calculating volunteer->dropoff distances: {e}")
        # Fallback: create matrix with default values for each volunteer
        distance_matrix = [[10.0 for _ in dropoff_locations] for _ in volunteers]
    
    try:
        # Distances between all dropoff points
        drops_matrix = await calculate_distance_matrix(
            origins=dropoff_locations,
            destinations=dropoff_locations
        )
    except Exception as e:
        print(f"Error calculating dropoff->dropoff distances: {e}")
        num_dropoffs = len(dropoff_locations)
        drops_matrix = [[10.0 for _ in range(num_dropoffs)] for _ in range(num_dropoffs)]
    
    dropoff_ids = [dp.id for dp in valid_dropoffs]
    
    # Get item_id from the pickup request items (use first item variant as the main item)
    item_id = ""
    if pickup_request:
        first_item = db.query(models.ItemsAtPickupPoint).filter(
            models.ItemsAtPickupPoint.pickupPointID == pickup_request.pickupPointID
        ).first()
        if first_item:
            item_id = first_item.itemVariantID
    
    # Car contents - initially empty for each volunteer
    # Each car has a vector of 0s representing no items currently loaded
    num_item_types = len(set([iap.itemVariantID for iap in db.query(models.ItemsAtPickupPoint).filter(
        models.ItemsAtPickupPoint.pickupPointID == pickup_request.pickupPointID
    ).all()])) if pickup_request else 0
    car_contents = [[0.0 for _ in range(num_item_types)] for _ in volunteers]
    
    return schemas.RoutingInput(
        distance_matrix=distance_matrix,
        drops_matrix=drops_matrix,
        item_volumes=item_volumes,
        car_caps=[v.maxVolume for v in volunteers],
        volunteer_ids=[v.id for v in volunteers],
        dropoff_ids=dropoff_ids,
        car_contents=car_contents,
        item_id=item_id
    )
