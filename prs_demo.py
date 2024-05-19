import matplotlib.pyplot as plt
from socket_server import *

if __name__ == '__main__':
    # Environment initialization
    prs = PrsEnv(is_print=0, not_test_mode=1)
    prs.npc_start(5)
    # How many NPCs are there
    ma = np.array(prs.server.maps.floor3)
    # print(ma.shape)(172, 228)
    prs.agent.rotate_right(degree=30)
    # prs.agent.goto_target_goal((2, 130, 120), position_mode=1)
    # robot navigate to floor3 point (130, 120)
    # API document come soon!
    map_room = prs.server.maps.floor3

    time.sleep(60)
    prs.finish_env()