import sys
import random
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QSlider, QLabel, QSplitter, QTreeView,
    QGroupBox, QFormLayout, QMessageBox
)

@dataclass(frozen=True)
class Node:
    x: int
    y: int
    is_wall: bool

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
        if n1 not in self.adjacency_list:
            self.adjacency_list[n1] = []
        if n2 not in self.adjacency_list:
            self.adjacency_list[n2] = []
        if n2 not in self.adjacency_list[n1]:
            self.adjacency_list[n1].append(n2)
        if n1 not in self.adjacency_list[n2]:
            self.adjacency_list[n2].append(n1)

    def get_neighbors(self, node: Node) -> List[Node]:
        return self.adjacency_list.get(node, [])

class MazeGenerator:
    DIRECTIONS = [(0, -2), (2, 0), (0, 2), (-2, 0)]

    @classmethod
    def generate(cls, width: int, height: int, cycle_percentage: float = 0.07) -> Graph:
        w = width if width % 2 != 0 else width + 1
        h = height if height % 2 != 0 else height + 1

        graph = Graph()
        grid = {}

        for y in range(h):
            for x in range(w):
                node = Node(x, y, is_wall=True)
                grid[(x, y)] = node
                graph.add_node(node)

        start_cell = Node(1, 1, is_wall=False)
        grid[(1, 1)] = start_cell
        graph.nodes[(1, 1)] = start_cell

        stack = [start_cell]
        visited = {start_cell}

        while stack:
            current = stack[-1]
            unvisited_neighbors = []

            for dx, dy in cls.DIRECTIONS:
                nx, ny = current.x + dx, current.y + dy
                if 0 < nx < w - 1 and 0 < ny < h - 1:
                    neighbor = grid[(nx, ny)]
                    if neighbor.is_wall and neighbor not in visited:
                        unvisited_neighbors.append((dx, dy, neighbor))

            if unvisited_neighbors:
                dx, dy, neighbor = random.choice(unvisited_neighbors)
                wall_x, wall_y = current.x + dx // 2, current.y + dy // 2
                
                wall_node = Node(wall_x, wall_y, is_wall=False)
                grid[(wall_x, wall_y)] = wall_node
                graph.nodes[(wall_x, wall_y)] = wall_node

                neighbor_node = Node(neighbor.x, neighbor.y, is_wall=False)
                grid[(neighbor.x, neighbor.y)] = neighbor_node
                graph.nodes[(neighbor.x, neighbor.y)] = neighbor_node

                visited.add(neighbor_node)
                stack.append(neighbor_node)

                graph.add_edge(current, wall_node)
                graph.add_edge(wall_node, neighbor_node)
            else:
                stack.pop()

        internal_walls = [
            node for node in graph.nodes.values()
            if node.is_wall and 0 < node.x < w - 1 and 0 < node.y < h - 1
        ]
        num_walls_to_remove = int(len(internal_walls) * random.uniform(cycle_percentage, 0.10))
        walls_to_open = random.sample(internal_walls, min(num_walls_to_remove, len(internal_walls)))

        for wall in walls_to_open:
            opened_wall = Node(wall.x, wall.y, is_wall=False)
            grid[(wall.x, wall.y)] = opened_wall
            graph.nodes[(wall.x, wall.y)] = opened_wall
            
            wx, wy = opened_wall.x, opened_wall.y
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                n_key = (wx + dx, wy + dy)
                if n_key in grid and not grid[n_key].is_wall:
                    graph.add_edge(opened_wall, grid[n_key])

        return graph

@dataclass
class SearchResult:
    success: bool
    path: List[Node]
    parents: Dict[Node, Optional[Node]]
    explored_order: List[Node]
    explored_nodes_count: int
    found_target: Optional[Node]

