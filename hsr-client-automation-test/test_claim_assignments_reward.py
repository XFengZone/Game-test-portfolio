from tools import WindowTools
from airtest.core.api import *
import config

class Test_assignments():
    def test_claim_rewards(self):
        WindowTools.press_and_hold("ESCAPE",0)
        sleep(1.0)
        touch(Template("images/assignments_image.png",threshold=0.8))
        sleep(2)
        assert_exists(Template("images/assignments_check.png",threshold=0.8),"进入委托界面失败")
        #try:
        if exists(Template("images/claim_reward.png",threshold=0.8)):
            touch(Template("images/claim_reward.png",threshold=0.8))
            sleep(1.0)
            assert_exists(Template("images/get_rewards.png",threshold=0.8),"领取委托奖励失败")
            touch(Template("images/click_to_close.png",threshold=0.8))
            sleep(1.0)

        #except Exception as e:
            #print(f"奖励无法领取，{e}")
        WindowTools.return_from_setting_menu()

