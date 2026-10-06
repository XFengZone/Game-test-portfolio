from airtest.core.api import *
from tools import WindowTools, assert_fps_near,measure_while
import config
import tools

class Test_setting():

    def test_change_fps(self):
        """
        更改游戏内帧率，包括从60帧改变至30帧，30帧改变至60帧
        :return:
        """
        win = device()
        #进入游戏后按ESC
        WindowTools.enter_setting()
        #检测初始状态是否为60帧，若不是则切换后开始测试

        if exists(Template("images/30fps.png",threshold=0.9)):
            touch(Template("images/30fps.png",threshold=0.9))
            sleep(0.5)
            touch(Template("images/60fps_notclick.png",threshold=0.8))
            sleep(0.5)

        # 判断是否切换到60帧
        assert_exists(Template("images/60fps.png", threshold=0.9), "切换60帧失败！")
        #在60帧状态下，测试游戏帧数表现
        #返回到游戏主界面

        WindowTools.return_from_setting_menu()
        #操控角色前后左右移动
        def move_60():
        #向后移动0.75秒
            WindowTools.press_and_hold("S",0.75)
            #向前移动0.75秒
            WindowTools.press_and_hold("W",0.75)
            #向左移动0.75秒
            WindowTools.press_and_hold("A", 0.75)
            #向右移动0.75秒
            WindowTools.press_and_hold("D", 0.75)

        median_60, samples_60, n60 = tools.measure_fps_during(move_60, interval=0.15)
        print(f"[FPS] 60帧档位移动期间样本: {samples_60}")
        print(f"[FPS] 60帧档位中位数: {median_60}")
        #验证60帧档位的实际帧率
        tol_60 = 60 * config.FPS_TOL_RATIO
        assert abs(median_60 - 60) <= tol_60, (
            f"60帧档位移动期间实测中位帧率 {median_60}，超出容差 ±{tol_60:.1f}\n"
            f"    全部样本({len(samples_60)}个): {samples_60}"
        )

        #切换至30帧，继续测试游戏帧数内表现
        WindowTools.press_and_hold("ESCAPE", 0)
        sleep(1.0)
        touch(Template("images/setting_image.png", threshold=0.8))
        sleep(1.0)
        touch(Template("images/60fps.png", threshold=0.9))
        sleep(0.5)
        touch(Template("images/30fps_notclick.png",threshold=0.8))
        WindowTools.return_from_setting_menu()
        def move_30():
            WindowTools.press_and_hold("S", 0.75)
            WindowTools.press_and_hold("W", 0.75)
            WindowTools.press_and_hold("A", 0.75)
            WindowTools.press_and_hold("D", 0.75)

        median_30, samples_30, n_30 = tools.measure_fps_during(move_30, interval=0.15)
        print(f"[FPS] 30帧档位移动期间样本: {samples_30}")
        print(f"[FPS] 30帧档位中位数: {median_30}")
        #验证30帧档位的实际帧率
        tol_30 = 30 * config.FPS_TOL_RATIO
        assert abs(median_30 - 30) <= tol_30, (
            f"30帧档位【移动期间】实测中位帧率 {median_30}，超出容差 ±{tol_30:.1f}\n"
            f"    全部样本({len(samples_30)}个): {samples_30}"
        )
        # ── 相对判据：档位切换必须产生明显差异 ──
        assert median_60 > median_30 * 1.3, (
            f"帧率档位切换未产生预期差异：60档={median_60}, 30档={median_30}"
        )

    def test_change_voice(self):
        """
        更改游戏内总音量，音量大小从10变为0再变为5
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


