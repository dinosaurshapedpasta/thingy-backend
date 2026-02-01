import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from scipy.optimize import minimize

# 1. Setup Backend
service = QiskitRuntimeService()
backend = service.least_busy(simulator=False, operational=True)
print(f"Using backend: {backend.name}")

# 2. Data & Constants
# Keep these small! 3x3x2 = 18 qubits. 3x3x3 = 27 qubits (slower).
N0, V = 3, 2 
dist_matrix = np.random.rand(N0, N0)
np.fill_diagonal(dist_matrix, 0)
n_qubits = N0 * N0 * V

def qubit_index(i, alpha, v):
    return i + N0 * alpha + N0 * N0 * v

# 3. Hamiltonian Construction
def get_hamiltonian(dist_matrix, N0, V):
    num_qubits = N0 * N0 * V
    def get_y_op(i, alpha, v):
        idx = qubit_index(i, alpha, v)
        z_op = SparsePauliOp.from_sparse_list([("Z", [idx], -0.5)], num_qubits=num_qubits)
        i_op = SparsePauliOp.from_sparse_list([("I", [idx], 0.5)], num_qubits=num_qubits)
        return i_op + z_op

    H_cost = SparsePauliOp.from_list([("I" * num_qubits, 0)])
    A, B, C = 1.0, 10.0, 10.0

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

# 4. Prepare QAOA and Transpile (Crucial for hardware)
ansatz = QAOAAnsatz(cost_operator=H_total, reps=1)
pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
transpiled_ansatz = pm.run(ansatz)
mapped_H = H_total.apply_layout(transpiled_ansatz.layout)

# 5. Optimization Loop (Job Mode)
# No Session here to avoid the 400 error
estimator = Estimator(mode=backend)

def cost_func(params):
    print(f"Evaluating parameters: {params}")
    # We send a single job for each iteration
    job = estimator.run([(transpiled_ansatz, mapped_H, params)])
    result = job.result()[0]
    return result.data.evs

print(f"Starting hardware optimization for {n_qubits} qubits...")
init_params = np.random.rand(ansatz.num_parameters)
res = minimize(cost_func, x0=init_params, method='COBYLA', options={'maxiter': 10})

print("Optimal Parameters:", res.x)
print("Lowest Expectation Value:", res.fun)