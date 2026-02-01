# Testing the Auction Routing System

## Quick Start

### 1. Setup Environment

```bash
# Get API key from https://openrouteservice.org/dev/#/signup
export OPENROUTE_API_KEY=your_key_here

# Start your server
uvicorn app.main:app --reload
```

### 2. Run Automated Tests

```bash
# Run the full test suite
python test_auction.py
```

This will:
- ✅ Test Maps API integration
- ✅ Create mock volunteers
- ✅ Simulate pickup request workflow
- ✅ Calculate travel times
- ✅ Generate adjacency matrix
- ✅ Show routing results

## Manual API Testing

### Step 1: Create Test Users (Volunteers)

```bash
# Create volunteer 1 (High karma, large capacity)
curl -X POST http://localhost:8000/user \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "id": "volunteer_001",
    "name": "Alice",
    "karma": 95,
    "maxVolume": 200.0,
    "userType": 1
  }'

# Create volunteer 2 (Medium karma, medium capacity)
curl -X POST http://localhost:8000/user \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "id": "volunteer_002",
    "name": "Bob",
    "karma": 50,
    "maxVolume": 100.0,
    "userType": 1
  }'

# Create volunteer 3 (Low karma, small capacity)
curl -X POST http://localhost:8000/user \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "id": "volunteer_003",
    "name": "Charlie",
    "karma": 20,
    "maxVolume": 50.0,
    "userType": 1
  }'
```

### Step 2: Create Pickup Point

```bash
# Create pickup point in London
curl -X POST http://localhost:8000/pickup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "id": "pickup_001",
    "name": "Central London Food Bank",
    "location": "51.5074,-0.1278"
  }'
```

### Step 3: Create Pickup Request (Starts Auction)

```bash
# Manager creates pickup request
curl -X POST http://localhost:8000/pickuprequests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer MANAGER_TOKEN" \
  -d '{
    "id": "request_001",
    "pickupPointID": "pickup_001"
  }'

# This triggers the auction workflow:
# - Broadcasts to all volunteers
# - Waits 60 seconds for responses
# - Calculates travel times
# - Generates routes
```

### Step 4: Volunteers Respond (Within 60 seconds)

```bash
# Alice accepts (nearby location)
curl -X POST http://localhost:8000/pickuprequests/request_001/accept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ALICE_TOKEN"
# TODO: Add GPS location to this endpoint

# Bob accepts (farther location)
curl -X POST http://localhost:8000/pickuprequests/request_001/accept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer BOB_TOKEN"

# Charlie denies
curl -X POST http://localhost:8000/pickuprequests/request_001/deny \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer CHARLIE_TOKEN"
```

### Step 5: View Results (After 60 seconds)

```bash
# Get all responses
curl -X GET http://localhost:8000/pickuprequests/request_001/responses \
  -H "Authorization: Bearer MANAGER_TOKEN"

# Response:
# [
#   {"userID": "volunteer_001", "response": "accept"},
#   {"userID": "volunteer_002", "response": "accept"},
#   {"userID": "volunteer_003", "response": "deny"}
# ]
```

## Test Data: London Locations

### Automated Test (Random Locations)

The `test_auction.py` script automatically generates:
- **Random pickup point**: One of 8 London landmarks
- **Random volunteer locations**: GPS coordinates within Central London boundaries

**London boundaries used:**
- Latitude: 51.4° to 51.6° (covers central London)
- Longitude: -0.3° to 0.1° (west to east)

**Landmark pickup points:**
- Tower Bridge Food Bank (`51.5055,-0.0754`)
- Westminster Community Center (`51.5014,-0.1419`)
- Camden Market Hub (`51.5415,-0.1426`)
- Kensington Aid Point (`51.4900,-0.1900`)
- Greenwich Food Hub (`51.4826,0.0077`)
- Shoreditch Distribution (`51.5250,-0.0800`)
- Brixton Community Kitchen (`51.4615,-0.1145`)
- Notting Hill Center (`51.5095,-0.2000`)

