"""
程序化 BGM：用 stdlib array + math 合成五声音阶循环旋律。
无 numpy / threading 依赖，兼容 pygbag WASM 环境。
"""
from __future__ import annotations
import array
import math
import pygame

_enabled = False
_current_sound = None
_current_channel = None

RATE = 44100

# 五声音阶（A 小调五声）
_PENTA = [220.0, 261.6, 293.7, 349.2, 392.0,
          440.0, 523.3, 587.3, 698.5, 784.0]

_MELODIES = {
    'dungeon': [0, 2, 1, 4, 3, 2, 0, 4,  2, 3, 1, 0, 4, 2, 3, 1],
    'cyber':   [4, 6, 7, 5, 4, 7, 6, 9,  5, 4, 6, 7, 4, 5, 9, 6],
    'forest':  [0, 1, 3, 2, 4, 3, 1, 0,  2, 4, 3, 1, 2, 0, 4, 2],
    'lava':    [4, 3, 7, 5, 4, 6, 3, 7,  5, 4, 3, 6, 7, 4, 5, 3],
}

_BPM = {
    'dungeon': 90,
    'cyber':   130,
    'forest':  80,
    'lava':    110,
}


def _make_note(freq: float, dur: float, waveform: str = 'square', vol: float = 0.08) -> array.array:
    frames = int(RATE * dur)
    buf = array.array('h')
    attack  = min(int(RATE * 0.01), frames // 4)
    release = min(int(RATE * 0.05), frames // 4)
    for i in range(frames):
        t = i / RATE
        if waveform == 'square':
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif waveform == 'tri':
            phase = (t * freq) % 1.0
            v = 2 * abs(2 * (phase - math.floor(phase + 0.5))) - 1
        else:
            v = math.sin(2 * math.pi * freq * t)
        # 包络
        if i < attack:
            env = i / max(1, attack)
        elif i >= frames - release:
            env = (frames - i) / max(1, release)
        else:
            env = 1.0
        buf.append(int(v * env * vol * 32767))
    return buf


def _build_loop(theme_key: str) -> pygame.mixer.Sound | None:
    melody = _MELODIES.get(theme_key, _MELODIES['dungeon'])
    bpm    = _BPM.get(theme_key, 100)
    beat   = 60.0 / bpm
    wf     = 'square' if theme_key in ('dungeon', 'lava') else 'tri'

    combined = array.array('h')
    silence_frames = int(RATE * beat * 0.2)
    silence = array.array('h', [0] * silence_frames)

    for idx in melody:
        freq = _PENTA[idx % len(_PENTA)]
        combined.extend(_make_note(freq, beat * 0.8, waveform=wf))
        combined.extend(silence)

    try:
        snd = pygame.mixer.Sound(buffer=combined)
        snd.set_volume(0.35)
        return snd
    except Exception:
        return None


def start(theme_key: str):
    global _enabled, _current_sound, _current_channel
    stop()
    try:
        snd = _build_loop(theme_key)
        if snd is None:
            return
        _current_sound = snd
        _current_channel = snd.play(loops=-1)
        _enabled = True
    except Exception:
        pass


def stop():
    global _current_sound, _current_channel, _enabled
    if _current_channel:
        try:
            _current_channel.stop()
        except Exception:
            pass
        _current_channel = None
    _current_sound = None
    _enabled = False
