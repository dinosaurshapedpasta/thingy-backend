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

The test suite covers all currently registered endpoints:

### ✅ Item Endpoints (`/items`)
- `POST /items/` - Create new item
- `GET /items/{id}` - Get item by ID
- `PATCH /items/{id}` - Update item
- 404 error handling

### ✅ Pickup Point Endpoints (`/pickup`)
- `POST /pickup/` - Create pickup point
- `GET /pickup/{id}` - Get pickup point
- `PATCH /pickup/{id}` - Update pickup point
- `GET /pickup/{id}/items` - Get items at pickup point
- 404 error handling

### ✅ User Endpoints (`/user`)
- `GET /user/{id}` - Get user (404 test)
- `PATCH /user/{id}` - Update user (404 test)

### ✅ Integration Tests
- Multi-resource creation and retrieval
- Sequential updates
- Item and pickup point workflows

### ✅ Edge Cases & Boundary Tests (8 tests)
- Zero, negative, and extremely large volumes
- Special characters and emojis in names
- Very long names (500+ characters)
- Empty string values
- Unicode locations (Japanese, Chinese, etc.)
- High decimal precision

### ✅ Duplicate & Conflict Tests (3 tests)
- Duplicate ID handling
- Update-then-create workflows
- Database constraint validation

### ✅ Sequential Operation Tests (4 tests)
- Create-update-get cycles
- Rapid-fire creation (20+ items)
- Alternating create/update patterns
- Batch operations

### ✅ Data Integrity Tests (4 tests)
- Data persistence after multiple reads
- ID preservation during updates
- Consistency across operations
- Partial field updates

### ✅ Complex Workflow Tests (4 tests)
- Complete item lifecycle
- Ecosystem creation (10 items + 5 pickups)
- Batch updates with verification
- Interleaved operations

### ✅ Stress & Performance Tests (3 tests)
- Creating 50+ items with similar names
- 100+ sequential updates
- Repeated 404 requests (30+)

### ✅ Advanced Edge Cases (10 tests)
- Scientific notation volumes
- HTML/SQL injection attempts
- Null bytes and special sequences
- Very long IDs (255+ chars)
- Tab/newline characters

### ✅ ID Format Tests (6 tests)
- UUID formats
- Mixed case IDs
- Special characters in IDs
- Numeric-only IDs
- Underscores and dashes

### ✅ Volume Boundary Tests (5 tests)
- Maximum float values
- Minimum positive float
- Many decimal places
- Volume sign flips
- Zero transitions

### ✅ Response Validation (5 tests)
- Field presence checks
- Type validation
- Value preservation
- List type verification

### ✅ Cross-Resource Operations (3 tests)
- Alternating creates
- Sequential updates
- Interleaved gets

### ✅ Bulk Operations (4 tests)
- 100 item creation
- 50 sequential updates
- 75 sequential gets
- 50 pickup validations

### ✅ State Transitions (2 tests)
- Multiple update states
- Location changes

### ✅ Error Recovery (3 tests)
- Create after failed get
- Update after failed update
- Multiple 404s then success

### ✅ Idempotency (2 tests)
- GET idempotency
- Update to same values

### ✅ Special Characters (5 tests)
- Quotes and apostrophes
- Backslashes and forward slashes
- Parentheses and brackets
- Various punctuation

### ✅ Consistency Verification (4 tests)
- POST-GET consistency
- PATCH-GET consistency
- Multiple GET consistency
- Pickup items consistency

### ✅ Performance Regression (3 tests)
- Sequential creates
- Sequential updates
- Mixed operations

### ✅ Comprehensive Scenarios (3 tests)
- Full CRUD cycles
- Warehouse simulation
- Integration scenarios

### ✅ Final Comprehensive Suite (30 tests)
- Name length variations (5 scenarios)
- Location format tests
- Volume patterns (zigzag, oscillation, powers)
- International character sets (10 languages)
- Coordinate formats
- Multi-word names
- Rapid operations (25+ items)
- Precision checks
- Cascading updates
- Chain verification
- Final integration (combines all)

**Total: 128 comprehensive test cases** covering:
- ✅ All CRUD operations
- ✅ Error handling (404s, constraints, IntegrityErrors)
- ✅ Edge cases and boundaries (100+ scenarios)
- ✅ Data integrity and consistency
- ✅ Complex workflows and stress testing
- ✅ International support (Unicode, emojis, 10+ languages)
- ✅ Security (SQL injection, XSS attempts)
- ✅ Performance under load (100+ operations)
- ✅ Volume calculations (precision, boundaries, transitions)
- ✅ Real-world scenarios (warehouse, logistics)

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