Run the test multiple times to see different scenarios!

### Example Travel Times

Between these locations (driving):
- Tower Bridge → Camden: ~12 minutes
- Westminster → Kensington: ~15 minutes
- Camden → Greenwich: ~25 minutes
- Brixton → Shoreditch: ~20 minutes

### Manual Testing Coordinates

Use these coordinates for manual API testing:

| Location | Coordinates | Description |
|----------|-------------|-------------|
| **Tower Bridge** | `51.5055,-0.0754` | Tourist area |
| **Camden Market** | `51.5415,-0.1426` | North London |
| **Kensington** | `51.4900,-0.1900` | West London |
| **Greenwich** | `51.4826,0.0077` | East London |
| **Westminster** | `51.5014,-0.1419` | Central London |

## Understanding the Adjacency Matrix

The system calculates a cost matrix for each volunteer:

```python
# Example matrix calculation:
base_cost = travel_time_minutes  # From Maps API

# Adjustments:
capacity_factor = 1.0 / (1.0 + maxVolume / 100.0)
karma_factor = 1.0 / (1.0 + karma / 100.0)

final_cost = base_cost * capacity_factor * karma_factor

# Lower cost = better match
```

### Example Calculation

Volunteer: Alice
- Travel time: 15 minutes
- Max volume: 200L
- Karma: 95

```
capacity_factor = 1.0 / (1.0 + 200/100) = 0.33
karma_factor = 1.0 / (1.0 + 95/100) = 0.51
final_cost = 15 * 0.33 * 0.51 = 2.52
```

Volunteer: Charlie
- Travel time: 15 minutes
- Max volume: 50L
- Karma: 20

```
capacity_factor = 1.0 / (1.0 + 50/100) = 0.67
karma_factor = 1.0 / (1.0 + 20/100) = 0.83
final_cost = 15 * 0.67 * 0.83 = 8.34
```

**Alice has lower cost → gets priority!**

## Testing Maps API Directly

```bash
# Test OpenRouteService API
curl -X POST \
  'https://api.openrouteservice.org/v2/matrix/driving-car' \
  -H "Authorization: $OPENROUTE_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "locations": [
      [-0.1278, 51.5074],
      [-0.0754, 51.5055]
    ],
    "metrics": ["duration", "distance"]
  }'

# Response:
# {
#   "durations": [[0, 720], [720, 0]],     # seconds
#   "distances": [[0, 3500], [3500, 0]],   # meters
#   "metadata": {...}
# }
```

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $OPENROUTE_API_KEY

# Test API key
curl -X GET \
  'https://api.openrouteservice.org/v2/health' \
  -H "Authorization: $OPENROUTE_API_KEY"
```

### Common Errors

**401 Unauthorized**
- Invalid or missing API key
- Get new key at https://openrouteservice.org/dev/#/signup

**403 Forbidden**
- Rate limit exceeded (40 req/min on free tier)
- Wait a minute or upgrade plan

**422 Invalid Request**
- Check location format: `[lon, lat]` not `[lat, lon]`!
- OpenRouteService uses `[longitude, latitude]` order

### Debug Mode

```python
# Enable debug logging in auction.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Run test
python test_auction.py
```

## Next Steps

1. ✅ Test the basic workflow with `test_auction.py`
2. 📍 Add GPS location field to `PickupRequestResponses` model
3. 🔔 Implement notification system (WebSocket/Push)
4. 🗺️ Integrate your routing algorithm
5. 🚀 Test with real volunteers in production

## Performance Tips

- **Cache results**: Store common routes in Redis/DB
- **Batch requests**: Calculate all volunteer-to-pickup distances in one API call
- **Rate limiting**: Use exponential backoff
- **Fallback**: Implement Haversine distance as backup

See `MAPS_API_SETUP.md` for more details on API providers and optimization.
