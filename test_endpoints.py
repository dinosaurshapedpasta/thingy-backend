"""
Automated test script for all API endpoints.
Run with: pytest test_endpoints.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import schemas

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
def sample_user():
    """Create a sample user for testing."""
    user_data = {
        "id": "user-test-001",
        "name": "Test User",
        "karma": 100,
        "maxVolume": 50.0,
        "userType": 1
    }
    response = client.post("/user/", json=user_data)
    # If no POST endpoint exists, we'll need to create directly in DB
    # For now, return the data
    return user_data


@pytest.fixture
def sample_storage():
    """Create a sample storage point for testing."""
    storage_data = {
        "id": "storage-test-001",
        "name": "Test Storage",
        "maxVolume": 100.0,
        "location": "Test Location"
    }
    response = client.post("/storage/", json=storage_data)
    return storage_data


@pytest.fixture
def sample_dropoff():
    """Create a sample dropoff point for testing."""
    dropoff_data = {
        "id": "dropoff-test-001",
        "name": "Test Dropoff",
        "location": "Test Dropoff Location"
    }
    response = client.post("/dropoff/", json=dropoff_data)
    return dropoff_data


# ============================================================================
# DEFAULT ENDPOINTS
# ============================================================================

class TestDefaultEndpoints:
    """Tests for default/health check endpoints."""

    def test_health_check(self):
        """Test the API health check endpoint."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "online" in response.json()["message"].lower()


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
# STORAGE ENDPOINTS
# ============================================================================

