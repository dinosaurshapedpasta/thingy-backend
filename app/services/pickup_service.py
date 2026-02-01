"""
Pickup Service Module

Handles the routing logic for pickup requests.
Gets all volunteers who accepted a pickup request and prepares routing data.

Flow:
1. Volunteers accept pickup request and submit their GPS via /user/me/location
2. Manager triggers routing when ready
3. Calculate travel times via Maps API
4. Prepare routing input for VSP algorithm
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import models
from app import schemas
from app.services.maps_service import calculate_distance_matrix, parse_location_string


def get_accepted_volunteers(db: Session, pickup_request_id: str) -> List[models.User]:
    """Get all volunteers who accepted a pickup request and have GPS location."""
    # Get all accepted responses
    accepted_responses = db.query(models.PickupRequestResponses).filter(
        models.PickupRequestResponses.requestID == pickup_request_id,
        models.PickupRequestResponses.result == 1  # 1 = accepted
    ).all()
    
    # Get user data for each accepted response
    volunteers = []
    for response in accepted_responses:
        user = db.query(models.User).filter(
            models.User.id == response.userID
        ).first()
        # Only include volunteers who have GPS location
        if user and user.latitude is not None and user.longitude is not None:
            volunteers.append(user)
    
    return volunteers


def get_pickup_request(db: Session, pickup_request_id: str) -> Optional[models.PickupRequest]:
    """Get a pickup request by ID."""
    return db.query(models.PickupRequest).filter(
        models.PickupRequest.id == pickup_request_id
    ).first()


async def prepare_routing_input_with_distances(
    db: Session,
    pickup_request_id: str
) -> Optional[schemas.RoutingInput]:
    """
    Prepare routing input with REAL distances calculated via OpenRouteService.
    
    Returns:
    - distance_matrix: Travel times from EACH volunteer to all drop-off points (in minutes)
    - drops_matrix: Travel times between all drop-off points (in minutes)
    - item_volumes: Volume of each item at the pickup point
    - car_caps: Capacity of each volunteer's car
    - volunteer_ids: List of all accepted volunteer IDs
    - dropoff_ids: List of all drop-off point IDs
    """
    pickup_request = get_pickup_request(db, pickup_request_id)
    if not pickup_request:
        return None
    
    # Get all accepted volunteers with GPS
    volunteers = get_accepted_volunteers(db, pickup_request_id)
    
    if not volunteers:
        return None
    
    # Get volunteer locations
    volunteer_locations = [(v.latitude, v.longitude) for v in volunteers]
    
    # Get all drop-off points with their locations
    dropoff_points = db.query(models.DropOffPoint).all()
    
    if not dropoff_points:
        return schemas.RoutingInput(
            distance_matrix=[],
            drops_matrix=[],
            item_volumes=[],
            car_caps=[v.maxVolume for v in volunteers],
            volunteer_ids=[v.id for v in volunteers],
            dropoff_ids=[],
            car_contents=[],
            item_id=""
        )
    
    # Parse drop-off locations
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
            dropoff_ids=[],
            car_contents=[],
            item_id=""
        )
    
    # Get item volumes from pickup point
    item_volumes = []
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
    if items_at_pickup:
        item_id = items_at_pickup[0].itemVariantID
    
    # Car contents - initially empty for each volunteer
    num_item_types = len(set([iap.itemVariantID for iap in items_at_pickup])) if items_at_pickup else 0
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
