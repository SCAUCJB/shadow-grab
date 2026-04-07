"""
程序化 BGM：用 numpy 合成五声音阶循环旋律。
每个主题有不同的速度和音色风格。
若 numpy 不可用则静默跳过。
"""
import threading
import pygame

_enabled = False
try:
    import numpy as np
    _enabled = True
except ImportError:
    pass

RATE = 44100
_playing = False
_stop_evt = threading.Event()
_thread = None

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


def _make_note(freq: float, dur: float, waveform='square', vol=0.08):
    frames = int(RATE * dur)
    t = np.linspace(0, dur, frames, endpoint=False)
    if waveform == 'square':
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    elif waveform == 'tri':
        wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:
        wave = np.sin(2 * np.pi * freq * t)
    # 包络（防爆音）
    attack = min(int(RATE * 0.01), frames // 4)
    release = min(int(RATE * 0.05), frames // 4)
    env = np.ones(frames)
    env[:attack] = np.linspace(0, 1, attack)
    env[-release:] = np.linspace(1, 0, release)
    wave = (wave * env * vol * 32767).astype(np.int16)
    return wave


def _bgm_loop(theme_key: str):
    melody = _MELODIES.get(theme_key, _MELODIES['dungeon'])
    bpm    = _BPM.get(theme_key, 100)
    beat   = 60.0 / bpm
    wf     = 'square' if theme_key in ('dungeon', 'lava') else 'tri'

    # 合成一整段循环
    notes = []
    for idx in melody:
        freq = _PENTA[idx % len(_PENTA)]
        notes.append(_make_note(freq, beat * 0.8, waveform=wf))
        notes.append(np.zeros(int(RATE * beat * 0.2), dtype=np.int16))
    loop_wave = np.concatenate(notes)

    sound = pygame.sndarray.make_sound(loop_wave)
    sound.set_volume(0.35)
    ch = sound.play(loops=-1)

    _stop_evt.wait()   # 阻塞直到 stop() 被调用
    if ch:
        ch.stop()


def start(theme_key: str):
    global _playing, _thread, _stop_evt
    if not _enabled:
        return
    stop()
    _stop_evt = threading.Event()
    _thread = threading.Thread(target=_bgm_loop, args=(theme_key,), daemon=True)
    _playing = True
    _thread.start()


def stop():
    global _playing
    if not _enabled:
        return
    _stop_evt.set()
    _playing = False
