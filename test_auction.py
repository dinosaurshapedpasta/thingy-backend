#!/usr/bin/env python3
"""
Test script for the auction routing system.

This demonstrates the full workflow:
1. Create a pickup request
2. Simulate volunteer responses with GPS locations
3. Calculate travel times and adjacency matrix
4. Generate routes

Run this to test the system end-to-end.
"""

import asyncio
import os
import random
from sqlalchemy.orm import Session

from app.database.config import SessionLocal, Base, engine
from app.database import crud, models
from app import schemas
from app.auction import auction_manager, handle_pickup_request


def generate_random_london_location() -> str:
    """
    Generate random GPS coordinates in and around Central London.

    Returns:
        String in format "lat,lon"
    """
    # Central London boundaries
    # Latitude: 51.4 to 51.6 (covers most of central London)
    # Longitude: -0.3 to 0.1 (west to east London)

    lat = random.uniform(51.4, 51.6)
    lon = random.uniform(-0.3, 0.1)

    return f"{lat:.6f},{lon:.6f}"


def get_london_landmark_location() -> tuple[str, str]:
    """
    Get a random London landmark location for pickup point.

    Returns:
        Tuple of (name, location)
    """
    landmarks = [
        ("Tower Bridge Food Bank", "51.5055,-0.0754"),
        ("Westminster Community Center", "51.5014,-0.1419"),
        ("Camden Market Hub", "51.5415,-0.1426"),
        ("Kensington Aid Point", "51.4900,-0.1900"),
        ("Greenwich Food Hub", "51.4826,0.0077"),
        ("Shoreditch Distribution", "51.5250,-0.0800"),
        ("Brixton Community Kitchen", "51.4615,-0.1145"),
        ("Notting Hill Center", "51.5095,-0.2000"),
    ]

    name, location = random.choice(landmarks)
    return name, location