class TestStorageEndpoints:
    """Tests for storage point endpoints."""

    def test_create_storage_point(self):
        """Test creating a new storage point."""
        storage_data = {
            "id": "storage-001",
            "name": "Main Storage",
            "maxVolume": 200.0,
            "location": "123 Storage St"
        }
        response = client.post("/storage/", json=storage_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == storage_data["id"]
        assert data["name"] == storage_data["name"]
        assert data["maxVolume"] == storage_data["maxVolume"]
        assert data["location"] == storage_data["location"]

    def test_get_storage_point(self, sample_storage):
        """Test retrieving a storage point by ID."""
        storage_id = sample_storage["id"]
        response = client.get(f"/storage/{storage_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == storage_id
        assert data["name"] == sample_storage["name"]

    def test_get_storage_point_not_found(self):
        """Test getting a non-existent storage point returns 404."""
        response = client.get("/storage/nonexistent-storage")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_storage_point(self, sample_storage):
        """Test updating a storage point."""
        storage_id = sample_storage["id"]
        updated_data = {
            "id": storage_id,
            "name": "Updated Storage Name",
            "maxVolume": 300.0,
            "location": "456 New Location"
        }
        response = client.patch(f"/storage/{storage_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == updated_data["name"]
        assert data["maxVolume"] == updated_data["maxVolume"]
        assert data["location"] == updated_data["location"]

    def test_update_storage_point_not_found(self):
        """Test updating a non-existent storage point returns 404."""
        updated_data = {
            "id": "storage-999",
            "name": "Ghost Storage",
            "maxVolume": 100.0,
            "location": "Nowhere"
        }
        response = client.patch("/storage/nonexistent-storage", json=updated_data)
        assert response.status_code == 404

    def test_get_storage_items(self, sample_storage):
        """Test getting items from a storage point."""
        storage_id = sample_storage["id"]
        response = client.get(f"/storage/{storage_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_storage_items_not_found(self):
        """Test getting items from non-existent storage point returns 404."""
        response = client.get("/storage/nonexistent-storage/items")
        assert response.status_code == 404


# ============================================================================
# DROPOFF ENDPOINTS
# ============================================================================

class TestDropoffEndpoints:
    """Tests for dropoff point endpoints."""

    def test_create_dropoff_point(self):
        """Test creating a new dropoff point."""
        dropoff_data = {
            "id": "dropoff-001",
            "name": "Main Dropoff",
            "location": "789 Dropoff Ave"
        }
        response = client.post("/dropoff/", json=dropoff_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dropoff_data["id"]
        assert data["name"] == dropoff_data["name"]
        assert data["location"] == dropoff_data["location"]

    def test_get_dropoff_point(self, sample_dropoff):
        """Test retrieving a dropoff point by ID."""
        dropoff_id = sample_dropoff["id"]
        response = client.get(f"/dropoff/{dropoff_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dropoff_id
        assert data["name"] == sample_dropoff["name"]

    def test_get_dropoff_point_not_found(self):
        """Test getting a non-existent dropoff point returns 404."""
        response = client.get("/dropoff/nonexistent-dropoff")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_dropoff_point(self, sample_dropoff):
        """Test updating a dropoff point."""
        dropoff_id = sample_dropoff["id"]
        updated_data = {
            "id": dropoff_id,
            "name": "Updated Dropoff Name",
            "location": "999 Updated Location"
        }
        response = client.patch(f"/dropoff/{dropoff_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == updated_data["name"]
        assert data["location"] == updated_data["location"]

    def test_update_dropoff_point_not_found(self):
        """Test updating a non-existent dropoff point returns 404."""
        updated_data = {
            "id": "dropoff-999",
            "name": "Ghost Dropoff",
            "location": "Nowhere"
        }
        response = client.patch("/dropoff/nonexistent-dropoff", json=updated_data)
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for multiple endpoints."""

    def test_create_and_retrieve_workflow(self):
        """Test complete workflow: create storage, create dropoff, retrieve both."""
        # Create storage point
        storage_data = {
            "id": "storage-integration-001",
            "name": "Integration Storage",
            "maxVolume": 150.0,
            "location": "Integration Test Location"
        }
        storage_response = client.post("/storage/", json=storage_data)
        assert storage_response.status_code == 200

        # Create dropoff point
        dropoff_data = {
            "id": "dropoff-integration-001",
            "name": "Integration Dropoff",
            "location": "Integration Dropoff Location"
        }
        dropoff_response = client.post("/dropoff/", json=dropoff_data)
        assert dropoff_response.status_code == 200

        # Retrieve both
        storage_get = client.get(f"/storage/{storage_data['id']}")
        assert storage_get.status_code == 200
        assert storage_get.json()["name"] == storage_data["name"]

        dropoff_get = client.get(f"/dropoff/{dropoff_data['id']}")
        assert dropoff_get.status_code == 200
        assert dropoff_get.json()["name"] == dropoff_data["name"]

    def test_update_multiple_resources(self):
        """Test updating multiple resources in sequence."""
        # Create storage
        storage_data = {
            "id": "storage-multi-001",
            "name": "Original Storage",
            "maxVolume": 100.0,
            "location": "Original Location"
        }
        client.post("/storage/", json=storage_data)

        # Update storage multiple times
        for i in range(3):
            updated_data = {
                "id": storage_data["id"],
                "name": f"Updated Storage {i}",
                "maxVolume": 100.0 + (i * 50),
                "location": f"Location {i}"
            }
            response = client.patch(f"/storage/{storage_data['id']}", json=updated_data)
            assert response.status_code == 200
            assert response.json()["name"] == updated_data["name"]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    """Run tests directly without pytest."""
    print("=" * 80)
    print("Running automated endpoint tests...")
    print("=" * 80)

    # Test health check
    print("\n[TEST] Health check endpoint...")
    response = client.get("/test")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    # Test storage endpoints
    print("\n[TEST] Creating storage point...")
    storage_data = {
        "id": "storage-001",
        "name": "Test Storage",
        "maxVolume": 200.0,
        "location": "Test Location"
    }
    response = client.post("/storage/", json=storage_data)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Getting storage point...")
    response = client.get("/storage/storage-001")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    # Test dropoff endpoints
    print("\n[TEST] Creating dropoff point...")
    dropoff_data = {
        "id": "dropoff-001",
        "name": "Test Dropoff",
        "location": "Test Dropoff Location"
    }
    response = client.post("/dropoff/", json=dropoff_data)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Getting dropoff point...")
    response = client.get("/dropoff/dropoff-001")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\n[TEST] Testing 404 responses...")
    response = client.get("/storage/nonexistent")
    print(f"  Storage 404 Status: {response.status_code}")

    response = client.get("/dropoff/nonexistent")
    print(f"  Dropoff 404 Status: {response.status_code}")

    print("\n" + "=" * 80)
    print("All manual tests completed!")
    print("Run 'pytest test_endpoints.py -v' for comprehensive automated testing")
    print("=" * 80)
