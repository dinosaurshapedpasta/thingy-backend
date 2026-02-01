"""
Test script to verify auction routing input with multiple volunteers.
Run with: python test_auction_routing.py
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database.models import Base, User, DropOffPoint, PickupPoint, PickupRequest, ItemVariant, ItemsAtPickupPoint, Auction, AuctionBid
from app.services.auction_service import prepare_routing_input_with_distances, create_auction, submit_bid
from app import schemas


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_routing.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_data(db):
    """Create test data with multiple volunteers, dropoffs, and items."""
    
    # Create multiple volunteers with different capacities
    volunteers = [
        User(
            id="volunteer-1",
            name="Alice",
            karma=80,
            maxVolume=30.0,
            userType=0
        ),
        User(
            id="volunteer-2", 
            name="Bob",
            karma=90,
            maxVolume=50.0,
            userType=0
        ),
        User(
            id="volunteer-3",
            name="Charlie",
            karma=100,
            maxVolume=40.0,
            userType=0
        )
    ]
    for v in volunteers:
        db.add(v)
    
    # Create dropoff points in London area
    dropoff_locations = [
        ("51.5074,-0.1278", "Westminster"),      # Central London
        ("51.5155,-0.1419", "Oxford Circus"),    # Shopping district
        ("51.5033,-0.1195", "London Eye"),       # South Bank
        ("51.5194,-0.1270", "Kings Cross"),      # North
        ("51.4975,-0.1357", "Victoria"),         # Southwest
    ]
    
    dropoffs = []
    for i, (loc, name) in enumerate(dropoff_locations):
        dp = DropOffPoint(
            id=f"dropoff-{i+1}",
            name=name,
            location=loc
        )
        dropoffs.append(dp)
        db.add(dp)
    
    # Create pickup point
    pickup = PickupPoint(
        id="pickup-1",
        name="Charity Warehouse",
        location="51.5200,-0.1000"  # East London
    )
    db.add(pickup)
    
    # Create 5 item variants (types)
    items = [
        ItemVariant(id="item-type-1", name="Canned Food", volume=2.0),
        ItemVariant(id="item-type-2", name="Clothing", volume=5.0),
        ItemVariant(id="item-type-3", name="Toiletries", volume=3.0),
        ItemVariant(id="item-type-4", name="Bedding", volume=15.0),
        ItemVariant(id="item-type-5", name="Kitchen Items", volume=10.0),
    ]
    for item in items:
        db.add(item)
    
    # Add items to pickup point (some quantity of each type)
    items_at_pickup = [
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-type-1", quantity=4),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-type-2", quantity=3),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-type-3", quantity=2),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-type-4", quantity=1),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-type-5", quantity=2),
    ]
    for iap in items_at_pickup:
        db.add(iap)
    
    # Create pickup request
    pickup_request = PickupRequest(
        id="request-1",
        pickupPointID="pickup-1"
    )
    db.add(pickup_request)
    
    db.commit()
    
    return {
        "volunteers": volunteers,
        "dropoffs": dropoffs,
        "pickup_request": pickup_request
    }


def create_auction_with_bids(db, pickup_request_id: str, volunteer_bids: list):
    """
    Create an auction and simulate multiple volunteers accepting.
    
    volunteer_bids: list of tuples (volunteer_id, latitude, longitude)
    """
    # Create auction
    auction = Auction(
        id=f"auction-{uuid.uuid4().hex[:8]}",
        pickupRequestID=pickup_request_id,
        status="active",
        createdAt=datetime.utcnow()
    )
    db.add(auction)
    db.commit()
    
    # Submit bids from each volunteer
    for vol_id, lat, lon in volunteer_bids:
        bid = AuctionBid(
            auctionID=auction.id,
            userID=vol_id,
            accepted=True,
            latitude=lat,
            longitude=lon,
            estimatedTime=10.0,
            score=0.5,
            createdAt=datetime.utcnow()
        )
        db.add(bid)
    
    db.commit()
    return auction


async def test_routing_input_with_multiple_volunteers():
    """Test that routing input includes ALL available volunteers."""
    
    # Reset database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    try:
        # Setup test data
        print("=" * 60)
        print("Setting up test data...")
        data = setup_test_data(db)
        
        # Create auction with multiple volunteer bids
        # Volunteers at different locations in London
        volunteer_bids = [
            ("volunteer-1", 51.5100, -0.1300),  # Near Westminster
            ("volunteer-2", 51.5180, -0.1400),  # Near Oxford Circus
            ("volunteer-3", 51.5050, -0.1200),  # Near London Eye
        ]
        
        auction = create_auction_with_bids(db, "request-1", volunteer_bids)
        print(f"\nCreated auction: {auction.id}")
        print(f"  - Status: {auction.status}")
        print(f"  - Number of accepted bids: {len(volunteer_bids)}")
        
        # Get routing input with real distances
        print("\n" + "=" * 60)
        print("Calling prepare_routing_input_with_distances()...")
        print("(This will call OpenRouteService API for real travel times)")
        
        routing_input = await prepare_routing_input_with_distances(db, auction.id)
        
        if routing_input is None:
            print("\nERROR: routing_input is None!")
            return False
        
        # Print the actual JSON output
        print("\n" + "=" * 60)
        print("ROUTING INPUT (JSON):")
        print("=" * 60)
        
        import json
        output = {
            "distance_matrix": [[round(t, 2) for t in row] for row in routing_input.distance_matrix],
            "drops_matrix": [[round(t, 2) for t in row] for row in routing_input.drops_matrix],
            "item_volumes": routing_input.item_volumes,
            "car_caps": routing_input.car_caps,
            "volunteer_ids": routing_input.volunteer_ids,
            "dropoff_ids": routing_input.dropoff_ids,
            "car_contents": routing_input.car_contents,
            "item_id": routing_input.item_id
        }
        print(json.dumps(output, indent=2))
        
        # Validate structure
        print("\n" + "=" * 60)
        print("VALIDATION:")
        print("=" * 60)
        
        errors = []
        total_volume = sum(routing_input.item_volumes)
        
        # Check volunteer count matches
        if len(routing_input.volunteer_ids) != 3:
            errors.append(f"Expected 3 volunteers, got {len(routing_input.volunteer_ids)}")
        
        if len(routing_input.car_caps) != 3:
            errors.append(f"Expected 3 car capacities, got {len(routing_input.car_caps)}")
        
        if len(routing_input.distance_matrix) != 3:
            errors.append(f"Expected 3 rows in distance_matrix, got {len(routing_input.distance_matrix)}")
        
        # Check dropoff count
        if len(routing_input.dropoff_ids) != 5:
            errors.append(f"Expected 5 dropoffs, got {len(routing_input.dropoff_ids)}")
        
        # Check matrix dimensions
        for i, row in enumerate(routing_input.distance_matrix):
            if len(row) != 5:
                errors.append(f"distance_matrix row {i} has {len(row)} columns, expected 5")
        
        # Check item volumes
        # 4 type-1 (2.0) + 3 type-2 (5.0) + 2 type-3 (3.0) + 1 type-4 (15.0) + 2 type-5 (10.0)
        # = 8 + 15 + 6 + 15 + 20 = 64
        expected_volume = 4 * 2.0 + 3 * 5.0 + 2 * 3.0 + 1 * 15.0 + 2 * 10.0
        if abs(total_volume - expected_volume) > 0.01:
            errors.append(f"Expected total volume {expected_volume}, got {total_volume}")
        
        # Check car_contents - should have 3 volunteers, each with vector for 5 item types
        if len(routing_input.car_contents) != 3:
            errors.append(f"Expected 3 car_contents rows (one per volunteer), got {len(routing_input.car_contents)}")
        
        # Each car should have a vector of 5 zeros (one per item type)
        for i, car in enumerate(routing_input.car_contents):
            if len(car) != 5:
                errors.append(f"car_contents[{i}] has {len(car)} elements, expected 5 (one per item type)")
        
        # Check item_id is set
        if not routing_input.item_id:
            errors.append("item_id is empty, expected an item variant ID")
        
        if errors:
            print("\n❌ VALIDATION FAILED:")
            for err in errors:
                print(f"   - {err}")
            return False
        else:
            print("\n✅ ALL VALIDATIONS PASSED!")
            return True
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING AUCTION ROUTING INPUT WITH MULTIPLE VOLUNTEERS")
    print("=" * 60)
    
    result = asyncio.run(test_routing_input_with_multiple_volunteers())
    
    print("\n" + "=" * 60)
    if result:
        print("TEST PASSED ✅")
    else:
        print("TEST FAILED ❌")
    print("=" * 60)
