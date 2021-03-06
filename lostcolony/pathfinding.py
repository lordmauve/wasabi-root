import heapq
import math
from math import sqrt
from collections import ChainMap, defaultdict


def cube_round(h):
    """Round cubic hexagonal coordinates to an integer cubic tile."""
    x, y, z = h
    rx = round(x)
    ry = round(y)
    rz = round(z)

    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)

    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry

    return rx, ry, rz


def cube_to_hex(h):
    """Convert a 3-tuple of cubic coords to 2 "even-q vertical" coords."""
    x, _, z = h
    return x, z + (x + (int(x) % 2)) // 2


def hex_to_cube(h):
    """Convert a 2-tuple of "even-q vertical" coords to cubic coords."""
    x, row = h

    z = row - ((x + (x & 1)) >> 1)
    return (
        x,
        -x - z,
        z
    )


def hex_round(h):
    return cube_to_hex(cube_round(hex_to_cube(h)))


root3 = 3 ** 0.5

# The calculated dimensions of a tile in pixels.
#
# They aren't round numbers due to the way we have to align tile graphics to
# pixel boundaries. See the implementation of coord_to_screen for the integer
# version; it is from those numbers that these are derived.
#
# These need to be exact or the errors add up!!!
HEX_WIDTH = 95 * 4 / 3
HEX_HEIGHT = root3 * 0.25 * 128


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]

# TODO: This doesn't calculate a correct distance. (0,0) to (1,1) should be adjacent.
# See HexGrid.distance


def heuristic(a, b):
    """Get the distance between points a and b."""
    (x1, y1) = a
    (x2, y2) = b
    dx = x1 - x2
    dy = y1 - y2
    return sqrt(dx * dx + dy * dy)


class NoPath(Exception):
    """There is no route to the goal."""



class HexGrid:
    def __init__(self):
        self.cells = {} # hex coord : val ; bit 0 blocks sight, bit 1 blocks movement so 3 == 1 | 2 which blocks both
        self.layers = []

