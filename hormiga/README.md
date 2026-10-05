# DESAFÍO DE LA HORMIGA - SISTEMA DE NAVEGACIÓN Y BÚSQUEDA EN LABERINTOS PROCEDURALES

Este proyecto es una aplicación interactiva desarrollada en **Python 3.12** y **PyQt6** que simula el comportamiento de una hormiga inteligente navegando por un laberinto generado de forma procedural. El objetivo de la hormiga es recolectar múltiples fuentes de comida distribuidas aleatoriamente y, posteriormente, encontrar la ruta óptima hacia la salida del laberinto utilizando algoritmos fundamentales de la teoría de grafos: **Búsqueda en Anchura (BFS)** y **Búsqueda en Profundidad (DFS)**.

---

## OBJETIVO

El objetivo principal del proyecto es proporcionar una herramienta visual, didáctica y robusta para:

1. Comprender la generación procedural de laberintos mediante algoritmos de grafos.
2. Analizar y comparar visualmente el comportamiento, la eficiencia y la estructura de expansión de los algoritmos de búsqueda **BFS** y **DFS**.
3. Demostrar la resolución de problemas de optimización secuencial (recolección de múltiples objetivos y escape) mediante la abstracción de un entorno físico en un grafo matemático.

---

## REQUISITOS

- **Sistema Operativo:** Windows, macOS o Linux.
- **Lenguaje:** Python 3.12 o superior.
- **Bibliotecas Requeridas:**
  - `PyQt6` (para la interfaz gráfica de usuario).

---

## INSTALACIÓN

1. Asegúrese de tener instalado Python 3.12+. Puede verificarlo ejecutando:

   ```bash
   python --version
   ```

2. Instale la biblioteca `PyQt6` utilizando el gestor de paquetes `pip`:
   ```bash
   pip install PyQt6
   ```

---

## EJECUCIÓN

Para iniciar la aplicación, ejecute el archivo principal desde su terminal:

```bash
python main.py
```

---

## DESCRIPCIÓN DE LA INTERFAZ GRÁFICA

La interfaz de usuario ha sido diseñada meticulosamente utilizando un esquema de paneles divididos (`QSplitter`) para ofrecer una experiencia fluida y responsiva:

1. **Panel Izquierdo (Tablero de Simulación):**
   - Renderiza el laberinto en tiempo real.
   - Muestra de forma animada la expansión de la frontera de búsqueda, los nodos explorados, el camino resultante y el movimiento físico de la hormiga.
   - Permite la interacción directa mediante arrastrar y soltar (Drag and Drop) para reubicar a la hormiga.

2. **Panel Derecho (Control y Datos):**
   - **Grupo de Controles:** Permite seleccionar el algoritmo de búsqueda (BFS o DFS), ajustar la velocidad de la animación mediante un deslizador (de 10 ms a 1000 ms), iniciar, pausar/reanudar la simulación, reiniciar la búsqueda actual o generar un nuevo laberinto procedural.
   - **Grupo de Estadísticas:** Muestra en tiempo real el estado de la simulación, la cantidad de comida recolectada, el número total de nodos explorados y la longitud acumulada del camino recorrido.
   - **Árbol de Búsqueda (`QTreeView`):** Representa jerárquicamente la estructura del árbol de expansión generado por el algoritmo en tiempo real, mostrando las relaciones padre-hijo de los nodos descubiertos.

---

## GENERACIÓN PROCEDURAL DE LABERINTOS

El laberinto no es estático; se genera dinámicamente utilizando conceptos avanzados de teoría de grafos:

### Grafos, Nodos y Aristas

El tablero de juego se modela internamente como un **grafo no dirigido y no ponderado** $G = (V, E)$:

- **Nodos ($V$):** Cada celda del tablero $(x, y)$ representa un nodo. Los nodos pueden ser transitables (caminos) o no transitables (paredes).
- **Aristas ($E$):** Conexiones bidireccionales entre nodos transitables adyacentes (arriba, abajo, izquierda, derecha). Al no ser ponderado, el costo de transitar de un nodo a otro es uniforme (igual a 1).

