# main.py
import tkinter as tk
from tkinter import messagebox
from parking_algo import ParkingLot
import time

GRID_SIZE = 6
CELL_SIZE = 60
ANIMATION_DELAY_MS = 300  # ms per step

# Colors
OCCUPIED_COLOR = "red"
FREE_COLOR = "lightgreen"
PATH_COLOR = "yellow"
CAR_COLOR = "blue"
GRAPH_EDGE_COLOR = "#999"
GRAPH_NODE_COLOR = "#74c0fc"
HIGHLIGHT_EDGE_COLOR = "orange"

class SmartParkingFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Smart Parking Finder")
        total_w = GRID_SIZE * CELL_SIZE + 420
        total_h = max(GRID_SIZE * CELL_SIZE + 40, 520)
        self.root.geometry(f"{total_w}x{total_h}")

        # Model
        self.lot = ParkingLot(GRID_SIZE)

        # State
        self.current_pos = None      # where car currently is (None until placed)
        self.destination = None
        self.current_path = []       # nodes of current path
        self.path_index = 0
        self.animating = False
        self.use_bfs = True

        # UI: left grid canvas
        self.grid_canvas = tk.Canvas(self.root,
                                     width=GRID_SIZE * CELL_SIZE,
                                     height=GRID_SIZE * CELL_SIZE,
                                     bg="white", highlightthickness=0)
        self.grid_canvas.place(x=20, y=20)
        self.grid_canvas.bind("<Button-1>", self.on_grid_click)

        # UI: right panel (controls + graph preview)
        panel_x = GRID_SIZE * CELL_SIZE + 40
        self.panel_frame = tk.Frame(self.root)
        self.panel_frame.place(x=panel_x, y=20)

        tk.Button(self.panel_frame, text="🔄 Randomize Occupied", width=20, command=self.reset).pack(pady=6)
        self.algo_btn = tk.Button(self.panel_frame, text="Algorithm: BFS", width=20, command=self.toggle_algo)
        self.algo_btn.pack(pady=6)
        tk.Button(self.panel_frame, text="Show Graph Window", width=20, command=self.show_graph_window).pack(pady=6)
        tk.Button(self.panel_frame, text="Exit", width=20, command=self.root.destroy).pack(pady=6)

        # legend
        self._make_legend()

        # Graph preview canvas
        self.graph_preview = tk.Canvas(self.panel_frame, width=320, height=320, bg="white", highlightthickness=1)
        self.graph_preview.pack(pady=8)

        # Info label
        self.info_label = tk.Label(self.root, text="Click a free cell to place the car (start).", font=("Arial", 12))
        self.info_label.place(x=20, y=GRID_SIZE * CELL_SIZE + 30)

        # Draw initial
        self.draw_grid()
        self.draw_graph_preview()

    def _make_legend(self):
        frame = tk.Frame(self.panel_frame)
        frame.pack(pady=8, anchor="w")
        labels = [("Free", FREE_COLOR), ("Occupied", OCCUPIED_COLOR),
                  ("Car", CAR_COLOR), ("Path", PATH_COLOR)]
        for text, col in labels:
            f = tk.Frame(frame)
            f.pack(anchor="w")
            c = tk.Canvas(f, width=18, height=18, bg=col)
            c.pack(side="left", padx=4)
            tk.Label(f, text=text).pack(side="left", padx=6)

    def toggle_algo(self):
        self.use_bfs = not self.use_bfs
        self.algo_btn.config(text=f"Algorithm: {'BFS' if self.use_bfs else 'A*'}")

    def reset(self):
        if self.animating:
            messagebox.showinfo("Wait", "Please wait until current animation finishes.")
            return
        self.lot.randomize_occupied()
        self.current_pos = None
        self.destination = None
        self.current_path = []
        self.path_index = 0
        self.draw_grid()
        self.draw_graph_preview()
        self.info_label.config(text="Click a free cell to place the car (start).")

    # ---------- Drawing grid ----------
    def draw_grid(self):
        self.grid_canvas.delete("all")
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x1 = j * CELL_SIZE
                y1 = i * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                fill = OCCUPIED_COLOR if self.lot.spots[i][j] == 1 else FREE_COLOR
                self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#222")

        # draw path cells (if any)
        for idx, node in enumerate(self.current_path):
            # keep the path visible until a new target selected
            self._fill_cell(node, PATH_COLOR)

        # draw car
        if self.current_pos:
            self._draw_car(self.current_pos)

    def _fill_cell(self, node, color):
        i, j = node
        x1 = j * CELL_SIZE + 2
        y1 = i * CELL_SIZE + 2
        x2 = x1 + CELL_SIZE - 4
        y2 = y1 + CELL_SIZE - 4
        self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#111")

    def _draw_car(self, node):
        i, j = node
        cx = j * CELL_SIZE + CELL_SIZE / 2
        cy = i * CELL_SIZE + CELL_SIZE / 2
        r = CELL_SIZE / 3.5
        self.grid_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=CAR_COLOR, outline="white", width=2)

    # ---------- Graph preview ----------
    def draw_graph_preview(self, highlight_edge=None, highlight_node=None):
        """Draw small graph preview. Optionally highlight an edge (tuple of two nodes) or a node."""
        canvas = self.graph_preview
        canvas.delete("all")
        margin = 30
        w = int(canvas['width'])
        h = int(canvas['height'])
        spacing_x = (w - 2 * margin) / (GRID_SIZE - 1) if GRID_SIZE > 1 else 0
        spacing_y = (h - 2 * margin) / (GRID_SIZE - 1) if GRID_SIZE > 1 else 0

        # positions
        self.node_pos = {}
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.lot.spots[i][j] == 0:
                    x = margin + j * spacing_x
                    y = margin + i * spacing_y
                    self.node_pos[(i, j)] = (x, y)

        # draw edges
        for node, neighbors in self.lot.graph.items():
            if node not in self.node_pos:
                continue
            x, y = self.node_pos[node]
            for nb in neighbors:
                if nb not in self.node_pos:
                    continue
                nx, ny = self.node_pos[nb]
                # highlight if this is the current traversal edge
                if highlight_edge and (node, nb) == highlight_edge:
                    canvas.create_line(x, y, nx, ny, fill=HIGHLIGHT_EDGE_COLOR, width=4)
                else:
                    canvas.create_line(x, y, nx, ny, fill=GRAPH_EDGE_COLOR, width=1)

        # draw nodes
        for node, (x, y) in self.node_pos.items():
            color = GRAPH_NODE_COLOR
            canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=color, outline="#333")

        # draw path nodes in path color
        for node in self.current_path:
            if node in self.node_pos:
                x, y = self.node_pos[node]
                canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=PATH_COLOR, outline="#333")

        # draw the car as a larger dot
        if self.current_pos and self.current_pos in self.node_pos:
            cx, cy = self.node_pos[self.current_pos]
            canvas.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill=CAR_COLOR, outline="white", width=2)

        # optionally highlight a node
        if highlight_node and highlight_node in self.node_pos:
            x, y = self.node_pos[highlight_node]
            canvas.create_oval(x - 12, y - 12, x + 12, y + 12, outline="orange", width=3)

    # ---------- Full graph window ----------
    def show_graph_window(self):
        win = tk.Toplevel(self.root)
        win.title("Graph Visualization")
        canvas = tk.Canvas(win, width=480, height=480, bg="white")
        canvas.pack(padx=10, pady=10)
        margin = 40
        w = 480 - 2 * margin
        h = 480 - 2 * margin
        spacing_x = w / (GRID_SIZE - 1) if GRID_SIZE > 1 else 0
        spacing_y = h / (GRID_SIZE - 1) if GRID_SIZE > 1 else 0
        positions = {}
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.lot.spots[i][j] == 0:
                    x = margin + j * spacing_x
                    y = margin + i * spacing_y
                    positions[(i, j)] = (x, y)

        # draw edges
        for node, neighbors in self.lot.graph.items():
            if node not in positions:
                continue
            x, y = positions[node]
            for nb in neighbors:
                if nb not in positions:
                    continue
                nx, ny = positions[nb]
                canvas.create_line(x, y, nx, ny, fill=GRAPH_EDGE_COLOR)

        # nodes
        for node, (x, y) in positions.items():
            canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=GRAPH_NODE_COLOR, outline="#333")

        # car
        if self.current_pos and self.current_pos in positions:
            cx, cy = positions[self.current_pos]
            canvas.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill=CAR_COLOR, outline="white", width=2)

        # animate path on graph if there is a current_path
        if self.current_path:
            for idx, node in enumerate(self.current_path):
                def make_highlight(n=node):
                    if n in positions:
                        x, y = positions[n]
                        canvas.create_oval(x - 14, y - 14, x + 14, y + 14, outline="orange", width=3)
                win.after(200 * idx, make_highlight)

    # ---------- Click handling ----------
    def on_grid_click(self, event):
        if self.animating:
            return  # ignore clicks while animation runs

        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            return

        if self.lot.spots[row][col] == 1:
            messagebox.showwarning("Occupied", "This spot is occupied. Choose another.")
            return

        if self.current_pos is None:
            self.current_pos = (row, col)
            self.info_label.config(text="Select destination (click another free cell).")
            self.draw_grid()
            self.draw_graph_preview()
            return

        # set destination and start moving (start from current_pos)
        self.destination = (row, col)
        if self.use_bfs:
            path = self.lot.bfs_path(self.current_pos, self.destination)
        else:
            path = self.lot.a_star_path(self.current_pos, self.destination)
        if not path:
            messagebox.showinfo("No path", "No route available to the selected destination.")
            self.destination = None
            return

        # keep path visible until user picks next destination later
        self.current_path = path[:]  # copy
        self.path_index = 0
        self.animating = True
        self.info_label.config(text=f"Moving: {self.current_pos} → {self.destination}")
        self._animate_step()

    # ---------- Animation step (non-blocking) ----------
    def _animate_step(self):
        """Advance animation by one step and schedule next."""
        if not self.animating:
            return

        if self.path_index >= len(self.current_path):
            # finished
            self.animating = False
            self.current_pos = self.current_path[-1] if self.current_path else self.current_pos
            self.info_label.config(text=f"Reached {self.current_pos}. Click a new destination to move again.")
            self.draw_grid()
            self.draw_graph_preview()
            return

        # current traversal node
        node = self.current_path[self.path_index]
        # update car position visually as moving step-by-step
        self.current_pos = node
        # highlight edges on graph: from previous node to current node
        highlight_edge = None
        if self.path_index > 0:
            prev = self.current_path[self.path_index - 1]
            highlight_edge = (prev, node)

        # redraw grid and graph preview with highlights
        self.draw_grid()
        self.draw_graph_preview(highlight_edge=highlight_edge, highlight_node=node)

        # increment and schedule next
        self.path_index += 1
        self.root.after(ANIMATION_DELAY_MS, self._animate_step)


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartParkingFinder(root)
    root.mainloop()
