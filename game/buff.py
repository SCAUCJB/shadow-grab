"""
增益道具系统

三种增益类型：
  speed   — 加速：移动速度 ×1.8，持续 6 秒，绿色闪电图标
  magnet  — 磁力：自动吸附范围内碎片（无需经过），持续 5 秒，蓝色磁铁图标
  stealth — 隐身：完全隐身（无痕迹），持续 4 秒，白色幽灵图标
"""
from __future__ import annotations
from game import fonts
import math
import pygame
from game.config import TILE, PLAYER_SPEED

BUFF_ITEM_RADIUS = 8

BUFF_CONFIGS = {
    'speed':   {'duration': 360, 'color': (80, 230, 80),   'label': '速', 'desc': '加速'},
    'magnet':  {'duration': 300, 'color': (80, 160, 255),  'label': '磁', 'desc': '磁力'},
    'stealth': {'duration': 240, 'color': (220, 220, 255), 'label': '隐', 'desc': '隐身'},
}

MAGNET_RADIUS  = 5 * TILE   # 磁力吸附范围（像素）
SPEED_FACTOR   = 1.8


class BuffItem:
    """地图上可拾取的增益道具"""

    def __init__(self, col: int, row: int, buff_type: str):
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.buff_type = buff_type
        self.alive = True
        self._t = 0
        self._cfg = BUFF_CONFIGS[buff_type]

    def update(self):
        self._t += 1

    def check_pickup(self, player) -> bool:
        if not self.alive:
            return False
        # 同类增益不叠加
        if any(b.buff_type == self.buff_type for b in player.buffs):
            return False
        if math.hypot(player.x - self.x, player.y - self.y) < BUFF_ITEM_RADIUS + 14:
            self.alive = False
            player.buffs.append(BuffEffect(self.buff_type))
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return
        col = self._cfg['color']
        t   = self._t
        bob = math.sin(t * 0.1) * 2
        pulse = BUFF_ITEM_RADIUS + math.sin(t * 0.14) * 2
        cx, cy = int(self.x), int(self.y + bob)

        # 星形背景光晕
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, 60), (20, 20), int(pulse) + 6)
        surface.blit(s, (cx - 20, cy - 20))

        # 五角星
        _draw_star(surface, cx, cy, int(pulse), col)

        # 文字标签
        lbl = fonts.get(13).render(self._cfg['label'], True, (20, 20, 30))
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))


class BuffEffect:
    """玩家身上的激活增益"""

    def __init__(self, buff_type: str):
        self.buff_type = buff_type
        self.timer = BUFF_CONFIGS[buff_type]['duration']
        self._cfg  = BUFF_CONFIGS[buff_type]

    @property
    def alive(self):
        return self.timer > 0

    def update(self):
        self.timer -= 1

    @property
    def ratio(self):
        return self.timer / self._cfg['duration']

    def draw_indicator(self, surface, x: int, y: int, idx: int):
        """在玩家头顶绘制增益图标（idx 控制纵向偏移）"""
        col = self._cfg['color']
        iy  = y - 22 - idx * 14
        # 进度条
        bar_w = 24
        bar_x = x - bar_w // 2
        pygame.draw.rect(surface, (40, 40, 40), (bar_x - 1, iy - 1, bar_w + 2, 7))
        filled = int(bar_w * self.ratio)
        if filled > 0:
            pygame.draw.rect(surface, col, (bar_x, iy, filled, 5))
        # 文字
        t = fonts.get(11).render(self._cfg['label'], True, col)
        surface.blit(t, (x + 14, iy - 2))


# ── 工具函数 ──────────────────────────────────────────────


def _draw_star(surface, cx, cy, r, color):
    """绘制五角星"""
    pts = []
    for i in range(10):
        angle = math.radians(-90 + 36 * i)
        radius = r if i % 2 == 0 else r * 0.45
        pts.append((cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle)))
    pygame.draw.polygon(surface, color, pts)
    dark = tuple(max(0, c - 50) for c in color)
    pygame.draw.polygon(surface, dark, pts, 2)


def apply_speed(player) -> float:
    """返回当前帧的实际速度倍数"""
    for b in player.buffs:
        if b.buff_type == 'speed':
            return SPEED_FACTOR
    return 1.0


def is_stealthed(player) -> bool:
    return any(b.buff_type == 'stealth' for b in player.buffs)


def magnet_radius(player) -> float:
    if any(b.buff_type == 'magnet' for b in player.buffs):
        return MAGNET_RADIUS
    return 0.0