### Algoritmo Randomized DFS (Búsqueda en Profundidad Aleatoria)

Para garantizar que el laberinto sea un "laberinto perfecto" (completamente conectado y sin ciclos iniciales), se utiliza el algoritmo **Randomized DFS con Backtracking**:

1. Se inicia con una cuadrícula llena de paredes.
2. Se selecciona un nodo inicial (típicamente la posición de la hormiga en `(1, 1)`).
3. Se marca como transitable y se añade a una pila de backtracking.
4. Mientras la pila no esté vacía, se evalúan los vecinos a una distancia de 2 celdas que aún sean paredes.
5. Si existen vecinos no visitados, se elige uno al azar, se derriba la pared intermedia (haciéndola transitable), se conecta mediante aristas en el grafo, se marca el vecino como visitado y se añade a la pila.
6. Si no hay vecinos disponibles, se realiza un _backtrack_ (se extrae el nodo de la pila).

### Generación de Ciclos (Caminos Alternativos)

Para evitar que el laberinto sea estrictamente un árbol (donde solo existe un único camino entre dos puntos cualesquiera), el generador selecciona un porcentaje controlado de paredes internas residuales (entre el 7% y el 10%) y las elimina. Esto introduce ciclos controlados en el grafo, permitiendo que BFS y DFS demuestren sus diferencias al encontrar rutas alternativas.

---

## ALGORITMOS DE BÚSQUEDA: BFS VS DFS

La hormiga utiliza estos algoritmos para planificar su ruta hacia cada objetivo.

### BFS (Búsqueda en Anchura)

- **Estructura de Datos:** Utiliza una cola **FIFO** (First-In, First-Out) mediante `collections.deque`.
- **Funcionamiento:** Explora los nodos de manera radial, nivel por nivel. Primero visita todos los vecinos directos del nodo inicial, luego los vecinos de sus vecinos, y así sucesivamente.
- **Garantía:** En grafos no ponderados, BFS garantiza encontrar siempre el **camino más corto** en términos de número de pasos.

### DFS (Búsqueda en Profundidad)

- **Estructura de Datos:** Utiliza una pila **LIFO** (Last-In, First-Out) implementada con una lista nativa de Python.
- **Funcionamiento:** Explora lo más profundo posible a lo largo de cada rama antes de realizar backtracking. Avanza por un camino hasta encontrar un callejón sin salida o un nodo ya visitado, y luego retrocede para explorar rutas alternativas.
- **Garantía:** No garantiza encontrar el camino más corto. Su ruta suele ser sinuosa y subóptima en presencia de ciclos.

### Diferencias Clave

| Característica     | BFS (Búsqueda en Anchura)                | DFS (Búsqueda en Profundidad)         |
| :----------------- | :--------------------------------------- | :------------------------------------ |
| **Estructura**     | Cola (FIFO)                              | Pila (LIFO)                           |
| **Comportamiento** | Expansión radial y uniforme              | Exploración profunda y lineal         |
| **Camino Óptimo**  | Sí (Garantizado en grafos no ponderados) | No (Suele ser subóptimo)              |
| **Visualización**  | Onda expansiva celeste                   | Línea serpenteante que busca el fondo |

---

## MÚLTIPLES COMIDAS Y BÚSQUEDA SECUENCIAL

El desafío requiere que la hormiga recolecte entre **5 y 7 comidas** distribuidas aleatoriamente antes de escapar por la salida:

1. **Ubicación de Comidas:** Se seleccionan nodos transitables aleatorios que no coincidan con la posición inicial de la hormiga ni con la salida.
2. **Búsqueda Secuencial:** La hormiga no busca todas las comidas simultáneamente. El sistema gestiona un conjunto de comidas pendientes (`remaining_foods`).
3. **Segmentos de Búsqueda:**
   - La hormiga ejecuta una sesión de búsqueda (BFS o DFS) tomando como origen su posición actual y como objetivos el conjunto de comidas restantes.
   - Una vez que el algoritmo encuentra la comida más cercana (según su estrategia de exploración), se traza el camino.
   - La hormiga camina físicamente por el camino hasta llegar a la comida, la consume (se elimina de `remaining_foods` y pasa a `collected_foods`) y actualiza las estadísticas.
   - Este proceso se repite secuencialmente hasta que `remaining_foods` queda vacío.
