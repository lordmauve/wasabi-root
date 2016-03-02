from collections import defaultdict
from lostcolony.actor import Character, Actor
from lostcolony import animation
from lostcolony.faction import Faction
from itertools import chain
from lostcolony.weapon import Rifle
import time


class World:
    """
    Top-level container for the map, factions, actors etc
    """

    def __init__(self, grid):
        # TODO: un-hardcode this. can we set this in tiled?
        self.grid = grid
        self.actors_by_pos = defaultdict(set)
        self.grid.layers.insert(0, self.actors_by_pos)

        self.factions = [self.init_player()]  # first faction is the player
        self.factions += self.init_npcs()

    def init_player(self):
        # Stub code - this should come from scenario set-up
        faction = Faction("Player")

        rex = Character(self, animation.rex, faction=faction, position = (5,5), facing=4, colour = (255,215,0))
        rex.weapon = Rifle(rex)

        rex2 = Character(self, animation.rex, faction=faction, position = (6,5), facing=0, colour = (128,215,0))
        rex2.weapon = Rifle(rex)

        Actor(self, animation.raptor, faction=faction, position = (7,5), facing=3, colour = (20,20,20)) # pet dino

        return faction

    def init_npcs(self):
        # to do: get from scenario set-up
        targets = Faction("Targets for weapon testing")
        victim = Actor(self, animation.raptor, position=(8,8), faction=targets, facing=3)
        return [targets]

    @property
    def actors(self):
        return chain.from_iterable(faction.actors for faction in self.factions)

    def field_of_fire_colours(self):
        return (
            (actor, actor.colour,)
            for actor in self.factions[0].actors
            if isinstance(actor, Character)
        )

    def drawables(self):
        return self.actors

    def get_actors(self, hex):
        """Get a list of actors "in" the given tile."""
        return self.actors_by_pos.get(hex) or []

    def get_characters(self):
        return (
            actor
            for actor in self.factions[0].actors
            if isinstance(actor, Character)
        )

    def update(self, dt):
        t = time.time()
        for a in self.actors:
            a.update(t, dt)
