The provided code and explanation cover a comprehensive approach to solving a maze problem using various search algorithms and techniques. Here's a summary of the key components and their functionalities:

### 1. Maze Generation (`maze.py`)

The `generate_maze` function uses a depth-first search (DFS) algorithm to create a maze. It starts from a random cell and recursively explores neighboring cells, carving paths and walls as it goes. The function also includes an optional parameter `cycle_percentage` to inject cycles into the maze, making it more challenging and realistic.

```python
def generate_maze(width: int, height: int, cycle_percentage: float = 0.0) -> Graph:
    """
    Genera un laberinto de tamaño width x height usando el algoritmo de DFS.
    cycle_percentage opcionalmente introduce ciclos en el laberinto.
    """
    graph = Graph(width, height)
    start_node = graph.nodes[(0, 0)]
    stack = [start_node]
    visited = set()

    while stack:
        current = stack[-1]

        if current not in visited:
            visited.add(current)
            neighbors = [n for n in graph.get_neighbors(current) if n not in visited]
            if neighbors:
                next_node = random.choice(neighbors)
                graph.carve_wall(current, next_node)
                stack.append(next_node)
            else:
                stack.pop()
        else:
            stack.pop()

    # Introducir ciclos en el laberinto
    if cycle_percentage > 0:
        for _ in range(int(width * height * cycle_percentage)):
            node = random.choice(list(graph.nodes.values()))
            neighbors = [n for n in graph.get_neighbors(node) if n not in visited]
            if neighbors:
                next_node = random.choice(neighbors)
                graph.carve_wall(node, next_node)

    return graph
```

### 2. Search Result (`SearchResult`)

The `SearchResult` data class is used to encapsulate the results of a search algorithm. It includes information such as whether the search was successful, the path taken, the order in which nodes were explored, the number of explored nodes, and the node where the search stopped (if applicable).

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Set

@dataclass
class SearchResult:
    success: bool
    path: List[Node]
    parents: Dict[Node, Optional[Node]]
    explored_order: List[Node]
    explored_nodes_count: int
    found_target: Optional[Node]
```

### 3. BFS Multiobjetivo (`algorithms/bfs.py`)

The `bfs_multi_target` function implements the Breadth-First Search (BFS) algorithm using a FIFO queue. It is designed to find the shortest path to any of a set of target nodes in the maze. The function ensures that the path is optimal in terms of the number of edges traversed.

```python
from collections import deque
from typing import Set, Dict, Optional, List

def bfs_multi_target(graph: Graph, start: Node, targets: Set[Node]) -> SearchResult:
    """
    Ejecuta BFS utilizando una cola FIFO real para encontrar el objetivo 
    más cercano entre un conjunto de metas múltiples.
    """
    queue = deque([start])
    visited: Set[Node] = {start}
    parents: Dict[Node, Optional[Node]] = {start: None}
    explored_order: List[Node] = []
    
    found_target: Optional[Node] = None

    while queue:
        current = queue.popleft() # Extracción FIFO real
        explored_order.append(current)

        if current in targets:
            found_target = current
            break

        # Orden determinista de vecinos: Norte, Este, Sur, Oeste
        # (Asumiendo que graph.get_neighbors respeta o ordena determinísticamente)
        neighbors = sorted(graph.get_neighbors(current), key=lambda n: (n.y, n.x))

        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                parents[neighbor] = current
                queue.append(neighbor)

    # Reconstrucción del camino si se encontró objetivo
    path: List[Node] = []
    if found_target:
        curr = found_target
        while curr is not None:
            path.append(curr)
            curr = parents[curr]
        path.reverse()

    return SearchResult(
        success=found_target is not None,
        path=path,
        parents=parents,
        explored_order=explored_order,
        explored_nodes_count=len(explored_order),
        found_target=found_target
    )
```

### 4. DFS Multiobjetivo (`algorithms/dfs.py`)

The `dfs_multi_target` function implements the Depth-First Search (DFS) algorithm using a LIFO stack. It is designed to explore the maze as deeply as possible before backtracking. The function does not guarantee the shortest path but can be useful for exploring all possible paths.

```python
from typing import Set, Dict, Optional, List

