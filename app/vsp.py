import math
import random
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ==========================================
# 1. Input Processing
# ==========================================
def process_input(input_data):
    num_vols = len(input_data["volunteer_ids"])
    num_drops = len(input_data["dropoff_ids"])
    total_nodes = num_vols + num_drops

    # Stitch Matrices
    full_matrix = [[0.0] * total_nodes for _ in range(total_nodes)]
    
    # B. Volunteer -> Drop
    for v_idx in range(num_vols):
        for d_idx in range(num_drops):
            dist = input_data["distance_matrix"][v_idx][d_idx]
            full_matrix[v_idx][num_vols + d_idx] = int(dist * 100)
            full_matrix[num_vols + d_idx][v_idx] = int(dist * 100)

    # C. Drop -> Drop
    for i in range(num_drops):
        for j in range(num_drops):
            dist = input_data["drops_matrix"][i][j]
            full_matrix[num_vols + i][num_vols + j] = int(dist * 100)

    return {
        "matrix": full_matrix,
        "num_vols": num_vols,
        "num_nodes": num_drops,
        "idx_homes": list(range(0, num_vols)),
        "idx_nodes": list(range(num_vols, total_nodes)),
        "node_sizes": input_data["item_volumes"],
        "car_caps": [int(c) for c in input_data["car_caps"]],
        "drop_ids": input_data["dropoff_ids"],
        "vol_ids": input_data["volunteer_ids"]
    }

# ==========================================
# 2. Logic: Assign Roles
# ==========================================
def assign_roles(data):
    assignments = {}
    taken_nodes = set()
    edges = []
    
    for vol_idx in range(data["num_vols"]):
        home_node = data["idx_homes"][vol_idx]
        for node_idx in data["idx_nodes"]:
            dist = data["matrix"][home_node][node_idx]
            edges.append((dist, vol_idx, node_idx))
            
    edges.sort(key=lambda x: x[0])
    
    for _, vol, node in edges:
        if vol not in assignments and node not in taken_nodes:
            assignments[vol] = node
            taken_nodes.add(node)
            
    demands = [0] * len(data["matrix"])
    
    # 1. Drops (Negative Demand)
    for i, node_idx in enumerate(data["idx_nodes"]):
        if i < len(data["node_sizes"]):
            demands[node_idx] = -int(data["node_sizes"][i])

    # 2. Pickups (Positive Demand = Capacity)
    for vol, node_idx in assignments.items():
        demands[node_idx] = data["car_caps"][vol] 

    return assignments, demands

# ==========================================
# 3. Solver (Returns List of Tuples)
# ==========================================
def solve_routing(input_payload):
    data = process_input(input_payload)
    forced_first_moves, calculated_demands = assign_roles(data)

    manager = pywrapcp.RoutingIndexManager(
        len(data["matrix"]), data["num_vols"], data["idx_homes"], data["idx_homes"]
    )
    routing = pywrapcp.RoutingModel(manager)

    transit_idx = routing.RegisterTransitCallback(
        lambda from_index, to_index: data["matrix"][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
    )
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    demand_idx = routing.RegisterUnaryTransitCallback(
        lambda from_index: calculated_demands[manager.IndexToNode(from_index)]
    )
    
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, data["car_caps"], True, "Capacity"
    )

    solver = routing.solver()
    for vol_idx, target_node in forced_first_moves.items():
        solver.Add(routing.NextVar(routing.Start(vol_idx)) == manager.NodeToIndex(target_node))

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    
    solution = routing.SolveWithParameters(search_parameters)
    cap_dim = routing.GetDimensionOrDie("Capacity")

    all_routes = []
    
    if solution:
        for vehicle_id in range(data["num_vols"]):
            route = []
            index = routing.Start(vehicle_id)
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                
                if node_index < data["num_vols"]:
                    current_id = data["vol_ids"][node_index]
                else:
                    drop_idx = node_index - data["num_vols"]
                    current_id = data["drop_ids"][drop_idx]

                arrival_load = solution.Value(cap_dim.CumulVar(index))
                demand = calculated_demands[node_index]
                load_leaving = arrival_load + demand
                
                route.append((current_id, load_leaving))
                
                index = solution.Value(routing.NextVar(index))
            
            end_load = solution.Value(cap_dim.CumulVar(index))
            vol_id = data["vol_ids"][vehicle_id]
            route.append((vol_id, end_load))
            
            all_routes.append(route)
            
    return all_routes

# ==========================================
# 4. New Data
# ==========================================
def generate_new_payload():
    return {
        # 3 Vehicles, 10 Drops
        # Matrix Rows: Vol-1, Vol-2, Vol-3
        # Matrix Cols: Drop-1 ... Drop-10
        "distance_matrix": [
            [12.5, 4.2, 8.8, 15.1, 3.3, 9.9, 14.2, 5.5, 11.1, 7.7], 
            [5.5, 13.1, 2.2, 8.8, 11.4, 4.4, 9.1, 14.8, 3.6, 12.2], 
            [9.9, 7.7, 14.4, 2.5, 8.1, 12.6, 5.3, 9.2, 13.3, 4.4]
        ],
        # 10x10 Matrix for Drops (Diagonal is 0.0)
        "drops_matrix": [
            [0.0, 5.2, 8.1, 12.4, 7.3, 9.1, 14.5, 6.2, 11.3, 10.1],
            [5.2, 0.0, 4.4, 9.2, 3.5, 6.7, 11.2, 5.8, 8.4, 7.7],
            [8.1, 4.4, 0.0, 6.1, 5.2, 3.3, 8.5, 9.1, 5.5, 4.9],
            [12.4, 9.2, 6.1, 0.0, 8.8, 5.5, 4.2, 12.1, 7.6, 3.3],
            [7.3, 3.5, 5.2, 8.8, 0.0, 4.1, 9.4, 4.4, 6.6, 6.2],
            [9.1, 6.7, 3.3, 5.5, 4.1, 0.0, 5.5, 7.7, 2.2, 3.8],
            [14.5, 11.2, 8.5, 4.2, 9.4, 5.5, 0.0, 13.3, 6.1, 2.5],
            [6.2, 5.8, 9.1, 12.1, 4.4, 7.7, 13.3, 0.0, 10.5, 9.9],
            [11.3, 8.4, 5.5, 7.6, 6.6, 2.2, 6.1, 10.5, 0.0, 5.1],
            [10.1, 7.7, 4.9, 3.3, 6.2, 3.8, 2.5, 9.9, 5.1, 0.0]
        ],
        # Sizes for 10 items
        "item_volumes": [5, 4, 3, 8, 2, 6, 7, 3, 5, 4],
        # Capacities for 3 vehicles
        "car_caps": [35, 25, 40],
        "volunteer_ids": ["Vol-A", "Vol-B", "Vol-C"],
        "dropoff_ids": ["D-01", "D-02", "D-03", "D-04", "D-05", "D-06", "D-07", "D-08", "D-09", "D-10"],
        "car_contents": [],
        "item_id": "test-item"
    }

if __name__ == "__main__":
    payload = generate_new_payload()
    result = solve_routing(payload)
    
    print("--- New Route Results ---")
    for r in result:
        print(r)