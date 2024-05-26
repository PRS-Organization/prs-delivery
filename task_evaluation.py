from env.socket_server import *

# Environment initialization
prs = PrsEnv(is_print=1)
rooms = prs.objs_data.rooms
room_mapping, room2gt = dict(), dict()
for room_i, room in enumerate(rooms):
    name, pos = room['roomName'], room['roomCenter']
    if pos['y'] < -0.8: continue
    name_f = prs.npcs[0].process_string_location(name)
    room_mapping[name] = [name_f, 'room' + str(room_i)]
    room2gt[name_f] = [name, 'room' + str(room_i)]
# print(prs.receptacles_information)
# print(prs.objs_data.room_receptacles)
# print(room_mapping)
# print(room2gt)
# prs.
# ===============================npc sit test========================================
# for loc in prs.npcs[0].env.location['F3_Bedroom_2'][::1]:
# prs.npcs[0].goto_randomly(loc)
# res, obj = prs.npcs[0].go_to_object('Seat')
# suc = prs.npcs[0].npc_action('sit', obj)
# print(res, obj, suc)
# time.sleep(2)
# suc = prs.npcs[0].npc_action('stand')
# time.sleep(0.5)
# prs.npcs[0].goto_randomly(prs.npcs[0].env.location['F3_OfficeSpaceRoom'][0], radius=1)
# ------------------------------------------------------------------
# for i in range(100):
#     s_now = prs.agent.observation(degree=0, up_down=20)
#     tar_obj_inf = prs.objs_data.get_info_from_name('BaggedCake01')
#     tar_obj_id = tar_obj_inf['itemId']
#     obj_info = prs.server.object_query(tar_obj_id)
#     obj_pos = obj_info['position']
#     print('----------', tar_obj_inf, obj_info)

# ob = prs.agent.observation(up_down=10)
# approach_target(ob, 0, 'red apple', 1)
# prs.agent.head_camera_look_at((-14.7, 0.1, -3.2), accuracy=1)
# time.sleep(3)
# print(prs.receptacles_information["F3_Bedroom_6"]['receptacle names'])
# print(prs.objs_data.room_receptacles["F3_Bedroom_6"]['receptacles'][0])
# print(prs.objs_data.room_receptacles["F3_Bedroom_6"]['receptacles'][1])
# prs.finish_env()
# -------------------------------------------------------------------------------------
grasps = prs.objs_data.grasp_items
# print(prs.objs_data.receptacles)
# with open('data/npc_data.json', 'r') as file:
#     npc_data = json.load(file)
with open(os.path.join('task', 'result', 'deliver_task_5_19_reasoning_result.json'), 'r') as file:
    task_result_reasoning = json.load(file)
with open(os.path.join('task', 'dataset', 'deliver_task_5_19_test_set.json'), 'r') as file:
    task_data = json.load(file)
with open(os.path.join('task', 'result', 'deliver_task_5_19_result.json'), 'r') as file:
    task_result_already = json.load(file)
tasks = list(task_data.keys())
print('task:', len(tasks))
import random

random.shuffle(tasks)
task_result, errors, error_num = task_result_already, [], 0
finish_task = list(task_result.keys())
for task_i, task_id in enumerate(tasks):
    # if task_id in finish_task: continue
    if task_id != '6_2025_07_10T13_37_17_12_1_1':
        continue
    else:
        continue
    print('task:', task_id)
    task = task_data[task_id]
    # print(task)
    # {'npc_name': 'Noah', 'npc_id': 2, 'time': '2025-03-16T08:23:58', 'npc_location': 'F3_OfficeRoom02', 'npc_action': 'sit', 'npc_position': {'x': -6.774, 'y': 0.0, 'z': -6.65
    # 1}, 'target_object_id': 364, 'target_object_name': 'Apple_3', 'target_object_type': 'Apple', 'target_object_pos': {'x': -10.653, 'y': 0.9, 'z': -4.195}, 'target_object_roo
    # m': 'F3_KitchenRoom', 'target_object_receptacle': 'Apple_2', 'target_object_feature': 'round', 'directive': ['Grasp the round apple on the apple in the kitchen room.', "It's 08:23 now, give this item to Noah in the office room."], 'task_id': '2_2025_03_16T08_23_58_0_0_0'}
    task_npc_id = task['npc_id']
    # prs.npcs[task_npc_id].directive_following(task)
    # try:
    start_time = time.time()
    instruction, npc_information, data = prs.delivery_task_import(task)

    now = prs.env_time.current_date.strftime("%d %H:%M:%S")
    # print(instruction, now, task_i)
    # print(data)
    # ------------ baseline
    time.sleep(0.5)
    # break
    delivery_execution(prs, instruction, npc_information)
    # available_instructions = {'first person instruction': 'Grasp the black console gaming pad from the low coffee table in the living room and take it to the bedroom.',
    #  'third person instruction': 'Retrieve the black console gaming pad on the low coffee table in the living room and bring it to the bedroom for Brian, the one in the light-colored jacket.'}
    # ------------ baseline
    result = prs.delivery_task_evaluate(task, score=1, save=0)
    end_time = time.time()
    print("程序运行时间为：", end_time - start_time, "秒- ", task_id)
    print(result['task_score'])
    task_result[task_id] = result
    # except Exception as e:
    #     error_num += 1
    #     print('??????????????', e, '-------', task_id)
    #     errors.append(task_id)
    # if task_i == 1:
    if error_num > 3:
        break
    break
    with open('task/result/deliver_task_5_19_result.json', 'w') as file:
        json.dump(task_result, file, indent=4)
    # break