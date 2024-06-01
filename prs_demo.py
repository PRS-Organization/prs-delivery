from env.socket_server import *
import matplotlib.pyplot as plt
# from env.socket_server import server
# import sys

if __name__ == '__main__':
    # Environment initialization
    prs = PrsEnv(is_print=0, start_up_mode=0)
    prs.npc_start(5)
    # How many NPCs are there
    ma = np.array(prs.server.maps.floor3)
    # print(ma.shape)(172, 228)
    prs.agent.rotate_right(degree=30)
    prs.agent.initial_pose()
    prs.agent.go_to_destination(tar_location='kitchen')
    prs.agent.direction_adjust(position=(0, 0, 0))
    print(prs.agent.query_near_objects())
    print(len(prs.agent.get_room_area('kitchen room')))
    print(prs.agent.get_receptacles_within_room(room_name='kitchen room'))
    prs.agent.goto_receptacle(room='kitchen room', recepacle=0, random=0)
    print(prs.agent.object_information_query(obj_id=0))

    rgb = prs.agent.head_camera_look_at()
    rgb = prs.agent.observation(degree=0, camera=0)
    view = prs.agent.site_view(pos=(0, 0, 0))
    depth = prs.agent.get_depth()
    arr, tags = prs.agent.get_segmentation(camera_type=0, decode=1)
    print(tags)
    plt.imshow(arr)
    plt.show()

    marked_arr = np.zeros_like(arr)
    for tag in tags:
        if tags[tag] == 'Npc_UniformMale_8':
            aaa = tag
            break
    marked_arr[arr == aaa] = 1
    prs.agent.object_interaction(marked_arr, manipulaton=1)
    # prs.agent.goto_target_goal((2, 130, 120), position_mode=1)
    # robot navigate to floor3 point (130, 120)
    # API document come soon!
    map_room = prs.server.maps.floor3

    time.sleep(60)
    prs.finish_env()