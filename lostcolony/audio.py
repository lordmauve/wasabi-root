import os

import pygame  # We use pygame for audio, pyglet has some issues

effects = {}


def init():
    pygame.init()
    normal_music()
    for fx in "sniper rifle_burst shotgun autocannon forest_walk".split():
        effects[fx] = pygame.mixer.Sound(os.path.join("sounds", "%s.wav" % fx))
    effects["forest_walk"].set_volume(0.2)


def start_walk(effect_name):
    if effect_name is None:
        return None
    ch = effects[effect_name].play(loops=-1)
    return ch


def stop_walk(walk_id):
    if walk_id is not None:
        walk_id.fadeout(100)


def normal_music():
    pygame.mixer.music.load(os.path.join("music", "Swamplandia.ogg"))
    pygame.mixer.music.play(loops=-1)
    pygame.mixer.music.set_volume(0.5)


def action_music():
    pygame.mixer.music.load(os.path.join("music", "Swamplandia.ogg"))
    pygame.mixer.music.play(loops=-1)
    pygame.mixer.music.set_volume(0.5)


def quit():
    pygame.quit()