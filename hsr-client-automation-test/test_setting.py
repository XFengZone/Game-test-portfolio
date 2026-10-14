from airtest.core.api import *
from tools import WindowTools,measure_while
import pytest
import config
import tools

class Test_setting():

    @pytest.mark.parametrize("target_fps", [60, 30], ids=["60帧档位", "30帧档位"])
    def test_change_fps(self, target_fps):
        """
        把帧率切到目标档位，在固定移动轨迹下采样，断言实测帧率达到标称值
        """
        WindowTools.enter_setting()
        WindowTools.set_fps(target_fps)
        assert_exists(Template(config.FPS_SELECTED_TEMPLATE[target_fps], threshold=0.9),
                      f"{target_fps}帧档位未被选中")
        WindowTools.return_from_setting_menu()

        median, samples, n = tools.measure_fps_during(WindowTools.run_movement, interval=config.FPS_SAMPLE_INTERVAL)
        print(f"[FPS] {target_fps}帧档位移动期间样本: {samples}")
        print(f"[FPS] {target_fps}帧档位中位数: {median}")

        tol = target_fps * config.FPS_TOL_RATIO
        assert abs(median - target_fps) <= tol, (
            f"{target_fps}帧档位移动期间实测中位帧率 {median}，超出容差 ±{tol:.1f}\n"
            f"    全部样本({len(samples)}个): {samples}"
        )

    def test_change_voice(self):
        """
            更改游戏内总音量，音量大小从10变为0再变为5
            前置条件：
          - 系统音量保持正常水平且【未静音】
          - 测试期间不要播放其他音频，避免干扰回环采集
          - 断言均为跨档位相对关系，不依赖系统音量的具体数值
        :return:
        """
        vol_db={}
        WindowTools.enter_setting()
        touch(Template("images/voice_setting.png",threshold=0.8))
        sleep(1.0)
        assert_exists(Template("images/voice_check.png",threshold=0.8))
        #step1：调节音量为10
        WindowTools.set_volume(config.X_LEFT,config.X_RIGHT,config.Y,10)
        WindowTools.return_from_setting_menu()
        #平A测试音量（边录边发声）
        vol_db["10"] = measure_while(lambda: (touch((800, 450)), sleep(2.5)))
        #step2：调节音量为0
        WindowTools.enter_setting()
        touch(Template("images/voice_setting.png", threshold=0.8))
        sleep(1.0)
        assert_exists(Template("images/voice_check.png", threshold=0.8))
        WindowTools.set_volume(config.X_LEFT, config.X_RIGHT, config.Y, 0)
        WindowTools.return_from_setting_menu()
        # 平A测试音量（边录边发声）
        vol_db["0"] = measure_while(lambda: (touch((800, 450)), sleep(2.5)))
        #step3:调节音量为5
        WindowTools.enter_setting()
        touch(Template("images/voice_setting.png", threshold=0.8))
        sleep(1.0)
        assert_exists(Template("images/voice_check.png", threshold=0.8))
        WindowTools.set_volume(config.X_LEFT, config.X_RIGHT, config.Y, 5)
        WindowTools.return_from_setting_menu()
        # 平A测试音量
        vol_db["5"] = measure_while(lambda: (touch((800, 450)), sleep(2.5)))

        tools.assert_volume_trend(vol_db)

if __name__=="__main__":
    pass

