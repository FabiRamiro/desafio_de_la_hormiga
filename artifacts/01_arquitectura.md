# Documento de Arquitectura de Software: Desafío de la Hormiga
**Versión:** 1.0.0  
**Stack Tecnológico:** Python 3.12, PyQt6  
**Rol:** Arquitecto Senior de Software  

---

## 1. Introducción y Visión General

El proyecto **"Desafío de la Hormiga"** es una aplicación educativa de escritorio diseñada para visualizar el funcionamiento de algoritmos clásicos de búsqueda en grafos (**BFS** - Breadth-First Search y **DFS** - Depth-First Search). La aplicación simula una hormiga autónoma que debe recolectar un conjunto dinámico de elementos (comidas) distribuidos en un laberinto generado proceduralmente, para finalmente encontrar la salida.

### Principios Arquitectónicos
1. **Separación de Responsabilidades (SoC):** El motor lógico (grafo y algoritmos) no tiene dependencias de la interfaz gráfica (PyQt6).
2. **Inmutabilidad y Estado Explícito:** El estado de la simulación está centralizado y controlado mediante una máquina de estados determinista.
3. **Modelado Matemático Riguroso:** El tablero se abstrae estrictamente como un **grafo no dirigido y no ponderado**.

---

## 2. Arquitectura de Módulos (Estructura de Directorios)

```text
ant_challenge/
│
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt            # Dependencias (PyQt6)
│
├── core/                       # Lógica de dominio y estructuras de datos
│   ├── __init__.py
│   ├── graph.py                # Modelo de grafo (Nodos, Aristas, Adyacencia)
│   ├── maze_generator.py       # Generador DFS aleatorio + apertura de ciclos
│   └── entities.py             # Definición de Hormiga, Comida, Salida y Estados
│
├── algorithms/                 # Algoritmos de búsqueda clásica
│   ├── __init__.py
│   ├── base_search.py          # Clase abstracta / interfaz de búsqueda
│   ├── bfs.py                  # Implementación de BFS con control de pasos
│   └── dfs.py                  # Implementación de DFS con control de pasos
│
├── simulation/                 # Orquestador de la simulación y máquina de estados
│   ├── __init__.py
│   └── engine.py               # Máquina de estados y bucle de eventos lógicos
│
└── ui/                         # Interfaz gráfica (PyQt6)
    ├── __init__.py
    ├── main_window.py          # Ventana principal y layout general
    ├── board_view.py           # Renderizado del laberinto, grafo y entidades
    ├── tree_view.py            # Visualización del árbol de búsqueda (QTreeView/Custom)
    └── control_panel.py        # Botones, selectores y paneles de estadísticas
```

---

## 3. Diseño Detallado de Clases y Componentes

### 3.1 Módulo `core/graph.py`
Modela el tablero como un grafo abstracto.

* **`Node`**:
  * Atributos: `x: int`, `y: int`, `is_wall: bool`.
  * Métodos: `__hash__`, `__eq__`.
* **`Graph`**:
  * Atributos: `nodes: dict[tuple[int, int], Node]`, `adjacency_list: dict[Node, list[Node]]`.
  * Métodos:
    * `add_edge(node1: Node, node2: Node)`: Añade arista bidireccional.
    * `remove_edge(...)`: Operación auxiliar.
    * `get_neighbors(node: Node) -> list[Node]`: Retorna vecinos transitables ortogonales.
    * `validate_reachability(start: Node, targets: list[Node]) -> bool`: Valida conectividad mediante BFS rápido.

### 3.2 Módulo `core/maze_generator.py`
Encargado de la creación procedural del laberinto perfecto y posterior inyección de ciclos.

* **`MazeGenerator`**:
  * Métodos:
    * `generate(width: int, height: int, cycle_percentage: float) -> Graph`:
      1. Inicializa cuadrícula llena de paredes (`is_wall = True`).
      2. Ejecuta *Randomized DFS* con backtracking para excavar pasillos (crea un laberinto perfecto, garantizando árbol abarcador).
      3. Selecciona aleatoriamente entre el 5% y 10% de las paredes internas restantes y las convierte en pasillos para crear ciclos y rutas alternativas.
      4. Valida que todas las entidades puedan ser colocadas y alcanzadas.

### 3.3 Módulo `algorithms/`
Los algoritmos deben permitir ejecución paso a paso (step-by-step) para pausar, avanzar o retroceder en la visualización.

* **`SearchState` (Enum)**: `EXPLORING`, `FOUND`, `EXHAUSTED`.
* **`SearchStepResult`**:
  * Estructura de datos que contiene: `current_node`, `frontier: list`, `visited: set`, `parent_map: dict`, `path_found: list`, `status: SearchState`.
* **`BaseSearch` (ABC)**:
  * Interfaz con método `step() -> SearchStepResult` o generadores de Python (`yield`).