def dfs_multi_target(graph: Graph, start: Node, targets: Set[Node]) -> SearchResult:
    """
    Ejecuta DFS utilizando una pila LIFO real. 
    Para respetar el orden determinista (Norte, Este, Sur, Oeste) en una pila LIFO,
    los vecinos se insertan en orden inverso.
    """
    stack = [start]
    visited: Set[Node] = set()
    parents: Dict[Node, Optional[Node]] = {start: None}
    explored_order: List[Node] = []
    
    found_target: Optional[Node] = None

    while stack:
        current = stack.pop() # Extracción LIFO real

        if current in visited:
            continue

        visited.add(current)
        explored_order.append(current)

        if current in targets:
            found_target = current
            break

        # Orden determinista: Norte, Este, Sur, Oeste. 
        # Como es LIFO, invertimos la lista para que el Norte sea procesado primero.
        neighbors = sorted(graph.get_neighbors(current), key=lambda n: (n.y, n.x), reverse=True)

        for neighbor in neighbors:
            if neighbor not in visited and neighbor not in parents:
                parents[neighbor] = current
                stack.append(neighbor)

    # Reconstrucción del camino
    path: List[Node] = []
    if found_target:
        curr = found_target
        while curr is not None:
            path.append(curr)
            curr = parents[curr]
        path.reverse()

    return SearchResult(
        success=found_target is not None,
        path=path,
        parents=parents,
        explored_order=explored_order,
        explored_nodes_count=len(explored_order),
        found_target=found_target
    )
```

### 5. Búsqueda Secuencial y Gestión de Estadísticas Acumuladas (`simulation/engine.py`)

The `SimulationEngine` class manages the simulation of the ant's search for food and the exit in the maze. It initializes the simulation with a random number of food items and a set of transitable nodes. The `execute_sequential_search` method runs the search algorithm iteratively, moving the ant from one food item to another and then to the exit. It accumulates statistics such as the total number of explored nodes and the total path length.

```python
import random
from typing import List, Optional, Dict, Set

class SimulationEngine:
    def __init__(self, graph: Graph, start_node: Node, exit_node: Node):
        self.graph = graph
        self.ant_position = start_node
        self.exit_node = exit_node
        
        # Selección de cantidad de comidas (5 a 7)
        num_foods = random.randint(5, 7)
        
        # Obtener celdas transitables únicas excluyendo start y exit
        all_transitables = [
            n for n in graph.nodes.values() 
            if not n.is_wall and n != start_node and n != exit_node
        ]
        self.remaining_foods: Set[Node] = set(random.sample(all_transitables, min(num_foods, len(all_transitables))))
        self.collected_foods: List[Node] = []

        # Estadísticas acumuladas globales
        self.total_explored_nodes = 0
        self.total_path_length = 0
        self.search_history = []

    def execute_sequential_search(self, search_algorithm_func):
        """
        Ejecuta la búsqueda secuencial sobre todas las comidas y luego hacia la salida,
        acumulando estadísticas en tiempo real.
        """
        current_position = self.ant_position

        while self.remaining_foods:
            # Invoca el algoritmo de búsqueda (BFS o DFS) hacia el conjunto de comidas restantes
            result: SearchResult = search_algorithm_func(self.graph, current_position, self.remaining_foods)

            if not result.success:
                raise RuntimeError("¡Laberinto inválido! Existen comidas inaccesibles.")

            # Actualizar estadísticas acumuladas
            self.total_explored_nodes += result.explored_nodes_count
            self.total_path_length += len(result.path) - 1 # Número de aristas del camino

            found_food = result.found_target
            self.remaining_foods.remove(found_food)
            self.collected_foods.append(found_food)

            # Registrar historial de este tramo
            self.search_history.append(result)

            # Actualizar posición actual de la hormiga
            current_position = found_food
            self.ant_position = current_position

        # Fase Final: Buscar camino hacia la salida (Exit Node)
        result = search_algorithm_func(self.graph, current_position, {self.exit_node})
        if not result.success:
            raise RuntimeError("No se pudo encontrar un camino hacia la salida.")

        # Actualizar estadísticas acumuladas
        self.total_explored_nodes += result.explored_nodes_count
        self.total_path_length += len(result.path) - 1

        # Registrar historial de este tramo
        self.search_history.append(result)

        # Actualizar posición actual de la hormiga
        current_position = self.exit_node
        self.ant_position = current_position

        return SearchResult(
            success=True,
            path=result.path,
            parents=result.parents,
            explored_order=result.explored_order,
            explored_nodes_count=result.explored_nodes_count,
            found_target=self.exit_node
        )
```

### Summary

1. **Maze Generation**: The `generate_maze` function creates a maze using the DFS algorithm and optionally introduces cycles.
2. **Search Result**: The `SearchResult` data class encapsulates the results of a search algorithm, including the path, explored nodes, and success status.
3. **BFS Multiobjetivo**: The `bfs_multi_target` function finds the shortest path to any of a set of target nodes using BFS.
4. **DFS Multiobjetivo**: The `dfs_multi_target` function explores the maze as deeply as possible using DFS.
5. **Simulation Engine**: The `SimulationEngine` class manages the simulation of the ant's search for food and the exit, accumulating statistics and running the search algorithm iteratively.

This comprehensive approach ensures that the maze is generated, searched, and analyzed systematically, providing insights into the efficiency and effectiveness of different search algorithms.