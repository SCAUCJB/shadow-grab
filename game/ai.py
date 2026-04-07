"""
AI 控制器：用 BFS 寻路 + 有限状态机决策。

状态优先级：
  RETURN   — 携带碎片时直奔基地
  INTERCEPT — 发现玩家携带碎片且可见时，抢先守住玩家基地入口
  SEEK     — 寻找最近存活碎片
  WANDER   — 无碎片可拿时随机游走

难度差异：
  easy   : 速度 55%，无拦截，BFS 有噪声
  normal : 速度 75%，基础拦截
  hard   : 速度 92%，主动拦截 + 会用道具
"""
from __future__ import annotations
import math, random
from collections import deque
import pygame
from game.config import TILE, COLS, ROWS, PLAYER_SPEED

# 难度参数
DIFFICULTY = {
    'easy':   {'speed_ratio': 0.55, 'intercept': False, 'use_items': False, 'noise': 0.25},
    'normal': {'speed_ratio': 0.75, 'intercept': True,  'use_items': False, 'noise': 0.10},
    'hard':   {'speed_ratio': 0.92, 'intercept': True,  'use_items': True,  'noise': 0.03},
}

STATE_RETURN    = 'return'
STATE_INTERCEPT = 'intercept'
STATE_SEEK      = 'seek'
STATE_WANDER    = 'wander'


def _bfs(grid, start_col, start_row, goal_col, goal_row) -> list[tuple[int,int]]:
    """返回从 start 到 goal 的格子路径（不含起点），空列表表示不可达。"""
    if (start_col, start_row) == (goal_col, goal_row):
        return []
    visited = {(start_col, start_row)}
    parent  = {(start_col, start_row): None}
    queue   = deque([(start_col, start_row)])
    while queue:
        cc, cr = queue.popleft()
        for dc, dr in [(0,-1),(0,1),(-1,0),(1,0)]:
            nc, nr = cc+dc, cr+dr
            if (nc, nr) in visited:
                continue
            if not (0 <= nc < COLS and 0 <= nr < ROWS):
                continue
            if grid[nr][nc] == 1:
                continue
            visited.add((nc, nr))
            parent[(nc, nr)] = (cc, cr)
            if nc == goal_col and nr == goal_row:
                # 回溯路径
                path = []
                cur = (nc, nr)
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                return path[1:]   # 去掉起点
            queue.append((nc, nr))
    return []


class AIController:
    def __init__(self, difficulty: str = 'normal'):
        cfg = DIFFICULTY.get(difficulty, DIFFICULTY['normal'])
        self.speed      = PLAYER_SPEED * cfg['speed_ratio']
        self.intercept  = cfg['intercept']
        self.use_items  = cfg['use_items']
        self.noise      = cfg['noise']
        self.difficulty = difficulty

        self._state      = STATE_SEEK
        self._path: list[tuple[int,int]] = []
        self._target     = None
        self._wander_dir = (1, 0)
        self._wander_t   = 0
        self._think_t    = 0     # 思考间隔（不每帧重算路径）
        self._think_int  = 12    # 帧

    # ── 主更新（替代 Player.update 中的按键读取） ─────────
    def step(self, player, opponent, base, resources,
             smoke_items, decoy_items, grid) -> tuple[float, float]:
        """
        计算 AI 本帧应移动的 (dx, dy) 像素向量。
        调用方负责将结果写入 player.x/y 并做碰撞检测。
        """
        self._think_t += 1
        replan = (self._think_t >= self._think_int)
        if replan:
            self._think_t = 0
            self._plan(player, opponent, base, resources, grid)

        # 道具使用
        if self.use_items:
            self._maybe_use_items(player, opponent, smoke_items, decoy_items)

        # 沿路径移动
        dx, dy = self._follow_path(player, grid)
        return dx, dy

    # ── 决策 ─────────────────────────────────────────────
    def _plan(self, player, opponent, base, resources, grid):
        pc = int(player.x // TILE)
        pr = int(player.y // TILE)

        # 1. 携带碎片 → 回基地
        if player.carrying:
            self._state = STATE_RETURN
            gc = int(base.x // TILE)
            gr = int(base.y // TILE)
            self._path = _bfs(grid, pc, pr, gc, gr)
            return

        # 2. 拦截：对手可见且携带碎片 → 守住对手基地
        if self.intercept and opponent.carrying and opponent.visible:
            # 找对手要去的"我方"基地附近格子（对手基地就是 base，AI 基地就是 base）
            # 实际上是守住对手的目标基地（=对手的 base）
            # 这里 base 参数是 AI 自己的基地，opponent_base 需要从外面传
            # 简化：冲向对手当前位置前方截击
            ox = int(opponent.x // TILE)
            oy = int(opponent.y // TILE)
            self._state = STATE_INTERCEPT
            self._path  = _bfs(grid, pc, pr, ox, oy)
            return

        # 3. 寻找最近存活碎片
        alive = [r for r in resources if r.alive]
        if alive:
            # 按曼哈顿距离排序，加随机噪声
            def cost(r):
                d = abs(r.col - pc) + abs(r.row - pr)
                return d + random.uniform(0, self.noise * 20)
            target = min(alive, key=cost)
            self._state = STATE_SEEK
            self._path  = _bfs(grid, pc, pr, target.col, target.row)
            return

        # 4. 无碎片可拿 → 游走
        self._state = STATE_WANDER
        self._path  = []

    # ── 路径跟随 ─────────────────────────────────────────
    def _follow_path(self, player, grid) -> tuple[float, float]:
        if self._state == STATE_WANDER:
            return self._wander(player, grid)

        if not self._path:
            return 0.0, 0.0

        # 目标格子中心
        tc, tr = self._path[0]
        tx = tc * TILE + TILE // 2
        ty = tr * TILE + TILE // 2

        dx = tx - player.x
        dy = ty - player.y
        dist = math.hypot(dx, dy)

        if dist < self.speed + 2:
            # 到达当前路径节点
            self._path.pop(0)
            if not self._path:
                return 0.0, 0.0
            tc, tr = self._path[0]
            tx = tc * TILE + TILE // 2
            ty = tr * TILE + TILE // 2
            dx = tx - player.x
            dy = ty - player.y
            dist = math.hypot(dx, dy) or 1

        # 归一化 + 加噪声
        ndx = dx / dist * self.speed
        ndy = dy / dist * self.speed
        if self.noise > 0:
            ndx += random.uniform(-self.noise, self.noise) * self.speed
            ndy += random.uniform(-self.noise, self.noise) * self.speed
        return ndx, ndy

    def _wander(self, player, grid) -> tuple[float, float]:
        self._wander_t += 1
        if self._wander_t > 40:
            self._wander_t = 0
            dirs = [(1,0),(-1,0),(0,1),(0,-1)]
            random.shuffle(dirs)
            self._wander_dir = dirs[0]
        dc, dr = self._wander_dir
        return dc * self.speed, dr * self.speed

    # ── 道具使用 ─────────────────────────────────────────
    def _maybe_use_items(self, player, opponent, smoke_items, decoy_items):
        # 对手可见且距离很近时放烟雾
        if (player.smoke_count > 0
                and opponent.visible
                and math.hypot(player.x - opponent.x,
                               player.y - opponent.y) < 5 * TILE):
            # 返回信号让 scene 处理（通过标志位）
            player._ai_use_smoke = True

        # 有假信号时随机释放（每 300 帧 20% 概率）
        if player.decoy_count > 0 and random.random() < 0.003:
            player._ai_use_decoy = True
