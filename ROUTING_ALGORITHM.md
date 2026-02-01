# Routing Algorithm Explanation

## How the System Selects Drivers

The auction system selects the **volunteer with the LOWEST cost** to handle the pickup request.

**Lower cost = Better match** 🎯

## Cost Calculation Formula

For each volunteer, the system calculates:

```python
# 1. Get base travel time from Maps API
base_cost = travel_time_minutes  # From OpenRouteService

# 2. Calculate capacity adjustment
# More capacity = lower multiplier (better)
capacity_factor = 1.0 / (1.0 + maxVolume / 100.0)

# 3. Calculate karma adjustment
# Higher karma = lower multiplier (better)
karma_factor = 1.0 / (1.0 + karma / 100.0)

# 4. Calculate final cost
final_cost = base_cost * capacity_factor * karma_factor
```

### Why This Works

- **Distance/Time**: Closer volunteers have lower base cost
- **Capacity**: Volunteers who can carry more get a bonus (lower multiplier)
- **Karma**: Volunteers with better track record get priority (lower multiplier)

## Example Calculations

### Scenario: 3 volunteers, all 15 minutes away from pickup

#### Volunteer 1: Alice (High karma, large capacity)
```
base_cost = 15 minutes
capacity_factor = 1.0 / (1.0 + 200/100) = 1/3 = 0.33
karma_factor = 1.0 / (1.0 + 95/100) = 1/1.95 = 0.51

final_cost = 15 × 0.33 × 0.51 = 2.52  ⭐ LOWEST (WINS!)
```

#### Volunteer 2: Bob (Medium karma, medium capacity)
```
base_cost = 15 minutes
capacity_factor = 1.0 / (1.0 + 100/100) = 1/2 = 0.50
karma_factor = 1.0 / (1.0 + 50/100) = 1/1.5 = 0.67

final_cost = 15 × 0.50 × 0.67 = 5.03
```

#### Volunteer 3: Charlie (Low karma, small capacity)
```
base_cost = 15 minutes
capacity_factor = 1.0 / (1.0 + 50/100) = 1/1.5 = 0.67
karma_factor = 1.0 / (1.0 + 20/100) = 1/1.2 = 0.83

final_cost = 15 × 0.67 × 0.83 = 8.34
```

### Result
**Alice wins** with cost 2.52 (vs 5.03 and 8.34)

Even though all three are the same distance away, Alice's high karma and large capacity make her the best choice.

## Different Scenarios

### Scenario A: Close volunteer with low karma vs Far volunteer with high karma

**Alice**: 30 min away, karma 95, capacity 200L
```
cost = 30 × 0.33 × 0.51 = 5.05
```

**Bob**: 10 min away, karma 20, capacity 50L
```
cost = 10 × 0.67 × 0.83 = 5.56
```

**Winner: Alice** - Her high karma/capacity outweighs the extra distance!

### Scenario B: Very close volunteer with terrible karma

**Charlie**: 5 min away, karma 5, capacity 30L
```
capacity_factor = 1.0 / (1.0 + 30/100) = 0.77
karma_factor = 1.0 / (1.0 + 5/100) = 0.95
cost = 5 × 0.77 × 0.95 = 3.66
```

**Alice**: 15 min away, karma 95, capacity 200L
```
cost = 15 × 0.33 × 0.51 = 2.52
```

**Winner: Alice** - Even though Charlie is 10 min closer, Alice still wins due to superior stats!

## Tuning the Algorithm

You can adjust how much each factor matters by changing the divisors:

### Current (Balanced)
```python
capacity_factor = 1.0 / (1.0 + maxVolume / 100.0)
karma_factor = 1.0 / (1.0 + karma / 100.0)
```

### Emphasize Distance More
```python
# Reduce impact of karma/capacity (use larger divisors)
capacity_factor = 1.0 / (1.0 + maxVolume / 200.0)  # Divided by 200 instead of 100
karma_factor = 1.0 / (1.0 + karma / 200.0)
```

### Emphasize Karma/Capacity More
```python
# Increase impact of karma/capacity (use smaller divisors)
capacity_factor = 1.0 / (1.0 + maxVolume / 50.0)   # Divided by 50 instead of 100
karma_factor = 1.0 / (1.0 + karma / 50.0)
```

## Integration with Complex Routing

Currently, the system selects one volunteer for one pickup. For complex multi-pickup, multi-dropoff routing:

1. **Calculate full distance matrix**: All volunteers × all pickup/dropoff points
2. **Generate adjacency matrix**: NxM matrix where N = volunteers, M = locations
3. **Pass to routing algorithm**: Your external solver (TSP, VRP, genetic algorithm, etc.)
4. **Return optimized routes**: Multiple volunteers, each with ordered list of stops

### Example Integration Point

```python
async def _calculate_routes(
    self,
    adjacency_matrix: List[List[float]],
    volunteers: List[dict],
    pickup_point: models.PickupPoint
) -> List[dict]:
    # For complex routing, call your algorithm here:

    # Option 1: Use OR-Tools (Google's optimization library)
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp

    # Option 2: Use external API
    # response = await http_client.post("your-routing-api.com", ...)

    # Option 3: Use genetic algorithm
    # routes = genetic_algorithm.solve(adjacency_matrix, volunteers)

    # For now: simple greedy assignment
    return self._simple_greedy_assignment(adjacency_matrix, volunteers)
```

## Test Your Algorithm

Run the test script to see the algorithm in action:

```bash
export OPENROUTE_API_KEY=your_key_here
python test_auction.py
```

You'll see output like:

```
📊 Calculating travel times and costs...

Volunteer test_volunteer_001 (karma: 95, capacity: 200.0L) -> Cost: 2.52
Volunteer test_volunteer_002 (karma: 50, capacity: 100.0L) -> Cost: 5.03
✓ SELECTED: test_volunteer_001 with cost 2.52

🎯 ROUTE ASSIGNMENT:
--------------------------------------------------------

   ✓ WINNER: Alice (High Karma, Large Capacity)
     User ID:  test_volunteer_001
     Cost:     2.52 (LOWEST = BEST)
     Karma:    95
     Capacity: 200.0L
     Route:    test_pickup_001
```

## References

- [OpenRouteService API Docs](https://openrouteservice.org/dev/#/api-docs)
- [Vehicle Routing Problem](https://en.wikipedia.org/wiki/Vehicle_routing_problem)
- [Google OR-Tools](https://developers.google.com/optimization)
