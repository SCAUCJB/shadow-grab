from __future__ import annotations
import pygame
from game.config import TILE, PLAYER_SPEED, PLAYER_RADIUS, TRAIL_MAX_LEN, TRAIL_FADE_PER, COLS, ROWS
from game import sprites
from game.buff import apply_speed, is_stealthed


class Player:
    def __init__(self, pid: int, start_px: float, start_py: float,
                 color, trail_color, keys: dict):
        self.pid = pid
        self.x = float(start_px)
        self.y = float(start_py)
        self.color = color
        self.trail_color = trail_color
        self.keys = keys

        self.score = 0
        self.carrying = False
        self.smoke_count   = 0
        self.decoy_count   = 0
        self.barrier_count = 0
        self.is_ai = False
        self.buffs: list = []   # list[BuffEffect]
        self.lives = 3
        self.invincible_timer = 0

        self.trail: list[list] = []
        self.moving = False
        self.expose_timer = 0
        self.in_smoke = False
        self._frame = 0
        # AI 信号标志
        self._ai_use_smoke   = False
        self._ai_use_decoy   = False
        self._ai_use_barrier = False

    # ── AI 移动入口 ───────────────────────────────────────
    def ai_update(self, dx: float, dy: float, grid, barriers=None):
        self._apply_move(dx, dy, grid, barriers)

    # ── 玩家键盘移动 ──────────────────────────────────────
    def update(self, keys_pressed, grid, barriers=None):
        dx = dy = 0
        if keys_pressed[self.keys['up']]:    dy = -PLAYER_SPEED
        if keys_pressed[self.keys['down']]:  dy =  PLAYER_SPEED
        if keys_pressed[self.keys['left']]:  dx = -PLAYER_SPEED
        if keys_pressed[self.keys['right']]: dx =  PLAYER_SPEED

        if dx and dy:
            dx *= 0.707; dy *= 0.707

        self._apply_move(dx, dy, grid, barriers)

    def _apply_move(self, dx: float, dy: float, grid, barriers=None):
        # 加速增益
        speed_mul = apply_speed(self)
        dx *= speed_mul
        dy *= speed_mul

        # 增益计时
        for b in self.buffs:
            b.update()
        self.buffs = [b for b in self.buffs if b.alive]

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.moving = bool(dx or dy)
        self._frame += 1

        if self.moving:
            self.trail.append([self.x, self.y, 200])
            if len(self.trail) > TRAIL_MAX_LEN:
                self.trail.pop(0)
            self.expose_timer = 10
        else:
            self.expose_timer = max(0, self.expose_timer - 1)

        for t in self.trail:
            t[2] -= TRAIL_FADE_PER
        self.trail = [t for t in self.trail if t[2] > 0]

        nx, ny = self.x + dx, self.y + dy
        if not self._collides(nx, self.y, grid, barriers):
            self.x = nx
        if not self._collides(self.x, ny, grid, barriers):
            self.y = ny

    def _collides(self, px, py, grid, barriers=None) -> bool:
        r = PLAYER_RADIUS - 2
        for cx, cy in [(px-r, py-r), (px+r, py-r), (px-r, py+r), (px+r, py+r)]:
            col = int(cx // TILE)
            row = int(cy // TILE)
            if col < 0 or col >= COLS or row < 0 or row >= ROWS:
                return True
            if grid[row][col] == 1:
                return True
            # 检测放置的障碍物
            if barriers:
                for b in barriers:
                    if b.alive and b.col == col and b.row == row:
                        return True
        return False

    @property
    def visible(self):
        if self.in_smoke or is_stealthed(self):
            return False
        return self.moving or self.expose_timer > 0

    def tile_pos(self):
        return int(self.x // TILE), int(self.y // TILE)

    def draw(self, surface):
        # 隐身增益：不显示痕迹
        if not is_stealthed(self):
            for tx, ty, alpha in self.trail:
                s = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.trail_color, int(alpha)), (4, 4), 3)
                surface.blit(s, (tx - 4, ty - 4))

        sprites.draw_player(surface, int(self.x), int(self.y),
                            self.color, self.carrying,
                            self.visible, self._frame)

        if self.invincible_timer > 0 and (self.invincible_timer // 6) % 2 == 0:
            s = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 120), (14, 14), 13, 3)
            surface.blit(s, (int(self.x) - 14, int(self.y) - 14))

        # 增益指示条（头顶）
        for i, buff in enumerate(self.buffs):
            buff.draw_indicator(surface, int(self.x), int(self.y), i)
