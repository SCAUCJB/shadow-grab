from __future__ import annotations
import math
import pygame
from game.config import TILE, RESOURCE_RADIUS
from game import sprites


class Resource:
    def __init__(self, col: int, row: int, color=(255, 215, 50)):
        self.col = col
        self.row = row
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.color = color
        self.alive = True
        self._t = 0

    def update(self):
        self._t += 1

    def draw(self, surface):
        if not self.alive:
            return
        sprites.draw_resource(surface, self.x, self.y, self.color, self._t)

    def check_pickup(self, player) -> bool:
        if not self.alive or player.carrying:
            return False
        if math.hypot(player.x - self.x, player.y - self.y) < RESOURCE_RADIUS + 12:
            self.alive = False
            player.carrying = True
            return True
        return False
