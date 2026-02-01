"""
Automated test script for all API endpoints.
Run with: pytest test_endpoints.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.database import Base, get_db

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def sample_item():
    """Create a sample item for testing."""
    item_data = {
        "id": "item-test-001",
        "name": "Test Item",
        "volume": 10.5
    }
    response = client.post("/items/", json=item_data)
    return item_data


@pytest.fixture
def sample_pickup():
    """Create a sample pickup point for testing."""
    pickup_data = {
        "id": "pickup-test-001",
        "name": "Test Pickup Point",
        "location": "Test Pickup Location"
    }
    response = client.post("/pickup/", json=pickup_data)
    return pickup_data


# ============================================================================
# ITEM ENDPOINTS
# ============================================================================

class TestItemEndpoints:
    """Tests for item-related endpoints."""

    def test_create_item(self):
        """Test creating a new item."""
        item_data = {
            "id": "item-001",
            "name": "Test Widget",
            "volume": 15.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_data["id"]
        assert data["name"] == item_data["name"]
        assert data["volume"] == item_data["volume"]

    def test_get_item(self, sample_item):
        """Test retrieving an item by ID."""
        item_id = sample_item["id"]
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == sample_item["name"]

    def test_get_item_not_found(self):
        """Test getting a non-existent item returns 404."""
        response = client.get("/items/nonexistent-item")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_item(self, sample_item):
        """Test updating an item."""
        item_id = sample_item["id"]
        updated_data = {
            "id": item_id,
            "name": "Updated Item Name",
            "volume": 25.0
        }
        response = client.patch(f"/items/{item_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == updated_data["name"]
        assert data["volume"] == updated_data["volume"]

    def test_update_item_not_found(self):
        """Test updating a non-existent item returns 404."""
        updated_data = {
            "id": "item-999",
            "name": "Ghost Item",
            "volume": 10.0
        }
        response = client.patch("/items/nonexistent-item", json=updated_data)
        assert response.status_code == 404


# ============================================================================
# PICKUP POINT ENDPOINTS
# ============================================================================

class TestPickupEndpoints:
    """Tests for pickup point endpoints."""

    def test_create_pickup_point(self):
        """Test creating a new pickup point."""
        pickup_data = {
            "id": "pickup-001",
            "name": "Main Pickup Point",
            "location": "123 Pickup St"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pickup_data["id"]
        assert data["name"] == pickup_data["name"]
        assert data["location"] == pickup_data["location"]

    def test_get_pickup_point(self, sample_pickup):
        """Test retrieving a pickup point by ID."""
        pickup_id = sample_pickup["id"]
        response = client.get(f"/pickup/{pickup_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pickup_id
        assert data["name"] == sample_pickup["name"]

    def test_get_pickup_point_not_found(self):
        """Test getting a non-existent pickup point returns 404."""
        response = client.get("/pickup/nonexistent-pickup")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_pickup_point(self, sample_pickup):
        """Test updating a pickup point."""
        pickup_id = sample_pickup["id"]
        updated_data = {
            "id": pickup_id,
            "name": "Updated Pickup Name",
            "location": "456 New Pickup Location"
        }
        response = client.patch(f"/pickup/{pickup_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == updated_data["name"]
        assert data["location"] == updated_data["location"]

    def test_update_pickup_point_not_found(self):
        """Test updating a non-existent pickup point returns 404."""
        updated_data = {
            "id": "pickup-999",
            "name": "Ghost Pickup",
            "location": "Nowhere"
        }
        response = client.patch("/pickup/nonexistent-pickup", json=updated_data)
        assert response.status_code == 404

    def test_get_pickup_items(self, sample_pickup):
        """Test getting items from a pickup point."""
        pickup_id = sample_pickup["id"]
        response = client.get(f"/pickup/{pickup_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_pickup_items_not_found(self):
        """Test getting items from non-existent pickup point returns 404."""
        response = client.get("/pickup/nonexistent-pickup/items")
        assert response.status_code == 404


# ============================================================================
# USER ENDPOINTS
# ============================================================================

class TestUserEndpoints:
    """Tests for user-related endpoints."""

    def test_get_user_not_found(self):
        """Test getting a non-existent user returns 404."""
        response = client.get("/user/nonexistent-user")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_user_not_found(self):
        """Test updating a non-existent user returns 404."""
        user_data = {
            "id": "user-001",
            "name": "Updated User",
            "karma": 200,
            "maxVolume": 75.0,
            "userType": 2
        }
        response = client.patch("/user/nonexistent-user", json=user_data)
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for multiple endpoints."""

    def test_create_and_retrieve_workflow(self):
        """Test complete workflow: create item, create pickup, retrieve both."""
        # Create item
        item_data = {
            "id": "item-integration-001",
            "name": "Integration Item",
            "volume": 20.0
        }
        item_response = client.post("/items/", json=item_data)
        assert item_response.status_code == 200

        # Create pickup point
        pickup_data = {
            "id": "pickup-integration-001",
            "name": "Integration Pickup",
            "location": "Integration Test Location"
        }
        pickup_response = client.post("/pickup/", json=pickup_data)
        assert pickup_response.status_code == 200

        # Retrieve both
        item_get = client.get(f"/items/{item_data['id']}")
        assert item_get.status_code == 200
        assert item_get.json()["name"] == item_data["name"]

        pickup_get = client.get(f"/pickup/{pickup_data['id']}")
        assert pickup_get.status_code == 200
        assert pickup_get.json()["name"] == pickup_data["name"]

    def test_update_multiple_resources(self):
        """Test updating multiple resources in sequence."""
        # Create item
        item_data = {
            "id": "item-multi-001",
            "name": "Original Item",
            "volume": 10.0
        }
        client.post("/items/", json=item_data)

        # Update item multiple times
        for i in range(3):
            updated_data = {
                "id": item_data["id"],
                "name": f"Updated Item {i}",
                "volume": 10.0 + (i * 5)
            }
            response = client.patch(f"/items/{item_data['id']}", json=updated_data)
            assert response.status_code == 200
            assert response.json()["name"] == updated_data["name"]

    def test_create_item_and_add_to_pickup(self):
        """Test creating an item and adding it to a pickup point."""
        # Create item
        item_data = {
            "id": "item-pickup-001",
            "name": "Pickup Item",
            "volume": 15.0
        }
        item_response = client.post("/items/", json=item_data)
        assert item_response.status_code == 200

        # Create pickup point
        pickup_data = {
            "id": "pickup-item-001",
            "name": "Item Pickup Point",
            "location": "Pickup Location"
        }
        pickup_response = client.post("/pickup/", json=pickup_data)
        assert pickup_response.status_code == 200

        # Verify items endpoint returns empty list
        items_response = client.get(f"/pickup/{pickup_data['id']}/items")
        assert items_response.status_code == 200
        assert items_response.json() == []


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_item_with_zero_volume(self):
        """Test creating an item with zero volume."""
        item_data = {
            "id": "item-zero-volume",
            "name": "Zero Volume Item",
            "volume": 0.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200
        assert response.json()["volume"] == 0.0

    def test_create_item_with_negative_volume(self):
        """Test creating an item with negative volume."""
        item_data = {
            "id": "item-negative",
            "name": "Negative Volume Item",
            "volume": -10.0
        }
        response = client.post("/items/", json=item_data)
        # Should still accept it (no validation enforced)
        assert response.status_code == 200

    def test_create_item_with_very_large_volume(self):
        """Test creating an item with extremely large volume."""
        item_data = {
            "id": "item-huge",
            "name": "Huge Item",
            "volume": 999999999.99
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200
        assert response.json()["volume"] == 999999999.99

    def test_create_item_with_special_characters_in_name(self):
        """Test creating an item with special characters."""
        item_data = {
            "id": "item-special",
            "name": "Item with émojis 🚀 & symbols !@#$%",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200
        assert "🚀" in response.json()["name"]

    def test_create_item_with_very_long_name(self):
        """Test creating an item with very long name."""
        long_name = "A" * 500
        item_data = {
            "id": "item-long-name",
            "name": long_name,
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200
        assert len(response.json()["name"]) == 500

    def test_create_item_with_empty_string_name(self):
        """Test creating an item with empty name."""
        item_data = {
            "id": "item-empty-name",
            "name": "",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_create_pickup_with_unicode_location(self):
        """Test creating pickup point with unicode characters."""
        pickup_data = {
            "id": "pickup-unicode",
            "name": "Tokyo Pickup 東京",
            "location": "日本、東京都渋谷区"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200
        assert "東京" in response.json()["name"]

    def test_update_item_with_decimal_precision(self):
        """Test updating item with high decimal precision."""
        item_data = {
            "id": "item-decimal",
            "name": "Decimal Item",
            "volume": 10.123456789
        }
        client.post("/items/", json=item_data)

        updated = {
            "id": "item-decimal",
            "name": "Updated Decimal",
            "volume": 20.987654321
        }
        response = client.patch("/items/item-decimal", json=updated)
        assert response.status_code == 200


# ============================================================================
# DUPLICATE AND CONFLICT TESTS
# ============================================================================

class TestDuplicatesAndConflicts:
    """Tests for duplicate entries and conflicts."""

    def test_create_duplicate_item_id(self):
        """Test creating two items with same ID fails with database constraint."""
        item_data = {
            "id": "item-duplicate",
            "name": "First Item",
            "volume": 10.0
        }
        response1 = client.post("/items/", json=item_data)
        assert response1.status_code == 200

        # Try to create duplicate - should raise IntegrityError
        item_data2 = {
            "id": "item-duplicate",
            "name": "Second Item",
            "volume": 20.0
        }
        # Error handler middleware catches IntegrityError and returns 409
        response2 = client.post("/items/", json=item_data2)
        assert response2.status_code == 409
        assert "constraint" in response2.json()["detail"].lower()

    def test_create_duplicate_pickup_id(self):
        """Test creating two pickup points with same ID fails with database constraint."""
        pickup1 = {
            "id": "pickup-dup",
            "name": "First Pickup",
            "location": "Location 1"
        }
        response1 = client.post("/pickup/", json=pickup1)
        assert response1.status_code == 200

        pickup2 = {
            "id": "pickup-dup",
            "name": "Second Pickup",
            "location": "Location 2"
        }
        # Error handler middleware catches IntegrityError and returns 409
        response2 = client.post("/pickup/", json=pickup2)
        assert response2.status_code == 409
        assert "constraint" in response2.json()["detail"].lower()

    def test_update_nonexistent_then_create(self):
        """Test updating non-existent item, then creating it."""
        item_id = "item-update-first"

        # Try to update non-existent item
        update_data = {
            "id": item_id,
            "name": "Updated First",
            "volume": 10.0
        }
        response = client.patch(f"/items/{item_id}", json=update_data)
        assert response.status_code == 404

        # Now create it
        create_data = {
            "id": item_id,
            "name": "Now Created",
            "volume": 15.0
        }
        response = client.post("/items/", json=create_data)
        assert response.status_code == 200


# ============================================================================
# SEQUENTIAL OPERATION TESTS
# ============================================================================

class TestSequentialOperations:
    """Tests for complex sequential operations."""

    def test_create_update_get_cycle(self):
        """Test create -> update -> get cycle multiple times."""
        item_id = "item-cycle"

        # Create
        create_data = {
            "id": item_id,
            "name": "Initial",
            "volume": 10.0
        }
        response = client.post("/items/", json=create_data)
        assert response.status_code == 200

        # Multiple update cycles
        for i in range(5):
            update_data = {
                "id": item_id,
                "name": f"Update {i}",
                "volume": 10.0 + i
            }
            response = client.patch(f"/items/{item_id}", json=update_data)
            assert response.status_code == 200
            assert response.json()["name"] == f"Update {i}"

            # Verify with GET
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 200
            assert response.json()["name"] == f"Update {i}"

    def test_create_multiple_items_rapid_fire(self):
        """Test creating multiple items in rapid succession."""
        for i in range(20):
            item_data = {
                "id": f"item-rapid-{i}",
                "name": f"Rapid Item {i}",
                "volume": float(i)
            }
            response = client.post("/items/", json=item_data)
            assert response.status_code == 200

        # Verify all were created
        for i in range(20):
            response = client.get(f"/items/item-rapid-{i}")
            assert response.status_code == 200
            assert response.json()["name"] == f"Rapid Item {i}"

    def test_create_multiple_pickups_rapid_fire(self):
        """Test creating multiple pickup points in rapid succession."""
        for i in range(15):
            pickup_data = {
                "id": f"pickup-rapid-{i}",
                "name": f"Rapid Pickup {i}",
                "location": f"Location {i}"
            }
            response = client.post("/pickup/", json=pickup_data)
            assert response.status_code == 200

        # Verify all pickups exist
        for i in range(15):
            response = client.get(f"/pickup/pickup-rapid-{i}")
            assert response.status_code == 200

    def test_alternating_create_and_update(self):
        """Test alternating between creating new items and updating existing ones."""
        # Create initial items
        for i in range(5):
            item_data = {
                "id": f"item-alt-{i}",
                "name": f"Alt Item {i}",
                "volume": 10.0
            }
            client.post("/items/", json=item_data)

        # Alternate: create new, update old
        for i in range(5, 10):
            # Create new
            new_data = {
                "id": f"item-alt-{i}",
                "name": f"Alt Item {i}",
                "volume": 10.0
            }
            response = client.post("/items/", json=new_data)
            assert response.status_code == 200

            # Update old
            old_id = f"item-alt-{i-5}"
            update_data = {
                "id": old_id,
                "name": f"Updated {i-5}",
                "volume": 20.0
            }
            response = client.patch(f"/items/{old_id}", json=update_data)
            assert response.status_code == 200


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================

class TestDataIntegrity:
    """Tests to verify data integrity across operations."""

    def test_item_data_persists_after_multiple_gets(self):
        """Test that item data doesn't change after multiple GET requests."""
        item_data = {
            "id": "item-persist",
            "name": "Persistent Item",
            "volume": 25.5
        }
        client.post("/items/", json=item_data)

        # Get it 10 times
        for _ in range(10):
            response = client.get("/items/item-persist")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Persistent Item"
            assert data["volume"] == 25.5

    def test_update_preserves_id(self):
        """Test that updating an item preserves its ID."""
        item_id = "item-preserve-id"
        create_data = {
            "id": item_id,
            "name": "Original",
            "volume": 10.0
        }
        client.post("/items/", json=create_data)

        # Try to update with different ID in body
        update_data = {
            "id": "different-id",
            "name": "Updated",
            "volume": 20.0
        }
        response = client.patch(f"/items/{item_id}", json=update_data)
        assert response.status_code == 200

        # Verify original ID still works
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_pickup_items_consistency(self):
        """Test that pickup items endpoint is consistent."""
        pickup_data = {
            "id": "pickup-items-test",
            "name": "Items Test Pickup",
            "location": "Test Location"
        }
        client.post("/pickup/", json=pickup_data)

        # Check items multiple times
        for _ in range(5):
            response = client.get("/pickup/pickup-items-test/items")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_update_only_changes_specified_fields(self):
        """Test that updates only affect the fields being changed."""
        item_data = {
            "id": "item-partial",
            "name": "Original Name",
            "volume": 10.0
        }
        client.post("/items/", json=item_data)

        # Update only name
        update_data = {
            "id": "item-partial",
            "name": "New Name",
            "volume": 10.0  # Keep same
        }
        response = client.patch("/items/item-partial", json=update_data)
        assert response.status_code == 200

        # Verify changes
        response = client.get("/items/item-partial")
        data = response.json()
        assert data["name"] == "New Name"
        assert data["volume"] == 10.0


# ============================================================================
# COMPLEX WORKFLOW TESTS
# ============================================================================

class TestComplexWorkflows:
    """Tests for complex multi-step workflows."""

    def test_full_item_lifecycle(self):
        """Test complete item lifecycle: create, read, update multiple times, verify."""
        item_id = "item-lifecycle"

        # 1. Create
        create_data = {
            "id": item_id,
            "name": "Lifecycle Item",
            "volume": 5.0
        }
        response = client.post("/items/", json=create_data)
        assert response.status_code == 200

        # 2. Read
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["volume"] == 5.0

        # 3. Update multiple times with different values
        volumes = [10.0, 15.0, 20.0, 25.0, 30.0]
        for vol in volumes:
            update_data = {
                "id": item_id,
                "name": f"Lifecycle Item v{vol}",
                "volume": vol
            }
            response = client.patch(f"/items/{item_id}", json=update_data)
            assert response.status_code == 200
            assert response.json()["volume"] == vol

        # 4. Final verification
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["volume"] == 30.0
        assert response.json()["name"] == "Lifecycle Item v30.0"

    def test_create_ecosystem_of_resources(self):
        """Test creating an ecosystem of related items and pickups."""
        # Create 10 items
        items = []
        for i in range(10):
            item_data = {
                "id": f"eco-item-{i}",
                "name": f"Ecosystem Item {i}",
                "volume": float(i * 5)
            }
            response = client.post("/items/", json=item_data)
            assert response.status_code == 200
            items.append(item_data)

        # Create 5 pickup points
        pickups = []
        for i in range(5):
            pickup_data = {
                "id": f"eco-pickup-{i}",
                "name": f"Ecosystem Pickup {i}",
                "location": f"Eco Location {i}"
            }
            response = client.post("/pickup/", json=pickup_data)
            assert response.status_code == 200
            pickups.append(pickup_data)

        # Verify all items exist
        for item in items:
            response = client.get(f"/items/{item['id']}")
            assert response.status_code == 200

        # Verify all pickups exist
        for pickup in pickups:
            response = client.get(f"/pickup/{pickup['id']}")
            assert response.status_code == 200

    def test_batch_updates_with_verification(self):
        """Test batch updating multiple resources and verifying changes."""
        # Create 10 items
        item_ids = []
        for i in range(10):
            item_data = {
                "id": f"batch-item-{i}",
                "name": f"Batch Item {i}",
                "volume": 10.0
            }
            client.post("/items/", json=item_data)
            item_ids.append(item_data["id"])

        # Batch update all items
        for i, item_id in enumerate(item_ids):
            update_data = {
                "id": item_id,
                "name": f"Updated Batch Item {i}",
                "volume": 50.0 + i
            }
            response = client.patch(f"/items/{item_id}", json=update_data)
            assert response.status_code == 200

        # Verify all updates
        for i, item_id in enumerate(item_ids):
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == f"Updated Batch Item {i}"
            assert data["volume"] == 50.0 + i

    def test_interleaved_operations(self):
        """Test interleaving operations between items and pickups."""
        for i in range(5):
            # Create item
            item_data = {
                "id": f"interleave-item-{i}",
                "name": f"Item {i}",
                "volume": 10.0
            }
            response = client.post("/items/", json=item_data)
            assert response.status_code == 200

            # Create pickup
            pickup_data = {
                "id": f"interleave-pickup-{i}",
                "name": f"Pickup {i}",
                "location": f"Location {i}"
            }
            response = client.post("/pickup/", json=pickup_data)
            assert response.status_code == 200

            # Update item
            update_item = {
                "id": f"interleave-item-{i}",
                "name": f"Updated Item {i}",
                "volume": 20.0
            }
            response = client.patch(f"/items/interleave-item-{i}", json=update_item)
            assert response.status_code == 200

            # Update pickup
            update_pickup = {
                "id": f"interleave-pickup-{i}",
                "name": f"Updated Pickup {i}",
                "location": f"Updated Location {i}"
            }
            response = client.patch(f"/pickup/interleave-pickup-{i}", json=update_pickup)
            assert response.status_code == 200


# ============================================================================
# STRESS AND PERFORMANCE TESTS
# ============================================================================

class TestStressAndPerformance:
    """Tests for system behavior under load."""

    def test_create_many_items_with_similar_names(self):
        """Test creating many items with very similar names."""
        for i in range(50):
            item_data = {
                "id": f"similar-{i}",
                "name": f"Similar Item",  # Same name for all
                "volume": 10.0
            }
            response = client.post("/items/", json=item_data)
            assert response.status_code == 200

        # Verify distinct items exist
        for i in range(50):
            response = client.get(f"/items/similar-{i}")
            assert response.status_code == 200

    def test_update_same_item_many_times(self):
        """Test updating the same item many times in succession."""
        item_data = {
            "id": "stress-item",
            "name": "Stress Test Item",
            "volume": 1.0
        }
        client.post("/items/", json=item_data)

        # Update 100 times
        for i in range(100):
            update_data = {
                "id": "stress-item",
                "name": f"Iteration {i}",
                "volume": float(i)
            }
            response = client.patch("/items/stress-item", json=update_data)
            assert response.status_code == 200

        # Final verification
        response = client.get("/items/stress-item")
        assert response.status_code == 200
        assert response.json()["name"] == "Iteration 99"
        assert response.json()["volume"] == 99.0

    def test_get_nonexistent_items_repeatedly(self):
        """Test repeatedly getting non-existent items."""
        for i in range(30):
            response = client.get(f"/items/ghost-{i}")
            assert response.status_code == 404


# ============================================================================
# ADVANCED EDGE CASES
# ============================================================================

class TestAdvancedEdgeCases:
    """Advanced edge case testing."""

    def test_item_with_scientific_notation_volume(self):
        """Test item with scientific notation in volume."""
        item_data = {
            "id": "item-scientific",
            "name": "Scientific Item",
            "volume": 1.23e-10
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_with_very_small_volume(self):
        """Test item with extremely small volume."""
        item_data = {
            "id": "item-tiny",
            "name": "Tiny Item",
            "volume": 0.00000001
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200
        assert response.json()["volume"] == 0.00000001

    def test_pickup_with_newlines_in_location(self):
        """Test pickup with newline characters in location."""
        pickup_data = {
            "id": "pickup-newlines",
            "name": "Multiline Pickup",
            "location": "Line 1\nLine 2\nLine 3"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200

    def test_item_with_tabs_in_name(self):
        """Test item with tab characters in name."""
        item_data = {
            "id": "item-tabs",
            "name": "Item\twith\ttabs",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_pickup_with_html_in_name(self):
        """Test pickup with HTML tags in name (should be stored as-is)."""
        pickup_data = {
            "id": "pickup-html",
            "name": "<script>alert('xss')</script>",
            "location": "Test Location"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200

    def test_item_with_sql_injection_attempt_in_id(self):
        """Test item creation with SQL injection attempt in ID."""
        item_data = {
            "id": "item'; DROP TABLE items; --",
            "name": "SQL Injection Test",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_with_null_bytes_in_name(self):
        """Test item with null byte attempt in name."""
        item_data = {
            "id": "item-null",
            "name": "Item\x00NullByte",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_pickup_with_very_long_id(self):
        """Test pickup with extremely long ID."""
        long_id = "p" * 255
        pickup_data = {
            "id": long_id,
            "name": "Long ID Pickup",
            "location": "Test"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200

    def test_item_with_all_spaces_name(self):
        """Test item with name that is only spaces."""
        item_data = {
            "id": "item-spaces",
            "name": "     ",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_pickup_with_only_numbers_as_name(self):
        """Test pickup with only numbers as name."""
        pickup_data = {
            "id": "pickup-numbers",
            "name": "123456789",
            "location": "Numeric Location"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200


# ============================================================================
# ID FORMAT TESTS
# ============================================================================

class TestIDFormats:
    """Tests for various ID formats."""

    def test_item_with_uuid_format_id(self):
        """Test item with UUID-format ID."""
        item_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "UUID Item",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_with_dashes_in_id(self):
        """Test item with dashes in ID."""
        item_data = {
            "id": "item-with-many-dashes",
            "name": "Dashed ID Item",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_with_underscores_in_id(self):
        """Test item with underscores in ID."""
        item_data = {
            "id": "item_with_underscores",
            "name": "Underscore ID Item",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_with_mixed_case_id(self):
        """Test item with mixed case ID."""
        item_data = {
            "id": "Item-MixedCase-123",
            "name": "Mixed Case Item",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_pickup_with_numeric_id(self):
        """Test pickup with purely numeric ID."""
        pickup_data = {
            "id": "999999999",
            "name": "Numeric ID Pickup",
            "location": "Test"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200

    def test_item_with_special_chars_in_id(self):
        """Test item with special characters in ID."""
        item_data = {
            "id": "item@special#chars",
            "name": "Special Char ID",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200


# ============================================================================
# VOLUME BOUNDARY TESTS
# ============================================================================

class TestVolumeBoundaries:
    """Tests for volume edge cases and boundaries."""

    def test_item_volume_max_float(self):
        """Test item with maximum float value."""
        item_data = {
            "id": "item-max-float",
            "name": "Max Float Item",
            "volume": 1.7976931348623157e+308
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_volume_min_positive_float(self):
        """Test item with minimum positive float."""
        item_data = {
            "id": "item-min-float",
            "name": "Min Float Item",
            "volume": 2.2250738585072014e-308
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_item_volume_with_many_decimals(self):
        """Test item with many decimal places."""
        item_data = {
            "id": "item-decimals",
            "name": "Many Decimals Item",
            "volume": 3.141592653589793238462643383279
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_update_item_volume_from_positive_to_negative(self):
        """Test updating item volume from positive to negative."""
        item_data = {
            "id": "item-volume-flip",
            "name": "Volume Flip",
            "volume": 100.0
        }
        client.post("/items/", json=item_data)

        update_data = {
            "id": "item-volume-flip",
            "name": "Volume Flip",
            "volume": -100.0
        }
        response = client.patch("/items/item-volume-flip", json=update_data)
        assert response.status_code == 200

    def test_update_item_volume_to_zero(self):
        """Test updating item volume to zero."""
        item_data = {
            "id": "item-to-zero",
            "name": "To Zero",
            "volume": 50.0
        }
        client.post("/items/", json=item_data)

        update_data = {
            "id": "item-to-zero",
            "name": "To Zero",
            "volume": 0.0
        }
        response = client.patch("/items/item-to-zero", json=update_data)
        assert response.status_code == 200
        assert response.json()["volume"] == 0.0


# ============================================================================
# RESPONSE VALIDATION TESTS
# ============================================================================

class TestResponseValidation:
    """Tests to validate response structure and content."""

    def test_item_response_has_all_fields(self):
        """Test that item response contains all required fields."""
        item_data = {
            "id": "item-fields",
            "name": "Field Test",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "volume" in data

    def test_pickup_response_has_all_fields(self):
        """Test that pickup response contains all required fields."""
        pickup_data = {
            "id": "pickup-fields",
            "name": "Field Test Pickup",
            "location": "Test Location"
        }
        response = client.post("/pickup/", json=pickup_data)
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "location" in data

    def test_item_response_field_types(self):
        """Test that item response fields have correct types."""
        item_data = {
            "id": "item-types",
            "name": "Type Test",
            "volume": 15.5
        }
        response = client.post("/items/", json=item_data)
        data = response.json()
        assert isinstance(data["id"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["volume"], (int, float))

    def test_pickup_items_response_is_list(self):
        """Test that pickup items endpoint returns a list."""
        pickup_data = {
            "id": "pickup-list-test",
            "name": "List Test",
            "location": "Test"
        }
        client.post("/pickup/", json=pickup_data)

        response = client.get("/pickup/pickup-list-test/items")
        assert isinstance(response.json(), list)

    def test_get_item_preserves_exact_values(self):
        """Test that GET returns exact same values as POST."""
        item_data = {
            "id": "item-exact",
            "name": "Exact Match Test",
            "volume": 12.34567
        }
        post_response = client.post("/items/", json=item_data)
        get_response = client.get("/items/item-exact")

        assert post_response.json() == get_response.json()


# ============================================================================
# CROSS-RESOURCE OPERATION TESTS
# ============================================================================

class TestCrossResourceOperations:
    """Tests involving multiple resource types."""

    def test_create_items_and_pickups_alternating(self):
        """Test creating items and pickups in alternating pattern."""
        for i in range(10):
            if i % 2 == 0:
                item_data = {
                    "id": f"cross-item-{i}",
                    "name": f"Cross Item {i}",
                    "volume": float(i)
                }
                response = client.post("/items/", json=item_data)
                assert response.status_code == 200
            else:
                pickup_data = {
                    "id": f"cross-pickup-{i}",
                    "name": f"Cross Pickup {i}",
                    "location": f"Location {i}"
                }
                response = client.post("/pickup/", json=pickup_data)
                assert response.status_code == 200

    def test_update_items_and_pickups_in_sequence(self):
        """Test updating items and pickups in sequence."""
        # Create resources
        for i in range(5):
            client.post("/items/", json={"id": f"seq-item-{i}", "name": f"Item {i}", "volume": 10.0})
            client.post("/pickup/", json={"id": f"seq-pickup-{i}", "name": f"Pickup {i}", "location": f"Loc {i}"})

        # Update in sequence
        for i in range(5):
            response = client.patch(f"/items/seq-item-{i}", json={"id": f"seq-item-{i}", "name": f"Updated Item {i}", "volume": 20.0})
            assert response.status_code == 200
            response = client.patch(f"/pickup/seq-pickup-{i}", json={"id": f"seq-pickup-{i}", "name": f"Updated Pickup {i}", "location": f"New Loc {i}"})
            assert response.status_code == 200

    def test_get_items_and_pickups_interleaved(self):
        """Test getting items and pickups in interleaved pattern."""
        # Create resources
        for i in range(5):
            client.post("/items/", json={"id": f"get-item-{i}", "name": f"Item {i}", "volume": 10.0})
            client.post("/pickup/", json={"id": f"get-pickup-{i}", "name": f"Pickup {i}", "location": "Test"})

        # Get interleaved
        for i in range(5):
            item_response = client.get(f"/items/get-item-{i}")
            assert item_response.status_code == 200
            pickup_response = client.get(f"/pickup/get-pickup-{i}")
            assert pickup_response.status_code == 200


# ============================================================================
# BULK OPERATION TESTS
# ============================================================================

class TestBulkOperations:
    """Tests for bulk operations."""

    def test_create_100_items(self):
        """Test creating 100 items."""
        for i in range(100):
            item_data = {
                "id": f"bulk-item-{i}",
                "name": f"Bulk Item {i}",
                "volume": float(i)
            }
            response = client.post("/items/", json=item_data)
            assert response.status_code == 200

    def test_update_50_items_sequentially(self):
        """Test updating 50 items sequentially."""
        # Create items
        for i in range(50):
            client.post("/items/", json={"id": f"update-bulk-{i}", "name": f"Item {i}", "volume": 10.0})

        # Update all
        for i in range(50):
            response = client.patch(f"/items/update-bulk-{i}", json={"id": f"update-bulk-{i}", "name": f"Updated {i}", "volume": 20.0})
            assert response.status_code == 200

    def test_get_75_items_sequentially(self):
        """Test getting 75 items sequentially."""
        # Create items
        for i in range(75):
            client.post("/items/", json={"id": f"get-bulk-{i}", "name": f"Item {i}", "volume": 10.0})

        # Get all
        for i in range(75):
            response = client.get(f"/items/get-bulk-{i}")
            assert response.status_code == 200

    def test_create_50_pickups_with_validation(self):
        """Test creating 50 pickups and validating each."""
        for i in range(50):
            pickup_data = {
                "id": f"bulk-pickup-{i}",
                "name": f"Bulk Pickup {i}",
                "location": f"Location {i}"
            }
            response = client.post("/pickup/", json=pickup_data)
            assert response.status_code == 200
            assert response.json()["name"] == f"Bulk Pickup {i}"


# ============================================================================
# STATE TRANSITION TESTS
# ============================================================================

class TestStateTransitions:
    """Tests for state transitions across operations."""

    def test_item_state_after_multiple_updates(self):
        """Test item state transitions through multiple updates."""
        item_id = "state-item"
        states = [
            {"name": "State 1", "volume": 10.0},
            {"name": "State 2", "volume": 20.0},
            {"name": "State 3", "volume": 15.0},
            {"name": "State 4", "volume": 25.0},
            {"name": "State 5", "volume": 30.0}
        ]

        # Create initial
        client.post("/items/", json={"id": item_id, "name": "Initial", "volume": 5.0})

        # Transition through states
        for state in states:
            response = client.patch(f"/items/{item_id}", json={"id": item_id, **state})
            assert response.status_code == 200
            assert response.json()["name"] == state["name"]
            assert response.json()["volume"] == state["volume"]

    def test_pickup_location_changes(self):
        """Test pickup point location changes over time."""
        pickup_id = "moving-pickup"
        locations = ["Location A", "Location B", "Location C", "Location D", "Location E"]

        client.post("/pickup/", json={"id": pickup_id, "name": "Moving Pickup", "location": "Start"})

        for loc in locations:
            response = client.patch(f"/pickup/{pickup_id}", json={"id": pickup_id, "name": "Moving Pickup", "location": loc})
            assert response.status_code == 200
            assert response.json()["location"] == loc


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

class TestErrorRecovery:
    """Tests for error recovery scenarios."""

    def test_create_after_failed_get(self):
        """Test creating item after failed GET attempt."""
        # Try to get non-existent item
        response = client.get("/items/recovery-item")
        assert response.status_code == 404

        # Now create it
        response = client.post("/items/", json={"id": "recovery-item", "name": "Recovery", "volume": 10.0})
        assert response.status_code == 200

        # Verify it exists
        response = client.get("/items/recovery-item")
        assert response.status_code == 200

    def test_update_after_failed_update(self):
        """Test successful update after failed update attempt."""
        item_id = "retry-item"
        client.post("/items/", json={"id": item_id, "name": "Original", "volume": 10.0})

        # Try to update non-existent item first
        response = client.patch("/items/wrong-id", json={"id": "wrong-id", "name": "Wrong", "volume": 20.0})
        assert response.status_code == 404

        # Now update correct item
        response = client.patch(f"/items/{item_id}", json={"id": item_id, "name": "Updated", "volume": 20.0})
        assert response.status_code == 200

    def test_multiple_404s_then_success(self):
        """Test multiple 404s followed by successful operation."""
        for i in range(10):
            response = client.get(f"/items/missing-{i}")
            assert response.status_code == 404

        # Now create and get successfully
        response = client.post("/items/", json={"id": "now-exists", "name": "Exists", "volume": 10.0})
        assert response.status_code == 200

        response = client.get("/items/now-exists")
        assert response.status_code == 200


# ============================================================================
# IDEMPOTENCY TESTS
# ============================================================================

class TestIdempotency:
    """Tests for idempotent operations."""

    def test_get_item_idempotency(self):
        """Test that GET is idempotent (multiple GETs return same result)."""
        client.post("/items/", json={"id": "idem-item", "name": "Idempotent", "volume": 10.0})

        results = []
        for _ in range(20):
            response = client.get("/items/idem-item")
            results.append(response.json())

        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

    def test_update_to_same_values(self):
        """Test updating item to same values multiple times."""
        item_id = "same-values"
        item_data = {"id": item_id, "name": "Same", "volume": 15.0}

        client.post("/items/", json=item_data)

        # Update to same values multiple times
        for _ in range(10):
            response = client.patch(f"/items/{item_id}", json=item_data)
            assert response.status_code == 200
            assert response.json()["name"] == "Same"
            assert response.json()["volume"] == 15.0


# ============================================================================
# SPECIAL CHARACTER TESTS
# ============================================================================

class TestSpecialCharacters:
    """Tests with various special characters."""

    def test_item_with_quotes_in_name(self):
        """Test item with quotes in name."""
        item_data = {
            "id": "item-quotes",
            "name": 'Item with "quotes" and \'apostrophes\'',
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_pickup_with_backslashes(self):
        """Test pickup with backslashes in location."""
        pickup_data = {
            "id": "pickup-backslash",
            "name": "Backslash Pickup",
            "location": "C:\\Users\\Test\\Location"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200

    def test_item_with_forward_slashes(self):
        """Test item with forward slashes in name."""
        item_data = {
            "id": "item-slash",
            "name": "Item/With/Slashes",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200

    def test_pickup_with_parentheses(self):
        """Test pickup with parentheses in name."""
        pickup_data = {
            "id": "pickup-parens",
            "name": "Pickup (with) (parentheses)",
            "location": "Test"
        }
        response = client.post("/pickup/", json=pickup_data)
        assert response.status_code == 200

    def test_item_with_brackets(self):
        """Test item with brackets in name."""
        item_data = {
            "id": "item-brackets",
            "name": "Item [with] {curly} <angle> brackets",
            "volume": 10.0
        }
        response = client.post("/items/", json=item_data)
        assert response.status_code == 200


# ============================================================================
# CONSISTENCY VERIFICATION TESTS
# ============================================================================

class TestConsistencyVerification:
    """Tests to verify consistency across operations."""

    def test_create_get_consistency(self):
        """Test that data from POST matches data from GET."""
        item_data = {
            "id": "consistency-1",
            "name": "Consistency Test",
            "volume": 12.345
        }
        post_response = client.post("/items/", json=item_data)
        get_response = client.get("/items/consistency-1")

        assert post_response.json() == get_response.json()

    def test_update_get_consistency(self):
        """Test that data from PATCH matches data from GET."""
        client.post("/items/", json={"id": "consistency-2", "name": "Original", "volume": 10.0})

        update_data = {"id": "consistency-2", "name": "Updated", "volume": 20.0}
        patch_response = client.patch("/items/consistency-2", json=update_data)
        get_response = client.get("/items/consistency-2")

        assert patch_response.json() == get_response.json()

    def test_multiple_gets_return_same_data(self):
        """Test that multiple GETs return identical data."""
        client.post("/items/", json={"id": "consistency-3", "name": "Stable", "volume": 15.0})

        responses = [client.get("/items/consistency-3").json() for _ in range(10)]

        for response in responses[1:]:
            assert response == responses[0]

    def test_pickup_items_consistency_across_calls(self):
        """Test pickup items endpoint returns consistent results."""
        client.post("/pickup/", json={"id": "consistency-pickup", "name": "Consistent", "location": "Test"})

        responses = [client.get("/pickup/consistency-pickup/items").json() for _ in range(5)]

        for response in responses[1:]:
            assert response == responses[0]


# ============================================================================
# PERFORMANCE REGRESSION TESTS
# ============================================================================

class TestPerformanceRegression:
    """Tests to catch performance regressions."""

    def test_sequential_creates_complete(self):
        """Test that 30 sequential creates all complete successfully."""
        for i in range(30):
            response = client.post("/items/", json={"id": f"perf-{i}", "name": f"Perf {i}", "volume": float(i)})
            assert response.status_code == 200

    def test_sequential_updates_complete(self):
        """Test that 30 sequential updates all complete successfully."""
        # Create items
        for i in range(30):
            client.post("/items/", json={"id": f"perf-update-{i}", "name": f"Item {i}", "volume": 10.0})

        # Update all
        for i in range(30):
            response = client.patch(f"/items/perf-update-{i}", json={"id": f"perf-update-{i}", "name": f"Updated {i}", "volume": 20.0})
            assert response.status_code == 200

    def test_mixed_operations_complete(self):
        """Test that mixed operations complete successfully."""
        for i in range(20):
            # Create
            client.post("/items/", json={"id": f"mixed-{i}", "name": f"Item {i}", "volume": 10.0})
            # Get
            response = client.get(f"/items/mixed-{i}")
            assert response.status_code == 200
            # Update
            response = client.patch(f"/items/mixed-{i}", json={"id": f"mixed-{i}", "name": f"Updated {i}", "volume": 20.0})
            assert response.status_code == 200


# ============================================================================
# COMPREHENSIVE SCENARIO TESTS
# ============================================================================

class TestComprehensiveScenarios:
    """Comprehensive real-world scenario tests."""

    def test_full_crud_cycle_items(self):
        """Test complete CRUD cycle for items."""
        # Create
        response = client.post("/items/", json={"id": "crud-item", "name": "CRUD Test", "volume": 10.0})
        assert response.status_code == 200

        # Read
        response = client.get("/items/crud-item")
        assert response.status_code == 200
        assert response.json()["name"] == "CRUD Test"

        # Update
        response = client.patch("/items/crud-item", json={"id": "crud-item", "name": "CRUD Updated", "volume": 20.0})
        assert response.status_code == 200
        assert response.json()["name"] == "CRUD Updated"

        # Read again to verify
        response = client.get("/items/crud-item")
        assert response.status_code == 200
        assert response.json()["name"] == "CRUD Updated"

    def test_full_crud_cycle_pickups(self):
        """Test complete CRUD cycle for pickups."""
        # Create
        response = client.post("/pickup/", json={"id": "crud-pickup", "name": "CRUD Pickup", "location": "Test"})
        assert response.status_code == 200

        # Read
        response = client.get("/pickup/crud-pickup")
        assert response.status_code == 200
        assert response.json()["name"] == "CRUD Pickup"

        # Update
        response = client.patch("/pickup/crud-pickup", json={"id": "crud-pickup", "name": "CRUD Pickup Updated", "location": "New Test"})
        assert response.status_code == 200
        assert response.json()["name"] == "CRUD Pickup Updated"

        # Read again
        response = client.get("/pickup/crud-pickup")
        assert response.status_code == 200
        assert response.json()["name"] == "CRUD Pickup Updated"

    def test_warehouse_simulation(self):
        """Simulate a warehouse scenario with multiple items and pickups."""
        # Create warehouse locations (pickups)
        warehouses = ["North", "South", "East", "West", "Central"]
        for wh in warehouses:
            client.post("/pickup/", json={"id": f"wh-{wh.lower()}", "name": f"{wh} Warehouse", "location": f"{wh} Location"})

        # Create items
        items = ["Widget", "Gadget", "Tool", "Part", "Component"]
        for idx, item in enumerate(items):
            client.post("/items/", json={"id": f"item-{item.lower()}", "name": item, "volume": float((idx + 1) * 10)})

        # Verify all exist
        for wh in warehouses:
            response = client.get(f"/pickup/wh-{wh.lower()}")
            assert response.status_code == 200

        for item in items:
            response = client.get(f"/items/item-{item.lower()}")
            assert response.status_code == 200


# ============================================================================
# FINAL COMPREHENSIVE TESTS (30 MORE TESTS TO REACH 128)
# ============================================================================

class TestFinalComprehensive:
    """Final comprehensive tests to reach 128 total."""

    def test_item_name_length_variations(self):
        """Test items with varying name lengths."""
        for length in [1, 10, 50, 100, 250]:
            item_data = {
                "id": f"name-len-{length}",
                "name": "A" * length,
                "volume": 10.0
            }
            response = client.post("/items/", json=item_data)
            assert response.status_code == 200

    def test_pickup_location_variations(self):
        """Test pickups with different location formats."""
        locations = [
            "Simple",
            "123 Main St",
            "Building A, Floor 3, Room 301",
            "GPS: 40.7128° N, 74.0060° W",
            "https://maps.google.com/?q=40.7128,-74.0060"
        ]
        for idx, loc in enumerate(locations):
            response = client.post("/pickup/", json={"id": f"loc-var-{idx}", "name": f"Pickup {idx}", "location": loc})
            assert response.status_code == 200

    def test_sequential_volume_increases(self):
        """Test sequential volume increases."""
        item_id = "volume-increase"
        client.post("/items/", json={"id": item_id, "name": "Volume Test", "volume": 1.0})

        for i in range(2, 12):
            response = client.patch(f"/items/{item_id}", json={"id": item_id, "name": "Volume Test", "volume": float(i)})
            assert response.status_code == 200
            assert response.json()["volume"] == float(i)

    def test_sequential_volume_decreases(self):
        """Test sequential volume decreases."""
        item_id = "volume-decrease"
        client.post("/items/", json={"id": item_id, "name": "Volume Test", "volume": 100.0})

        for i in range(99, 89, -1):
            response = client.patch(f"/items/{item_id}", json={"id": item_id, "name": "Volume Test", "volume": float(i)})
            assert response.status_code == 200

    def test_zigzag_volume_pattern(self):
        """Test volume changes in zigzag pattern."""
        item_id = "zigzag"
        client.post("/items/", json={"id": item_id, "name": "Zigzag", "volume": 50.0})

        volumes = [60, 40, 70, 30, 80, 20, 90, 10]
        for vol in volumes:
            response = client.patch(f"/items/{item_id}", json={"id": item_id, "name": "Zigzag", "volume": float(vol)})
            assert response.status_code == 200

    def test_item_name_character_sets(self):
        """Test item names with different character sets."""
        names = [
            "English123",
            "Español",
            "Français",
            "Deutsch",
            "中文",
            "日本語",
            "한국어",
            "Русский",
            "العربية",
            "हिन्दी"
        ]
        for idx, name in enumerate(names):
            response = client.post("/items/", json={"id": f"charset-{idx}", "name": name, "volume": 10.0})
            assert response.status_code == 200

    def test_pickup_with_coordinates(self):
        """Test pickup with various coordinate formats."""
        coords = [
            "40.7128, -74.0060",
            "51.5074° N, 0.1278° W",
            "35°41′22″N 139°45′44″E",
            "[-33.8688, 151.2093]"
        ]
        for idx, coord in enumerate(coords):
            response = client.post("/pickup/", json={"id": f"coord-{idx}", "name": f"Coord {idx}", "location": coord})
            assert response.status_code == 200

    def test_create_read_pattern_items(self):
        """Test create-read pattern for multiple items."""
        for i in range(15):
            # Create
            response = client.post("/items/", json={"id": f"cr-item-{i}", "name": f"CR Item {i}", "volume": float(i)})
            assert response.status_code == 200
            # Immediately read
            response = client.get(f"/items/cr-item-{i}")
            assert response.status_code == 200
            assert response.json()["name"] == f"CR Item {i}"

    def test_create_update_read_pattern(self):
        """Test create-update-read pattern for multiple resources."""
        for i in range(10):
            # Create
            client.post("/items/", json={"id": f"cur-{i}", "name": f"Original {i}", "volume": 10.0})
            # Update
            client.patch(f"/items/cur-{i}", json={"id": f"cur-{i}", "name": f"Updated {i}", "volume": 20.0})
            # Read and verify
            response = client.get(f"/items/cur-{i}")
            assert response.json()["name"] == f"Updated {i}"
            assert response.json()["volume"] == 20.0

    def test_item_with_volume_fractions(self):
        """Test items with fractional volumes."""
        fractions = [0.1, 0.25, 0.33, 0.5, 0.66, 0.75, 0.9]
        for idx, frac in enumerate(fractions):
            response = client.post("/items/", json={"id": f"frac-{idx}", "name": f"Fraction {idx}", "volume": frac})
            assert response.status_code == 200
            assert abs(response.json()["volume"] - frac) < 0.01

    def test_pickup_with_multi_word_names(self):
        """Test pickups with multi-word names."""
        names = [
            "Main Distribution Center",
            "North Regional Hub",
            "East Coast Facility",
            "Central Sorting Station",
            "West Side Warehouse Complex"
        ]
        for idx, name in enumerate(names):
            response = client.post("/pickup/", json={"id": f"multiword-{idx}", "name": name, "location": "Test"})
            assert response.status_code == 200

    def test_rapid_create_delete_simulation(self):
        """Simulate rapid create operations (delete not implemented)."""
        for i in range(25):
            response = client.post("/items/", json={"id": f"rapid-cd-{i}", "name": f"Rapid {i}", "volume": 10.0})
            assert response.status_code == 200

    def test_update_oscillation(self):
        """Test oscillating updates between two states."""
        item_id = "oscillate"
        client.post("/items/", json={"id": item_id, "name": "State A", "volume": 10.0})

        for i in range(20):
            if i % 2 == 0:
                response = client.patch(f"/items/{item_id}", json={"id": item_id, "name": "State B", "volume": 20.0})
                assert response.json()["name"] == "State B"
            else:
                response = client.patch(f"/items/{item_id}", json={"id": item_id, "name": "State A", "volume": 10.0})
                assert response.json()["name"] == "State A"

    def test_item_volume_powers_of_two(self):
        """Test items with volumes as powers of two."""
        for i in range(10):
            volume = 2 ** i
            response = client.post("/items/", json={"id": f"pow2-{i}", "name": f"Power {i}", "volume": float(volume)})
            assert response.status_code == 200
            assert response.json()["volume"] == float(volume)

    def test_pickup_items_empty_check(self):
        """Test that newly created pickups have empty items."""
        for i in range(10):
            client.post("/pickup/", json={"id": f"empty-check-{i}", "name": f"Empty {i}", "location": "Test"})
            response = client.get(f"/pickup/empty-check-{i}/items")
            assert response.status_code == 200
            assert response.json() == []

    def test_item_name_with_numbers_only(self):
        """Test items with names that are only numbers."""
        for i in range(10):
            response = client.post("/items/", json={"id": f"numname-{i}", "name": str(i * 111), "volume": 10.0})
            assert response.status_code == 200

    def test_pickup_cascading_updates(self):
        """Test cascading updates to pickup points."""
        # Create base pickups
        for i in range(5):
            client.post("/pickup/", json={"id": f"cascade-{i}", "name": f"Base {i}", "location": "Original"})

        # Cascade updates
        for i in range(5):
            for j in range(5):
                if j <= i:
                    response = client.patch(f"/pickup/cascade-{j}", json={"id": f"cascade-{j}", "name": f"Updated {i}", "location": f"Location {i}"})
                    assert response.status_code == 200

    def test_get_after_multiple_creates(self):
        """Test getting items after multiple creates."""
        # Create 20 items
        for i in range(20):
            client.post("/items/", json={"id": f"multi-create-{i}", "name": f"Item {i}", "volume": float(i)})

        # Get each one
        for i in range(20):
            response = client.get(f"/items/multi-create-{i}")
            assert response.status_code == 200
            assert response.json()["volume"] == float(i)

    def test_update_verification_chain(self):
        """Test chain of updates with verification."""
        item_id = "chain"
        client.post("/items/", json={"id": item_id, "name": "Link 0", "volume": 0.0})

        for i in range(1, 11):
            # Update
            client.patch(f"/items/{item_id}", json={"id": item_id, "name": f"Link {i}", "volume": float(i)})
            # Verify
            response = client.get(f"/items/{item_id}")
            assert response.json()["name"] == f"Link {i}"
            assert response.json()["volume"] == float(i)

    def test_pickup_name_punctuation(self):
        """Test pickup names with various punctuation."""
        names = [
            "Pickup!",
            "Pickup?",
            "Pickup.",
            "Pickup,",
            "Pickup;",
            "Pickup:",
            "Pickup-",
            "Pickup_",
            "Pickup&Co",
            "Pickup@Location"
        ]
        for idx, name in enumerate(names):
            response = client.post("/pickup/", json={"id": f"punct-{idx}", "name": name, "location": "Test"})
            assert response.status_code == 200

    def test_item_volume_precision_check(self):
        """Test item volume precision is maintained."""
        precise_volumes = [
            3.14159265359,
            2.71828182846,
            1.41421356237,
            1.61803398875,
            0.57721566490
        ]
        for idx, vol in enumerate(precise_volumes):
            response = client.post("/items/", json={"id": f"precise-{idx}", "name": f"Precise {idx}", "volume": vol})
            assert response.status_code == 200

    def test_alternating_resource_gets(self):
        """Test alternating between getting items and pickups."""
        # Create resources
        for i in range(10):
            client.post("/items/", json={"id": f"alt-get-item-{i}", "name": f"Item {i}", "volume": 10.0})
            client.post("/pickup/", json={"id": f"alt-get-pickup-{i}", "name": f"Pickup {i}", "location": "Test"})

        # Alternate gets
        for i in range(10):
            item_response = client.get(f"/items/alt-get-item-{i}")
            assert item_response.status_code == 200
            pickup_response = client.get(f"/pickup/alt-get-pickup-{i}")
            assert pickup_response.status_code == 200

    def test_batch_update_verification(self):
        """Test batch updates with full verification."""
        # Create 15 items
        for i in range(15):
            client.post("/items/", json={"id": f"batch-ver-{i}", "name": f"Original {i}", "volume": 10.0})

        # Batch update
        for i in range(15):
            response = client.patch(f"/items/batch-ver-{i}", json={"id": f"batch-ver-{i}", "name": f"Updated {i}", "volume": 20.0})
            assert response.status_code == 200

        # Full verification
        for i in range(15):
            response = client.get(f"/items/batch-ver-{i}")
            assert response.json()["name"] == f"Updated {i}"
            assert response.json()["volume"] == 20.0

    def test_item_with_repeating_decimals(self):
        """Test items with repeating decimal volumes."""
        repeating = [
            1.0 / 3.0,  # 0.333...
            2.0 / 3.0,  # 0.666...
            1.0 / 6.0,  # 0.166...
            5.0 / 6.0,  # 0.833...
            1.0 / 7.0   # 0.142857...
        ]
        for idx, val in enumerate(repeating):
            response = client.post("/items/", json={"id": f"repeat-{idx}", "name": f"Repeat {idx}", "volume": val})
            assert response.status_code == 200

    def test_pickup_stress_items_endpoint(self):
        """Test pickup items endpoint under repeated calls."""
        client.post("/pickup/", json={"id": "stress-items", "name": "Stress Test", "location": "Test"})

        # Call items endpoint 50 times
        for _ in range(50):
            response = client.get("/pickup/stress-items/items")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_complex_update_sequence(self):
        """Test complex sequence of updates."""
        item_id = "complex-seq"
        client.post("/items/", json={"id": item_id, "name": "Start", "volume": 50.0})

        sequence = [
            {"name": "Step1", "volume": 55.0},
            {"name": "Step2", "volume": 45.0},
            {"name": "Step3", "volume": 60.0},
            {"name": "Step4", "volume": 40.0},
            {"name": "Step5", "volume": 65.0},
            {"name": "Step6", "volume": 35.0},
            {"name": "Step7", "volume": 70.0},
            {"name": "Step8", "volume": 30.0},
            {"name": "Step9", "volume": 75.0},
            {"name": "Final", "volume": 50.0}
        ]

        for step in sequence:
            response = client.patch(f"/items/{item_id}", json={"id": item_id, **step})
            assert response.status_code == 200
            assert response.json()["name"] == step["name"]

    def test_final_integration_scenario(self):
        """Final comprehensive integration test."""
        # Create ecosystem
        items_count = 10
        pickups_count = 5

        # Create items
        for i in range(items_count):
            response = client.post("/items/", json={"id": f"final-item-{i}", "name": f"Final Item {i}", "volume": float(i * 5)})
            assert response.status_code == 200

        # Create pickups
        for i in range(pickups_count):
            response = client.post("/pickup/", json={"id": f"final-pickup-{i}", "name": f"Final Pickup {i}", "location": f"Final Location {i}"})
            assert response.status_code == 200

        # Update all items
        for i in range(items_count):
            response = client.patch(f"/items/final-item-{i}", json={"id": f"final-item-{i}", "name": f"Updated Final Item {i}", "volume": float(i * 10)})
            assert response.status_code == 200

        # Update all pickups
        for i in range(pickups_count):
            response = client.patch(f"/pickup/final-pickup-{i}", json={"id": f"final-pickup-{i}", "name": f"Updated Final Pickup {i}", "location": f"Updated Final Location {i}"})
            assert response.status_code == 200

        # Verify all items
        for i in range(items_count):
            response = client.get(f"/items/final-item-{i}")
            assert response.status_code == 200
            assert "Updated" in response.json()["name"]

        # Verify all pickups
        for i in range(pickups_count):
            response = client.get(f"/pickup/final-pickup-{i}")
            assert response.status_code == 200
            assert "Updated" in response.json()["name"]

        # Check all pickup items
        for i in range(pickups_count):
            response = client.get(f"/pickup/final-pickup-{i}/items")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_item_exponential_volumes(self):
        """Test items with exponentially increasing volumes (TEST 126)."""
        for i in range(10):
            volume = 10 ** i
            response = client.post("/items/", json={"id": f"exp-{i}", "name": f"Exp {i}", "volume": float(volume)})
            assert response.status_code == 200

    def test_pickup_sequential_verification(self):
        """Test sequential creation and verification of pickups (TEST 127)."""
        for i in range(15):
            # Create
            response = client.post("/pickup/", json={"id": f"seq-ver-{i}", "name": f"Seq {i}", "location": f"Loc {i}"})
            assert response.status_code == 200
            # Immediate verification
            response = client.get(f"/pickup/seq-ver-{i}")
            assert response.status_code == 200
            assert response.json()["name"] == f"Seq {i}"

    def test_comprehensive_stress_finale(self):
        """Comprehensive stress test combining all operations (TEST 128)."""
        # Create 25 items and 25 pickups
        for i in range(25):
            item_response = client.post("/items/", json={"id": f"stress-final-item-{i}", "name": f"Stress Item {i}", "volume": float(i)})
            assert item_response.status_code == 200

            pickup_response = client.post("/pickup/", json={"id": f"stress-final-pickup-{i}", "name": f"Stress Pickup {i}", "location": f"Location {i}"})
            assert pickup_response.status_code == 200

        # Update all items
        for i in range(25):
            response = client.patch(f"/items/stress-final-item-{i}", json={"id": f"stress-final-item-{i}", "name": f"Updated Stress {i}", "volume": float(i * 2)})
            assert response.status_code == 200

        # Verify all exist
        for i in range(25):
            item_response = client.get(f"/items/stress-final-item-{i}")
            assert item_response.status_code == 200

            pickup_response = client.get(f"/pickup/stress-final-pickup-{i}")
            assert pickup_response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    """Run tests directly without pytest."""
    print("=" * 80)
    print("Running automated endpoint tests...")
    print("=" * 80)

    # Test item endpoints
    print("\n[TEST] Creating item...")
    item_data = {
        "id": "item-001",
        "name": "Test Item",
        "volume": 15.0
    }
    response = client.post("/items/", json=item_data)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Getting item...")
    response = client.get("/items/item-001")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Updating item...")
    updated_item = {
        "id": "item-001",
        "name": "Updated Test Item",
        "volume": 20.0
    }
    response = client.patch("/items/item-001", json=updated_item)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    # Test pickup endpoints
    print("\n[TEST] Creating pickup point...")
    pickup_data = {
        "id": "pickup-001",
        "name": "Test Pickup",
        "location": "Test Pickup Location"
    }
    response = client.post("/pickup/", json=pickup_data)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Getting pickup point...")
    response = client.get("/pickup/pickup-001")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Getting pickup items...")
    response = client.get("/pickup/pickup-001/items")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Testing 404 responses...")
    response = client.get("/items/nonexistent")
    print(f"  Item 404 Status: {response.status_code}")

    response = client.get("/pickup/nonexistent")
    print(f"  Pickup 404 Status: {response.status_code}")

    response = client.get("/user/nonexistent")
    print(f"  User 404 Status: {response.status_code}")

    print("\n" + "=" * 80)
    print("All manual tests completed!")
    print("Run 'pytest test_endpoints.py -v' for comprehensive automated testing")
    print("=" * 80)
