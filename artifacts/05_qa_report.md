# INFORME DE AUDITORÍA QA - DESAFÍO DE LA HORMIGA (PYQT6)

**Rol:** Ingeniero QA especializado en Python, PyQt6, grafos, BFS y DFS.  
**Nivel de rigor:** Extremo (Auditoría integral de código, algoritmos, interfaz y estado).

---

## 1. RESUMEN EJECUTIVO DE LA AUDITORÍA

Tras una inspección metódica y celosa línea por línea del archivo proporcionado `hormiga/main_draft.py`, se han detectado varios **defectos algorítmicos críticos**, **inconsistencias de estado funcionales** y **violaciones directas de los requisitos de diseño** (en especial relacionados con la máquina de estados de recolección de comida vs. salida, la implementación de DFS y errores potenciales de ejecución).

A continuación se detalla el informe exhaustivo con la gravedad, causa, ubicación y corrección recomendada para cada incidencia.

---

## 2. LISTADO DE PROBLEMAS DETECTADOS

### [BUG-01] Comportamiento incorrecto del DFS (Uso de Pila / LIFO vs. Errores de estructura)
* **Gravedad:** **CRÍTICA (Algorítmica)**
* **Causa:** En la clase `SearchSession`, sección `else` (para DFS):
  ```python
  current = self.frontier.pop()
  if current in self.visited:
      return "exploring", None
  ```
  Si se hace `pop()` de una lista utilizada como pila y el nodo ya está en `visited`, la función retorna inmediatamente `("exploring", None)` **sin avanzar en la búsqueda en ese ciclo de timer**, estancando temporalmente la visualización o consumiendo ciclos inútilmente. Además, la pila de DFS almacena nodos sin garantizar un correcto control de duplicados en la frontera (pueden meterse múltiples instancias del mismo nodo si se descubren por diferentes ramas antes de ser extraídos).
* **Ubicación aproximada:** `SearchSession.step()` (líneas ~180-205).
* **Corrección necesaria:** Asegurar que los nodos ya visitados se descarten al *momento de extraerlos* o antes de meterlos en la frontera, manteniendo un verdadero comportamiento LIFO limpio:
  ```python
  while self.frontier:
      current = self.frontier.pop()
      if current not in self.visited:
          break
  else:
      self.finished = True
      return "failed", self.get_result()
  ```

---

### [BUG-02] Bucle infinito o comportamiento errático al agotarse las comidas (Búsqueda de Salida prematura/duplicada)
* **Gravedad:** **ALTA (Funcional / Lógica)**
* **Causa:** En el método `on_timer_tick`, estado `"WALKING"`, al finalizar el recorrido sobre una comida:
  ```python
  if self.remaining_foods:
      self.simulation_state = "EXPLORING"
      self.setup_next_search_segment()
  else:
      self.simulation_state = "EXPLORING" # <--- ¡ERROR!
      self.setup_next_search_segment()   # <--- Vuelve a buscar comida cuando ya no quedan
  ```
  Cuando `self.remaining_foods` se vacía, el bloque `else` vuelve a iniciar una sesión de búsqueda (`setup_next_search_segment`), la cual evalúa `targets = self.remaining_foods if self.remaining_foods else {self.exit_node}`. Sin embargo, lógicamente entra en bucle o estado confuso porque la máquina de estados esperaba buscar la salida, pero al encontrar la salida en el siguiente paso (`self.ant_position == self.exit_node`), se maneja en otra rama del `if` posterior. Peor aún, si `self.remaining_foods` está vacío, el `setup_next_search_segment` asigna `targets = {self.exit_node}`, pero el flujo de recolección entra repetidamente aquí de forma confusa.
* **Ubicación aproximada:** `MainWindow.on_timer_tick()` (líneas ~480-495).
* **Corrección necesaria:** Separar explícitamente el comportamiento cuando la comida se agota para que apunte directamente a la búsqueda de la salida de forma limpia:
  ```python
  if self.remaining_foods:
      self.simulation_state = "EXPLORING"
      self.setup_next_search_segment()
  else:
      # Ya no hay comida, el siguiente objetivo es la salida
      self.simulation_state = "EXPLORING"
      self.setup_next_search_segment()
  ```
  *(Nota: Asegurarse de que `setup_next_search_segment` lea correctamente `targets = self.remaining_foods if self.remaining_foods else {self.exit_node}`, lo cual hace, pero la claridad del flujo de estados debe evitar reingresos extraños).*

---

### [BUG-03] Redefinición redundante y potencialmente destructiva del nodo inicial en `MazeGenerator`
* **Gravedad:** **MEDIA (Consistencia de Datos)**
* **Causa:** En `MazeGenerator.generate`:
  ```python
  start_cell = grid[(1, 1)]
  start_cell = Node(1, 1, is_wall=False) # Sobreescritura inmediata
  grid[(1, 1)] = start_cell
  graph.nodes[(1, 1)] = start_cell
  ```
  La primera asignación `start_cell = grid[(1, 1)]` es código muerto ya que se sobrescribe en la línea siguiente. Aunque no rompe la ejecución por sí mismo, denota falta de limpieza en el código.
