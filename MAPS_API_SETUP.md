# Maps API Setup Guide

## OpenRouteService (Recommended for Development)

### Why OpenRouteService?
- ✅ **2,000 free requests/day**
- ✅ No credit card required
- ✅ Perfect for hackathons and MVPs
- ✅ Distance matrix API included

### Get Your Free API Key

1. **Sign up** at https://openrouteservice.org/dev/#/signup
2. Verify your email
3. Go to your dashboard: https://openrouteservice.org/dev/#/home
4. Copy your API key (looks like: `5b3ce3597851110001cf6248...`)

### Configure Your App

Add to your environment variables:

```bash
# .env file
OPENROUTE_API_KEY=your_api_key_here
```

Or set it directly:

```bash
export OPENROUTE_API_KEY=your_api_key_here
```

### Test It

```bash
# Test the API directly
curl -X POST \
  'https://api.openrouteservice.org/v2/matrix/driving-car' \
  -H 'Authorization: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "locations": [[-0.1278,51.5074], [-0.0754,51.5055]],
    "metrics": ["duration"]
  }'

# Expected response:
# {
#   "durations": [[0, 720], [720, 0]],  # 720 seconds = 12 minutes
#   "metadata": {...}
# }
```

### Test Your Integration

Run the test script:

```bash
# Set your API key
export OPENROUTE_API_KEY=your_key_here

# Run the test
python test_auction.py
```

This will:
1. Test the Maps API integration
2. Create test volunteers with different karma/capacity
3. Simulate a pickup request with responses
4. Calculate travel times and adjacency matrix
5. Show the routing results

### Location Format

Locations should be in `"lat,lon"` format:
- Example: `"51.5074,-0.1278"` (London)
- Example: `"40.7128,-74.0060"` (New York)

## Alternative Services

### For Production/Scale

| Service | Free Tier | Cost | Sign Up |
|---------|-----------|------|---------|
| **HERE Maps** | 250,000/month | $1/1k | https://developer.here.com/sign-up |
| **Mapbox** | 100,000/month | $0.60/1k | https://account.mapbox.com/auth/signup/ |
| **Google Maps** | $200 credit/month | $5/1k | https://console.cloud.google.com/ |

### HERE Maps Setup (Best Free Tier)

1. Sign up at https://developer.here.com/sign-up
2. Create a project and get API key
3. Use their Matrix API: https://developer.here.com/documentation/matrix-routing-api/

```python
# Replace in auction.py:
HERE_API_KEY = os.getenv("HERE_API_KEY", "")
url = f"https://matrix.router.hereapi.com/v8/matrix"
params = {"apiKey": HERE_API_KEY}
# See docs for full implementation
```

### Google Maps Setup (Most Accurate)

1. Go to https://console.cloud.google.com/
2. Enable Distance Matrix API
3. Create API key with restrictions
4. **Warning**: Requires credit card, charges after $200/month

```python
# Replace in auction.py:
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY", "")
url = "https://maps.googleapis.com/maps/api/distancematrix/json"
params = {
    "origins": "lat,lon",
    "destinations": "lat,lon",
    "key": GOOGLE_MAPS_KEY
}
```

## Rate Limits

| Service | Daily Limit | Rate Limit |
|---------|-------------|------------|
| OpenRouteService | 2,000 | 40 req/min |
| HERE | 8,333 (250k/month) | 5 req/sec |
| Mapbox | 3,333 (100k/month) | 600 req/min |
| Google | ~40,000 ($200 credit) | - |

## Optimization Tips

1. **Cache results**: Store frequently requested routes in Redis/DB
2. **Batch requests**: Use matrix API for multiple origins/destinations at once
3. **Rate limiting**: Implement exponential backoff for failed requests
4. **Fallback**: Use straight-line distance calculation as backup

```python
# Simple fallback using Haversine formula
from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance in km"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    # Estimate time: assume 40 km/h average speed
    minutes = (km / 40) * 60
    return minutes
```
