"""
主游戏场景（Week 4：主题系统 + 像素美术 + BGM）
"""
from __future__ import annotations
import random
import pygame
from game.config import SCREEN_W, SCREEN_H, TILE, COLS, ROWS, RESOURCE_COUNT, RESOURCE_GOAL, PLAYER_LIVES, GUARD_COUNT
from game import map_gen, sound, bgm, theme, sprites, fonts
from game.ai import AIController
from game.player import Player
from game.resource import Resource
from game.base import Base
from game.standoff import StandoffManager
from game.item import SmokeItem, SmokeCloud
from game.decoy import DecoyItem, Ghost
from game.barrier import BarrierItem, PlacedBarrier, try_place
from game.buff import BuffItem, magnet_radius
from game.guard import Guard, GUARD_INVINCIBLE_DUR

SMOKE_ITEM_COUNT   = 3
DECOY_ITEM_COUNT   = 2
BARRIER_ITEM_COUNT = 3
BUFF_TYPES         = ['speed', 'magnet', 'stealth']  # 各刷出 1 个


class GameScene:
    def __init__(self, seed: int = None, ai_difficulty: str | None = None):
        """
        ai_difficulty: None = 双人模式；'easy'/'normal'/'hard' = 单人 vs AI
        """
        self.seed = seed if seed is not None else random.randint(0, 99999)
        self.ai_difficulty = ai_difficulty
        self._build(self.seed)

    def _build(self, seed):
        self.grid, rooms = map_gen.generate(seed)
        floors = map_gen.floor_cells(self.grid)
        rng = random.Random(seed)

        # 主题
        self.theme = theme.pick(seed)
        theme_key = next(k for k, v in theme.THEMES.items() if v is self.theme)
        bgm.start(theme_key)

        sorted_rooms = sorted(rooms, key=lambda r: r[0] + r[1])
        r1, r2 = sorted_rooms[0], sorted_rooms[-1]
        cx1, cy1 = map_gen.room_center(r1)
        cx2, cy2 = map_gen.room_center(r2)

        C = self.theme
        self.p1 = Player(1, cx1*TILE+TILE//2, cy1*TILE+TILE//2,
                         C['p1'], C['trail1'],
                         {'up':pygame.K_w,'down':pygame.K_s,
                          'left':pygame.K_a,'right':pygame.K_d})
        self.p2 = Player(2, cx2*TILE+TILE//2, cy2*TILE+TILE//2,
                         C['p2'], C['trail2'],
                         {'up':pygame.K_UP,'down':pygame.K_DOWN,
                          'left':pygame.K_LEFT,'right':pygame.K_RIGHT})
        self.base1 = Base(cx1, cy1, 1, C['base1'])
        self.base2 = Base(cx2, cy2, 2, C['base2'])

        avoid = {(cx1,cy1),(cx2,cy2)}
        cands = [c for c in floors
                 if c not in avoid
                 and abs(c[0]-cx1)+abs(c[1]-cy1)>3
                 and abs(c[0]-cx2)+abs(c[1]-cy2)>3]
        rng.shuffle(cands)

        self.resources   = [Resource(c,r, C['resource'])
                            for c,r in cands[:RESOURCE_COUNT]]
        self.smoke_items = [SmokeItem(c,r)
                            for c,r in cands[RESOURCE_COUNT:RESOURCE_COUNT+SMOKE_ITEM_COUNT]]
        self.decoy_items = [DecoyItem(c,r)
                            for c,r in cands[RESOURCE_COUNT+SMOKE_ITEM_COUNT:
                                             RESOURCE_COUNT+SMOKE_ITEM_COUNT+DECOY_ITEM_COUNT]]
        off = RESOURCE_COUNT + SMOKE_ITEM_COUNT + DECOY_ITEM_COUNT
        self.barrier_items = [BarrierItem(c,r)
                              for c,r in cands[off:off+BARRIER_ITEM_COUNT]]
        off2 = off + BARRIER_ITEM_COUNT
        self.buff_items = [BuffItem(c, r, bt)
                           for bt, (c, r) in
                           zip(BUFF_TYPES, cands[off2:off2+len(BUFF_TYPES)])]
        self.smoke_clouds: list[SmokeCloud] = []
        self.ghosts: list[Ghost] = []
        self.placed_barriers: list[PlacedBarrier] = []
        self.standoff = StandoffManager()
        self.winner   = None

        # 守卫：排除双方出生房间
        spawn_rooms = [r for r in rooms if r not in (r1, r2)]
        rng.shuffle(spawn_rooms)
        self.guards: list[Guard] = [
            Guard(room, i, self.grid)
            for i, room in enumerate(spawn_rooms[:GUARD_COUNT])
        ]
        self.p1.lives = PLAYER_LIVES
        self.p2.lives = PLAYER_LIVES

        # AI
        if self.ai_difficulty:
            self.ai = AIController(self.ai_difficulty)
            self.p2.is_ai = True
        else:
            self.ai = None
        self._map_surf = self._render_map()
        self._font_sm  = fonts.get(20)
        self._frame    = 0

    # ── 地图渲染（预烘焙） ────────────────────────────────
    def _render_map(self):
        C = self.theme
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill(C['bg'])
        for row in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c*TILE, row*TILE, TILE, TILE)
                if self.grid[row][c] == 1:
                    sprites.draw_wall_tile(surf, rect,
                                           C['wall'], C['wall_hi'],
                                           row*COLS+c)
                else:
                    sprites.draw_floor_tile(surf, rect, C['floor'], C['grid'])
        return surf

    # ── 触屏更新（P1 移动已由外部处理，此处只跑 P2/道具/胜负）──
    def update_touch(self, events) -> int | None:
        """触屏模式：P1 移动已在 main.py 中通过 ai_update 完成，
        这里只处理 AI(P2)、道具更新、胜负判定。"""
        # 传空 keys 给 update，P1 已移动完毕，内部会 skip P1 键盘
        class _FakeKeys(dict):
            def __getitem__(self, k): return False
        return self._update_internal(_FakeKeys(), events, skip_p1=True)

    # ── 更新 ─────────────────────────────────────────────
    def update(self, keys, events) -> int | None:
        return self._update_internal(keys, events, skip_p1=False)

    def _update_internal(self, keys, events, skip_p1=False) -> int | None:
        if self.winner:
            return self.winner

        self._frame += 1

        self.p1.in_smoke = any(sc.covers(self.p1.x,self.p1.y) for sc in self.smoke_clouds)
        self.p2.in_smoke = any(sc.covers(self.p2.x,self.p2.y) for sc in self.smoke_clouds)

        bs = self.placed_barriers  # 简称
        if not skip_p1:
            self.p1.update(keys, self.grid, bs)

        if self.ai:
            dx, dy = self.ai.step(self.p2, self.p1, self.base2,
                                  self.resources, self.smoke_items,
                                  self.decoy_items, self.grid)
            self.p2.ai_update(dx, dy, self.grid, bs)
            if self.p2._ai_use_smoke:
                self.p2._ai_use_smoke = False
                if self.p2.smoke_count > 0:
                    self.p2.smoke_count -= 1
                    self.smoke_clouds.append(SmokeCloud(self.p2.x, self.p2.y))
                    sound.play('smoke')
            if self.p2._ai_use_decoy:
                self.p2._ai_use_decoy = False
                if self.p2.decoy_count > 0:
                    self.p2.decoy_count -= 1
                    self.ghosts.append(Ghost(self.p2.x, self.p2.y,
                                            self.theme['trail2'], self.grid))
                    sound.play('decoy')
            if self.p2._ai_use_barrier:
                self.p2._ai_use_barrier = False
                b = try_place(self.p2, bs, self.grid)
                if b:
                    bs.append(b)
                    sound.play('barrier')
        else:
            self.p2.update(keys, self.grid, bs)

        for event in events:
            if event.type == pygame.KEYDOWN:
                # 烟雾
                if event.key == pygame.K_f and self.p1.smoke_count > 0:
                    self.p1.smoke_count -= 1
                    self.smoke_clouds.append(SmokeCloud(self.p1.x, self.p1.y))
                    sound.play('smoke')
                if event.key == pygame.K_PERIOD and self.p2.smoke_count > 0:
                    self.p2.smoke_count -= 1
                    self.smoke_clouds.append(SmokeCloud(self.p2.x, self.p2.y))
                    sound.play('smoke')
                # 假信号
                if event.key == pygame.K_g and self.p1.decoy_count > 0:
                    self.p1.decoy_count -= 1
                    self.ghosts.append(Ghost(self.p1.x, self.p1.y,
                                            self.theme['trail1'], self.grid))
                    sound.play('decoy')
                if event.key == pygame.K_SLASH and self.p2.decoy_count > 0:
                    self.p2.decoy_count -= 1
                    self.ghosts.append(Ghost(self.p2.x, self.p2.y,
                                            self.theme['trail2'], self.grid))
                    sound.play('decoy')
                # 障碍物
                if event.key == pygame.K_h:
                    b = try_place(self.p1, bs, self.grid)
                    if b:
                        bs.append(b)
                        sound.play('barrier')
                if event.key == pygame.K_SEMICOLON and not self.ai:
                    b = try_place(self.p2, bs, self.grid)
                    if b:
                        bs.append(b)
                        sound.play('barrier')

        for item in self.smoke_items:
            item.update()
            if item.check_pickup(self.p1) or item.check_pickup(self.p2):
                sound.play('pickup')
        for item in self.decoy_items:
            item.update()
            if item.check_pickup(self.p1) or item.check_pickup(self.p2):
                sound.play('pickup')
        for item in self.barrier_items:
            item.update()
            if item.check_pickup(self.p1) or item.check_pickup(self.p2):
                sound.play('pickup')

        # 增益道具拾取
        for item in self.buff_items:
            item.update()
            if item.check_pickup(self.p1) or item.check_pickup(self.p2):
                sound.play('buff')

        # 磁力：自动拾取范围内碎片
        for player in (self.p1, self.p2):
            mr = magnet_radius(player)
            if mr > 0 and not player.carrying:
                import math as _math
                for res in self.resources:
                    if res.alive and _math.hypot(player.x - res.x,
                                                  player.y - res.y) < mr:
                        res.alive = False
                        player.carrying = True
                        sound.play('pickup')
                        break

        # 障碍物生命周期
        for b in self.placed_barriers: b.update()
        self.placed_barriers = [b for b in self.placed_barriers if b.alive]

        for sc in self.smoke_clouds: sc.update()
        self.smoke_clouds = [sc for sc in self.smoke_clouds if sc.alive]
        for g in self.ghosts: g.update()
        self.ghosts = [g for g in self.ghosts if g.alive]

        # 守卫更新
        for guard in self.guards:
            caught, entered_chase = guard.update(
                [self.p1, self.p2], self.grid, self.placed_barriers)
            if entered_chase:
                sound.play('guard_alert')
            for player in caught:
                self._on_guard_catch(player)

        standoff_res = self.standoff.resource if self.standoff.active else None
        winner_pid, won_res = self.standoff.update(self.p1, self.p2, self.resources)
        if winner_pid and won_res:
            p = self.p1 if winner_pid == 1 else self.p2
            if not p.carrying:
                won_res.alive = False
                p.carrying = True
                sound.play('pickup')

        for res in self.resources:
            if res is standoff_res: continue
            res.update()
            if res.check_pickup(self.p1) or res.check_pickup(self.p2):
                sound.play('pickup')

        self.base1.update()
        self.base2.update()
        if self.base1.check_deposit(self.p1):
            sound.play('deposit')
            if self.p1.score >= RESOURCE_GOAL:
                self.winner = 1; sound.play('win')
        if self.base2.check_deposit(self.p2):
            sound.play('deposit')
            if self.p2.score >= RESOURCE_GOAL:
                self.winner = 2; sound.play('win')

        return self.winner

    def _on_guard_catch(self, player):
        """守卫捕捉玩家：扣血、掉落碎片、传送回基地、短暂无敌。"""
        sound.play('guard_catch')
        if player.carrying:
            player.carrying = False
            tc = int(player.x // TILE)
            tr = int(player.y // TILE)
            self.resources.append(Resource(tc, tr, self.theme['resource']))
        player.lives -= 1
        base = self.base1 if player.pid == 1 else self.base2
        player.x = float(base.x)
        player.y = float(base.y)
        player.invincible_timer = GUARD_INVINCIBLE_DUR
        if player.lives <= 0:
            self.winner = 2 if player.pid == 1 else 1
            sound.play('win')

    # ── 渲染 ─────────────────────────────────────────────
    def draw(self, surface):
        surface.blit(self._map_surf, (0, 0))
        self.base1.draw(surface)
        self.base2.draw(surface)
        for res in self.resources: res.draw(surface)
        for item in self.smoke_items: item.draw(surface)
        for item in self.decoy_items: item.draw(surface)
        for item in self.barrier_items: item.draw(surface)
        for b in self.placed_barriers: b.draw(surface)
        for item in self.buff_items: item.draw(surface)
        for sc in self.smoke_clouds: sc.draw(surface)
        for g in self.ghosts: g.draw(surface)
        self.standoff.draw(surface)
        for guard in self.guards:
            guard.draw(surface)
        self.p1.draw(surface)
        self.p2.draw(surface)
        self._draw_hud(surface)

    def _draw_hud(self, surface):
        C = self.theme
        font = fonts.get(28)

        from game.buff import BUFF_CONFIGS
        def inv(p):
            lives_str = "♥" * max(0, p.lives) + "♡" * max(0, PLAYER_LIVES - p.lives)
            parts = [f"P{p.pid}  {p.score}/{RESOURCE_GOAL}  {lives_str}"]
            if p.carrying:      parts.append("【碎片】")
            if p.smoke_count:   parts.append(f"烟×{p.smoke_count}")
            if p.decoy_count:   parts.append(f"诱×{p.decoy_count}")
            if p.barrier_count: parts.append(f"障×{p.barrier_count}")
            for b in p.buffs:
                parts.append(BUFF_CONFIGS[b.buff_type]['desc'])
            return "  ".join(parts)

        t1 = font.render(inv(self.p1), True, C['p1'])
        t2 = font.render(inv(self.p2), True, C['p2'])
        surface.blit(t1, (10, 8))
        surface.blit(t2, (SCREEN_W - t2.get_width() - 10, 8))

        h1 = self._font_sm.render("WASD  F烟雾  G假信号  H障碍", True,
                                   tuple(c//2 for c in C['p1']))
        h2 = self._font_sm.render("↑↓←→  .烟雾  /假信号  ;障碍", True,
                                   tuple(c//2 for c in C['p2']))
        surface.blit(h1, (10, 34))
        surface.blit(h2, (SCREEN_W - h2.get_width() - 10, 34))

        theme_t = self._font_sm.render(
            f"主题：{C['name']}  seed:{self.seed}", True, (80,80,100))
        surface.blit(theme_t, (SCREEN_W//2 - theme_t.get_width()//2, 10))

    def restart(self, new_seed=None):
        bgm.stop()
        seed = new_seed if new_seed is not None else random.randint(0, 99999)
        self.seed = seed
        self._build(seed)
