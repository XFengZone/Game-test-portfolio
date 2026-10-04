import os
# paddlepaddle 3.3.1 的 oneDNN 路径不支持 PP-OCRv6 模型，关掉走普通 CPU 路径
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")
from airtest.core.settings import Settings as ST

GAME_TITLE="崩坏：星穹铁道"
WINDOW_WIDTH=1600
WINDOW_HEIGHT=900

X_LEFT=1264
X_RIGHT=1436
Y=220

#只保留纯模板匹配，禁用特征点匹配(sift/brisk)兜底
ST.CVSTRATEGY = ["mstpl", "tpl"]

# ── 帧率识别配置 ──────────────────────────────────────────
# 帧率数字在窗口客户区里的位置 (x1, y1, x2, y2)，坐标系 1600x900
FPS_ROI = (456, 29, 480, 49)
FPS_SAT_MIN = 60           #OCR饱和度，小于该饱和度值的数字字母被过滤
FPS_UPSCALE = 4            #截图后的放大倍数
FPS_SAMPLE_COUNT = 10      #采样数
FPS_SAMPLE_INTERVAL = 0.15 #采样间隔时间，单位：秒
FPS_TOL_RATIO = 0.10       #容错率
# ── 音量验证配置 ──────────────────────────────────────────
VOLUME_RECORD_SECONDS = 2.5          # 每次录多久（要覆盖平A那一下）
VOLUME_SILENCE_DBFS = -55.0          # 音量0的静音判据，必须小于这个值。-80可能误报，某些游戏的音量滑条在 0 档仍允许有微弱底噪。-30抓不到BGM残留
VOLUME_MIN_DYNAMIC_RANGE_DB = 25.0   # 最大值与最小值的差必须大于这个值。区分"完全失效"（0~2 dB）与"正常工作"（143 dB）
