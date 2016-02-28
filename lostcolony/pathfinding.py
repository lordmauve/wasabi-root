import heapq
import math


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


def heuristic(a, b):
    """Get the distance between points a and b."""
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)


class Grid:
    def __init__(self):
        self.cells = {}

    def __setitem__(self, coords, value):
        self.cells[coords] = value

    def __getitem__(self, coords):
        return self.cells.get(coords)

    def __contains__(self, coords):
        return bool(self.cells.get(coords))

    NEIGHBOURS_EVEN = [
        (0, -1),
        (1, 0),
        (1, 1),
        (0, 1),
        (-1, 1),
        (-1, 0),
    ]
    NEIGHBOURS_ODD = [
        (0, -1),
        (1, -1),
        (1, 0),
        (0, 1),
        (-1, 0),
        (-1, -1)
    ]

    def coord_to_world(self, coord):
        """Convert a map coordinate to a cartesian world coordinate."""
        cx, cy = coord
        wx = 3/2 * cx
        wy = 3 ** 0.5 * (cy - 0.5 * (cx & 1))
        return wx, wy

    def neighbours(self, coords):
        """Iterate over the neigbours of the given coords.

        Note that we use an "even-q vertical" layout in the terminology of
        http://www.redblobgames.com/grids/hexagons/#coordinates

        """
        x, y = coords
        neighbours = self.NEIGHBOURS_ODD if x % 2 else self.NEIGHBOURS_ODD
        for dx, dy in neighbours:
            c = x + dx, y + dy
            if c in self:
                yield c

    def cost(self, a, b):
        """Calculate the distance between two pairs of coordinates."""
        wa = self.coord_to_world(a)
        wb = self.coord_to_world(b)
        return math.sqrt(wa * wa + wb * wb)

    def find_path(self, start, goal):
        """Find a path from start to goal using A*.

        This can be quite expensive if goal is unreachable.

        """
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while not frontier.empty():
            current = frontier.get()

            if current == goal:
                break

            for next in self.neighbors(current):
                new_cost = cost_so_far[current] + self.distance(current, next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + heuristic(goal, next)
                    frontier.put(next, priority)
                    came_from[next] = current

        return came_from, cost_so_far