4. **Búsqueda de la Salida:** Cuando ya no quedan comidas en el tablero, la simulación inicia un último segmento de búsqueda tomando como único objetivo el nodo de salida (`exit_node`). Al llegar a él, la simulación finaliza con éxito.

---

## ÁRBOL DE BÚSQUEDA Y ESTADÍSTICAS

### Árbol de Búsqueda (`QTreeView`)

A medida que el algoritmo explora el grafo, cada nodo descubierto se inserta en un modelo jerárquico (`QStandardItemModel`) reflejando su relación de procedencia (nodo padre -> nodo hijo). Esto permite visualizar la estructura del árbol de búsqueda en tiempo real, expandiendo las ramas activas y mostrando cómo se ramifica la exploración según el algoritmo seleccionado.

### Estadísticas Mostradas

- **Comidas Recogidas:** Muestra el progreso actual (ej. `3 / 6`).
- **Nodos Explorados:** Contador acumulado de todos los nodos analizados por el algoritmo de búsqueda a lo largo de todos los segmentos.
- **Longitud de Camino:** Suma total de pasos físicos que la hormiga ha dado sobre el tablero.
- **Estado:** Muestra el estado actual de la máquina de estados de la aplicación (`IDLE`, `EXPLORING`, `WALKING`, `PAUSED`, `FINISHED`).

---

## GUÍA DE USO INTERACTIVO

### Cómo Mover Manualmente la Hormiga (Drag and Drop)

- Haga clic izquierdo sobre la hormiga, mantenga presionado el botón del mouse y arrástrela a cualquier otra celda transitable del laberinto.
- **Restricciones:**
  - El arrastre solo está permitido cuando la simulación está en estado `IDLE` (Inactiva).
  - No se puede arrastrar a la hormiga mientras está buscando (`EXPLORING`), caminando (`WALKING`), pausada (`PAUSED`) o si la simulación ya ha finalizado (`FINISHED`).
  - No se puede soltar a la hormiga sobre una pared, sobre una comida o sobre la salida.

### Controles de Simulación

- **Iniciar BFS / DFS:** Seleccione el algoritmo deseado en el menú desplegable y haga clic en el botón **"Iniciar"**.
- **Pausar:** Durante la exploración o la caminata, haga clic en **"Pausar"** para detener temporalmente el temporizador de la simulación.
- **Reanudar:** Haga clic en **"Reanudar"** para continuar la simulación exactamente desde el punto donde se pausó.
- **Reiniciar Búsqueda:** Detiene la simulación actual, devuelve a la hormiga a su posición inicial (o a la última posición establecida manualmente), regenera aleatoriamente las comidas y limpia el historial de exploración y el árbol de búsqueda.
- **Generar un Nuevo Laberinto:** Detiene cualquier proceso activo, genera un diseño de laberinto completamente nuevo, reubica a la hormiga en la esquina superior izquierda `(1, 1)`, la salida en la esquina inferior derecha y distribuye nuevas comidas.

### Significado de los Colores en el Tablero

- **Gris Oscuro:** Paredes del laberinto (bloques no transitables).
- **Blanco:** Caminos transitables.
- **Celeste Claro:** Nodos explorados (ya extraídos de la frontera de búsqueda).
- **Amarillo Claro:** Nodos en la frontera de búsqueda (esperando ser explorados).
- **Naranja:** Nodo que está siendo explorado activamente en el paso actual.
- **Línea Magenta:** Ruta planificada desde la posición actual de la hormiga hasta el objetivo encontrado.
- **Círculo Verde:** Comida disponible para recolectar.
- **Cuadrado Púrpura con la letra "E":** Salida del laberinto (Exit).
- **Hormiga (Diseño Detallado):** Representación gráfica estilizada que incluye cabeza, tórax, abdomen, seis patas y dos antenas, escalada dinámicamente según el tamaño de la celda.

