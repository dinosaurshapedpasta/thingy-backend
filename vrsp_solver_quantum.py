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

distance_matrix, drops_matrix, item_volumes, car_caps = generate_data(42)

def H_A(y, c, t, A):
    N0, _, V = y.shape
    
    total = 0.0
    for v in range(V):
        for i in range(N0):
            for j in range(N0):
                if i != j:
                    # cost for visiting i then j by same vehicle
                    for alpha in range(N0 - 1):
                        total += A * c[i, j, v] * y[i, alpha, v] * y[j, alpha + 1, v]
            
            # cost for departure from depot
            for alpha in range(1, N0):
                term1 = (1 - np.sum(y[:, alpha - 1, v]) + y[i, alpha - 1, v])
                total += A * (t[v] + c[0, i, v]) * term1 * y[i, alpha, v]
            
            # cost for return to depot
            for alpha in range(N0 - 1):
                term2 = (1 - np.sum(y[:, alpha + 1, v]) + y[i, alpha + 1, v])
                total += A * c[i, 0, v] * term2 * y[i, alpha, v]
    
    return total

def H_B(y, B):
    # Sum over cities and vehicles: exactly one visit
    return B * np.sum((1 - np.sum(y, axis=(1, 2)))**2)

def H_C(y, C):
    # Sum over positions: unique assignment
    return C * np.sum((1 - np.sum(y, axis=(0, 2)))**2)

# 2. Formulate the Ising Hamiltonian
def generate_hamiltonian(distance_matrix, drops_matrix, item_volumes, car_caps):
    N0 = np.shape(drops_matrix)
    V = np.shape(distance_matrix)
    N = distance_matrix.shape[0]
    # c[i, j, v]
    c = np.zeros((N, N, V))
    for v in range(V):
        c[:, :, v] = distance_matrix
    t = np.zeros(V) # atm i do not care

    # Binary decision variables
    # y[i, alpha, v] = 1 if vehicle v visits customer i in position alpha
    y = np.zeros((N0, N0, V), dtype=int)  

    # Hamiltonian weights
    max_edge = np.max(distance_matrix)
    A = 1.0
    B = C = 10 * N0 * max_edge
    h_a = H_A(y, c, t, A)
    # h_b = H_B()


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
