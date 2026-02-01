"""
Test script to verify the full routing flow:
1. Create pickup request
2. Volunteers accept and set their GPS location
3. Get routing input
4. Run VSP algorithm
5. Apply results to database

Run with: python test_full_routing.py
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database.models import Base, User, DropOffPoint, PickupPoint, PickupRequest, ItemVariant, ItemsAtPickupPoint, PickupRequestResponses, ItemsInCar
from app.services.routing_service import execute_routing, get_volunteer_car_contents
from app.vsp import solve_routing
from app import schemas


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_full_routing.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_data(db):
    """Create test data for routing."""
    
    # Create volunteers with GPS locations
    volunteers = [
        User(id="vol-1", name="Alice", karma=80, maxVolume=35, userType=0, latitude=51.5100, longitude=-0.1300),
        User(id="vol-2", name="Bob", karma=90, maxVolume=25, userType=0, latitude=51.5180, longitude=-0.1400),
        User(id="vol-3", name="Charlie", karma=100, maxVolume=40, userType=0, latitude=51.5050, longitude=-0.1200),
    ]
    for v in volunteers:
        db.add(v)
    
    # Create dropoff points (10 points in London area)
    dropoff_locations = [
        ("51.5074,-0.1278", "Westminster"),
        ("51.5155,-0.1419", "Oxford Circus"),
        ("51.5033,-0.1195", "London Eye"),
        ("51.5194,-0.1270", "Kings Cross"),
        ("51.4975,-0.1357", "Victoria"),
        ("51.5136,-0.0889", "Bank"),
        ("51.5225,-0.1543", "Baker Street"),
        ("51.5010,-0.1246", "Waterloo"),
        ("51.5145,-0.0831", "Liverpool Street"),
        ("51.5030,-0.1128", "Southwark"),
    ]
    
    for i, (loc, name) in enumerate(dropoff_locations):
        dp = DropOffPoint(id=f"drop-{i+1}", name=name, location=loc)
        db.add(dp)
    
    # Create pickup point
    pickup = PickupPoint(id="pickup-1", name="Charity Warehouse", location="51.5200,-0.1000")
    db.add(pickup)
    
    # Create 5 item types
    items = [
        ItemVariant(id="item-1", name="Canned Food", volume=5.0),
        ItemVariant(id="item-2", name="Clothing", volume=4.0),
        ItemVariant(id="item-3", name="Toiletries", volume=3.0),
        ItemVariant(id="item-4", name="Bedding", volume=8.0),
        ItemVariant(id="item-5", name="Kitchen Items", volume=2.0),
    ]
    for item in items:
        db.add(item)
    
    # Add items to pickup point
    items_at_pickup = [
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-1", quantity=2),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-2", quantity=3),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-3", quantity=2),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-4", quantity=1),
        ItemsAtPickupPoint(pickupPointID="pickup-1", itemVariantID="item-5", quantity=2),
    ]
    for iap in items_at_pickup:
        db.add(iap)
    
    # Create pickup request
    pickup_request = PickupRequest(id="request-1", pickupPointID="pickup-1")
    db.add(pickup_request)
    
    db.commit()
    return volunteers


def create_pickup_responses(db, pickup_request_id: str, volunteer_ids: list):
    """Create pickup request responses (volunteers accepting)."""
    
    for vol_id in volunteer_ids:
        response = PickupRequestResponses(
            requestID=pickup_request_id,
            userID=vol_id,
            result=1  # 1 = accepted
        )
        db.add(response)
    
    db.commit()


async def test_full_routing_flow():
    """Test the complete routing flow."""
    
    # Reset database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    try:
        print("=" * 60)
        print("FULL ROUTING FLOW TEST (Pickup Request Based)")
        print("=" * 60)
        
        # Step 1: Setup data
        print("\n1. Setting up test data...")
        volunteers = setup_test_data(db)
        print(f"   Created {len(volunteers)} volunteers with GPS locations")
        for vol in volunteers:
            print(f"     - {vol.name}: ({vol.latitude}, {vol.longitude})")
        
        # Step 2: Volunteers accept pickup request
        print("\n2. Volunteers accepting pickup request...")
        volunteer_ids = ["vol-1", "vol-2", "vol-3"]
        create_pickup_responses(db, "request-1", volunteer_ids)
        print(f"   {len(volunteer_ids)} volunteers accepted")
        
        # Step 3: Check car contents before routing
        print("\n3. Car contents BEFORE routing:")
        for vol in volunteers:
            contents = get_volunteer_car_contents(db, vol.id)
            print(f"   {vol.name} ({vol.id}): {contents if contents else 'Empty'}")
        
        # Step 4: Execute routing
        print("\n4. Executing routing algorithm...")
        result = await execute_routing(db, "request-1")
        
        if not result:
            print("   ERROR: Routing failed!")
            return False
        
        print("   Routing completed successfully!")
        
        # Step 5: Display routes
        print("\n5. Computed Routes:")
        print("-" * 60)
        for i, route in enumerate(result["routes"]):
            print(f"\n   Route {i+1}:")
            for j, (location, load) in enumerate(route):
                if j == 0:
                    print(f"     START: {location} (load: {load})")
                elif j == len(route) - 1:
                    print(f"     END:   {location} (remaining: {load})")
                else:
                    print(f"     STOP:  {location} (load after: {load})")
        
        # Step 6: Display changes
        print("\n6. Database Changes:")
        print("-" * 60)
        
        print("\n   Volunteers updated:")
        for update in result["changes"]["volunteers_updated"]:
            print(f"     - {update['volunteer_id']}: final load = {update['final_load']}")
        
        print("\n   Deliveries made:")
        for delivery in result["changes"]["deliveries"]:
            print(f"     - {delivery['volunteer_id']} dropped {delivery['quantity']} at {delivery['dropoff_id']}")
        
        # Step 7: Check car contents after routing
        print("\n7. Car contents AFTER routing:")
        for vol in volunteers:
            contents = get_volunteer_car_contents(db, vol.id)
            print(f"   {vol.name} ({vol.id}): {contents if contents else 'Empty'}")
        
        # Output as JSON
        print("\n8. Full result as JSON:")
        print("-" * 60)
        import json
        # Convert tuples to lists for JSON serialization
        json_result = {
            "pickup_request_id": result["pickup_request_id"],
            "routes": [[list(stop) for stop in route] for route in result["routes"]],
            "changes": result["changes"]
        }
        print(json.dumps(json_result, indent=2))
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY ✅")
        print("=" * 60)
        return True
        
    finally:
        db.close()


if __name__ == "__main__":
    result = asyncio.run(test_full_routing_flow())
    if not result:
        print("\nTEST FAILED ❌")
