from game import fonts
"""
像素风精灵绘制（纯 pygame 绘图，无需图片文件）。
所有 draw_* 函数直接在 surface 上绘制。
"""
import math
import pygame

# ── 玩家 ─────────────────────────────────────────────────


def draw_player(surface, x: int, y: int, color, carrying: bool,
                visible: bool, frame: int):
    """
    像素风小人：头 + 身体 + 腿（走路动画）。
    visible=False 时只画极暗轮廓（自己视角小点）。
    """
    cx, cy = int(x), int(y)

    if not visible:
        s = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, 45), (7, 7), 5)
        surface.blit(s, (cx - 7, cy - 7))
        return

    # 走路摆腿
    leg = int(math.sin(frame * 0.25) * 3)

    # 身体
    body_rect = pygame.Rect(cx - 5, cy - 4, 10, 9)
    pygame.draw.rect(surface, color, body_rect, border_radius=2)

    # 头
    pygame.draw.circle(surface, color, (cx, cy - 9), 6)
    # 眼睛
    eye_col = (20, 20, 30)
    pygame.draw.circle(surface, eye_col, (cx - 2, cy - 10), 1)
    pygame.draw.circle(surface, eye_col, (cx + 2, cy - 10), 1)

    # 腿
    dark = tuple(max(0, c - 60) for c in color)
    pygame.draw.line(surface, dark, (cx - 3, cy + 5), (cx - 3 + leg, cy + 10), 2)
    pygame.draw.line(surface, dark, (cx + 3, cy + 5), (cx + 3 - leg, cy + 10), 2)

    # 携带碎片时头顶光环
    if carrying:
        s = pygame.Surface((30, 30), pygame.SRCALPHA)
        t = frame * 0.08
        r = 13 + math.sin(t) * 2
        pygame.draw.circle(s, (255, 220, 60, 140), (15, 15), int(r), 2)
        surface.blit(s, (cx - 15, cy - 24))


# ── 资源碎片 ─────────────────────────────────────────────


def draw_resource(surface, x: int, y: int, color, frame: int):
    """旋转的像素钻石"""
    t = frame * 0.06
    bob = math.sin(t) * 3
    cx, cy = x, int(y + bob)
    angle = frame * 2  # 度

    pts_base = [(0, -10), (7, 0), (0, 7), (-7, 0)]
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    pts = [(cx + int(px * cos_a - py * sin_a),
            cy + int(px * sin_a + py * cos_a))
           for px, py in pts_base]

    # 外层亮色
    pygame.draw.polygon(surface, color, pts)
    # 内层高亮
    inner = [(cx + int(px * 0.5 * cos_a - py * 0.5 * sin_a),
              cy + int(px * 0.5 * sin_a + py * 0.5 * cos_a))
             for px, py in pts_base]
    bright = tuple(min(255, c + 60) for c in color)
    pygame.draw.polygon(surface, bright, inner)
    # 外圈
    dark = tuple(max(0, c - 40) for c in color)
    pygame.draw.polygon(surface, dark, pts, 2)


# ── 基地 ─────────────────────────────────────────────────


def draw_base(surface, x: int, y: int, color, pid: int, frame: int):
    """像素风六边形基地"""
    t = frame * 0.05
    pulse = 22 + math.sin(t) * 4

    # 脉冲光晕
    s = pygame.Surface((80, 80), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, 40), (40, 40), int(pulse) + 10)
    surface.blit(s, (x - 40, y - 40))

    # 六边形
    pts = []
    for i in range(6):
        a = math.radians(60 * i + 30)
        pts.append((x + int(pulse * math.cos(a)),
                    y + int(pulse * math.sin(a))))
    pygame.draw.polygon(surface, (*color, 60),  pts)  # 需要 SRCALPHA
    # 实心不透明版
    pygame.draw.polygon(surface, color, pts, 3)

    # 内部小六边形
    inner = []
    for i in range(6):
        a = math.radians(60 * i + 30)
        r = pulse * 0.5
        inner.append((x + int(r * math.cos(a)), y + int(r * math.sin(a))))
    pygame.draw.polygon(surface, color, inner, 2)

    # 标签
    font = fonts.get(20)
    lbl = font.render(f"P{pid}", True, color)
    surface.blit(lbl, (x - lbl.get_width() // 2, y - lbl.get_height() // 2))


# ── 地图瓦片 ─────────────────────────────────────────────


def draw_wall_tile(surface, rect: pygame.Rect, wall_col, hi_col, seed_val: int):
    """带砖纹的墙壁"""
    pygame.draw.rect(surface, wall_col, rect)
    # 随机砖缝（用 seed 保持稳定）
    r = (seed_val * 2654435761) & 0xFFFF
    if r % 3 == 0:
        mid_y = rect.y + rect.height // 2
        pygame.draw.line(surface, hi_col,
                         (rect.x, mid_y), (rect.right, mid_y), 1)
    elif r % 3 == 1:
        mid_x = rect.x + rect.width // 2
        pygame.draw.line(surface, hi_col,
                         (mid_x, rect.y), (mid_x, rect.bottom), 1)
    # 顶部/左侧高亮边（模拟光源）
    pygame.draw.line(surface, hi_col,
                     (rect.x, rect.y), (rect.right, rect.y), 1)
    pygame.draw.line(surface, hi_col,
                     (rect.x, rect.y), (rect.x, rect.bottom), 1)


def draw_floor_tile(surface, rect: pygame.Rect, floor_col, grid_col):
    pygame.draw.rect(surface, floor_col, rect)
    pygame.draw.rect(surface, grid_col, rect, 1)
