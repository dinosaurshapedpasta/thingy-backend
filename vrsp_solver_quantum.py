import numpy as np

# 1. Get synthetic data

def generate_data(seed):
    # a) make adjacency matrices for cars to drop-off points
    rng = np.random.default_rng(seed)
    cars = 2
    drops = 2
    distance_matrix = rng.random((cars, drops)) # 2 vehicles, 2 drop points
    distance_matrix = distance_matrix.T + distance_matrix / 2 # symmetry-y-ness-y
    # b) make synthetic car capacities
    car_caps = [300 * (1 + rng.random()) for _ in range(cars)] # random capacity between [300, 600]
    # c) make synthetic item volumes
    items = 5
    item_volumes = [10 * (1 + rng.random()) for _ in range(items)] # random volume between [10, 20] for items
    # d) make distances between drop-off points
    drops_matrix = rng.random((drops, drops))
    drops_matrix = drops_matrix.T + drops_matrix / 2
    np.fill_diagonal(drops_matrix, 0) # For symmetry-y distance-y things
    print(distance_matrix, drops_matrix, item_volumes, car_caps)
    return distance_matrix, drops_matrix, item_volumes, car_caps

generate_data(42)

# 2. Formulate the Ising Hamiltonian


# 3. Define a cost function in terms of the matrices

# 4. Ansatz parameters

# 5. QAOA loop.

# a) Make Hamiltonian decomposition of H_C (ground state encodes the solution)
# b) Make Hamiltonian mixer (Pauli-X Mixer for now)
# c) Compose circuit layers (approx time evolution?)
# d) return the expected value of the evolution
# e) classically minimise the exp val
# f) measure output state

# 6. Post processing
# a) re-insert the starting node/replace virtual node
