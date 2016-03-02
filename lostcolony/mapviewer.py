from collections import defaultdict
import os
from glob import iglob

import pyglet
from pyglet import gl
from pyglet.window import key

from lostcolony.pathfinding import (
    HexGrid, HEX_WIDTH, HEX_HEIGHT
)
from lostcolony.tile_outline import TileOutline
from lostcolony.ui import UI
from lostcolony.world import World
from lostcolony.maploader import Map


class Camera:
    WSCALE = HEX_WIDTH / 2
    HSCALE = HEX_HEIGHT / 2

    def __init__(self, viewport, pos=(0, 0)):
        self.viewport = viewport
        self.pos = pos

    def pan(self, dx, dy):
        """Move the camera by a relative offset."""
        x, y = self.pos
        self.pos = x - dx, y + dy

    def coord_to_viewport(self, coord):
        """Given a tile coordinate, get its viewport position."""
        cx, cy = self.pos
        wx, wy = HexGrid.coord_to_world(coord)
        sx, sy = HexGrid.coord_to_screen(coord)
        return (
            sx - cx,
            self.viewport[1] - sy + cy
        )

    def viewport_to_world(self, coord):
        """Get the world coordinate for a viewport coordinate."""
        x, y = coord
        cx, cy = self.pos
        wx = (x + cx) / self.WSCALE
        wy = (self.viewport[1] - y + cy) / self.HSCALE
        return wx, wy

    def viewport_to_coord(self, coord):
        """Given a viewport coordinate, get the tile coordinate."""
        return HexGrid.world_to_coord(self.viewport_to_world(coord))

#    def viewport_to_world(self, coord):
#        """Get the world coordinate of the tile for a viewport coordinate."""
#        return HexGrid.coord_to_world(self.viewport_to_coord(coord))

    def viewport_bounds(self):
        """Return the p1, p2 bounds of the viewport in screen space."""
        x, y = self.pos
        w, h = self.viewport
        return self.pos, (x + w, y + h)

    def coord_bounds(self):
        """Return the x1, y1, x2, y2 bounds of the viewport in map coords."""
        return self.viewport_to_coord((0, 0)), self.viewport_to_coord(self.viewport)

    def world_bounds(self):
        """Return the x1, y1, x2, y2 bounds of the viewport in world coords."""
        return self.viewport_to_world((0, 0)), self.viewport_to_world(self.viewport)


class Scene:
    def __init__(self, window, map):
        self.camera = Camera((window.width, window.height), pos=(0, 0))
        self.cursor = TileOutline((255, 0, 0))
        self.window = window
        self.images = {}
        self.mouse_coords = (0, 0)

        self.floor = map.floor
        self.objects = map.objects
        self.grid = map.grid
        self.world = World(self.grid)

    def draw(self):
        """Draw the floor and any decals."""
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glAlphaFunc(gl.GL_GREATER, 0.0)
        (cx1, cy1), (cx2, cy2) = self.camera.coord_bounds()
        for y in range(cy2 - 1, cy1 + 4):
            for x in range(cx1 - 1, cx2 + 3):
                imgs = self.floor.get((x, y))
                if imgs:
                    sx, sy = self.camera.coord_to_viewport((x, y))
                    for img in imgs:
                        img.blit(sx, sy, 0)
        self.cursor.draw()

    def get_drawables(self):
        """Get a list of drawable objects.

        These objects need to be depth-sorted along with any game objects
        within the camera bounds, and drawn using painter's algorithm,

        TODO: Refactor this all into a scenegraph class that can manage both
        static graphics and game objects.

        """
        (cx1, cy1), (cx2, cy2) = self.camera.coord_bounds()
        objects = []
        for y in range(cy2 - 1, cy1 + 4):
            for x in range(cx1 - 1, cx2 + 3):
                obj = self.objects.get((x, y))
                if obj is not None:
                    sx, sy = self.camera.coord_to_viewport((x, y))
                    objects.append((sy, sx, obj))

                for actor in self.world.get_actors((x, y)):
                    sx, sy = self.camera.coord_to_viewport((x, y))
                    sx, sy, pic = actor.drawable(sx, sy)
                    objects.append((round(sy), round(sx), pic))
        return objects

    def hover(self, x, y):
        """Set the position of the mouse cursor."""
        self.mouse_coords = x, y
        self.update_cursor()

    def update_cursor(self):
        """Recalculate the cursor position from the mouse coords."""
        c = self.camera.viewport_to_coord(self.mouse_coords)
        self.cursor.pos = self.camera.coord_to_viewport(c)


window = pyglet.window.Window(resizable=True)
keys = key.KeyStateHandler()
window.push_handlers(keys)

game_map = Map("maps/encounter-01.tmx")
tmxmap = Scene(window, game_map)
ui = UI(tmxmap.world, tmxmap.camera)


@window.event
def on_draw():
    window.clear()
    tmxmap.draw()
    ui.draw()

    drawables = tmxmap.get_drawables()
    drawables.sort(reverse=True, key=lambda t: (t[0], t[1]))
    for y, x, img in drawables:
        img.blit(x, y, 0)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if pyglet.window.mouse.LEFT:
        # Drag screen
        tmxmap.camera.pan(dx, dy)
        tmxmap.hover(x, y)
    elif pyglet.window.mouse.RIGHT:
        # Select by area
        pass


@window.event
def on_mouse_motion(x, y, dx, dy):
    tmxmap.hover(x, y)
    mx, my = 0, 0
    if x < window.width * 0.05:
        mx = -1
    elif x > window.width * 0.95:
        mx = 1

    if y < window.height * 0.05:
        my = 1
    elif y > window.height * 0.95:
        my = -1

    tmxmap.camera_vector = mx, my


@window.event
def on_mouse_release(x, y, button, mods):
    """
    Placeholder for a click event.

    Currently tells the UI to send a guy walking

    :param x: x position
    :param y: y position
    """
    if pyglet.window.mouse.LEFT == button:
        ui.go((x, y))


@window.event
def on_resize(*args):
    tmxmap.camera.viewport = window.width, window.height


def on_key_press(symbol, mods):
    if symbol == pyglet.window.key._1:
        ui.select_by_name("rex")
    if symbol == pyglet.window.key._2:
        ui.select_by_name("max")
    if symbol == pyglet.window.key._3:
        ui.select_by_name("ping")
    if symbol == pyglet.window.key._4:
        ui.select_by_name("tom")
    if symbol == pyglet.window.key.TAB:
        ui.select_next_hero()
# Using push_handlers to avoid breaking the other handler
window.push_handlers(on_key_press)

def update(_, dt):

    tmxmap.world.update(dt)

    if keys[key.W]:
        tmxmap.camera.pan(0, -20)
        tmxmap.update_cursor()
    if keys[key.S]:
        tmxmap.camera.pan(0, 20)
        tmxmap.update_cursor()
    if keys[key.A]:
        tmxmap.camera.pan(20, 0)
        tmxmap.update_cursor()
    if keys[key.D]:
        tmxmap.camera.pan(-20, 0)
        tmxmap.update_cursor()
# to be deleted:
#    ox, oy = tmxmap.camera
#    dx, dy = tmxmap.camera_vector
#
#    nx = ox + dx * dt * 500
#    ny = oy + dy * dt * 500
#
#    tmxmap.camera = nx, ny

pyglet.clock.schedule(update, 1/60)
