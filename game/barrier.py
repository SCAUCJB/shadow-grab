"""
障碍物道具系统

BarrierItem  — 地图上可拾取的道具（橙色砖块图标）
PlacedBarrier — 玩家放置后生效的临时障碍，占据 1 个格子，阻断所有人通行
"""
from __future__ import annotations
from game import fonts
import math
import pygame
from game.config import TILE, COLS, ROWS

BARRIER_ITEM_RADIUS = 8
BARRIER_DURATION    = 480   # 帧（8 秒 @ 60fps）
MAX_PLACED          = 2     # 每位玩家同时最多放置数量


class BarrierItem:
    """可拾取的障碍物道具"""

    def __init__(self, col: int, row: int):
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.alive = True
        self._t = 0

    def update(self):
        self._t += 1

    def check_pickup(self, player) -> bool:
        if not self.alive or player.barrier_count >= 1:
            return False
        if math.hypot(player.x - self.x, player.y - self.y) < BARRIER_ITEM_RADIUS + 14:
            self.alive = False
            player.barrier_count += 1
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return
        bob = math.sin(self._t * 0.09) * 2
        cx, cy = int(self.x), int(self.y + bob)
        r = BARRIER_ITEM_RADIUS
        # 砖块外形（矩形 + 砖缝）
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.rect(surface, (200, 120, 40), rect, border_radius=2)
        pygame.draw.rect(surface, (240, 160, 70), rect, 2, border_radius=2)
        # 砖缝
        pygame.draw.line(surface, (150, 80, 20),
                         (cx - r, cy), (cx + r, cy), 1)
        pygame.draw.line(surface, (150, 80, 20),
                         (cx, cy - r), (cx, cy), 1)
        # 文字
        t = fonts.get(12).render("障", True, (60, 30, 10))
        surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))


class PlacedBarrier:
    """已放置的临时障碍物"""

    def __init__(self, col: int, row: int, owner_pid: int, owner_color):
        self.col   = col
        self.row   = row
        self.timer = BARRIER_DURATION
        self.owner_pid   = owner_pid
        self.owner_color = owner_color

    @property
    def alive(self):
        return self.timer > 0

    def update(self):
        self.timer -= 1

    def draw(self, surface):
        if not self.alive:
            return
        x = self.col * TILE
        y = self.row * TILE
        ratio = self.timer / BARRIER_DURATION

        # 主体砖块
        col_bright = tuple(int(c * (0.5 + 0.5 * ratio)) for c in self.owner_color)
        rect = pygame.Rect(x + 2, y + 2, TILE - 4, TILE - 4)
        pygame.draw.rect(surface, col_bright, rect, border_radius=3)

        # 砖缝
        dark = tuple(max(0, c - 60) for c in col_bright)
        mid_x, mid_y = x + TILE // 2, y + TILE // 2
        pygame.draw.line(surface, dark, (x + 2, mid_y), (x + TILE - 2, mid_y), 1)
        pygame.draw.line(surface, dark, (mid_x, y + 2), (mid_x, mid_y), 1)

        # 外框（闪烁警告：最后 2 秒）
        if ratio < 0.25:
            flash = int(abs(math.sin(self.timer * 0.3)) * 255)
            pygame.draw.rect(surface, (flash, flash, 50), rect, 2, border_radius=3)
        else:
            pygame.draw.rect(surface, self.owner_color, rect, 2, border_radius=3)

        # 倒计时
        remain = self.timer / 60
        t = fonts.get(14).render(f"{remain:.0f}", True, (220, 220, 220))
        surface.blit(t, (x + TILE // 2 - t.get_width() // 2,
                         y + TILE // 2 - t.get_height() // 2))


def try_place(player, placed_barriers: list[PlacedBarrier],
              grid) -> PlacedBarrier | None:
    """
    尝试在玩家脚下放置障碍。
    返回新 PlacedBarrier，或 None（无法放置）。
    """
    if player.barrier_count <= 0:
        return None

    col = int(player.x // TILE)
    row = int(player.y // TILE)

    # 不能放在墙上 / 已有障碍 / 越界
    if not (0 < col < COLS - 1 and 0 < row < ROWS - 1):
        return None
    if grid[row][col] == 1:
        return None
    if any(b.col == col and b.row == row and b.alive for b in placed_barriers):
        return None

    # 统计该玩家当前存活障碍数
    owned = sum(1 for b in placed_barriers
                if b.alive and b.owner_pid == player.pid)
    if owned >= MAX_PLACED:
        return None

    player.barrier_count -= 1
    return PlacedBarrier(col, row, player.pid, player.color)
