"""
随机地图生成：用 BSP (Binary Space Partition) 切割房间 + 走廊连接。
双方使用相同 seed，保证地图公平。
"""
import random
from game.config import COLS, ROWS


def generate(seed: int):
    """返回 grid[row][col]，0=地板，1=墙"""
    rng = random.Random(seed)
    grid = [[1] * COLS for _ in range(ROWS)]

    rooms = []
    _bsp(rng, grid, rooms, 1, 1, COLS - 2, ROWS - 2, depth=0)
    _connect_rooms(rng, grid, rooms)

    # 确保边界全是墙
    for r in range(ROWS):
        grid[r][0] = grid[r][COLS - 1] = 1
    for c in range(COLS):
        grid[0][c] = grid[ROWS - 1][c] = 1

    return grid, rooms


def _bsp(rng, grid, rooms, x1, y1, x2, y2, depth):
    w, h = x2 - x1, y2 - y1
    if w < 6 or h < 6 or depth >= 4:
        # 挖一个房间
        rw = rng.randint(max(3, w // 2), max(3, w - 1))
        rh = rng.randint(max(3, h // 2), max(3, h - 1))
        rx = rng.randint(x1, x2 - rw)
        ry = rng.randint(y1, y2 - rh)
        for r in range(ry, ry + rh):
            for c in range(rx, rx + rw):
                grid[r][c] = 0
        rooms.append((rx, ry, rw, rh))
        return

    if rng.random() < 0.5 and w >= 8:
        mid = rng.randint(x1 + 3, x2 - 3)
        _bsp(rng, grid, rooms, x1, y1, mid, y2, depth + 1)
        _bsp(rng, grid, rooms, mid, y1, x2, y2, depth + 1)
    else:
        mid = rng.randint(y1 + 3, y2 - 3)
        _bsp(rng, grid, rooms, x1, y1, x2, mid, depth + 1)
        _bsp(rng, grid, rooms, x1, mid, x2, y2, depth + 1)


def _connect_rooms(rng, grid, rooms):
    if len(rooms) < 2:
        return
    shuffled = rooms[:]
    rng.shuffle(shuffled)
    for i in range(len(shuffled) - 1):
        ax, ay, aw, ah = shuffled[i]
        bx, by, bw, bh = shuffled[i + 1]
        cx1 = ax + aw // 2
        cy1 = ay + ah // 2
        cx2 = bx + bw // 2
        cy2 = by + bh // 2
        # L 形走廊
        if rng.random() < 0.5:
            _hcorridor(grid, cx1, cx2, cy1)
            _vcorridor(grid, cy1, cy2, cx2)
        else:
            _vcorridor(grid, cy1, cy2, cx1)
            _hcorridor(grid, cx1, cx2, cy2)


def _hcorridor(grid, x1, x2, y):
    for c in range(min(x1, x2), max(x1, x2) + 1):
        if 0 < y < ROWS - 1 and 0 < c < COLS - 1:
            grid[y][c] = 0


def _vcorridor(grid, y1, y2, x):
    for r in range(min(y1, y2), max(y1, y2) + 1):
        if 0 < r < ROWS - 1 and 0 < x < COLS - 1:
            grid[r][x] = 0


def room_center(room):
    x, y, w, h = room
    return x + w // 2, y + h // 2


def floor_cells(grid):
    """返回所有地板格子的 (col, row) 列表"""
    cells = []
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == 0:
                cells.append((c, r))
    return cells
