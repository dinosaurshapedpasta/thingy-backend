"""
Routing Service Module

Orchestrates the full routing flow:
1. Get routing input from pickup service
2. Run VSP algorithm to optimize routes
3. Apply results to database (update car contents, etc.)
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from app.database import models
from app import schemas
from app.vsp import solve_routing
from app.services.pickup_service import prepare_routing_input_with_distances


async def execute_routing(
    db: Session,
    pickup_request_id: str
) -> Optional[Dict]:
    """
    Execute the full routing flow for a pickup request.
    
    1. Get routing input data (volunteers, dropoffs, distances)
    2. Run VSP algorithm
    3. Apply results to database
    
    Returns:
        Dictionary with routes and applied changes, or None if failed
    """
    # Step 1: Get routing input
    routing_input = await prepare_routing_input_with_distances(db, pickup_request_id)
    
    if not routing_input:
        return None
    
    # Convert Pydantic model to dict for VSP
    input_payload = {
        "distance_matrix": routing_input.distance_matrix,
        "drops_matrix": routing_input.drops_matrix,
        "item_volumes": routing_input.item_volumes,
        "car_caps": routing_input.car_caps,
        "volunteer_ids": routing_input.volunteer_ids,
        "dropoff_ids": routing_input.dropoff_ids,
        "car_contents": routing_input.car_contents,
        "item_id": routing_input.item_id
    }
    
    # Step 2: Run VSP algorithm
    routes = solve_routing(input_payload)
    
    if not routes:
        return None
    
    # Step 3: Apply results to database
    changes = apply_routing_results(
        db=db,
        routes=routes,
        volunteer_ids=routing_input.volunteer_ids,
        dropoff_ids=routing_input.dropoff_ids,
        item_id=routing_input.item_id,
        pickup_request_id=pickup_request_id
    )
    
    return {
        "pickup_request_id": pickup_request_id,
        "routes": routes,
        "changes": changes
    }


def apply_routing_results(
    db: Session,
    routes: List[List[Tuple[str, int]]],
    volunteer_ids: List[str],
    dropoff_ids: List[str],
    item_id: str,
    pickup_request_id: str
) -> Dict:
    """
    Apply routing results to the database.
    
    Each route is a list of tuples: [(location_id, load_at_that_point), ...]
    - First tuple: (volunteer_id, 0) - starting point
    - Middle tuples: (dropoff_id, load_after_pickup/dropoff)
    - Last tuple: (volunteer_id, remaining_load) - return home
    
    Updates:
    - ItemsInCar: Update volunteer car contents based on final load
    - Could also track deliveries made at each dropoff
    """
    changes = {
        "volunteers_updated": [],
        "deliveries": []
    }
    
    for route in routes:
        if len(route) < 2:
            continue
        
        # First tuple is the volunteer starting point
        volunteer_id = route[0][0]
        
        # Last tuple is volunteer returning home with remaining load
        final_load = route[-1][1]
        
        # Track deliveries made at dropoffs (middle tuples)
        for i in range(1, len(route) - 1):
            location_id, load_at_location = route[i]
            
            # This is a dropoff point
            if location_id in dropoff_ids:
                # Calculate how much was dropped off at this location
                # (difference between previous load and current load)
                if i > 0:
                    prev_load = route[i-1][1]
                    dropped_off = prev_load - load_at_location
                    
                    if dropped_off > 0:
                        changes["deliveries"].append({
                            "volunteer_id": volunteer_id,
                            "dropoff_id": location_id,
                            "item_id": item_id,
                            "quantity": dropped_off
                        })
        
        # Update volunteer's car contents with final load
        update_volunteer_car_contents(
            db=db,
            volunteer_id=volunteer_id,
            item_id=item_id,
            quantity=final_load
        )
        
        changes["volunteers_updated"].append({
            "volunteer_id": volunteer_id,
            "final_load": final_load
        })
    
    db.commit()
    
    return changes


def update_volunteer_car_contents(
    db: Session,
    volunteer_id: str,
    item_id: str,
    quantity: int
) -> None:
    """
    Add items to a volunteer's car (items they're taking home after the route).
    
    This ADDS to any existing quantity of the same item type in their car.
    """
    # Check if record exists for this item type
    existing = db.query(models.ItemsInCar).filter(
        models.ItemsInCar.userID == volunteer_id,
        models.ItemsInCar.itemVariantID == item_id
    ).first()
    
    if existing:
        # Add to existing quantity
        existing.quantity += quantity
    else:
        if quantity > 0:
            new_record = models.ItemsInCar(
                userID=volunteer_id,
                itemVariantID=item_id,
                quantity=quantity
            )
            db.add(new_record)


def get_volunteer_car_contents(
    db: Session,
    volunteer_id: str
) -> List[Dict]:
    """
    Get all items currently in a volunteer's car.
    """
    items = db.query(models.ItemsInCar).filter(
        models.ItemsInCar.userID == volunteer_id
    ).all()
    
    return [
        {
            "item_id": item.itemVariantID,
            "quantity": item.quantity
        }
        for item in items
    ]