#    def __setitem__(self, coords, value):
#        self.cells[coords] = value

    def blocks_sight(self, coord):
        return self.cells.get(coord, 1) & 1

    def blocks_movement(self, coord):
        """Return True if the given coordinates are blocked."""
        return any(layer.get(coord) for layer in self.layers) or self.cells.get(coord, 2) & 2

    """ depreciated
    def blocked(self, coords):
        return any(layer.get(coords) for layer in self.layers) or self.cells.get(coords, True)
    """

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

    @staticmethod
    def coord_to_world(coord):
        """Convert a map coordinate to a Cartesian world coordinate."""
        cx, cy = coord
        wx = 1.5 * cx
        wy = root3 * (cy - 0.5 * (cx & 1))
        return wx, wy

    @staticmethod
    def coord_to_screen(coord):
        """Convert a map coordinate to screenspace coordinates."""
        cx, cy = coord
        return (
            cx * 95,
            (2 * cy - (cx & 1)) * 24
        )

    @staticmethod
    def world_to_coord(coord):
        """Get the map coordinates for a screenspace pixel (x, y)."""
        x, y = coord
        q = x / 1.5
        r = -x / 3 + root3 / 3 * y
        return cube_to_hex(cube_round((q, -q - r, r)))

    @classmethod
    def neighbours(cls, coords):
        """Iterate over the neighbour of the given coords.

        Note that we use an "even-q vertical" layout in the terminology of
        http://www.redblobgames.com/grids/hexagons/#coordinates

        """
        x, y = coords
        neighbours = cls.NEIGHBOURS_ODD if x % 2 else cls.NEIGHBOURS_EVEN
        for dx, dy in neighbours:
            yield x + dx, y + dy

    def unblocked_neighbours(self, coords):
        """Adjacent cells that are not blocked."""
        return (c for c in self.neighbours(coords) if not self.blocks_movement(c))

    def hex_in_front(self, coords, facing):
        """
        Adjacent hex in the facing direction. May be off-map.

        :param coords:
        :param facing:
        :return: Tuple: empty if the front hex is off-map
        """
        x, y = coords
        neighbours = HexGrid.NEIGHBOURS_ODD if x % 2 else HexGrid.NEIGHBOURS_EVEN
        dx, dy = neighbours[facing]
        ret = x + dx, y + dy,
        return ret

    @staticmethod
    def distance(a, b):
        """Calculate the distance between two pairs of coordinates."""
        ax, ay = HexGrid.coord_to_world(a)
        bx, by = HexGrid.coord_to_world(b)
        dx = ax - bx
        dy = ay - by
        return math.sqrt(dx * dx + dy * dy)

    def find_path(self, start, goal):
        """Find a path from start to goal using A*.

        This can be quite expensive if goal is unreachable.

        """
        if self.blocks_movement(goal):
            raise NoPath(start, goal)
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

            for next in self.unblocked_neighbours(current):
                new_cost = cost_so_far[current] + self.distance(current, next)
                if (next not in cost_so_far or new_cost < cost_so_far[next]):
                    cost_so_far[next] = new_cost
                    priority = new_cost + heuristic(goal, next)
                    frontier.put(next, priority)
                    came_from[next] = current
        else:
            raise NoPath(start, goal)

        path = [goal]
        while current != start:
            current = came_from[current]
            path.append(current)
        return path

    @staticmethod
    def distance(start, target):
        sx, sy, sz = hex_to_cube(start)
        tx, ty, tz = hex_to_cube(target)
        return max(abs(sx-tx), abs(sy-ty), abs(sz-tz))

    def reachable(self, tile, dist=20):
        """Get the set of tiles that are reachable in at most dist steps.

        This is a variation of Dijkstra's Algorithm. Note that this step does
        not consider object layers, only the base grid.

        """
        seen = {tile,}
        found = {tile,}
        costs = {tile: 0}
        frontier = PriorityQueue()
        frontier.put(tile, 0)

        x, y = self.coord_to_world(tile)
        while not frontier.empty():
            t = frontier.get()
            cost = costs[t]
            if cost <= dist:
                found.add(t)
            for t in self.neighbours(t):
                if self.blocks_movement(t):
                    continue
                newcost = cost + 1
                if t in costs:
                    oldcost = costs[t]
                    if newcost < oldcost:
                        costs[t] = newcost
                else:
                    costs[t] = newcost

                if t not in seen and newcost <= dist:
                    seen.add(t)
                    frontier.put(t, newcost)
        return found

    def obstacles_in_line_of_sight(self, start, target):
        """
        Can you see the target from the starting position?

        The first blocking terrain type is considered visible: you can see ito
        the bush, but not through it.  This is used for line-of-sight attacks,
        e.g. you can throw a grenade over some things you can't shoot through

        :param start: Observer coordinates
        :param target: Target coordinates
        :return: set of obstacle coordinates (empty if full line of sight)
        """
        if start == target:
            # Simplest case, avoids division by 0 in the code below
            return set()
        c_start = self.coord_to_world(start)
        c_target = self.coord_to_world(target)
        # Delta
        delta = (c_target[0] - c_start[0], c_target[1] - c_start[1])
        d_len = (delta[0] ** 2 + delta[1] ** 2) ** 0.5
        # Normalize to unit
        d_1 = (delta[0] / d_len, delta[1] / d_len)
        # Look for obstacles
        obstacles = set()
        for i in range(1, int(math.ceil(d_len))):
            checked = (c_start[0] + d_1[0] * i, c_start[1] + d_1[1] * i,)
            for fuzzy_x, fuzzy_y in (-1e-6, -1e-6), (-1e-6, 1e-6), (1e-6, -1e-6), (1e-6, 1e-6):
                checked_coord = self.world_to_coord((checked[0] + fuzzy_x, checked[1] + fuzzy_y))
                if checked_coord != start and self.blocks_sight(checked_coord):
                    obstacles.add(checked_coord)
        return obstacles

    def visible(self, start, target):
        if target not in self.cells:
            return False # off-map

        obstacles = self.obstacles_in_line_of_sight(start, target)
        if obstacles and obstacles != {target}:
            return False

        return True

def test_hex_grid_distance():
    assert HexGrid.distance( (0,0), (1,1) ) == 1
    assert HexGrid.distance( (1,1), (0,0) ) == 1
    assert HexGrid.distance( (0,5), (7,0) ) == 9