---

## AGENTES CREWAI UTILIZADOS EN EL DESARROLLO

Este software fue desarrollado bajo una arquitectura de ingeniería de software colaborativa utilizando agentes de Inteligencia Artificial especializados:

1. **Líder Técnico e Integrador Final:** Responsable de unificar la arquitectura, los algoritmos de grafos, el backend y la interfaz gráfica en un único archivo ejecutable (`main.py`), garantizando la robustez del código y la ausencia de errores de ejecución.
2. **Arquitecto de Software:** Diseñó la estructura de clases desacoplada (`Node`, `Graph`, `MazeGenerator`, `SearchSession`, `BoardView`, `MainWindow`) y definió la máquina de estados de la simulación.
3. **Especialista de Grafos:** Diseñó el generador de laberintos mediante DFS aleatorio con remoción de paredes para ciclos, y estructuró las clases de búsqueda BFS y DFS.
4. **Backend Qwen:** Implementó la lógica de control de flujo, la gestión de la cola FIFO para BFS, la pila LIFO para DFS y la transición de estados de recolección secuencial.
5. **PyQt Qwen:** Desarrolló la interfaz gráfica de usuario, el renderizado personalizado con `QPainter` para la hormiga y los elementos del tablero, y la integración del árbol de búsqueda con `QTreeView`.
6. **Tester QA:** Realizó auditorías de código rigurosas, identificando y corrigiendo bugs críticos como el estancamiento del DFS al evaluar nodos duplicados en la frontera y el bucle infinito en la transición de recolección de comida a búsqueda de salida.

---

## EXPLICACIÓN

### 1. Los Dos Usos Distintos de DFS (¡Punto Crucial!)

**El algoritmo DFS se utiliza en dos momentos completamente diferentes y con propósitos distintos** dentro de la aplicación:

- **Uso 1 (Generación del Laberinto):** Se utiliza un **DFS aleatorio con backtracking** para tallar los caminos en una cuadrícula llena de paredes. Su propósito es crear una estructura de árbol de expansión que conecte todos los nodos del tablero sin ciclos iniciales.
- **Uso 2 (Estrategia de Búsqueda de la Hormiga):** Se utiliza **DFS estándar** como uno de los dos algoritmos de búsqueda seleccionables por el usuario. Su propósito es encontrar un camino desde la posición actual de la hormiga hasta la comida o la salida, mostrando visualmente su tendencia a explorar profundamente antes de ramificar.

### 2. Representación del Entorno como Grafo

El tablero no es una simple matriz bidimensional de caracteres. **Se transforma explícitamente en un grafo no dirigido y no ponderado**. Cada celda transitable es un objeto `Node` y las conexiones adyacentes son aristas en una lista de adyacencia (`Graph.adjacency_list`). Esto permite aplicar algoritmos de búsqueda de caminos estándar de la ciencia de la computación de forma pura.

### 3. Diferencia Algorítmica Estructural (FIFO vs LIFO)

La diferencia fundamental en la implementación de los dos algoritmos de búsqueda son las siguientes:

- **BFS (Búsqueda en Anchura):** Utiliza una cola **FIFO** (First-In, First-Out). Al extraer los nodos en el orden en que fueron descubiertos, la exploración se expande de manera uniforme y concéntrica, garantizando matemáticamente el camino más corto al objetivo.
- **DFS (Búsqueda en Profundidad):** Utiliza una pila **LIFO** (Last-In, First-Out). Al extraer siempre el último nodo descubierto, el algoritmo se "lanza" hacia el fondo de un camino y solo retrocede cuando no tiene más opciones, lo que resulta en rutas subóptimas pero ilustrativas de la teoría de la computación.
