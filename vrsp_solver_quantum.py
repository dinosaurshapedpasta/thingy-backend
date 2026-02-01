import numpy as np
from qiskit.quantum_info import SparsePauliOp, Pauli
from qiskit.circuit.library import QAOAAnsatz
from qiskit_aer.primitives import Estimator, Sampler
from scipy.optimize import minimize

# 1. Synthetic data
def generate_data(seed=42):
    rng = np.random.default_rng(seed)
    cars = 2
    drops = 2
    distance_matrix = rng.random((cars, drops))
    distance_matrix = distance_matrix.T + distance_matrix / 2
    car_caps = [300 * (1 + rng.random()) for _ in range(cars)]
    items = 2
    item_volumes = [10 * (1 + rng.random()) for _ in range(items)]
    drops_matrix = rng.random((drops, drops))
    drops_matrix = drops_matrix.T + drops_matrix / 2
    np.fill_diagonal(drops_matrix, 0)
    return distance_matrix, drops_matrix, item_volumes, car_caps

distance_matrix, drops_matrix, item_volumes, car_caps = generate_data()

# -----------------------------
# 2. Qubit mapping & Hamiltonians (UNCHANGED logic)
# -----------------------------
N0 = drops_matrix.shape[0]  
V = distance_matrix.shape[0]  
n_qubits = N0 * N0 * V

def qubit_index(i, alpha, v, N0=N0):
    return i + N0 * alpha + N0*N0 * v

def y_to_sparse_pauli(i, alpha, v, N0=N0, n_qubits=n_qubits):
    z_str = ['I'] * n_qubits
    z_str[qubit_index(i, alpha, v, N0)] = 'Z'
    pauli_str = ''.join(z_str)
    return SparsePauliOp(Pauli(pauli_str), coeffs=[-0.5]) + SparsePauliOp(Pauli('I'*n_qubits), coeffs=[0.5])

def H_A_sparse(A, c, V, N0, n_qubits):
    H = SparsePauliOp.from_list([], num_qubits=n_qubits)
    for v in range(V):
        for i in range(N0):
            for j in range(N0):
                if i != j:
                    for alpha in range(N0-1):
                        term = y_to_sparse_pauli(i, alpha, v, N0, n_qubits).compose(
                            y_to_sparse_pauli(j, alpha+1, v, N0, n_qubits)
                        )
                        H += A * c[i,j,v] * term
    return H

def H_B_sparse(B, V, N0, n_qubits):
    H = SparsePauliOp.from_list([], num_qubits=n_qubits)
    for i in range(N0):
        yi_sum = sum(y_to_sparse_pauli(i, alpha, v, N0, n_qubits)
                     for alpha in range(N0) for v in range(V))
        identity = SparsePauliOp(Pauli('I'*n_qubits), coeffs=[1.0])
        term = (identity - yi_sum).compose(identity - yi_sum)
        H += B * term
    return H

def H_C_sparse(C, V, N0, n_qubits):
    H = SparsePauliOp.from_list([], num_qubits=n_qubits)
    for alpha in range(N0):
        yalpha_sum = sum(y_to_sparse_pauli(i, alpha, v, N0, n_qubits)
                         for i in range(N0) for v in range(V))
        identity = SparsePauliOp(Pauli('I'*n_qubits), coeffs=[1.0])
        term = (identity - yalpha_sum).compose(identity - yalpha_sum)
        H += C * term
    return H

c_weights = np.zeros((N0, N0, V))
for v in range(V):
    c_weights[:, :, v] = distance_matrix

H_total = H_A_sparse(1.0, c_weights, V, N0, n_qubits) + \
          H_B_sparse(10 * N0, V, N0, n_qubits) + \
          H_C_sparse(10 * N0, V, N0, n_qubits)

# -----------------------------
# 3. Modernized QAOA Execution
# -----------------------------
# Using QAOAAnsatz handles the correct alternating layers of Cost and Mixer
ansatz = QAOAAnsatz(cost_operator=H_total, reps=1)
estimator = Estimator()

def qaoa_expectation(params):
    # Estimator is much faster for local optimization than manual bitstring loops
    job = estimator.run(ansatz, H_total, params)
    return job.result().values[0]

print(f"Starting optimization for {n_qubits} qubits...")
res = minimize(qaoa_expectation, x0=[0.5, 0.5], method='COBYLA')
print("Optimal Parameters (gamma, beta):", res.x)

# -----------------------------
# 4. Sampling & Decoding
# -----------------------------
sampler = Sampler()
optimized_circuit = ansatz.assign_parameters(res.x)
optimized_circuit.measure_all()

sample_job = sampler.run(optimized_circuit)
counts = sample_job.result().quasi_dists[0].binary_probabilities()

def decode_counts_to_routes(counts, N0, V):
    total_shots = sum(counts.values())
    decoded_results = []

    for bitstring, prob in counts.items():
        # Qiskit bitstring to indices
        bits = bitstring[::-1]
        y = np.zeros((N0, N0, V), dtype=int)
        for v in range(V):
            for alpha in range(N0):
                for i in range(N0):
                    idx = qubit_index(i, alpha, v, N0)
                    if idx < len(bits):
                        y[i, alpha, v] = int(bits[idx])
        
        # Simple Greedy Repair
        assigned = set()
        routes = []
        for v in range(V):
            v_route = []
            for alpha in range(N0):
                customer = np.where(y[:, alpha, v] == 1)[0]
                if len(customer) > 0 and customer[0] not in assigned:
                    v_route.append(int(customer[0]))
                    assigned.add(customer[0])
                else:
                    v_route.append(None)
            routes.append(v_route)
        decoded_results.append((routes, prob))
    
    return sorted(decoded_results, key=lambda x: x[1], reverse=True)

final_results = decode_counts_to_routes(counts, N0, V)

print("\n--- Top 3 Decoded Routes ---")
for r, p in final_results[:3]:
    print(f"Prob: {p:.4f}, Routes: {r}")