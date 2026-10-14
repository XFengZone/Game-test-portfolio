import sys

import tools

sys.coinit_flags = 0        # ★ 必须在最顶部：统一 COM 为 MTA（soundcard 需要）

import os
import pytest
import allure
from _pytest.config import hookimpl

# ── 这些 import 的顺序很重要 ──
from airtest.core.api import *
from airtest.core.settings import Settings as ST
import config
from tools import WindowTools


@pytest.fixture(scope="session", autouse=True)
def airtest_device():
    """
    整个测试会话只执行一次：连接游戏窗口。

    autouse=True 表示所有用例自动使用，不用在每个用例里显式声明。
    """
    auto_setup(__file__, devices=[f"Windows:///?title_re={config.GAME_TITLE}.*"])
    yield
    # teardown 可以留空，也可以在这里做收尾（比如断开连接）


@pytest.fixture(scope="session", autouse=True)
def normalized_window(airtest_device):
    """
    整个会话只执行一次：把游戏窗口固定到 (0,0) 且 1600x900。

    为什么必须做：FPS_ROI = (456, 29, 480, 49) 这类坐标是【基于
    固定窗口尺寸】标定的，窗口一旦移动或缩放，截图坐标系就变了。
    """
    ok = WindowTools.move_and_fix_window(
        config.GAME_TITLE, config.WINDOW_WIDTH, config.WINDOW_HEIGHT
    )
    if not ok:
        pytest.exit(f"未找到游戏窗口[{config.GAME_TITLE}]，请先启动游戏", returncode=1)
    sleep(0.5)      # 等窗口渲染稳定，避免第一次截图拿到半渲染画面

@pytest.fixture(scope="session", autouse=True)
def warm_up_ocr(normalized_window):
    """
    预热 OCR：提前触发模型加载（约 4~5 秒）。
    """
    from tools import _get_ocr
    _get_ocr()
@pytest.fixture(scope="function",autouse=True)
def reset_game_state():
    """
        后置：把帧率与音量恢复到基线（帧率 60 / 音量 10）

        为了效率，复位前先检查当前是否已在基线
        已经是基线就跳过，避免每次跑都白进两遍设置页。
        """
    yield
    #后置部分
    try:
        tools.WindowTools.restore_baseline_settings()
    except Exception as e:
        # teardown 里绝不抛异常，否则会盖掉用例本身的失败信息
        print(f"[conftest] 基线复位失败: {type(e).__name__}: {e}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        from airtest.core.api import G
        shot = f"report/failures/{item.name}.png"
        os.makedirs(os.path.dirname(shot), exist_ok=True)
        G.DEVICE.snapshot(filename=shot)
        # 把截图直接附到 allure 报告的那条用例上
        allure.attach.file(shot, name="失败截图",
                           attachment_type=allure.attachment_type.PNG)