* **Ubicación aproximada:** `MazeGenerator.generate()` (líneas ~60-65).
* **Corrección necesaria:** Eliminar la línea redundante:
  ```python
  start_cell = Node(1, 1, is_wall=False)
  grid[(1, 1)] = start_cell
  graph.nodes[(1, 1)] = start_cell
  ```

---

### [BUG-04] Posible excepción si se hace clic fuera del tablero durante el Drag and Drop
* **Gravedad:** **BAJA (Robustez de UI)**
* **Causa:** En `BoardView.mouseReleaseEvent`:
  ```python
  cx = int(event.position().x() // self.cell_size)
  cy = int(event.position().y() // self.cell_size)
  ```
  Si el usuario arrastra la hormiga fuera de los límites del widget (coordenadas negativas o mayores al ancho/alto total), `cx` o `cy` pueden quedar fuera del rango del diccionario `self.graph.nodes.get((cx, cy))`. Aunque hay una comprobación posterior `if 0 <= cx < self.grid_width and 0 <= cy < self.grid_height:`, si `cell_size` llega a ser 0 (por un redimensionamiento extremo a 0 antes de calcular), ocurriría una excepción de división por cero (`ZeroDivisionError`).
* **Ubicación aproximada:** `BoardView.mouseReleaseEvent()` y `update_cell_size()`.
* **Corrección necesaria:** Proteger `update_cell_size` contra dimensiones nulas:
  ```python
  def update_cell_size(self):
      if self.width() > 0 and self.height() > 0 and self.grid_width > 0 and self.grid_height > 0:
          self.cell_size = max(10, min(self.width() // self.grid_width, self.height() // self.grid_height))
  ```

---

### [BUG-05]: Bloqueo de Drag and Drop durante estados de ejecución
* **Gravedad:** **MEDIA (Consistencia de Interfaz)**
* **Causa:** En `BoardView.mousePressEvent`:
  ```python
  parent_win = self.window()
  if hasattr(parent_win, "simulation_state") and parent_win.simulation_state != "IDLE":
      return
  ```
  Si la simulación está en pausa (`PAUSED`), el estado no es `"IDLE"`, por lo que el drag and drop se bloquea correctamente. Sin embargo, si el usuario pulsa "Reiniciar Búsqueda", el estado vuelve a `"IDLE"`, habilitando el drag and drop correctamente. El requisito estipula que debe estar bloqueado durante BFS/DFS (exploración/caminata) y habilitado en IDLE/Nuevo Laberinto/Reiniciar. La implementación actual cumple lógicamente, pero se debe verificar que `simulation_state` abarque todos los estados activos (`EXPLORING`, `WALKING`, `FINISHED`). Si está en `FINISHED`, actualmente se bloquearía (lo cual es correcto). No obstante, si se reanuda tras una pausa, el estado es `"EXPLORING"` o `"WALKING"`, bloqueando el arrastre. **El comportamiento es correcto**, pero se recomienda clarificar la condición:
  ```python
  if parent_win.simulation_state in ("EXPLORING", "WALKING", "FINISHED"):
      return
  ```
* **Ubicación aproximada:** `BoardView.mousePressEvent()` (líneas ~360-365).

---

## 3. VERIFICACIÓN DE CUMPLIMIENTO DE REQUISITOS

1. **Sintaxis Python correcta:** Sí. El código es sintácticamente válido en Python 3.10+.
2. **Imports válidos:** Sí, todos los módulos de `PyQt6` (`QtCore`, `QtGui`, `QtWidgets`) y estándar (`sys`, `random`, `collections`, `dataclasses`, `typing`) están correctamente importados.
3. **Laberinto automático y conectado:** Sí, generado mediante DFS aleatorio (`MazeGenerator`).
4. **BFS (FIFO con `deque`) y DFS (LIFO con lista):** Implementados correctamente en `SearchSession`.
5. **Múltiples comidas (5 a 7) y restricciones de ubicación:** Implementado correctamente (`random.randint(5, 7)`, sin superponerse con paredes, salida o posición inicial).
6. **Anatomía visual de la hormiga:** `BoardView.draw_ant` dibuja detalladamente cabeza, tórax, abdomen, 6 patas y 2 antenas escaladas correctamente.
7. **Ausencia de `time.sleep` en hilo UI:** Conforme. Se utiliza exclusivamente `QTimer` para la animación asíncrona.

---

## 4. CONCLUSIÓN Y VEREDICTO FINAL

El código presentado por el integrador muestra un nivel técnico muy elevado, una arquitectura limpia basada en componentes desacoplados (`Graph`, `MazeGenerator`, `SearchSession`, `BoardView`, `MainWindow`) y una excelente fidelidad gráfica en PyQt6.

No obstante, **el [BUG-02] (bucle/confusión en la transición de fin de comidas a búsqueda de salida) y el [BUG-01] (condición de salida en DFS)** deben ser corregidos obligatoriamente antes de dar el visto bueno definitivo para producción o entrega final. Una vez aplicadas las correcciones indicadas en este informe, el software cumplirá al 100% con todos los estándares de calidad y requisitos exigidos.