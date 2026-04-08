"""
守卫系统：巡逻 → 追击 → 返回 有限状态机。
守卫感知玩家的可见性（烟雾/隐身 buff 对守卫生效）。
"""
from __future__ import annotations
import math
import pygame
from game.config import TILE, COLS, ROWS
from game.pathfinding import bfs
from game import sprites

GUARD_SPEED          = 1.8    # px/帧
GUARD_VISION_PX      = 160    # 5 格视野半径
GUARD_CATCH_PX       = 18     # 捕捉距离
GUARD_SIGHT_LOSS_MAX = 90     # 失去视野多少帧后放弃追击
GUARD_REPLAN_INT     = 12     # 每隔多少帧重新 BFS
GUARD_INVINCIBLE_DUR = 120    # 玩家被捕后无敌帧数（2 秒）
GUARD_COLOR          = (210, 90, 210)

STATE_PATROL        = 'patrol'
STATE_CHASE         = 'chase'
STATE_RETURN_PATROL = 'return_patrol'


def _make_waypoints(rx: int, ry: int, rw: int, rh: int) -> list[tuple[float, float]]:
    """在房间内生成 2~4 个巡逻节点（像素中心坐标）。"""
    def center(col, row):
        return col * TILE + TILE // 2, row * TILE + TILE // 2

    if rw >= 4 and rh >= 4:
        return [
            center(rx + rw // 4,             ry + rh // 4),
            center(rx + 3 * rw // 4 - 1,     ry + rh // 4),
            center(rx + 3 * rw // 4 - 1,     ry + 3 * rh // 4 - 1),
            center(rx + rw // 4,             ry + 3 * rh // 4 - 1),
        ]
    else:
        # 小房间：两个对角节点
        return [
            center(rx + 1,      ry + 1),
            center(rx + rw - 2, ry + rh - 2),
        ]


class Guard:
    def __init__(self, room: tuple, guard_id: int, grid):
        rx, ry, rw, rh = room
        self.id    = guard_id
        self.color = GUARD_COLOR

        self.waypoints = _make_waypoints(rx, ry, rw, rh)
        self.x = float(self.waypoints[0][0])
        self.y = float(self.waypoints[0][1])
        self._wp_idx = 0

        self._state         = STATE_PATROL
        self._path: list    = []
        self._sight_lost_t  = 0
        self._replan_t      = 0
        self._frame         = 0
        self._target        = None   # 当前追击的 Player

    # ── 主更新 ───────────────────────────────────────────
    def update(self, players: list, grid, barriers=None) -> tuple[list, bool]:
        """
        每帧调用。
        返回 (caught_players, entered_chase)。
        caught_players: 本帧被捕的玩家列表。
        entered_chase:  本帧是否刚进入追击状态（用于播放提示音）。
        """
        self._frame += 1
        caught: list   = []
        entered_chase  = False

        if self._state == STATE_PATROL:
            self._do_patrol()
            target = self._scan(players)
            if target:
                self._state        = STATE_CHASE
                self._target       = target
                self._sight_lost_t = 0
                self._replan_t     = GUARD_REPLAN_INT  # 立即规划
                self._path         = []
                entered_chase      = True

        elif self._state == STATE_CHASE:
            target = self._target
            if self._can_see(target):
                self._sight_lost_t = 0
            else:
                self._sight_lost_t += 1

            if self._sight_lost_t >= GUARD_SIGHT_LOSS_MAX:
                self._state  = STATE_RETURN_PATROL
                self._path   = []
                self._target = None
            else:
                self._replan_t += 1
                if self._replan_t >= GUARD_REPLAN_INT or not self._path:
                    self._replan_t = 0
                    gc = int(target.x // TILE)
                    gr = int(target.y // TILE)
                    sc = int(self.x // TILE)
                    sr = int(self.y // TILE)
                    self._path = bfs(grid, sc, sr, gc, gr)
                self._move_along_path()

                # 捕捉检测（无敌期间免疫）
                if target.invincible_timer <= 0:
                    if math.hypot(self.x - target.x, self.y - target.y) < GUARD_CATCH_PX:
                        caught.append(target)
                        self._state  = STATE_RETURN_PATROL
                        self._path   = []
                        self._target = None

        elif self._state == STATE_RETURN_PATROL:
            if not self._path:
                wp = self._nearest_waypoint()
                wc = int(wp[0] // TILE)
                wr = int(wp[1] // TILE)
                sc = int(self.x // TILE)
                sr = int(self.y // TILE)
                self._path = bfs(grid, sc, sr, wc, wr)
                if not self._path:
                    self._state = STATE_PATROL
            else:
                self._move_along_path()
                if not self._path:
                    self._state = STATE_PATROL

        return caught, entered_chase

    # ── 巡逻移动 ────────────────────────────────────────
    def _do_patrol(self):
        tx, ty = self.waypoints[self._wp_idx]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < GUARD_SPEED + 2:
            self._wp_idx = (self._wp_idx + 1) % len(self.waypoints)
            return
        self.x += dx / dist * GUARD_SPEED
        self.y += dy / dist * GUARD_SPEED

    # ── 路径跟随 ────────────────────────────────────────
    def _move_along_path(self):
        if not self._path:
            return
        tc, tr = self._path[0]
        tx = tc * TILE + TILE // 2
        ty = tr * TILE + TILE // 2
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < GUARD_SPEED + 2:
            self._path.pop(0)
            return
        self.x += dx / dist * GUARD_SPEED
        self.y += dy / dist * GUARD_SPEED

    # ── 视野扫描 ────────────────────────────────────────
    def _scan(self, players: list):
        """返回距离最近且可见的玩家，否则返回 None。"""
        best, best_dist = None, float('inf')
        for p in players:
            if self._can_see(p):
                d = math.hypot(self.x - p.x, self.y - p.y)
                if d < best_dist:
                    best, best_dist = p, d
        return best

    def _can_see(self, player) -> bool:
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < GUARD_VISION_PX and player.visible

    def _nearest_waypoint(self) -> tuple[float, float]:
        return min(self.waypoints,
                   key=lambda wp: math.hypot(self.x - wp[0], self.y - wp[1]))

    # ── 渲染 ────────────────────────────────────────────
    def draw(self, surface):
        sprites.draw_guard(surface, int(self.x), int(self.y),
                           self.color, self._state, self._frame)
