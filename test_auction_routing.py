"""
Test script to verify auction routing input with multiple volunteers.
Run with: python test_auction_routing.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta
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
    
    # Create item variants
    items = [
        ItemVariant(id="item-small", name="Small Box", volume=5.0),
        ItemVariant(id="item-medium", name="Medium Box", volume=15.0),
        ItemVariant(id="item-large", name="Large Box", volume=30.0),
    ]
    for item in items:
        db.add(item)
    
    # Add items to pickup point
    items_at_pickup = [
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-small", quantity=3),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-medium", quantity=2),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-large", quantity=1),
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
        createdAt=datetime.utcnow(),
        expiresAt=datetime.utcnow() + timedelta(seconds=60)
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
        
        # Verify the output
        print("\n" + "=" * 60)
        print("ROUTING INPUT RESULTS:")
        print("=" * 60)
        
        print(f"\n1. volunteer_ids ({len(routing_input.volunteer_ids)} volunteers):")
        for vid in routing_input.volunteer_ids:
            print(f"   - {vid}")
        
        print(f"\n2. car_caps ({len(routing_input.car_caps)} capacities):")
        for i, cap in enumerate(routing_input.car_caps):
            print(f"   - Volunteer {i+1}: {cap} units")
        
        print(f"\n3. dropoff_ids ({len(routing_input.dropoff_ids)} dropoffs):")
        for did in routing_input.dropoff_ids:
            print(f"   - {did}")
        
        print(f"\n4. distance_matrix ({len(routing_input.distance_matrix)} rows x {len(routing_input.distance_matrix[0]) if routing_input.distance_matrix else 0} cols):")
        print("   (Travel time in minutes from each volunteer to each dropoff)")
        for i, row in enumerate(routing_input.distance_matrix):
            print(f"   Volunteer {i+1}: {[round(t, 2) for t in row]}")
        
        print(f"\n5. drops_matrix ({len(routing_input.drops_matrix)} x {len(routing_input.drops_matrix[0]) if routing_input.drops_matrix else 0}):")
        print("   (Travel time in minutes between dropoff points)")
        for i, row in enumerate(routing_input.drops_matrix):
            print(f"   From dropoff {i+1}: {[round(t, 2) for t in row]}")
        
        print(f"\n6. item_volumes ({len(routing_input.item_volumes)} items):")
        print(f"   {routing_input.item_volumes}")
        total_volume = sum(routing_input.item_volumes)
        print(f"   Total volume: {total_volume} units")
        
        # Validate structure
        print("\n" + "=" * 60)
        print("VALIDATION:")
        print("=" * 60)
        
        errors = []
        
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
        # 3 small (5.0) + 2 medium (15.0) + 1 large (30.0) = 15 + 30 + 30 = 75
        expected_volume = 3 * 5.0 + 2 * 15.0 + 1 * 30.0
        if abs(total_volume - expected_volume) > 0.01:
            errors.append(f"Expected total volume {expected_volume}, got {total_volume}")
        
        if errors:
            print("\n❌ VALIDATION FAILED:")
            for err in errors:
                print(f"   - {err}")
            return False
        else:
            print("\n✅ ALL VALIDATIONS PASSED!")
            print("\nThe routing input format is correct:")
            print("""
{
  "distance_matrix": [[vol1→d1, vol1→d2...], [vol2→d1, vol2→d2...], [vol3→d1, vol3→d2...]],
  "drops_matrix": [[d1→d1, d1→d2...], [d2→d1, d2→d2...], ...],
  "item_volumes": [5.0, 5.0, 5.0, 15.0, 15.0, 30.0],
  "car_caps": [30.0, 50.0, 40.0],
  "volunteer_ids": ["volunteer-1", "volunteer-2", "volunteer-3"],
  "dropoff_ids": ["dropoff-1", "dropoff-2", "dropoff-3", "dropoff-4", "dropoff-5"]
}
            """)
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
