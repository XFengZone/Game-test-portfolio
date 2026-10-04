from airtest.core.api import *
from tools import WindowTools, assert_fps_near,measure_while
import config
import tools
auto_setup(__file__, devices=[f"Windows:///?title_re={config.GAME_TITLE}.*"])

#将窗口放入左上角，拥有反作弊系统的游戏不可用，需自行移动到左上角
WindowTools.move_and_fix_window(config.GAME_TITLE, config.WINDOW_WIDTH,config.WINDOW_HEIGHT)

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
        #向后移动0.75秒
        WindowTools.press_and_hold("S",0.75)
        #向前移动0.75秒
        WindowTools.press_and_hold("W",0.75)
        #向左移动0.75秒
        WindowTools.press_and_hold("A", 0.75)
        #向右移动0.75秒
        WindowTools.press_and_hold("D", 0.75)
        #验证60帧档位的实际帧率
        assert_fps_near(60)

        #切换至30帧，继续测试游戏帧数内表现
        WindowTools.press_and_hold("ESCAPE", 0)
        sleep(1.0)
        touch(Template("images/setting_image.png", threshold=0.8))
        sleep(1.0)
        touch(Template("images/60fps.png", threshold=0.9))
        sleep(0.5)
        touch(Template("images/30fps_notclick.png",threshold=0.8))
        WindowTools.return_from_setting_menu()
        WindowTools.press_and_hold("S", 0.75)
        WindowTools.press_and_hold("W", 0.75)
        WindowTools.press_and_hold("A", 0.75)
        WindowTools.press_and_hold("D", 0.75)
        #验证30帧档位的实际帧率
        assert_fps_near(30)

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


