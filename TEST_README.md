# Automated Endpoint Testing

This document explains how to run the automated tests for all API endpoints.

## Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Option 1: Run with pytest (Recommended)

Run all tests with verbose output:
```bash
pytest test_endpoints.py -v
```

Run specific test classes:
```bash
# Test only storage endpoints
pytest test_endpoints.py::TestStorageEndpoints -v

# Test only dropoff endpoints
pytest test_endpoints.py::TestDropoffEndpoints -v

# Test only user endpoints
pytest test_endpoints.py::TestUserEndpoints -v
```

Run with coverage report:
```bash
pytest test_endpoints.py --cov=app --cov-report=html
```

### Option 2: Run as Python script

For a quick manual test of key endpoints:
```bash
python test_endpoints.py
```

## Test Coverage

The test suite covers:

### ✅ Default Endpoints
- `GET /test` - Health check

### ✅ Storage Endpoints
- `POST /storage/` - Create storage point
- `GET /storage/{id}` - Get storage point
- `PATCH /storage/{id}` - Update storage point
- `GET /storage/{id}/items` - Get items in storage
- 404 error handling

### ✅ Dropoff Endpoints
- `POST /dropoff/` - Create dropoff point
- `GET /dropoff/{id}` - Get dropoff point
- `PATCH /dropoff/{id}` - Update dropoff point
- 404 error handling

### ✅ User Endpoints
- `GET /user/{id}` - Get user (404 test)
- `PATCH /user/{id}` - Update user (404 test)

### ✅ Integration Tests
- Multi-resource creation and retrieval
- Sequential updates

## Test Database

Tests use a separate SQLite database (`test.db`) that is:
- Created automatically before tests run
- Reset between each test
- Isolated from your production database

## Example Output

```
======================== test session starts =========================
test_endpoints.py::TestDefaultEndpoints::test_health_check PASSED
test_endpoints.py::TestStorageEndpoints::test_create_storage_point PASSED
test_endpoints.py::TestStorageEndpoints::test_get_storage_point PASSED
test_endpoints.py::TestStorageEndpoints::test_update_storage_point PASSED
test_endpoints.py::TestDropoffEndpoints::test_create_dropoff_point PASSED
test_endpoints.py::TestDropoffEndpoints::test_get_dropoff_point PASSED
test_endpoints.py::TestDropoffEndpoints::test_update_dropoff_point PASSED
========================= 15 passed in 0.45s =========================
```

## Continuous Integration

To run tests in CI/CD pipeline:
```bash
pytest test_endpoints.py --junitxml=test-results.xml
```

## Troubleshooting

### Import Errors
If you get import errors, make sure you're in the project root directory and the virtual environment is activated:
```bash
source .venv/bin/activate  # On Linux/Mac
.venv\Scripts\activate     # On Windows
```

### Database Lock Errors
If you get "database is locked" errors:
```bash
rm test.db  # Remove test database and try again
```

### Port Already in Use
The TestClient doesn't use real ports, but if you have the actual server running, you may want to stop it to avoid confusion.
