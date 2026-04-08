# 屏幕与网格
SCREEN_W = 960
SCREEN_H = 640
TILE = 32                  # 每格像素
COLS = SCREEN_W // TILE    # 30 列
ROWS = SCREEN_H // TILE    # 20 行

FPS = 60

# 颜色
C_BG        = (18,  18,  24)
C_WALL      = (60,  60,  80)
C_FLOOR     = (30,  30,  42)
C_GRID      = (36,  36,  50)
C_P1        = (80,  200, 255)   # 蓝
C_P2        = (255, 100, 80)    # 红
C_TRAIL1    = (40,  100, 140)
C_TRAIL2    = (140, 50,  40)
C_RESOURCE  = (255, 220, 60)
C_BASE1     = (40,  140, 200)
C_BASE2     = (200, 70,  50)
C_TEXT      = (220, 220, 220)
C_HIGHLIGHT = (255, 255, 255)

# 玩家
PLAYER_SPEED  = 3           # 像素/帧（平滑移动）
PLAYER_RADIUS = 10

# 痕迹
TRAIL_MAX_LEN  = 80         # 最多保留帧数
TRAIL_FADE_PER = 3          # 每帧淡出量（0-255）

# 资源
RESOURCE_COUNT = 8          # 每局资源数
RESOURCE_RADIUS = 7
RESOURCE_GOAL   = 4         # 收集几个碎片胜利

# 基地
BASE_RADIUS = 20

# 生命值
PLAYER_LIVES = 3

# 守卫
GUARD_COUNT = 2
