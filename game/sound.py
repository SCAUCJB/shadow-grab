"""
音效生成（纯 Python stdlib，无 numpy 依赖）。
用 array 模块生成 PCM 数据，直接传给 pygame.mixer.Sound。
"""
from __future__ import annotations
import array
import math
import pygame

_RATE = 44100
_sounds: dict = {}
_enabled = False


def _make(freq: float, duration: float, vol: float = 0.35,
          decay: bool = True) -> pygame.mixer.Sound | None:
    frames = int(_RATE * duration)
    buf = array.array('h')
    for i in range(frames):
        t = i / _RATE
        v = math.sin(2 * math.pi * freq * t)
        if decay:
            env = max(0.0, 1.0 - i / frames)
        else:
            # 快速起音，慢速衰减
            attack = int(frames * 0.05)
            env = min(1.0, i / max(1, attack))
        buf.append(int(v * env * vol * 32767))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


def init():
    global _enabled
    try:
        pygame.mixer.pre_init(_RATE, -16, 1, 1024)
        _enabled = True
    except Exception:
        return

    _sounds['pickup']   = _make(880,  0.12, 0.28)
    _sounds['deposit']  = _make(660,  0.22, 0.38)
    _sounds['standoff'] = _make(330,  0.16, 0.32)
    _sounds['win']      = _make(523,  0.45, 0.45, decay=False)
    _sounds['smoke']    = _make(200,  0.18, 0.22)
    _sounds['decoy']    = _make(440,  0.14, 0.22)
    _sounds['barrier']  = _make(150,  0.16, 0.30)
    _sounds['buff']        = _make(740,  0.20, 0.30)
    _sounds['guard_alert'] = _make(880,  0.08, 0.30)
    _sounds['guard_catch'] = _make(220,  0.35, 0.45)


def play(name: str):
    if not _enabled:
        return
    s = _sounds.get(name)
    if s:
        s.play()