* **`BFS` / `DFS`**:
  * Heredan de `BaseSearch`. Mantienen internamente sus propias estructuras de datos (`deque` para BFS, `list`/Stack para DFS) y el mapa de padres para la reconstrucción de caminos.

### 3.4 Módulo `simulation/engine.py`
La máquina de estados de la simulación.

* **`SimulationState(Enum)`**:
  * `IDLE`, `SEARCHING_FOOD`, `WALKING_TO_FOOD`, `SEARCHING_EXIT`, `WALKING_TO_EXIT`, `PAUSED`, `COMPLETED`.
* **`SimulationEngine`**:
  * Atributos:
    * `graph: Graph`
    * `ant_position: Node`
    * `remaining_foods: set[Node]`
    * `collected_foods: list[Node]`
    * `exit_node: Node`
    * `state: SimulationState`
    * `current_algorithm: BaseSearch`
    * `statistics: dict` (nodos explorados, longitud acumulada, etc.)
  * Métodos:
    * `start()`: Inicializa el laberinto y fija la primera meta (comida más cercana o arbitraria).
    * `tick()`: Ejecuta un paso lógico de la simulación (llama al método `step()` del algoritmo activo o mueve a la hormiga un nodo a lo largo del camino reconstruido).
    * `pause()`, `resume()`, `reset_search()`, `new_maze()`.

### 3.5 Módulo `ui/` (PyQt6)
* **`MainWindow`**: Contenedor principal que une el `SimulationEngine` con la vista mediante un `QTimer` que regula los ciclos de refresco.
* **`BoardView` (QGraphicsView / QWidget personalizado)**:
  * Renderiza cada celda con códigos de colores precisos:
    * Paredes: Gris oscuro / Negro.
    * Pasillos: Blanco / Gris claro.
    * Nodos visitados: Azul claro / Cian.
    * Frontera: Amarillo.
    * Nodo actual: Naranja brillante.
    * Hormiga: Icono o círculo rojo.
    * Comida: Puntos verdes (pendientes) / Grises (recogidas).
    * Salida: Puerta / Cuadro morado.
    * Camino final: Línea o color magenta.
* **`ControlPanel`**: Contiene botones (`Iniciar`, `Pausar`, `Reanudar`, `Reiniciar Búsqueda`, `Nuevo Laberinto`), selector de algoritmo (`QComboBox`), y slider de velocidad.
* **`StatisticsPanel`**: Muestra métricas en tiempo real (comidas restantes/recogidas, nodos explorados, longitud acumulada).
* **`TreeView`**: Muestra jerárquicamente el árbol de padres generado por BFS/DFS durante la exploración.

---

## 4. Flujo de Datos y Ciclo de Vida de la Simulación

```text
[Inicio App] 
     │
     ▼
[Generación de Laberinto (MazeGenerator)] ──> Valida alcanzabilidad
     │
     ▼
[Estado: IDLE] <────────────────────────────────────────┐
     │ (Usuario presiona "Iniciar")                     │
     ▼                                                  │
[Estado: SEARCHING_FOOD]                                │
     │                                                  │
     ├─► Algoritmo (BFS/DFS) calcula paso a paso        │
     │                                                  │
     ▼                                                  │
[¿Comida Encontrada?] ── Sí ──► [Reconstruir Camino]    │
     │                                    │             │
     No                                   ▼             │
     │                         [Estado: WALKING_TO_FOOD]│
     │                                    │             │
     │                            Hormiga se desplaza   │
     │                                    │             │
     │                            Elimina de remaining  │
     │                                    │             │
     │                         [¿Quedan comidas?] ──────┤
     │                              │ Sí                │
     │                              No                  │
     │                              ▼                   │
     │                 [Estado: SEARCHING_EXIT]         │
     │                              │                   │
     │                              ▼                   │
     │                 [Estado: WALKING_TO_EXIT]        │
     │                              │                   │
     ▼                              ▼                   │
[Actualizar UI / Gráficos] ─────────────────────────────┘
```

---

## 5. Criterios de Aceptación Académica y Técnica

1. **Independencia del Grafo:** Ningún algoritmo de búsqueda conoce elementos de PyQt6; operan exclusivamente sobre objetos `Node` y `Graph`.
2. **Ciclos Garantizados:** El generador de laberintos introduce estrictamente entre 5% y 10% de apertura de paredes adicionales, garantizando múltiples rutas entre nodos.
3. **Gestión de Comidas:** La hormiga recolecta de 5 a 7 comidas secuencialmente. El sistema no permite buscar la salida hasta que `len(remaining_foods) == 0`.
4. **Control Temporal Robusto:** La simulación puede pausarse, reanudarse y reiniciarse en cualquier momento sin pérdida de consistencia en el estado del grafo.
5. **Estadísticas Confiables:** Se registran y muestran con precisión los nodos explorados, la frontera activa y la longitud acumulada del recorrido de la hormiga.