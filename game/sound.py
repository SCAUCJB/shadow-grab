"""
程序化音效生成（无需音频文件，用 numpy 合成正弦波）。
若 numpy 不可用则静默降级。
"""
import pygame

_enabled = False
try:
    import numpy as np
    pygame.mixer.pre_init(44100, -16, 1, 512)
    _enabled = True
except ImportError:
    pass

_RATE = 44100


def _make(freq: float, duration: float, vol: float = 0.4, decay: bool = True):
    if not _enabled:
        return None
    frames = int(_RATE * duration)
    t = np.linspace(0, duration, frames, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    if decay:
        env = np.linspace(1.0, 0.0, frames)
        wave *= env
    wave = (wave * vol * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(wave)
    return sound


# 预生成音效
_sounds: dict = {}


def init():
    """在 pygame.init() 之后调用"""
    if not _enabled:
        return
    _sounds['pickup']   = _make(880,  0.12, 0.3)
    _sounds['deposit']  = _make(660,  0.25, 0.4)
    _sounds['standoff'] = _make(330,  0.18, 0.35)
    _sounds['win']      = _make(523,  0.5,  0.5, decay=False)
    _sounds['smoke']    = _make(200,  0.2,  0.25)
    _sounds['decoy']    = _make(440,  0.15, 0.25)
    _sounds['barrier']  = _make(150,  0.18, 0.35)
    _sounds['buff']     = _make(740,  0.22, 0.35)


def play(name: str):
    s = _sounds.get(name)
    if s:
        s.play()
