# London Test Area Map

## Coverage Area

The test script generates random locations within Central London:

```
                 NORTH (51.6°)
                      ▲
                      |
    WEST (-0.3°) ◄────┼────► EAST (0.1°)
                      |
                      ▼
                 SOUTH (51.4°)
```

## Landmark Pickup Points

```
         Camden Market (51.54, -0.14)
                    ★
                    |
    Notting Hill    |         Shoreditch
    (51.51, -0.20)  |         (51.53, -0.08)
         ★          |              ★
                    |
        Westminster─┼─────Tower Bridge
        (51.50, -0.14)★      (51.51, -0.08)
             ★              ★
                    |
         Kensington |         Greenwich
         (51.49, -0.19)      (51.48, 0.01)
              ★     |              ★
                    |
              Brixton (51.46, -0.11)
                    ★
```

## Real London Map Reference

These coordinates correspond to actual London locations:

### North Area (51.53-51.60)
- **Camden Market**: Popular market, north central
- **Shoreditch**: Trendy east side district

### Central Area (51.49-51.52)
- **Westminster**: Government district, Houses of Parliament
- **Tower Bridge**: Iconic bridge, east of City
- **Notting Hill**: West London neighborhood
- **Kensington**: Affluent west London area

### South Area (51.40-51.48)
- **Brixton**: South London district
- **Greenwich**: Historic area, east London

## Random Volunteer Locations

Each test run, volunteers get random GPS coordinates like:
- `51.5234,-0.1567` (between Westminster and Camden)
- `51.4892,0.0234` (near Greenwich)
- `51.5678,-0.2134` (west of Notting Hill)

## Typical Distances

From Westminster (center) to:
- Camden: ~5 km (10-15 min drive)
- Tower Bridge: ~4 km (8-12 min drive)
- Greenwich: ~9 km (15-20 min drive)
- Kensington: ~3 km (7-10 min drive)
- Brixton: ~6 km (12-18 min drive)

## Coverage Statistics

**Area covered**: ~25 km² of Central London
**Population**: ~2 million people
**Realistic for**: Urban food delivery, volunteer coordination

## Test Scenarios

### Scenario 1: Volunteer close to pickup
```
Pickup:    Westminster (51.50, -0.14)
Volunteer: 51.5023, -0.1389 (~500m away)
Expected:  2-3 minutes drive
```

### Scenario 2: Volunteer across town
```
Pickup:    Westminster (51.50, -0.14)
Volunteer: Greenwich (51.48, 0.01)
Expected:  15-20 minutes drive
```

### Scenario 3: Multiple volunteers, different distances
```
Pickup:     Camden (51.54, -0.14)

Alice:      51.5405, -0.1423 (50m away, high karma)
  → Cost:   Very low (close + high karma)

Bob:        51.4900, -0.1900 (6km away, medium karma)
  → Cost:   Medium

Charlie:    51.4826, 0.0077 (10km away, low karma)
  → Cost:   High

Winner:     Alice (lowest cost)
```

## Google Maps Links

Test routes manually with Google Maps:

- [Westminster to Camden](https://www.google.com/maps/dir/51.5014,-0.1419/51.5415,-0.1426)
- [Tower Bridge to Greenwich](https://www.google.com/maps/dir/51.5055,-0.0754/51.4826,0.0077)
- [Kensington to Shoreditch](https://www.google.com/maps/dir/51.4900,-0.1900/51.5250,-0.0800)

## Running Tests

```bash
# Run with random locations
python test_auction.py

# Each run generates new random volunteer positions
# Pickup point randomly chosen from 8 landmarks
# Perfect for testing different scenarios!
```

## Visualization

Want to visualize your test results? Paste coordinates into:
- **Google Maps**: https://www.google.com/maps
- **OpenStreetMap**: https://www.openstreetmap.org
- **GPS Visualizer**: https://www.gpsvisualizer.com/

Example: `51.5074,-0.1278` → Paste into Google Maps search
