# CHATGPT CAN SUCK MY BALLS
import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.primitives import Sampler

np.random.seed(7)

# ---- problem size ----
num_pickups = 2
num_items = 2
num_drivers = 2
capacity = 10

# ---- pickup quantities ----
pickup_items = np.random.randint(0, 4, size=num_pickups)
pickup_items[-1] = num_items - np.sum(pickup_items[:-1])

# ---- nodes ----
# 0 = virtual storage
nodes = [0] + list(range(1, num_pickups + 1))
N = len(nodes)

# ---- distance matrix ----
dist = np.random.randint(1, 10, size=(N, N))
dist = (dist + dist.T) // 2
np.fill_diagonal(dist, 0)

print("Pickup items:", pickup_items)
print("Distance matrix:\n", dist)

qp = QuadraticProgram()

positions = list(range(N))

# ---- variables y_{i,α} ----
for i in nodes:
    for a in positions:
        qp.binary_var(name=f"y_{i}_{a}")


for a in positions:
    qp.linear_constraint(
        {f"y_{i}_{a}": 1 for i in nodes},
        sense="==",
        rhs=1,
        name=f"pos_{a}"
    )

for i in nodes:
    qp.linear_constraint(
        {f"y_{i}_{a}": 1 for a in positions},
        sense="==",
        rhs=1,
        name=f"node_{i}"
    )

quadratic = {}

for a in positions[:-1]:
    for i in nodes:
        for j in nodes:
            if i != j:
                quadratic[(f"y_{i}_{a}", f"y_{j}_{a+1}")] = dist[i][j]

qp.minimize(quadratic=quadratic)

qp.linear_constraint(
    {
        f"y_{i}_{a}": pickup_items[i-1]
        for i in nodes if i != 0
        for a in positions
    },
    sense="<=",
    rhs=capacity,
    name="capacity"
)

qaoa = QAOA(
    sampler=Sampler(),
    optimizer=COBYLA(),
    reps=1
)

optimizer = MinimumEigenOptimizer(qaoa)
result = optimizer.solve(qp)

print(result)

route = [None] * N
for i in nodes:
    for a in positions:
        if result.variables_dict[f"y_{i}_{a}"] > 0.5:
            route[a] = i

print("Route:", route)