async def test_auction_workflow():
    """Test the complete auction workflow with real data."""

    print("=" * 60)
    print("TESTING AUCTION ROUTING SYSTEM")
    print("=" * 60)

    # Check API key
    if not os.getenv("OPENROUTE_API_KEY"):
        print("\n⚠️  WARNING: OPENROUTE_API_KEY not set!")
        print("Get a free key at: https://openrouteservice.org/dev/#/signup")
        print("Then: export OPENROUTE_API_KEY=your_key_here\n")

    db: Session = SessionLocal()

    try:
        # 1. Setup test data
        print("\n1️⃣  Setting up test data...")

        # Create test pickup point (random London landmark)
        pickup_point = await create_test_pickup_point(db)
        print(f"   ✓ Created pickup point: {pickup_point.name}")
        print(f"     Location: {pickup_point.location} (lat,lon)")

        # Create test volunteers
        volunteers = await create_test_volunteers(db)
        print(f"   ✓ Created {len(volunteers)} test volunteers:")
        for v in volunteers:
            print(f"     - {v.name} (karma: {v.karma}, capacity: {v.maxVolume}L)")

        # 2. Create pickup request
        print("\n2️⃣  Creating pickup request...")
        pickup_request = schemas.PickupRequest(
            id="test_request_001",
            pickupPointID=pickup_point.id
        )
        db_request = crud.create_pickup_request(db, pickup_request)
        print(f"   ✓ Created pickup request: {db_request.id}")

        # 3. Simulate volunteer responses with random London locations
        print("\n3️⃣  Simulating volunteer responses (Y/N with GPS)...")
        print(f"     Pickup point is at: {pickup_point.location}\n")

        # Generate random locations for volunteers
        volunteer_locations = [
            generate_random_london_location(),  # Alice
            generate_random_london_location(),  # Bob
            None  # Charlie (will deny)
        ]

        # Volunteer 1: Alice accepts
        alice_location = volunteer_locations[0]
        response_1 = models.PickupRequestResponses(
            requestID=db_request.id,
            userID=volunteers[0].id,
            result=1,  # Accept
            location=alice_location  # Store GPS location
        )
        db.add(response_1)

        auction_manager.add_response(
            db_request.id,
            volunteers[0].id,
            accepted=True,
            gps_location=alice_location
        )
        print(f"   ✓ {volunteers[0].name} accepted")
        print(f"     Current location: {alice_location}")

        # Volunteer 2: Bob accepts
        bob_location = volunteer_locations[1]
        response_2 = models.PickupRequestResponses(
            requestID=db_request.id,
            userID=volunteers[1].id,
            result=1,  # Accept
            location=bob_location  # Store GPS location
        )
        db.add(response_2)

        auction_manager.add_response(
            db_request.id,
            volunteers[1].id,
            accepted=True,
            gps_location=bob_location
        )
        print(f"   ✓ {volunteers[1].name} accepted")
        print(f"     Current location: {bob_location}")

        # Volunteer 3: Charlie denies
        response_3 = models.PickupRequestResponses(
            requestID=db_request.id,
            userID=volunteers[2].id,
            result=0,  # Deny
            location=None  # No location needed for denial
        )
        db.add(response_3)

        auction_manager.add_response(
            db_request.id,
            volunteers[2].id,
            accepted=False,
            gps_location=None
        )
        print(f"   ✗ {volunteers[2].name} denied")

        db.commit()

        # 4. Start auction (this will wait 60 seconds and process)
        print("\n4️⃣  Starting auction...")
        print("   ⏳ Normally waits 60 seconds for responses...")
        print("   ⚡ Skipping wait for demo (modifying auction manager)\n")

        # For testing, we'll directly call _process_responses instead of waiting
        auction_manager.active_auctions[db_request.id] = {
            "request_id": db_request.id,
            "pickup_point_id": pickup_point.id,
            "start_time": None,
            "responses": [],
            "status": "waiting"
        }

        # Process responses immediately
        print("   📊 Calculating travel times and costs...\n")
        await auction_manager._process_responses(db_request.id, db)
        print()  # Extra newline for readability

        print("\n5️⃣  Results:")
        auction_data = auction_manager.active_auctions.get(db_request.id)
        if auction_data:
            print(f"   Auction Status: {auction_data['status']}")

            if auction_data['status'] == 'completed' and auction_data.get('routes'):
                print("\n   🎯 ROUTE ASSIGNMENT:")
                print("   " + "-" * 56)

                routes = auction_data['routes']
                for route in routes:
                    volunteer_id = route['user_id']
                    cost = route['cost']
                    details = route['volunteer_details']

                    # Get volunteer name
                    volunteer = crud.get_user(db, volunteer_id)
                    name = volunteer.name if volunteer else volunteer_id

                    print(f"\n   ✓ WINNER: {name}")
                    print(f"     User ID:  {volunteer_id}")
                    print(f"     Cost:     {cost:.2f} (LOWEST = BEST)")
                    print(f"     Karma:    {details['karma']}")
                    print(f"     Capacity: {details['capacity']}L")
                    print(f"     Route:    {' → '.join(route['route'])}")

                print("\n   " + "-" * 56)
                print("   💡 Lower cost = better match")
                print("      (closer distance + higher karma + more capacity)")

            elif auction_data['status'] == 'failed_no_volunteers':
                print("\n   ❌ No volunteers accepted the pickup request")

        print("\n" + "=" * 60)
        print("✅ Test completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup test data
        print("\n🧹 Cleaning up test data...")
        cleanup_test_data(db)
        db.close()
        print("   ✓ Cleanup complete\n")


async def create_test_pickup_point(db: Session) -> models.PickupPoint:
    """Create a test pickup point at a random London landmark."""
    landmark_name, landmark_location = get_london_landmark_location()

    pickup_point = schemas.PickupPointCreate(
        id="test_pickup_001",
        name=landmark_name,
        location=landmark_location
    )

    # Delete if exists
    existing = crud.get_pickup_point(db, pickup_point.id)
    if existing:
        db.delete(existing)
        db.commit()

    return crud.create_pickup_point(db, pickup_point)


async def create_test_volunteers(db: Session) -> list[models.User]:
    """Create test volunteer users with different karma and capacity."""
    volunteers_data = [
        {
            "id": "test_volunteer_001",
            "name": "Alice (High Karma, Large Capacity)",
            "karma": 95,
            "maxVolume": 200.0,
            "userType": 1  # Volunteer
        },
        {
            "id": "test_volunteer_002",
            "name": "Bob (Medium Karma, Medium Capacity)",
            "karma": 50,
            "maxVolume": 100.0,
            "userType": 1
        },
        {
            "id": "test_volunteer_003",
            "name": "Charlie (Low Karma, Small Capacity)",
            "karma": 20,
            "maxVolume": 50.0,
            "userType": 1
        }
    ]

    volunteers = []
    for v_data in volunteers_data:
        # Delete if exists
        existing = crud.get_user(db, v_data["id"])
        if existing:
            db.delete(existing)
            db.commit()

        volunteer = crud.create_user(db, schemas.UserCreate(**v_data))
        volunteers.append(volunteer)

    return volunteers


def cleanup_test_data(db: Session):
    """Remove all test data from database."""
    try:
        # Delete test pickup request responses
        db.query(models.PickupRequestResponses).filter(
            models.PickupRequestResponses.requestID.like("test_%")
        ).delete(synchronize_session=False)

        # Delete test pickup requests
        db.query(models.PickupRequest).filter(
            models.PickupRequest.id.like("test_%")
        ).delete(synchronize_session=False)

        # Delete test pickup points
        db.query(models.PickupPoint).filter(
            models.PickupPoint.id.like("test_%")
        ).delete(synchronize_session=False)

        # Delete test users
        db.query(models.User).filter(
            models.User.id.like("test_%")
        ).delete(synchronize_session=False)

        db.commit()
    except Exception as e:
        print(f"   ⚠️  Warning during cleanup: {e}")
        db.rollback()


async def test_travel_time_api():
    """Test the Maps API integration directly."""
    print("\n" + "=" * 60)
    print("TESTING MAPS API INTEGRATION")
    print("=" * 60)

    if not os.getenv("OPENROUTE_API_KEY"):
        print("\n⚠️  OPENROUTE_API_KEY not set. Skipping API test.")
        print("Get a free key at: https://openrouteservice.org/dev/#/signup\n")
        return

    # Test with random London locations
    origin = generate_random_london_location()
    destination = generate_random_london_location()

    print("\nTesting travel time calculation between two random London points...")
    print(f"Origin:      {origin}")
    print(f"Destination: {destination}")
    print("\nCalculating route...")

    manager = auction_manager
    travel_time = await manager._get_travel_time(
        origin=origin,
        destination=destination
    )

    print(f"\n✓ Travel time: {travel_time:.1f} minutes by car")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n🚀 Starting Auction System Tests\n")

    # Create database tables
    print("📦 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("   ✓ Database tables created\n")

    print("📍 Using random locations in Central London")
    print("   Boundaries: 51.4°-51.6° N, 0.3°W-0.1°E")
    print("   Covers: Westminster, Camden, Tower Bridge, Greenwich, etc.\n")

    # Test 1: Maps API integration
    asyncio.run(test_travel_time_api())

    # Test 2: Full auction workflow
    asyncio.run(test_auction_workflow())

    print("🎉 All tests completed!")
    print("\n💡 Run again to test with different random locations!\n")
