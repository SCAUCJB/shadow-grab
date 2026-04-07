"""
地图视觉主题：每局随机选一个主题，决定地图配色和粒子风格。
"""
import random

THEMES = {
    'dungeon': {
        'name':    '地牢',
        'bg':      (14,  12,  20),
        'wall':    (55,  50,  72),
        'wall_hi': (75,  70,  95),   # 墙砖高亮边
        'floor':   (26,  24,  36),
        'grid':    (32,  30,  44),
        'p1':      (80,  200, 255),
        'p2':      (255, 100, 80),
        'trail1':  (35,  90,  140),
        'trail2':  (140, 45,  35),
        'base1':   (40,  140, 200),
        'base2':   (200, 70,  50),
        'resource':(255, 215, 50),
        'smoke':   (130, 130, 145),
        'decoy':   (170, 110, 220),
    },
    'cyber': {
        'name':    '赛博',
        'bg':      (5,   8,   18),
        'wall':    (15,  40,  70),
        'wall_hi': (0,   180, 220),
        'floor':   (8,   14,  28),
        'grid':    (12,  28,  50),
        'p1':      (0,   240, 200),
        'p2':      (255, 60,  160),
        'trail1':  (0,   100, 90),
        'trail2':  (120, 20,  80),
        'base1':   (0,   180, 150),
        'base2':   (200, 40,  130),
        'resource':(255, 240, 80),
        'smoke':   (20,  80,  100),
        'decoy':   (120, 80,  255),
    },
    'forest': {
        'name':    '暗林',
        'bg':      (10,  18,  12),
        'wall':    (30,  55,  30),
        'wall_hi': (50,  90,  40),
        'floor':   (16,  28,  18),
        'grid':    (22,  38,  22),
        'p1':      (120, 230, 100),
        'p2':      (240, 160, 60),
        'trail1':  (50,  110, 40),
        'trail2':  (120, 75,  25),
        'base1':   (80,  180, 60),
        'base2':   (200, 130, 40),
        'resource':(255, 230, 80),
        'smoke':   (60,  90,  55),
        'decoy':   (180, 100, 210),
    },
    'lava': {
        'name':    '熔岩',
        'bg':      (18,  8,   5),
        'wall':    (70,  28,  15),
        'wall_hi': (200, 80,  20),
        'floor':   (28,  14,  8),
        'grid':    (40,  20,  10),
        'p1':      (255, 200, 60),
        'p2':      (100, 210, 255),
        'trail1':  (160, 100, 20),
        'trail2':  (40,  100, 160),
        'base1':   (220, 160, 30),
        'base2':   (60,  160, 220),
        'resource':(255, 240, 120),
        'smoke':   (100, 50,  30),
        'decoy':   (200, 80,  200),
    },
}

_THEME_KEYS = list(THEMES.keys())


def pick(seed: int) -> dict:
    rng = random.Random(seed ^ 0xDEAD)
    key = rng.choice(_THEME_KEYS)
    return THEMES[key]


def all_names() -> list[str]:
    return [v['name'] for v in THEMES.values()]
