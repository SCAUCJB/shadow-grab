#!/usr/bin/env python3
"""
Shadow Grab — 暗夺

PC：键盘操作（双人热座 / 单人 vs AI）
手机/平板：虚拟摇杆 + 按钮（强制单人 vs AI）

Pygbag 兼容：async main + asyncio.sleep(0) 每帧让出控制权
"""
import sys
import asyncio
import pygame

from game.config import SCREEN_W, SCREEN_H, FPS
from game import sound, bgm
from game.scene import GameScene
from game.ui import ModeSelectScreen, RoundEndScreen, MATCH_WIN
from game.touch import TouchControls
from game.item import SmokeCloud
from game.decoy import Ghost
from game.barrier import try_place

STATE_MODE_SELECT = 'mode_select'
STATE_PLAYING     = 'playing'
STATE_ROUND_END   = 'round_end'

# ── 触控道具触发处理 ──────────────────────────────────────

def _handle_touch_actions(triggered: list[str], scene):
    """将虚拟按钮触发映射为道具使用"""
    p = scene.p1
    if 'smoke' in triggered and p.smoke_count > 0:
        p.smoke_count -= 1
        scene.smoke_clouds.append(SmokeCloud(p.x, p.y))
        sound.play('smoke')
    if 'decoy' in triggered and p.decoy_count > 0:
        p.decoy_count -= 1
        scene.ghosts.append(
            Ghost(p.x, p.y, scene.theme['trail1'], scene.grid))
        sound.play('decoy')
    if 'barrier' in triggered and p.barrier_count > 0:
        b = try_place(p, scene.placed_barriers, scene.grid)
        if b:
            scene.placed_barriers.append(b)
            sound.play('barrier')


# ── 主循环 ────────────────────────────────────────────────

async def main():
    pygame.init()
    sound.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Shadow Grab — 暗夺")
    clock = pygame.time.Clock()

    # 检测是否为触屏模式（pygbag 环境 or 无法用键盘）
    # 通过平台标志判断：pygbag 设置 sys.platform = 'emscripten'
    is_touch = (getattr(sys, 'platform', '') == 'emscripten')

    state       = STATE_MODE_SELECT
    mode_scr    = ModeSelectScreen()
    scene       = None
    round_scr   = None
    match_score = [0, 0]
    ai_diff     = 'normal'   # 触屏默认普通难度

    touch = TouchControls()

    # 触屏模式：跳过模式选择，直接进入单人普通
    if is_touch:
        scene = GameScene(ai_difficulty='normal')
        state = STATE_PLAYING

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                bgm.stop(); pygame.quit(); sys.exit()

        # ── 模式选择（仅 PC）────────────────────────────
        if state == STATE_MODE_SELECT:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    bgm.stop(); pygame.quit(); sys.exit()
                result = mode_scr.handle(event)
                if result:
                    mode, diff = result
                    ai_diff = diff
                    match_score = [0, 0]
                    scene = GameScene(ai_difficulty=diff)
                    state = STATE_PLAYING

            mode_scr.update()
            mode_scr.draw(screen)

        # ── 游戏中 ───────────────────────────────────────
        elif state == STATE_PLAYING:
            if is_touch:
                # 触屏：摇杆方向 → P1 移动
                triggered = touch.handle_events(events)
                _handle_touch_actions(triggered, scene)
                touch.reset_buttons()

                dx_raw, dy_raw = touch.direction()
                from game.config import PLAYER_SPEED
                p1_dx = dx_raw * PLAYER_SPEED
                p1_dy = dy_raw * PLAYER_SPEED
                scene.p1.ai_update(p1_dx, p1_dy, scene.grid,
                                   scene.placed_barriers)
                # 更新场景（跳过 P1 键盘移动，传空 keys）
                winner = scene.update_touch(events)
            else:
                keys = pygame.key.get_pressed()
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            bgm.stop(); pygame.quit(); sys.exit()
                        if event.key == pygame.K_r:
                            scene.restart()
                winner = scene.update(keys, events)

            scene.draw(screen)

            if is_touch:
                touch.draw(screen, scene.p1)

            if winner:
                match_score[winner - 1] += 1
                round_scr = RoundEndScreen(
                    winner, match_score[:],
                    ai_mode=(ai_diff is not None))
                state = STATE_ROUND_END

        # ── 局间结算 ─────────────────────────────────────
        elif state == STATE_ROUND_END:
            if scene:
                scene.draw(screen)
                if is_touch:
                    touch.draw(screen, scene.p1)
            round_scr.update()
            round_scr.draw(screen)

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    bgm.stop(); pygame.quit(); sys.exit()
                result = round_scr.handle(event)
                # 触屏：点击屏幕中央继续
                if is_touch and event.type == pygame.MOUSEBUTTONDOWN:
                    result = 'next'
                if result == 'next':
                    if max(match_score) >= MATCH_WIN:
                        bgm.stop()
                        match_score = [0, 0]
                        if is_touch:
                            scene = GameScene(ai_difficulty=ai_diff)
                            state = STATE_PLAYING
                        else:
                            mode_scr = ModeSelectScreen()
                            state = STATE_MODE_SELECT
                    else:
                        scene = GameScene(ai_difficulty=ai_diff)
                        state = STATE_PLAYING
                elif result == 'quit':
                    bgm.stop(); pygame.quit(); sys.exit()

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)   # 让出控制权给浏览器（pygbag 必须）


asyncio.run(main())
