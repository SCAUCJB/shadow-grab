"""
虚拟摇杆 + 操作按钮（手机/平板触屏用）

布局：
  左下角：虚拟摇杆（控制移动方向）
  右下角：操作按钮（烟雾 / 假信号 / 障碍物）

检测逻辑：使用 pygame 鼠标/触摸事件，pygbag 会将手指事件映射为鼠标事件。
"""
from __future__ import annotations
import math
import pygame
from game import fonts
from game.config import SCREEN_W, SCREEN_H

# ── 布局常量 ──────────────────────────────────────────────
JOY_CX     = 110
JOY_CY     = SCREEN_H - 110
JOY_RADIUS = 70       # 底盘半径
KNOB_RADIUS = 28      # 摇杆球半径

BTN_RADIUS  = 32
_BTN_DEFS = [
    # (label, key_attr,  cx,               cy,              color)
    ('烟',  'smoke',  SCREEN_W - 210,  SCREEN_H - 70,  (130, 130, 145)),
    ('诱',  'decoy',  SCREEN_W - 140,  SCREEN_H - 140, (180, 110, 220)),
    ('障',  'barrier',SCREEN_W - 70,   SCREEN_H - 70,  (200, 120, 40)),
]


class VirtualJoystick:
    def __init__(self):
        self.active    = False
        self._touch_id = None   # 追踪同一个手指
        self.knob_x    = float(JOY_CX)
        self.knob_y    = float(JOY_CY)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if math.hypot(mx - JOY_CX, my - JOY_CY) < JOY_RADIUS + 20:
                self.active = True
                self._update_knob(mx, my)
        elif event.type == pygame.MOUSEMOTION and self.active:
            if event.buttons[0]:
                self._update_knob(*event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active:
                self.active = False
                self.knob_x = float(JOY_CX)
                self.knob_y = float(JOY_CY)

    def _update_knob(self, mx, my):
        dx = mx - JOY_CX
        dy = my - JOY_CY
        dist = math.hypot(dx, dy)
        if dist > JOY_RADIUS:
            dx = dx / dist * JOY_RADIUS
            dy = dy / dist * JOY_RADIUS
        self.knob_x = JOY_CX + dx
        self.knob_y = JOY_CY + dy

    def direction(self) -> tuple[float, float]:
        """返回归一化方向 (dx, dy)，范围 [-1, 1]"""
        if not self.active:
            return 0.0, 0.0
        dx = (self.knob_x - JOY_CX) / JOY_RADIUS
        dy = (self.knob_y - JOY_CY) / JOY_RADIUS
        mag = math.hypot(dx, dy)
        if mag < 0.1:
            return 0.0, 0.0
        return dx, dy

    def draw(self, surface):
        # 底盘
        s = pygame.Surface((JOY_RADIUS * 2 + 20, JOY_RADIUS * 2 + 20),
                           pygame.SRCALPHA)
        c = (40, 40, 40)
        pygame.draw.circle(s, (*c, 120),
                           (JOY_RADIUS + 10, JOY_RADIUS + 10), JOY_RADIUS)
        pygame.draw.circle(s, (100, 100, 100, 160),
                           (JOY_RADIUS + 10, JOY_RADIUS + 10), JOY_RADIUS, 3)
        surface.blit(s, (JOY_CX - JOY_RADIUS - 10,
                         JOY_CY - JOY_RADIUS - 10))
        # 摇杆球
        ks = pygame.Surface((KNOB_RADIUS * 2 + 4, KNOB_RADIUS * 2 + 4),
                            pygame.SRCALPHA)
        kc = (200, 200, 220) if self.active else (160, 160, 180)
        pygame.draw.circle(ks, (*kc, 200),
                           (KNOB_RADIUS + 2, KNOB_RADIUS + 2), KNOB_RADIUS)
        pygame.draw.circle(ks, (220, 220, 240, 255),
                           (KNOB_RADIUS + 2, KNOB_RADIUS + 2), KNOB_RADIUS, 2)
        surface.blit(ks, (int(self.knob_x) - KNOB_RADIUS - 2,
                          int(self.knob_y) - KNOB_RADIUS - 2))


class ActionButton:
    def __init__(self, label, key_attr, cx, cy, color):
        self.label    = label
        self.key_attr = key_attr   # 对应 player 的 xxx_count 属性
        self.cx = cx
        self.cy = cy
        self.color = color
        self.pressed  = False      # 本帧是否被触发
        self._held    = False

    def handle_event(self, event):
        """返回 True 表示本次点击触发了该按钮"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if math.hypot(event.pos[0] - self.cx,
                          event.pos[1] - self.cy) < BTN_RADIUS:
                self._held   = True
                self.pressed = True
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._held = False
        return False

    def reset(self):
        self.pressed = False

    def draw(self, surface, player):
        count = getattr(player, f'{self.key_attr}_count', 0)
        # 外圈（有道具时亮，无道具时暗）
        alpha = 200 if count > 0 else 80
        s = pygame.Surface((BTN_RADIUS * 2 + 4, BTN_RADIUS * 2 + 4),
                           pygame.SRCALPHA)
        col = self.color if count > 0 else (80, 80, 80)
        pygame.draw.circle(s, (*col, alpha),
                           (BTN_RADIUS + 2, BTN_RADIUS + 2), BTN_RADIUS)
        border = (220, 220, 220) if self._held else (160, 160, 160)
        pygame.draw.circle(s, (*border, 200),
                           (BTN_RADIUS + 2, BTN_RADIUS + 2), BTN_RADIUS, 3)
        surface.blit(s, (self.cx - BTN_RADIUS - 2,
                         self.cy - BTN_RADIUS - 2))
        # 标签
        lbl = fonts.get(18).render(self.label, True,
                                    (230, 230, 230) if count > 0 else (100, 100, 100))
        surface.blit(lbl, (self.cx - lbl.get_width() // 2,
                           self.cy - lbl.get_height() // 2 - 6))
        if count > 0:
            cnt = fonts.get(14).render(f'×{count}', True, (200, 200, 200))
            surface.blit(cnt, (self.cx - cnt.get_width() // 2,
                               self.cy + 8))


class TouchControls:
    """组合虚拟摇杆 + 三个操作按钮"""

    def __init__(self):
        self.joystick = VirtualJoystick()
        self.buttons  = [ActionButton(*d) for d in _BTN_DEFS]

    def handle_events(self, events) -> list[str]:
        """返回本帧触发的 key_attr 列表（如 ['smoke']）"""
        triggered = []
        self.joystick.handle_event.__func__  # 确认方法存在
        for event in events:
            self.joystick.handle_event(event)
            for btn in self.buttons:
                if btn.handle_event(event):
                    triggered.append(btn.key_attr)
        return triggered

    def reset_buttons(self):
        for btn in self.buttons:
            btn.reset()

    def draw(self, surface, player):
        self.joystick.draw(surface)
        for btn in self.buttons:
            btn.draw(surface, player)

    def direction(self):
        return self.joystick.direction()
