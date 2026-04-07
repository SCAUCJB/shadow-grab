from __future__ import annotations
import math
import pygame
from game.config import SCREEN_W, SCREEN_H, C_P1, C_P2, C_BG, C_TEXT
from game.theme import all_names
from game import fonts

MATCH_WIN = 2


class ModeSelectScreen:
    MODES = [
        ('双人对战',  '2p',  None,     "P1 vs P2  — 同一键盘热座"),
        ('单人 简单', '1p',  'easy',   "AI 速度 55%，不会拦截"),
        ('单人 普通', '1p',  'normal', "AI 速度 75%，会拦截"),
        ('单人 困难', '1p',  'hard',   "AI 速度 92%，主动拦截+用道具"),
    ]

    def __init__(self):
        self._t   = 0
        self._sel = 0

    def update(self):
        self._t += 1

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2

        title = fonts.get(80).render("SHADOW GRAB", True, (200, 200, 220))
        sub   = fonts.get(32).render("暗  夺", True, (130, 130, 170))
        surface.blit(title, (cx - title.get_width() // 2, 55))
        surface.blit(sub,   (cx - sub.get_width() // 2,  145))

        base_y = 225
        for i, (label, _, _, desc) in enumerate(self.MODES):
            selected = (i == self._sel)
            pulse = abs(math.sin(self._t * 0.06)) if selected else 0
            col = (int(200 + 55 * pulse), int(200 + 55 * pulse), 100) \
                  if selected else (120, 120, 140)

            item_y = base_y + i * 72
            if selected:
                bar = pygame.Surface((420, 58), pygame.SRCALPHA)
                bar.fill((255, 255, 100, int(60 * pulse)))
                surface.blit(bar, (cx - 210, item_y - 4))
                pygame.draw.rect(surface, col,
                                 pygame.Rect(cx - 210, item_y - 4, 420, 58),
                                 2, border_radius=6)

            lbl = fonts.get(30).render(label, True, col)
            surface.blit(lbl, (cx - lbl.get_width() // 2, item_y))
            dsc = fonts.get(18).render(desc, True, (100, 100, 120))
            surface.blit(dsc, (cx - dsc.get_width() // 2, item_y + 32))

        hint = fonts.get(20).render("↑ ↓ 选择    空格 确认", True, (90, 90, 110))
        surface.blit(hint, (cx - hint.get_width() // 2,
                            base_y + len(self.MODES) * 72 + 18))

        theme_str = " / ".join(all_names())
        ts = fonts.get(16).render(f"地图主题随机：{theme_str}", True, (70, 70, 90))
        surface.blit(ts, (cx - ts.get_width() // 2, SCREEN_H - 28))

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._sel = (self._sel - 1) % len(self.MODES)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._sel = (self._sel + 1) % len(self.MODES)
            if event.key == pygame.K_SPACE:
                _, mode, diff, _ = self.MODES[self._sel]
                return (mode, diff)
        return None


class RoundEndScreen:
    def __init__(self, round_winner: int, match_score: list[int],
                 ai_mode: bool = False):
        self.round_winner = round_winner
        self.match_score  = match_score
        self.ai_mode      = ai_mode
        self._t           = 0
        self.match_over   = max(match_score) >= MATCH_WIN

    def update(self):
        self._t += 1

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        cx    = SCREEN_W // 2
        color = C_P1 if self.round_winner == 1 else C_P2

        if self.match_over:
            winner = 1 if self.match_score[0] >= MATCH_WIN else 2
            w_label = ("你赢了！" if winner == 1 else "AI 胜出！") \
                      if self.ai_mode else f"Player {winner}  总冠军！"
            msg = fonts.get(64).render(w_label, True,
                                        C_P1 if winner == 1 else C_P2)
            sub = fonts.get(26).render("空格 = 重新开始    Q = 退出", True, C_TEXT)
        else:
            w_label = ("你赢得本局！" if self.round_winner == 1 else "AI 赢得本局") \
                      if self.ai_mode else f"Player {self.round_winner}  赢得本局"
            msg = fonts.get(64).render(w_label, True, color)
            sub = fonts.get(26).render("空格 = 下一局    Q = 退出", True, C_TEXT)

        p2_label = "AI" if self.ai_mode else "P2"
        score_txt = fonts.get(40).render(
            f"P1  {self.match_score[0]}  :  {self.match_score[1]}  {p2_label}",
            True, C_TEXT)

        surface.blit(msg,       (cx - msg.get_width() // 2,       SCREEN_H // 2 - 80))
        surface.blit(score_txt, (cx - score_txt.get_width() // 2, SCREEN_H // 2))
        surface.blit(sub,       (cx - sub.get_width() // 2,       SCREEN_H // 2 + 80))

    def handle(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return 'next'
            if event.key == pygame.K_q:
                return 'quit'
        return None
