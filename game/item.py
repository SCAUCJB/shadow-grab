from game import fonts
"""
干扰道具：烟雾弹
- 随机刷新在地图地板上
- 玩家经过时自动拾取（携带上限 1 个）
- 按下使用键释放：在自身位置产生烟雾云
- 烟雾云持续 5 秒，范围内的痕迹被遮盖，玩家强制显示为隐身
"""
import math
import random
import pygame
from game.config import TILE, C_TEXT

SMOKE_RADIUS   = 80     # 烟雾云像素半径
SMOKE_DURATION = 300    # 帧（60fps × 5s）
ITEM_RADIUS    = 8


class SmokeItem:
    """可拾取的烟雾弹道具"""
    def __init__(self, col, row):
        self.x = col * TILE + TILE // 2
        self.y = row * TILE + TILE // 2
        self.alive = True
        self._t = 0

    def update(self):
        self._t += 1

    def check_pickup(self, player) -> bool:
        if not self.alive or player.smoke_count >= 2:
            return False
        if math.hypot(player.x - self.x, player.y - self.y) < ITEM_RADIUS + 14:
            self.alive = False
            player.smoke_count += 1
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return
        bob = math.sin(self._t * 0.1) * 2
        cx, cy = int(self.x), int(self.y + bob)
        # 灰色六边形
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts.append((cx + ITEM_RADIUS * math.cos(a),
                        cy + ITEM_RADIUS * math.sin(a)))
        pygame.draw.polygon(surface, (160, 160, 180), pts)
        pygame.draw.polygon(surface, (220, 220, 240), pts, 2)
        font = fonts.get(14)
        t = font.render("烟", True, (40, 40, 60))
        surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))


class SmokeCloud:
    """已释放的烟雾云"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = SMOKE_DURATION
        self._particles = [
            (random.uniform(-SMOKE_RADIUS * 0.8, SMOKE_RADIUS * 0.8),
             random.uniform(-SMOKE_RADIUS * 0.8, SMOKE_RADIUS * 0.8))
            for _ in range(18)
        ]

    @property
    def alive(self):
        return self.timer > 0

    def update(self):
        self.timer -= 1

    def covers(self, px, py) -> bool:
        return math.hypot(px - self.x, py - self.y) < SMOKE_RADIUS

    def draw(self, surface):
        if not self.alive:
            return
        alpha = int(160 * (self.timer / SMOKE_DURATION))
        s = pygame.Surface((SMOKE_RADIUS * 2 + 40,
                            SMOKE_RADIUS * 2 + 40), pygame.SRCALPHA)
        cx = cy = SMOKE_RADIUS + 20
        for ox, oy in self._particles:
            r = random.randint(28, 42)
            col = (140, 140, 150, alpha // 2)
            pygame.draw.circle(s, col, (int(cx + ox), int(cy + oy)), r)
        pygame.draw.circle(s, (120, 120, 130, alpha),
                           (cx, cy), SMOKE_RADIUS)
        surface.blit(s, (self.x - SMOKE_RADIUS - 20,
                         self.y - SMOKE_RADIUS - 20))

        # 剩余时间
        remain = self.timer / 60
        font = fonts.get(18)
        t = font.render(f"{remain:.1f}s", True, (200, 200, 210))
        surface.blit(t, (int(self.x) - t.get_width() // 2,
                         int(self.y) - SMOKE_RADIUS - 14))
