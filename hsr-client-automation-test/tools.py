import win32gui

import time
from airtest.core.api import *
import statistics
import threading

import cv2
import numpy as np

import config

class WindowTools:
    @staticmethod
    def move_and_fix_window(title, width, height):
        """将窗口移动到左上角(0,0)并固定大小"""
        hwnd = win32gui.FindWindow(None, title)
        hwnd = win32gui.FindWindow(None, title)
        if hwnd != 0:
            print(f"实际找到的窗口标题是: [{win32gui.GetWindowText(hwnd)}]")
        if hwnd == 0:
            print(f"未找到标题为 [{title}] 的窗口，请检查游戏是否已打开")
            return False

        try:
            win32gui.MoveWindow(hwnd, 0, 0, width, height, True)
            print(f"成功将游戏窗口固定到(0, 0)，大小: {width}x{height}")
            time.sleep(1)  # 给窗口一点时间渲染
            return True
        except Exception as e:
            print(f"移动窗口失败: {e}")
            return False

    @staticmethod
    def press_and_hold(key:str,duration:float):
        """
        模拟键盘输入，如按下ESC，或长按->加速快进5秒
        :param key: 具体按键名称，详情可见Airtest官方文档
        :param duration: 按下具体按键的持续时间
        :return:
        """
        win=device()
        win.key_press(key)
        sleep(duration)
        win.key_release(key)
        sleep(0.5)
    @staticmethod
    def enter_setting():
        """进入游戏设置菜单"""
        WindowTools.press_and_hold("ESCAPE", 0)
        sleep(1.0)
        # 点击设置按钮，进入到设置界面
        touch(Template("images/setting_image.png", threshold=0.8))
        sleep(1.0)
    @staticmethod
    def return_from_setting_menu():
        """从游戏设置菜单中退出到游戏主界面"""
        WindowTools.press_and_hold("ESCAPE", 0)
        sleep(1.0)
        WindowTools.press_and_hold("ESCAPE", 0)
        sleep(1.0)
    @staticmethod
    def set_volume(x_left: int, x_right: int, y: int, target_volume: int):
        """
        使用相对坐标设置音量
        :param x_left: 滑动条最左侧 X 坐标 (音量0)
        :param x_right: 滑动条最右侧 X 坐标 (音量10)
        :param y: 滑动条 Y 坐标
        :param target_volume: 目标音量 (0-10)
        """
        if not 0 <= target_volume <= 10:
            print(f"目标音量 {target_volume} 超出范围 (0-10)")
            return

        # 计算数学映射:音量10对应x_right，音量0对应x_left
        target_x = int(x_left + (x_right - x_left) * (target_volume / 10.0))

        print(f"设置音量为 {target_volume}，目标坐标: ({target_x}, {y})")
        #直接点击轨道的对应位置
        touch((target_x, y))
        sleep(0.5)


# ── OCR 单例：初始化要 4~5 秒，全进程只初始化一次 ──────────────────────
_OCR_ENGINE = None

def _get_ocr():
    """
    懒加载 PaddleOCR。
    import 刻意放在函数内部：必须在 config 设置好 FLAGS_use_mkldnn 之后
    才导入 paddleocr，否则 oneDNN 报错路径又会被启用。
    """
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        from paddleocr import PaddleOCR
        _OCR_ENGINE = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
    return _OCR_ENGINE


