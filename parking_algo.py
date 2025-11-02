# parking_algo.py
import random
import heapq
from collections import deque

class ParkingLot:
    def __init__(self, size=6):
        self.size = size
        self.spots = [[0 for _ in range(size)] for _ in range(size)]
        self.randomize_occupied()
        self.graph = self.build_graph()

    def randomize_occupied(self):
        """Randomly occupy about 25% of spots"""
        for i in range(self.size):
            for j in range(self.size):
                self.spots[i][j] = random.choice([0, 0, 0, 1])  # 1 = occupied
        self.graph = self.build_graph()

    def build_graph(self):
        """Build adjacency list for all free nodes"""
        graph = {}
        for i in range(self.size):
            for j in range(self.size):
                if self.spots[i][j] == 0:
                    neighbors = []
                    if i > 0 and self.spots[i - 1][j] == 0:
                        neighbors.append((i - 1, j))
                    if i < self.size - 1 and self.spots[i + 1][j] == 0:
                        neighbors.append((i + 1, j))
                    if j > 0 and self.spots[i][j - 1] == 0:
                        neighbors.append((i, j - 1))
                    if j < self.size - 1 and self.spots[i][j + 1] == 0:
                        neighbors.append((i, j + 1))
                    graph[(i, j)] = neighbors
        return graph

    # ==========================
    # BFS (Shortest Path)
    # ==========================
    def bfs_path(self, start, goal):
        if start not in self.graph or goal not in self.graph:
            return None
        queue = deque([(start, [start])])
        visited = set([start])
        while queue:
            node, path = queue.popleft()
            if node == goal:
                return path
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    # ==========================
    # A* Search
    # ==========================
    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan distance

    def a_star_path(self, start, goal):
        if start not in self.graph or goal not in self.graph:
            return None

        pq = []
        heapq.heappush(pq, (0, start, [start]))
        g_cost = {start: 0}
        visited = set()

        while pq:
            f, node, path = heapq.heappop(pq)
            if node == goal:
                return path
            if node in visited:
                continue
            visited.add(node)

            for neighbor in self.graph.get(node, []):
                tentative_g = g_cost[node] + 1
                if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g
                    f = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(pq, (f, neighbor, path + [neighbor]))
        return None
