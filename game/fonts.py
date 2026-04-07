"""
中文字体加载工具。按优先级尝试 macOS 系统字体，全部失败则回退默认字体。
"""
import pygame

_CN_FONTS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Arial Unicode MS.ttf",
]

_cache: dict[int, pygame.font.Font] = {}


def get(size: int) -> pygame.font.Font:
    if size in _cache:
        return _cache[size]
    for path in _CN_FONTS:
        try:
            f = pygame.font.Font(path, size)
            _cache[size] = f
            return f
        except Exception:
            pass
    # 回退
    f = pygame.font.SysFont(None, size)
    _cache[size] = f
    return f