def _extract_digits_image(screen, debug=False):
    """
    裁剪 ROI -> 按【饱和度】过滤出彩色数字 -> 放大4倍
    为什么用饱和度而不是色相:
      帧率数字会变色 —— 跑满60帧显示【绿色】，未跑满(59/56)显示【黄色】。
      若只按"黄色(R-B>40)"过滤，绿色的60会被整块丢掉，
      导致采样到的全是掉帧数据、中位数被压低 -> 断言误报失败。
      绿和黄共同点是高饱和，而 FPS/CPU/GPU 标签是灰白(低饱和)，
      所以用 HSV 的 S 通道可以把"彩色数字"和"灰白标签"分开。
    """
    x1, y1, x2, y2 = config.FPS_ROI
    roi = screen[y1:y2, x1:x2]
    if roi.size == 0:
        raise ValueError(f"FPS ROI {config.FPS_ROI} 超出画面范围")

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    mask = s_channel > config.FPS_SAT_MIN

    if int(mask.sum()) == 0:
        raise ValueError(
            f"FPS ROI {config.FPS_ROI} 内没有高饱和像素(阈值{config.FPS_SAT_MIN}) — "
            f"帧率显示未开启 / ROI 坐标偏了 / 游戏配色变化"
        )

    out = np.zeros_like(roi)
    out[mask] = roi[mask]

    if debug:
        px = roi[mask].astype(np.int16)
        b, g, r = float(px[:, 0].mean()), float(px[:, 1].mean()), float(px[:, 2].mean())
        if g > r and g > b:
            color = "绿色(跑满了)"
        elif r > b and g > b:
            color = "黄色(未跑满)"
        else:
            color = f"其他(BGR≈{b:.0f},{g:.0f},{r:.0f})"
        print(f"[FPS调试] 命中{int(mask.sum())}像素 平均BGR=({b:.0f},{g:.0f},{r:.0f}) "
              f"-> {color} 饱和度均值={float(s_channel[mask].mean()):.0f}")

    return cv2.resize(out, None, fx=config.FPS_UPSCALE, fy=config.FPS_UPSCALE,
                      interpolation=cv2.INTER_CUBIC)

def _recognize(image):
    """OCR 识别小图，返回 (纯数字字符串, 原始文本)"""
    texts = []
    for item in _get_ocr().predict(image):
        data = item if isinstance(item, dict) else getattr(item, "json", {})
        if isinstance(data, dict) and "res" in data:
            data = data["res"]
        if isinstance(data, dict):
            texts.extend(data.get("rec_texts", []) or [])
    raw = "".join(str(t) for t in texts)
    return "".join(ch for ch in raw if ch.isdigit()), raw


def read_fps(debug=False):
    """读一次当前帧率。失败抛异常，不返回 None"""
    digits, raw = _recognize(_extract_digits_image(G.DEVICE.snapshot(), debug=debug))
    if not digits:
        raise ValueError(f"FPS 识别失败: OCR 输出={raw!r}")
    return int(digits)


def sample_fps(count=None, interval=None):
    """
    连续采样帧率，返回 (中位数, 样本列表)。
    先连续截图、再统一识别：截图是毫秒级、识别是0.6秒级，
    分开做才能把采样间隔压到 0.15 秒，真实反映帧率波动。
    """
    count = count or config.FPS_SAMPLE_COUNT
    interval = interval if interval is not None else config.FPS_SAMPLE_INTERVAL

    shots = []
    for i in range(count):
        shots.append(G.DEVICE.snapshot())
        if i < count - 1:
            sleep(interval)

    values, failed = [], 0
    for shot in shots:
        try:
            digits, _ = _recognize(_extract_digits_image(shot))
            if digits:
                values.append(int(digits))
            else:
                failed += 1
        except ValueError:
            failed += 1

    if not values:
        raise ValueError(f"FPS 采样全部失败: {count} 张截图无一识别成功")
    if failed > count / 2:
        raise ValueError(f"FPS 采样失败率过高: {failed}/{count}，结果不可信")

    return statistics.median(values), values

def assert_fps_near(target, tol_ratio=None, count=None):
    """
    采样并断言实测帧率接近目标值。这是"测试"和"脚本"的分界线。

    target   : 标称帧率，如 60 / 30
    tol_ratio: 允许的相对偏差，默认取 config.FPS_TOL_RATIO (0.10)
    """
    tol_ratio = tol_ratio if tol_ratio is not None else config.FPS_TOL_RATIO
    median, samples = sample_fps(count=count)
    tol = target * tol_ratio
    assert abs(median - target) <= tol, (
        f"{target}帧档位实测中位帧率 {median}，超出容差 ±{tol:.1f}\n"
        f"    全部样本: {samples}"
    )
    print(f"[FPS] {target}帧档位 -> 中位数 {median}  样本 {samples}")
    return median, samples
# ══════════════════════════════════════════════════════════════════════
# 音量验证
# ══════════════════════════════════════════════════════════════════════

