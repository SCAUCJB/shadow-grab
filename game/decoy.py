"""
假信号道具：
- 拾取后按键释放，在当前位置生成一个"幽灵"
- 幽灵以随机方向移动，留下与玩家相同颜色的假痕迹
- 持续 6 秒后消失
"""
from __future__ import annotations
from game import fonts
import math, random
import pygame
from game.config import TILE, COLS, ROWS, PLAYER_SPEED

DECOY_ITEM_RADIUS = 8
DECOY_DURATION    = 360   # 帧（6s）
GHOST_SPEED       = PLAYER_SPEED * 0.8
TURN_INTERVAL     = 40    # 每隔多少帧随机转向


class DecoyItem:
    """可拾取的假信号发生器"""
    def __init__(self, col, row):
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.alive = True
        self._t = 0

    def update(self):
        self._t += 1

    def check_pickup(self, player) -> bool:
        if not self.alive or player.decoy_count >= 1:
            return False
        if math.hypot(player.x - self.x, player.y - self.y) < DECOY_ITEM_RADIUS + 14:
            self.alive = False
            player.decoy_count += 1
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return
        bob = math.sin(self._t * 0.09) * 2
        cx, cy = int(self.x), int(self.y + bob)
        # 菱形
        pts = [(cx, cy - DECOY_ITEM_RADIUS),
               (cx + DECOY_ITEM_RADIUS, cy),
               (cx, cy + DECOY_ITEM_RADIUS),
               (cx - DECOY_ITEM_RADIUS, cy)]
        pygame.draw.polygon(surface, (180, 120, 220), pts)
        pygame.draw.polygon(surface, (220, 180, 255), pts, 2)
        font = fonts.get(14)
        t = font.render("诱", True, (40, 20, 60))
        surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))


class Ghost:
    """玩家释放的假信号幽灵"""
    def __init__(self, x: float, y: float, trail_color, grid):
        self.x = float(x)
        self.y = float(y)
        self.trail_color = trail_color
        self.grid = grid
        self.timer = DECOY_DURATION
        self._angle = random.uniform(0, math.tau)
        self._turn_t = 0
        self.trail: list[list] = []   # [px, py, alpha]

    @property
    def alive(self):
        return self.timer > 0

    def update(self):
        self.timer -= 1
        self._turn_t += 1
        if self._turn_t >= TURN_INTERVAL:
            self._turn_t = 0
            self._angle += random.uniform(-math.pi / 2, math.pi / 2)

        dx = math.cos(self._angle) * GHOST_SPEED
        dy = math.sin(self._angle) * GHOST_SPEED

        # 简单碰墙反弹
        nx, ny = self.x + dx, self.y + dy
        col = int(nx // TILE)
        row = int(ny // TILE)
        if 0 <= row < ROWS and 0 <= col < COLS and self.grid[row][col] == 0:
            self.x, self.y = nx, ny
        else:
            self._angle += math.pi + random.uniform(-0.5, 0.5)

        # 留痕
        self.trail.append([self.x, self.y, 180])
        if len(self.trail) > 60:
            self.trail.pop(0)
        for t in self.trail:
            t[2] -= 3
        self.trail = [t for t in self.trail if t[2] > 0]

    def draw(self, surface):
        # 痕迹（与玩家相同颜色，视觉上以假乱真）
        for tx, ty, alpha in self.trail:
            s = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.trail_color, int(alpha)), (4, 4), 3)
            surface.blit(s, (tx - 4, ty - 4))
        # 幽灵本体（极淡，几乎不可见）
        fade = int(60 * (self.timer / DECOY_DURATION))
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.trail_color, fade), (8, 8), 6)
        surface.blit(s, (int(self.x) - 8, int(self.y) - 8))