class SearchSession:
    def __init__(self, graph: Graph, start: Node, targets: Set[Node], algo_type: str):
        self.graph = graph
        self.start = start
        self.targets = targets
        self.algo_type = algo_type
        self.visited = set()
        self.parents = {start: None}
        self.explored_order = []
        self.frontier = []
        
        if algo_type == "BFS":
            self.frontier = deque([start])
            self.visited.add(start)
        else:
            self.frontier = [start]
            
        self.found_target = None
        self.current_node = None
        self.finished = False
        self.newly_discovered: List[Tuple[Node, Node]] = []

    def step(self) -> Tuple[str, Optional[SearchResult]]:
        self.newly_discovered.clear()
        if self.finished:
            return "finished", self.get_result()

        if not self.frontier:
            self.finished = True
            return "failed", self.get_result()

        if self.algo_type == "BFS":
            current = self.frontier.popleft()
            self.current_node = current
            self.explored_order.append(current)

            if current in self.targets:
                self.found_target = current
                self.finished = True
                return "found", self.get_result()

            neighbors = sorted(self.graph.get_neighbors(current), key=lambda n: (n.y, n.x))
            for neighbor in neighbors:
                if neighbor not in self.visited:
                    self.visited.add(neighbor)
                    self.parents[neighbor] = current
                    self.frontier.append(neighbor)
                    self.newly_discovered.append((current, neighbor))
        else:
            current = None
            while self.frontier:
                node = self.frontier.pop()
                if node not in self.visited:
                    current = node
                    break
            
            if current is None:
                self.finished = True
                return "failed", self.get_result()
                
            self.current_node = current
            self.visited.add(current)
            self.explored_order.append(current)

            if current in self.targets:
                self.found_target = current
                self.finished = True
                return "found", self.get_result()

            neighbors = sorted(self.graph.get_neighbors(current), key=lambda n: (n.y, n.x), reverse=True)
            for neighbor in neighbors:
                if neighbor not in self.visited:
                    self.parents[neighbor] = current
                    self.frontier.append(neighbor)
                    self.newly_discovered.append((current, neighbor))

        return "exploring", None

    def get_result(self) -> SearchResult:
        path = []
        if self.found_target:
            curr = self.found_target
            while curr is not None:
                path.append(curr)
                curr = self.parents.get(curr)
            path.reverse()
        return SearchResult(
            success=self.found_target is not None,
            path=path,
            parents=self.parents,
            explored_order=self.explored_order,
            explored_nodes_count=len(self.explored_order),
            found_target=self.found_target
        )

class BoardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[Graph] = None
        self.ant_position: Optional[Node] = None
        self.remaining_foods: Set[Node] = set()
        self.collected_foods: List[Node] = []
        self.exit_node: Optional[Node] = None
        
        self.explored_nodes: Set[Node] = set()
        self.frontier_nodes: Set[Node] = set()
        self.current_exploring_node: Optional[Node] = None
        self.current_path: List[Node] = []
        
        self.dragging_ant = False
        self.drag_pixel_pos = QPoint()
        self.cell_size = 30
        self.grid_width = 15
        self.grid_height = 15
        
        self.setMinimumSize(450, 450)

    def set_grid_size(self, w, h):
        self.grid_width = w
        self.grid_height = h
        self.update_cell_size()

    def update_cell_size(self):
        if self.width() > 0 and self.height() > 0 and self.grid_width > 0 and self.grid_height > 0:
            self.cell_size = max(10, min(self.width() // self.grid_width, self.height() // self.grid_height))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_cell_size()

    def paintEvent(self, event):
        if not self.graph:
            return

        painter = QPainter(self)
        self.update_cell_size()

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                node = self.graph.nodes.get((x, y))
                rect_x = x * self.cell_size
                rect_y = y * self.cell_size
                
                if not node or node.is_wall:
                    painter.setBrush(QBrush(QColor(40, 40, 40)))
                    painter.setPen(QPen(QColor(60, 60, 60), 1))
                else:
                    painter.setBrush(QBrush(QColor(240, 240, 240)))
                    painter.setPen(QPen(QColor(220, 220, 220), 1))
                
                painter.drawRect(rect_x, rect_y, self.cell_size, self.cell_size)

        for node in self.explored_nodes:
            if node != self.ant_position and node != self.exit_node and node not in self.remaining_foods:
                rect_x = node.x * self.cell_size
                rect_y = node.y * self.cell_size
                painter.setBrush(QBrush(QColor(173, 216, 230, 180)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(rect_x, rect_y, self.cell_size, self.cell_size)

        for node in self.frontier_nodes:
            if node != self.ant_position and node != self.exit_node and node not in self.remaining_foods:
                rect_x = node.x * self.cell_size
                rect_y = node.y * self.cell_size
                painter.setBrush(QBrush(QColor(255, 255, 153, 180)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(rect_x, rect_y, self.cell_size, self.cell_size)

        if self.current_exploring_node:
            rect_x = self.current_exploring_node.x * self.cell_size
            rect_y = self.current_exploring_node.y * self.cell_size
            painter.setBrush(QBrush(QColor(255, 165, 0, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect_x, rect_y, self.cell_size, self.cell_size)

        if len(self.current_path) > 1:
            painter.setPen(QPen(QColor(255, 0, 255), max(2, self.cell_size // 8)))
            for i in range(len(self.current_path) - 1):
                n1 = self.current_path[i]
                n2 = self.current_path[i+1]
                p1 = QPoint(int((n1.x + 0.5) * self.cell_size), int((n1.y + 0.5) * self.cell_size))
                p2 = QPoint(int((n2.x + 0.5) * self.cell_size), int((n2.y + 0.5) * self.cell_size))
                painter.drawLine(p1, p2)

        for food in self.remaining_foods:
            rect_x = food.x * self.cell_size
            rect_y = food.y * self.cell_size
            painter.setBrush(QBrush(QColor(46, 204, 113)))
            painter.setPen(QPen(QColor(39, 174, 96), 1))
            margin = self.cell_size // 4
            painter.drawEllipse(rect_x + margin, rect_y + margin, self.cell_size - 2 * margin, self.cell_size - 2 * margin)

        if self.exit_node:
            rect_x = self.exit_node.x * self.cell_size
            rect_y = self.exit_node.y * self.cell_size
            painter.setBrush(QBrush(QColor(155, 89, 182)))
            painter.setPen(QPen(QColor(142, 68, 173), 2))
            painter.drawRect(rect_x + 2, rect_y + 2, self.cell_size - 4, self.cell_size - 4)
            painter.setPen(QPen(Qt.GlobalColor.white))
            font = painter.font()
            font.setBold(True)
            font.setPixelSize(max(10, self.cell_size // 2))
            painter.setFont(font)
            painter.drawText(rect_x, rect_y, self.cell_size, self.cell_size, Qt.AlignmentFlag.AlignCenter, "E")

        if self.ant_position and not self.dragging_ant:
            cx = int((self.ant_position.x + 0.5) * self.cell_size)
            cy = int((self.ant_position.y + 0.5) * self.cell_size)
            self.draw_ant(painter, cx, cy, self.cell_size)

        if self.dragging_ant:
            self.draw_ant(painter, self.drag_pixel_pos.x(), self.drag_pixel_pos.y(), self.cell_size)

    def draw_ant(self, painter: QPainter, cx: int, cy: int, size: int):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        scale = size / 40.0
        body_color = QColor(45, 25, 15)
        leg_color = QColor(30, 15, 10)
        
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(QPoint(int(cx - 8 * scale), int(cy)), int(7 * scale), int(5 * scale))
        
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(5 * scale), int(4 * scale))
        
        painter.drawEllipse(QPoint(int(cx + 7 * scale), int(cy)), int(4 * scale), int(4 * scale))
        
        painter.setPen(QPen(leg_color, max(1, int(1.5 * scale))))
        leg_offsets = [
            (int(cx + 2 * scale), int(cy - 3 * scale), int(cx + 5 * scale), int(cy - 10 * scale)),
            (int(cx + 2 * scale), int(cy + 3 * scale), int(cx + 5 * scale), int(cy + 10 * scale)),
            (int(cx), int(cy - 4 * scale), int(cx), int(cy - 11 * scale)),
            (int(cx), int(cy + 4 * scale), int(cx), int(cy + 11 * scale)),
            (int(cx - 4 * scale), int(cy - 3 * scale), int(cx - 8 * scale), int(cy - 10 * scale)),
            (int(cx - 4 * scale), int(cy + 3 * scale), int(cx - 8 * scale), int(cy + 10 * scale))
        ]
        for x1, y1, x2, y2 in leg_offsets:
            painter.drawLine(int(cx), int(cy), x1, y1)
            painter.drawLine(x1, y1, x2, y2)
            
        painter.setPen(QPen(leg_color, max(1, int(1 * scale))))
        painter.drawLine(int(cx + 9 * scale), int(cy - 2 * scale), int(cx + 14 * scale), int(cy - 6 * scale))
        painter.drawLine(int(cx + 14 * scale), int(cy - 6 * scale), int(cx + 18 * scale), int(cy - 5 * scale))
        painter.drawLine(int(cx + 9 * scale), int(cy + 2 * scale), int(cx + 14 * scale), int(cy + 6 * scale))
        painter.drawLine(int(cx + 14 * scale), int(cy + 6 * scale), int(cx + 18 * scale), int(cy + 5 * scale))
        
        painter.restore()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.ant_position:
            parent_win = self.window()
            if hasattr(parent_win, "simulation_state"):
                if parent_win.simulation_state in ("EXPLORING", "WALKING", "FINISHED", "PAUSED"):
                    return

            if self.cell_size > 0:
                cx = int(event.position().x() // self.cell_size)
                cy = int(event.position().y() // self.cell_size)
                if cx == self.ant_position.x and cy == self.ant_position.y:
                    self.dragging_ant = True
                    self.drag_pixel_pos = event.position().toPoint()
                    self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging_ant:
            self.drag_pixel_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.dragging_ant:
            self.dragging_ant = False
            if self.cell_size > 0:
                cx = int(event.position().x() // self.cell_size)
                cy = int(event.position().y() // self.cell_size)
                
                if 0 <= cx < self.grid_width and 0 <= cy < self.grid_height:
                    node = self.graph.nodes.get((cx, cy))
                    if node and not node.is_wall:
                        if node not in self.remaining_foods and node != self.exit_node:
                            self.ant_position = node
                            parent_win = self.window()
                            if hasattr(parent_win, "update_ant_position_from_drag"):
                                parent_win.update_ant_position_from_drag(node)
            self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Desafío de la Hormiga - Integración Final")
        self.resize(1000, 700)

        self.grid_width = 15
        self.grid_height = 15
        self.graph: Optional[Graph] = None
        self.ant_position: Optional[Node] = None
        self.exit_node: Optional[Node] = None
        self.remaining_foods: Set[Node] = set()
        self.collected_foods: List[Node] = []

        self.simulation_state = "IDLE"
        self.total_explored_nodes = 0
        self.total_path_length = 0
        
        self.current_path: List[Node] = []
        self.walk_index = 0
        self.search_session: Optional[SearchSession] = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        
        self.tree_model = QStandardItemModel()
        self.node_to_item_map: Dict[Node, QStandardItem] = {}

        self.init_ui()
        self.generate_new_maze()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.board_view = BoardView()
        left_layout.addWidget(self.board_view)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMaximumWidth(350)
        splitter.addWidget(right_panel)

        ctrl_group = QGroupBox("Controles")
        ctrl_layout = QVBoxLayout(ctrl_group)
        
        form_layout = QFormLayout()
        self.algo_selector = QComboBox()
        self.algo_selector.addItems(["BFS", "DFS"])
        form_layout.addRow("Algoritmo:", self.algo_selector)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(500)
        form_layout.addRow("Velocidad (ms):", self.speed_slider)
        ctrl_layout.addLayout(form_layout)

        self.btn_start = QPushButton("Iniciar")
        self.btn_start.clicked.connect(self.start_simulation)
        ctrl_layout.addWidget(self.btn_start)

        self.btn_pause = QPushButton("Pausar")
        self.btn_pause.clicked.connect(self.pause_simulation)
        self.btn_pause.setEnabled(False)
        ctrl_layout.addWidget(self.btn_pause)

        self.btn_reset = QPushButton("Reiniciar Búsqueda")
        self.btn_reset.clicked.connect(self.reset_search)
        ctrl_layout.addWidget(self.btn_reset)

        self.btn_new_maze = QPushButton("Nuevo Laberinto")
        self.btn_new_maze.clicked.connect(self.generate_new_maze)
        ctrl_layout.addWidget(self.btn_new_maze)

        right_layout.addWidget(ctrl_group)

        stats_group = QGroupBox("Estadísticas")
        stats_layout = QFormLayout(stats_group)
        self.lbl_foods = QLabel("0 / 0")
        self.lbl_explored = QLabel("0")
        self.lbl_path_len = QLabel("0")
        self.lbl_state = QLabel("IDLE")
        stats_layout.addRow("Comidas Recogidas:", self.lbl_foods)
        stats_layout.addRow("Nodos Explorados:", self.lbl_explored)
        stats_layout.addRow("Longitud Camino:", self.lbl_path_len)
        stats_layout.addRow("Estado:", self.lbl_state)
        right_layout.addWidget(stats_group)

        tree_group = QGroupBox("Árbol de Búsqueda")
        tree_layout = QVBoxLayout(tree_group)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(True)
        tree_layout.addWidget(self.tree_view)
        right_layout.addWidget(tree_group)

    def generate_new_maze(self):
        self.timer.stop()
        self.simulation_state = "IDLE"
        self.total_explored_nodes = 0
        self.total_path_length = 0
        self.current_path.clear()
        self.search_session = None
        
        self.graph = MazeGenerator.generate(self.grid_width, self.grid_height, 0.07)
        
        self.ant_position = self.graph.nodes.get((1, 1))
        self.exit_node = self.graph.nodes.get((self.grid_width - 2, self.grid_height - 2))
        
        all_transitables = [
            n for n in self.graph.nodes.values()
            if not n.is_wall and n != self.ant_position and n != self.exit_node
        ]
        num_foods = random.randint(5, 7)
        self.remaining_foods = set(random.sample(all_transitables, min(num_foods, len(all_transitables))))
        self.collected_foods.clear()

        self.board_view.graph = self.graph
        self.board_view.ant_position = self.ant_position
        self.board_view.exit_node = self.exit_node
        self.board_view.remaining_foods = self.remaining_foods
        self.board_view.collected_foods = self.collected_foods
        self.board_view.set_grid_size(self.grid_width, self.grid_height)
        
        self.board_view.explored_nodes.clear()
        self.board_view.frontier_nodes.clear()
        self.board_view.current_exploring_node = None
        self.board_view.current_path.clear()

        self.tree_model.clear()
        self.node_to_item_map.clear()

        self.update_ui_stats()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("Pausar")
        self.board_view.update()

    def update_ant_position_from_drag(self, node: Node):
        self.ant_position = node
        self.board_view.ant_position = node
        self.update_ui_stats()

    def update_ui_stats(self):
        total_foods = len(self.remaining_foods) + len(self.collected_foods)
        self.lbl_foods.setText(f"{len(self.collected_foods)} / {total_foods}")
        self.lbl_explored.setText(str(self.total_explored_nodes))
        self.lbl_path_len.setText(str(self.total_path_length))
        self.lbl_state.setText(self.simulation_state)

    def start_simulation(self):
        if self.simulation_state == "IDLE":
            self.simulation_state = "EXPLORING"
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_pause.setText("Pausar")
            self.setup_next_search_segment()
            self.timer.start(self.speed_slider.value())
        elif self.simulation_state == "PAUSED":
            self.simulation_state = "EXPLORING" if self.search_session else "WALKING"
            self.btn_pause.setText("Pausar")
            self.timer.start(self.speed_slider.value())

    def pause_simulation(self):
        if self.simulation_state in ["EXPLORING", "WALKING"]:
            self.simulation_state = "PAUSED"
            self.btn_pause.setText("Reanudar")
            self.timer.stop()
            self.update_ui_stats()

    def reset_search(self):
        self.timer.stop()
        self.simulation_state = "IDLE"
        self.total_explored_nodes = 0
        self.total_path_length = 0
        self.current_path.clear()
        self.search_session = None
        
        self.collected_foods.clear()
        all_transitables = [
            n for n in self.graph.nodes.values()
            if not n.is_wall and n != self.ant_position and n != self.exit_node
        ]
        num_foods = random.randint(5, 7)
        self.remaining_foods = set(random.sample(all_transitables, min(num_foods, len(all_transitables))))
        
        self.board_view.remaining_foods = self.remaining_foods
        self.board_view.collected_foods = self.collected_foods
        self.board_view.explored_nodes.clear()
        self.board_view.frontier_nodes.clear()
        self.board_view.current_exploring_node = None
        self.board_view.current_path.clear()
        
        self.tree_model.clear()
        self.node_to_item_map.clear()
        
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("Pausar")
        self.update_ui_stats()
        self.board_view.update()

    def setup_next_search_segment(self):
        self.board_view.explored_nodes.clear()
        self.board_view.frontier_nodes.clear()
        self.board_view.current_exploring_node = None
        self.board_view.current_path.clear()
        
        self.tree_model.clear()
        self.node_to_item_map.clear()

        targets = self.remaining_foods if self.remaining_foods else {self.exit_node}
        algo = self.algo_selector.currentText()
        
        self.search_session = SearchSession(self.graph, self.ant_position, targets, algo)
        
        root_item = QStandardItem(f"Inicio ({self.ant_position.x}, {self.ant_position.y})")
        self.tree_model.appendRow(root_item)
        self.node_to_item_map[self.ant_position] = root_item

    def on_timer_tick(self):
        self.timer.setInterval(self.speed_slider.value())
        
        if self.simulation_state == "EXPLORING":
            if not self.search_session:
                return
            
            status, result = self.search_session.step()
            
            self.board_view.explored_nodes = set(self.search_session.explored_order)
            self.board_view.frontier_nodes = set(self.search_session.frontier)
            self.board_view.current_exploring_node = self.search_session.current_node
            
            for parent, child in self.search_session.newly_discovered:
                parent_item = self.node_to_item_map.get(parent)
                if parent_item:
                    child_item = QStandardItem(f"({child.x}, {child.y})")
                    parent_item.appendRow(child_item)
                    self.node_to_item_map[child] = child_item
                    self.tree_view.expand(parent_item.index())

            self.board_view.update()

            if status == "found" and result:
                self.total_explored_nodes += result.explored_nodes_count
                self.current_path = result.path
                self.walk_index = 0
                self.simulation_state = "WALKING"
                self.search_session = None
                self.board_view.current_path = self.current_path
                self.update_ui_stats()
            elif status == "failed":
                self.timer.stop()
                self.simulation_state = "IDLE"
                self.update_ui_stats()
                QMessageBox.critical(self, "Error", "No se encontró un camino al objetivo.")

        elif self.simulation_state == "WALKING":
            if self.walk_index < len(self.current_path):
                next_node = self.current_path[self.walk_index]
                self.ant_position = next_node
                self.board_view.ant_position = next_node
                self.walk_index += 1
                self.board_view.update()
            else:
                self.total_path_length += len(self.current_path) - 1
                self.current_path.clear()
                self.board_view.current_path.clear()
                
                if self.ant_position in self.remaining_foods:
                    self.remaining_foods.remove(self.ant_position)
                    self.collected_foods.append(self.ant_position)
                    self.update_ui_stats()
                    
                    self.simulation_state = "EXPLORING"
                    self.setup_next_search_segment()
                elif self.ant_position == self.exit_node:
                    self.timer.stop()
                    self.simulation_state = "FINISHED"
                    self.update_ui_stats()
                    self.btn_pause.setEnabled(False)
                    QMessageBox.information(self, "Éxito", "¡La hormiga ha recolectado toda la comida y llegó a la salida!")
                else:
                    self.timer.stop()
                    self.simulation_state = "IDLE"
                    self.update_ui_stats()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()