def record_system_audio(seconds=2.0, samplerate=48000):
    """
    录制系统正在播放的声音（WASAPI Loopback）。
    等价于 OBS 的"桌面音频"——只读系统音频输出流，不注入游戏、不读内存。
    """
    import soundcard as sc
    speaker = sc.default_speaker()
    mic = sc.get_microphone(id=str(speaker.name), include_loopback=True) #WASAPI_loopback回环采集开启可以屏蔽环境噪音
    with mic.recorder(samplerate=samplerate, channels=2) as rec: #48kHz，双声道
        data = rec.record(numframes=int(samplerate * seconds))
    return data


def peak_loudness_db(data, samplerate=48000, window_ms=50):
    """
    把录音切成 50ms 小窗口，算每窗 RMS，返回最响的那个（dBFS）。

    为什么用峰值不用整段平均：2秒里真正有声音的可能只有0.3秒，
    整段平均会被其余静音拉平，导致音量10和音量0测出来差不多。
    为什么切小窗口：不管声音落在哪，总有窗口能抓到，无需精确对齐时间。
    """
    mono = data.mean(axis=1) if data.ndim > 1 else data
    win = int(samplerate * window_ms / 1000)
    n = len(mono) // win
    if n == 0:
        return -100.0
    frames = mono[:n * win].reshape(n, win)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    return float(20 * np.log10(max(float(rms.max()), 1e-8)))


def measure_volume(duration=None, debug=True):
    """录一段，返回该段的峰值响度(dBFS)"""
    duration = duration or config.VOLUME_RECORD_SECONDS
    db = peak_loudness_db(record_system_audio(duration))
    if debug:
        print(f"[VOL] 录制 {duration}s -> 峰值响度 {db:.1f} dBFS")
    return db


def measure_while(action_fn, duration=None, debug=True):
    """
    一边录音、一边执行 action_fn。
    这样声音必然落在录音窗口内，不需要精确对齐时间。

    用法: measure_while(lambda: (touch((800, 450)), sleep(2.5)))
    """
    duration = duration or config.VOLUME_RECORD_SECONDS
    result = {}

    def _rec():
        result["db"] = peak_loudness_db(record_system_audio(duration))

    t = threading.Thread(target=_rec) #单开一个新的线程
    t.start()              # 启动这个录音线程，不影响代码程序继续向下执行
    sleep(0.3)             # 初始化音频设备，等录音真正开始
    action_fn()            # 发声动作，用lambda函数封装
    t.join()               # 等待录音到结束
    if debug:
        print(f"[VOL] 录制 {duration}s -> 峰值响度 {result['db']:.1f} dBFS")
    return result["db"]


def assert_volume_trend(db_levels):
    """
    跨档位断言：验证音量设置与实际响度的对应关系，而非绝对的数值判断。
    db_levels 形如 {"0": -70.2, "5": -40.1, "10": -12.8}
    """
    print("\n[VOL] 音量-响度曲线:")
    for lv in sorted(db_levels, key=lambda x: int(x)):
        print(f"      音量 {lv:>2} -> {db_levels[lv]:7.1f} dBFS")

    if "0" in db_levels and "10" in db_levels:
        quiet, loud = db_levels["0"], db_levels["10"]
        gap = loud - quiet
        print(f"      动态范围(0->10): {gap:.1f} dB")
        #验证滑动条是否有效
        assert gap >= config.VOLUME_MIN_DYNAMIC_RANGE_DB, (
            f"音量设置未有效影响实际输出: 音量0={quiet:.1f}dBFS, 音量10={loud:.1f}dBFS, "
            f"动态范围仅 {gap:.1f}dB (要求 ≥{config.VOLUME_MIN_DYNAMIC_RANGE_DB}dB)"
        )
        #验证总音量针对背景BGM的控制有效
        assert quiet <= config.VOLUME_SILENCE_DBFS, (
            f"音量设为0时仍有明显输出: {quiet:.1f} dBFS (要求 ≤{config.VOLUME_SILENCE_DBFS}dBFS)"
        )
    #单调性验证
    if "0" in db_levels and "5" in db_levels and "10" in db_levels:
        mid = db_levels["5"]
        assert db_levels["0"] < mid < db_levels["10"], (
            f"响度未随音量单调变化: 0={db_levels['0']:.1f}, 5={mid:.1f}, 10={db_levels['10']:.1f} dBFS"
        )
