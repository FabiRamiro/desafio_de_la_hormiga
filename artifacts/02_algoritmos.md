### Especificación Algorítmica Rigurosa y Código de Referencia

A continuación, se detalla el diseño algorítmico, el pseudocódigo formal y la implementación en Python 3.12 para los módulos críticos del "Desafío de la Hormiga": la **Generación del Laberinto con ciclos**, el **SearchResult**, los algoritmos de búsqueda multiobjetivo **BFS** y **DFS** con orden determinista, y la **Búsqueda Secuencial con persistencia de estadísticas**.

---

### 1. Generación del Laberinto (`core/maze_generator.py`)

El laberinto se inicializa como una cuadrícula llena de paredes. Se utiliza un algoritmo **Randomized DFS con backtracking** para excavar un laberinto perfecto (un árbol abarcador). Posteriormente, se eliminan aleatoriamente entre el **5% y el 10%** de las paredes internas restantes para inyectar ciclos, permitiendo múltiples rutas alternativas.

#### Orden Determinista de Vecinos (Norte, Este, Sur, Oeste):
* Norte: $(dx = 0, dy = -2)$
* Este: $(dx = 2, dy = 0)$
* Sur: $(dx = 0, dy = 2)$
* Oeste: $(dx = -2, dy = 0)$

```python
import random
from typing import Dict, List, Tuple

class Node:
    __slots__ = ('x', 'y', 'is_wall')
    def __init__(self, x: int, y: int, is_wall: bool = True):
        self.x = x
        self.y = y
        self.is_wall = is_wall

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return isinstance(other, Node) and self.x == other.x and self.y == other.y

class Graph:
    def __init__(self):
        self.nodes: Dict[Tuple[int, int], Node] = {}
        self.adjacency_list: Dict[Node, List[Node]] = {}

    def add_node(self, node: Node):
        key = (node.x, node.y)
        if key not in self.nodes:
            self.nodes[key] = node
            self.adjacency_list[node] = []

    def add_edge(self, n1: Node, n2: Node):
        if n2 not in self.adjacency_list[n1]:
            self.adjacency_list[n1].append(n2)
        if n1 not in self.adjacency_list[n2]:
            self.adjacency_list[n2].append(n1)

    def get_neighbors(self, node: Node) -> List[Node]:
        return self.adjacency_list.get(node, [])

class MazeGenerator:
    """
    Generador procedural de laberintos basado en DFS Aleatorio con Backtracking
    y apertura posterior de ciclos (5% a 10%).
    """
    DIRECTIONS = [(0, -2), (2, 0), (0, 2), (-2, 0)] # Norte, Este, Sur, Oeste

    @classmethod
    def generate(cls, width: int, height: int, cycle_percentage: float = 0.07) -> Graph:
        # Asegurar dimensiones impares para el mallado de paredes y pasillos
        w = width if width % 2 != 0 else width + 1
        h = height if height % 2 != 0 else height + 1

        graph = Graph()
        grid = {}

        # 1. Inicializar tablero lleno de paredes
        for y in range(h):
            for x in range(w):
                node = Node(x, y, is_wall=True)
                grid[(x, y)] = node
                graph.add_node(node)

        # 2. Randomized DFS con pila LIFO real
        start_cell = grid[(1, 1)]
        start_cell.is_wall = False
        stack = [start_cell]
        visited = {start_cell}

        while stack:
            current = stack[-1] # Consulta tope de pila
            unvisited_neighbors = []

            for dx, dy in cls.DIRECTIONS:
                nx, ny = current.x + dx, current.y + dy
                if 0 < nx < w - 1 and 0 < ny < h - 1:
                    neighbor = grid[(nx, ny)]
                    if neighbor not in visited:
                        unvisited_neighbors.append((dx, dy, neighbor))

            if unvisited_neighbors:
                # Seleccionar aleatoriamente un vecino no visitado
                dx, dy, neighbor = random.choice(unvisited_neighbors)
                # Romper la pared intermedia
                wall_x, wall_y = current.x + dx // 2, current.y + dy // 2
                wall_node = grid[(wall_x, wall_y)]
                wall_node.is_wall = False
                
                neighbor.is_wall = False
                visited.add(neighbor)
                stack.append(neighbor)

                # Actualizar aristas del grafo
                graph.add_edge(current, wall_node)
                graph.add_edge(wall_node, neighbor)
            else:
                stack.pop() # Backtracking riguroso LIFO

        # 3. Inyección de ciclos (abrir entre 5% y 10% de paredes internas restantes)
        internal_walls = [
            node for node in graph.nodes.values()
            if node.is_wall and 0 < node.x < w - 1 and 0 < node.y < h - 1
        ]
        
        num_walls_to_remove = int(len(internal_walls) * random.uniform(cycle_percentage, 0.10))
        walls_to_open = random.sample(internal_walls, min(num_walls_to_remove, len(internal_walls)))

        for wall in walls_to_open:
            wall.is_wall = False
            # Conectar ortogonalmente con sus vecinos transitables
            wx, wy = wall.x, wall.y
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                n_key = (wx + dx, wy + dy)
                if n_key in grid and not grid[n_key].is_wall:
                    graph.add_edge(wall, grid[n_key])

        return graph
```

---

### 2. Estructura de Resultado de Búsqueda (`SearchResult`)

```python
from dataclasses import dataclass
from typing import List, Dict, Set, Optional

@dataclass
class SearchResult:
    success: bool
    path: List[Node]
    parents: Dict[Node, Optional[Node]]
    explored_order: List[Node]
    explored_nodes_count: int
    found_target: Optional[Node]
```

---

### 3. BFS Multiobjetivo (`algorithms/bfs.py`)

BFS utiliza estrictamente una cola FIFO (`collections.deque`) y garantiza encontrar el objetivo más cercano en términos de número de aristas (camino mínimo).

```python
from collections import deque
from typing import Set, Optional

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

---

### 4. DFS Multiobjetivo (`algorithms/dfs.py`)

DFS utiliza una pila LIFO (`list` operada mediante `.append()` y `.pop()`). No garantiza optimalidad en la distancia, pero explora en profundidad.

```python
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

---

### 5. Búsqueda Secuencial y Gestión de Estadísticas Acumuladas (`simulation/engine.py`)

La simulación maneja de **5 a 7 comidas** usando `random.randint(5, 7)`. La hormiga ejecuta búsquedas iterativas hasta agotar el conjunto de comidas, acumulando métricas globales en cada ciclo, para finalmente buscar la salida.

```python
import random

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
        exit_target_set = {self.exit_node}
        exit_result: SearchResult = search_algorithm_func(self.graph, current_position, exit_target_set)

        if not exit_result.success:
            raise RuntimeError("¡La salida es inalcanzable desde la última comida!")

        # Acumular estadísticas finales de la salida
        self.total_explored_nodes += exit_result.explored_nodes_count
        self.total_path_length += len(exit_result.path) - 1
        self.search_history.append(exit_result)
        self.ant_position = self.exit_node

        return {
            "total_explored_nodes": self.total_explored_nodes,
            "total_path_length": self.total_path_length,
            "collected_count": len(self.collected_foods),
            "history": self.search_history
        }
```