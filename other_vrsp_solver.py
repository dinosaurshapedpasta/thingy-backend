import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from scipy.optimize import minimize

# 1. Setup & Backend Selection
service = QiskitRuntimeService()
backend = service.least_busy(simulator=False, operational=True)
print(f"Using backend: {backend.name}")

# Problem size: 3 customers, 2 vehicles = 18 qubits -> to not burn up all my credits
N0, V = 3, 2 
dist_matrix = np.random.rand(N0, N0)
np.fill_diagonal(dist_matrix, 0)
n_qubits = N0 * N0 * V

def qubit_index(i, alpha, v):
    return i + N0 * alpha + N0 * N0 * v

# 2. Hamiltonian Construction
def get_hamiltonian(dist_matrix, N0, V):
    num_qubits = N0 * N0 * V
    def get_y_op(i, alpha, v):
        idx = qubit_index(i, alpha, v)
        z_op = SparsePauliOp.from_sparse_list([("Z", [idx], -0.5)], num_qubits=num_qubits)
        i_op = SparsePauliOp.from_sparse_list([("I", [idx], 0.5)], num_qubits=num_qubits)
        return i_op + z_op

    H_cost = SparsePauliOp.from_list([("I" * num_qubits, 0)])
    A, B, C = 1.0, 15.0, 15.0 # Slightly higher penalties for hardware bc less maxiter runs

    for v in range(V):
        for i in range(N0):
            for j in range(N0):
                if i == j: continue
                for alpha in range(N0 - 1):
                    term = get_y_op(i, alpha, v) @ get_y_op(j, alpha + 1, v)
                    H_cost += A * dist_matrix[i, j] * term

    for i in range(N0):
        sum_y = sum(get_y_op(i, alpha, v) for alpha in range(N0) for v in range(V))
        H_cost += B * (sum_y - SparsePauliOp("I" * num_qubits))**2

    for v in range(V):
        for alpha in range(N0):
            sum_y = sum(get_y_op(i, alpha, v) for i in range(N0))
            H_cost += C * (sum_y - SparsePauliOp("I" * num_qubits))**2

    return H_cost.simplify()

H_total = get_hamiltonian(dist_matrix, N0, V)

# 3. Transpilation
ansatz = QAOAAnsatz(cost_operator=H_total, reps=1)
pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
transpiled_ansatz = pm.run(ansatz)
mapped_H = H_total.apply_layout(transpiled_ansatz.layout)

# 4. Optimization Loop (Estimator)
estimator = Estimator(mode=backend)

def cost_func(params):
    job = estimator.run([(transpiled_ansatz, mapped_H, params)])
    result = job.result()[0]
    ev = result.data.evs
    print(f"Expectation Value: {ev}")
    return ev

print(f"Optimizing for {n_qubits} qubits...")
init_params = [0.1, 0.1]
res = minimize(cost_func, x0=init_params, method='COBYLA', options={'maxiter': 2})

# 5. Final Sampling (Sampler)
print("\nOptimization finished. Sampling final state...")
sampler = Sampler(mode=backend)
optimized_circuit = transpiled_ansatz.assign_parameters(res.x)
optimized_circuit.measure_all()

# Higher shots for the final answer to beat the noise
sample_job = sampler.run([optimized_circuit], shots=2048)
counts = sample_job.result()[0].data.meas.get_counts()

# 6. Route Decoding
def decode_bitstring(bitstring, N0, V):
    bits = bitstring[:-1]
    routes = {v: [] for v in range(V)}
    for v in range(V):
        for alpha in range(N0):
            for i in range(N0):
                idx = qubit_index(i, alpha, v)
                if idx < len(bits) and bits[idx] == '1':
                    routes[v].append(f"Customer {i}")
    return routes

# Get most likely results
sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

print("\n--- FINAL QUANTUM RESULTS ---")
for i in range(min(3, len(sorted_counts))):
    bitstring, freq = sorted_counts[i]
    decoded = decode_bitstring(bitstring, N0, V)
    print(f"\nResult #{i+1} (Probability: {freq/2048:.2f})")
    for veh, path in decoded.items():
        print(f"  Vehicle {veh}: {' -> '.join(path) if path else 'Idle'}")