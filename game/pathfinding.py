"""
共享 BFS 寻路（从 ai.py 提取，供 guard.py 和 ai.py 共用）。
"""
from __future__ import annotations
from collections import deque
from game.config import COLS, ROWS


def bfs(grid, start_col: int, start_row: int,
        goal_col: int, goal_row: int) -> list[tuple[int, int]]:
    """返回从 start 到 goal 的格子路径（不含起点），空列表表示不可达。"""
    if (start_col, start_row) == (goal_col, goal_row):
        return []
    visited = {(start_col, start_row)}
    parent  = {(start_col, start_row): None}
    queue   = deque([(start_col, start_row)])
    while queue:
        cc, cr = queue.popleft()
        for dc, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nc, nr = cc + dc, cr + dr
            if (nc, nr) in visited:
                continue
            if not (0 <= nc < COLS and 0 <= nr < ROWS):
                continue
            if grid[nr][nc] == 1:
                continue
            visited.add((nc, nr))
            parent[(nc, nr)] = (cc, cr)
            if nc == goal_col and nr == goal_row:
                path = []
                cur = (nc, nr)
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                return path[1:]   # 去掉起点
            queue.append((nc, nr))
    return []
