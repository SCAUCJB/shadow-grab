from __future__ import annotations
import math
import pygame
from game.config import TILE, BASE_RADIUS
from game import sprites


class Base:
    def __init__(self, col: int, row: int, pid: int, color=None):
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.pid = pid
        self.color = color or ((40, 140, 200) if pid == 1 else (200, 70, 50))
        self._t = 0

    def update(self):
        self._t += 1

    def check_deposit(self, player) -> bool:
        if player.pid != self.pid or not player.carrying:
            return False
        if math.hypot(player.x - self.x, player.y - self.y) < BASE_RADIUS + 12:
            player.carrying = False
            player.score += 1
            return True
        return False

    def draw(self, surface):
        sprites.draw_base(surface, self.x, self.y, self.color, self.pid, self._t)
