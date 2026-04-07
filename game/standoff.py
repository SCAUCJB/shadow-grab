"""
对峙系统：双方同时靠近同一碎片时触发。
- 对峙期间碎片无法被拾取
- 先离开者判负（碎片归留守方）
- 若双方同时坚守 STANDOFF_SEC 秒，碎片消失（平局）
"""
from __future__ import annotations
from game import fonts
from typing import Optional, Tuple
import pygame
from game.config import SCREEN_W, SCREEN_H, C_P1, C_P2, C_TEXT, RESOURCE_RADIUS

STANDOFF_RANGE = RESOURCE_RADIUS + 20   # 触发对峙的距离
STANDOFF_SEC   = 3.0                    # 坚守满此时间双方都拿不到
FPS            = 60


class StandoffManager:
    def __init__(self):
        self.active     = False
        self.resource   = None   # 正在对峙的资源
        self.timer      = 0.0    # 已对峙帧数
        self.p1_in      = False
        self.p2_in      = False

    def _dist(self, player, res):
        import math
        return math.hypot(player.x - res.x, player.y - res.y)

    def update(self, p1, p2, resources) -> Tuple[Optional[int], Optional[object]]:
        """
        返回 (winner_pid or None, resource or None)
        winner_pid: 1/2 表示该玩家赢得对峙资源；None 表示无结果
        """
        if not self.active:
            # 扫描是否有碎片进入对峙状态
            for res in resources:
                if not res.alive:
                    continue
                p1_near = self._dist(p1, res) < STANDOFF_RANGE
                p2_near = self._dist(p2, res) < STANDOFF_RANGE
                if p1_near and p2_near and not p1.carrying and not p2.carrying:
                    self.active   = True
                    self.resource = res
                    self.timer    = 0.0
                    self.p1_in    = True
                    self.p2_in    = True
                    return None, None
            return None, None

        # 已在对峙中
        res = self.resource
        if not res.alive:          # 碎片被别处逻辑消耗（不应发生）
            self._reset()
            return None, None

        self.p1_in = self._dist(p1, res) < STANDOFF_RANGE and not p1.carrying
        self.p2_in = self._dist(p2, res) < STANDOFF_RANGE and not p2.carrying

        self.timer += 1

        # 有人离开
        if not self.p1_in and not self.p2_in:
            # 双方同时离开 → 平局，碎片消失
            res.alive = False
            self._reset()
            return None, None

        if not self.p1_in:
            # P1 先撤，P2 赢
            winner = 2
            self._reset()
            return winner, res

        if not self.p2_in:
            # P2 先撤，P1 赢
            winner = 1
            self._reset()
            return winner, res

        # 双方坚守满时间 → 平局消失
        if self.timer >= STANDOFF_SEC * FPS:
            res.alive = False
            self._reset()
            return None, None

        return None, None

    def _reset(self):
        self.active   = False
        self.resource = None
        self.timer    = 0.0

    def draw(self, surface):
        if not self.active or self.resource is None:
            return

        res = self.resource
        import math

        # 红色脉冲圈
        pulse = 18 + math.sin(self.timer * 0.3) * 5
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 60, 60, 100), (40, 40), int(pulse) + 10)
        pygame.draw.circle(s, (255, 60, 60, 180), (40, 40), int(pulse), 3)
        surface.blit(s, (int(res.x) - 40, int(res.y) - 40))

        # 对峙文字
        remain = max(0.0, STANDOFF_SEC - self.timer / FPS)
        font = fonts.get(26)
        txt = font.render(f"对峙！ {remain:.1f}s", True, (255, 80, 80))
        surface.blit(txt, (int(res.x) - txt.get_width() // 2,
                           int(res.y) - 40))

        # 双方状态指示
        font_sm = fonts.get(20)
        p1c = (80, 200, 255) if self.p1_in else (100, 100, 100)
        p2c = (255, 100, 80) if self.p2_in else (100, 100, 100)
        t1 = font_sm.render("P1 ●" if self.p1_in else "P1 ✗", True, p1c)
        t2 = font_sm.render("P2 ●" if self.p2_in else "P2 ✗", True, p2c)
        surface.blit(t1, (int(res.x) - 45, int(res.y) + 24))
        surface.blit(t2, (int(res.x) + 10, int(res.y) + 24))
