import time
import re
import difflib
import os
import matplotlib.pyplot as plt
# from env.socket_server import *
# from llm_process import *
from robot.llm_process import *
# Notice the relative path of the main script


def instruction_parsing_res(prs, instruction, resume):
    task_planning = instruction_parsing(instruction, resume)
    # task_planning = ['white bagged cake', 'marble dinner counter', 'living room', 'man with white coat', 'bed room']
    object_room, human_room = room_filter(prs, task_planning[2])[0], room_filter(prs, task_planning[4])[0]
    possible_receptacles, receptacles_index = approach_landmark(prs, task_planning[1], object_room)
    result_data = {'target_object': task_planning[0], 'target_object_receptacle': possible_receptacles,
                   'target_object_room': (object_room, task_planning[2]), 'target_human': task_planning[3],
                   'target_human_room': (human_room, task_planning[4])}
    return result_data


def calculate_similarity(a, b):
    len_a, len_b = len(a), len(b)
    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]
    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs_length = dp[len_a][len_b]
    similarity = 2.0 * lcs_length / (len_a + len_b)
    if similarity > 0.5:
        return True
    else:
        return False


def delivery_execution(prs, instruction, resume):
    '''
        1. Analyze language instructions to determine the target
        2. Locate/proceed to the room where the target item is located
        3. Find the container based on the semantic map
        4. Identify the target item using camera information (or explore if not found)
        5. Grasp the target item based on segmentation information
        6. After grasping, proceed to the room based on the information from step 1
        7. Locate and recognize the target person
    '''
    # prs.agent.initial_pose()
    task_planning = instruction_parsing(instruction, resume)
    # task_planning = ['white bagged cake', 'marble dinner counter', 'living room', 'man with white coat', 'bed room']
    # print(task_planning)
    object_room, human_room = room_filter(prs, task_planning[2])[0], room_filter(prs, task_planning[4])[0]
    # print(object_room, human_room)
    speed_time, camera_pitch = 3, 20
    prs.sim_speed(speed_time)
    # Unity rendering and runtime acceleration, notice the possibility of logical errors caused by fast rendering speed
    go_to_location(prs, object_room)
    prs.sim_speed(1)
    camera_rgb, camera_degree = scene_understanding(prs, task_planning[0], task_planning[1], pitch=camera_pitch, mode=1)
    possible_receptacles, receptacles_index = approach_landmark(prs, task_planning[1], object_room)
    for r_index, rec in enumerate(possible_receptacles):
        if camera_rgb is not None: break
        for time_i in range(2):
            prs.sim_speed(speed_time)
            prs.agent.goto_receptacle(room=object_room, recepacle=receptacles_index[r_index], random=1)
            prs.sim_speed(1)
            camera_rgb, camera_degree = scene_understanding(prs, task_planning[0], task_planning[1], pitch=camera_pitch, mode=1)
            if camera_rgb is not None: break
        if camera_rgb is None: pass
            # exploration of environment
        else:
            break
    if camera_rgb is not None:
        # Operate items and identify, determine room
        prs.sim_speed(1)
        manipulate_target(prs, task_planning[0], camera_degree, pitch=camera_pitch)
        time.sleep(1)
    prs.sim_speed(speed_time)
    go_to_location(prs, human_room)
    prs.sim_speed(1)
    camera_rgb, camera_degree = scene_understanding(prs, task_planning[3], pitch=camera_pitch, mode=1)
    search_result = 0
    if camera_rgb is not None:
        search_result = approach_target(camera_rgb, camera_degree, task_planning[3], 3)
    if not search_result:
        for room_i in prs.objs_data.room_area:
            if room_i['name'] == human_room:
                room_info = room_i
                break
        if room_info is None: return None
        receptacles_info = room_info['receptacles_list']
        # Locate possible receptacles in the room
        for r_index, rec in enumerate(receptacles_info):
            if camera_rgb is not None: break
            prs.sim_speed(speed_time)
            prs.agent.goto_receptacle(room=human_room, recepacle=r_index, random=1)
            prs.sim_speed(1)
            camera_rgb, camera_degree = scene_understanding(prs, task_planning[3], pitch=camera_pitch,
                                                            mode=1)
            if camera_rgb is None:
                pass
            else:
                search_result = approach_target(camera_rgb, camera_degree, task_planning[3], 3)
                break
    return 1


def target_matching(target, options=['room']):
    best_match, matches_with_similarity = None, []
    target_preprocess = re.sub(r'[^a-zA-Z0-9]', '', target).lower()
    for location in options:
        similarity = difflib.SequenceMatcher(None, target_preprocess, location.lower()).ratio()
        matches_with_similarity.append((similarity, location))
    matches_with_similarity.sort(key=lambda x: x[0], reverse=True)
    sorted_matches = [match[1] for match in matches_with_similarity]
    # Sort by similarity
    return sorted_matches


def instruction_parsing(task_instruction, description=None):
    background = 'Now you are a robotic assistant tasked with assisting in executing a human-centred item delivery mission. Please deduce the necessary execution actions and objectives based on the following task instructions:'
    npc_info = 'Introduction to the target person for the transportation mission: ' + description
    requirement = 'The following information needs to be extracted from the task: the target item, the container that holds the target item, the room where the target item is located, the visual characteristics of the target person (excluding the name but including gender for identification, such as a woman in a white dress), and the room where the target person is located (including the room number such as bedroom 1, with only the room name information and excluding ambiguous location descriptions, for example, outputting office 1). Only the inference results are required, the format is as follows:'
    reference = '<blue plastic bottle, dinner table, kitchen, yellow hair man with white shirt, bedroom 1>'
    prompt = background + task_instruction + npc_info + requirement + reference
    task_parameter = None
    for i in range(3):
        reasoning_result = llm_interaction(prompt)
        # reasoning_result = '<black console gaming pad, low coffee table, living room, man with light-colored jacket, bedroom>'
        # print(reasoning_result)
        try:
            cleaned_string = reasoning_result.strip('<>').strip()
            items = cleaned_string.split(',')
            task_parameter = [item.strip() for item in items]
            break
        except Exception as e:
            continue
    # decoded_str = s.encode('utf-8').decode('unicode-escape')
    return task_parameter


def go_to_location(prs, destination='bed room 1'):
    # go to the target room through global map
    if destination is not None:
        # prs.agent.goto_target_goal((-8.4, 0.1, 7.9), radius=1.5, position_mode=1)
        position = None
        for room in prs.objs_data.room_sampling_points:
            if room.split('_')[1] == destination:
                position = prs.objs_data.room_sampling_points[room]
        if position is None: return 0
        target = position[0]
        prs.agent.goto_target_goal(target, 1.25, position_mode=1)
        # Facing the center position of the room space
        prs.agent.head_camera_look_at(position[1], accuracy=0)


def room_filter(prs, destination, floor=2):
    rooms = prs.objs_data.room_area
    locations = [roo['name'] for roo in rooms]
    # locations = prs.objs_data.buliding_rooms[floor]
    best_match_rooms = target_matching(destination, locations)
    return best_match_rooms


def approach_landmark(prs, landmark, room):
    # Determine which one in the list has a higher similarity to the destination.
    # For 'bed room 1', it is desired to output 'bedroom1' instead of 'bedroom'
    room_info = None
    for room_i in prs.objs_data.room_area:
        if room_i['name'] == room:
            room_info = room_i
            break
    if room_info is None: return None
    landmarks, original_index = room_info['receptacles_list'], []
    potential_receptacles = target_matching(landmark, landmarks)
    for rec in potential_receptacles:
        original_index.append(landmarks.index(rec))
    return potential_receptacles, original_index
    #  Selecting potential containers through semantic matching


def scene_understanding(prs, target, surrounding=None, pitch=20, mode=0):
    # The angle of horizontal X-axis rotation, equivalent to the pitch angle, whether to segment
    observation_views = [0, -60, 60]
    for degree in observation_views:
        if surrounding is not None:
            target = target + ' or ' + surrounding
        context1 = 'Please answer yes or no. If there is '
        context2 = ', or there may be similar objects or content. Only answer yes or no!'
        detect_prompt = context1 + target + context2
        head_camera_rgb = prs.agent.observation(degree=degree, camera=0, up_down=pitch)
        if mode:
            recognition_result = lmm_interaction(detect_prompt, head_camera_rgb)
            if 'yes' in recognition_result.lower():
                return head_camera_rgb, degree
        else:
            if surrounding is not None:
                target = target + '. ' + surrounding
            seg = object_detect_module(head_camera_rgb, target)
            if seg is not None:
                return head_camera_rgb, degree
    prs.agent.joint_control(joint_id=14, target=0)
    # Adjust the camera to its original degree 0 (look straight ahead)
    return None, None


def approach_target(ego_view, camera_degree, target, distance=2):
    target_mask = object_detect_module(ego_view, target)
    res = 0
    if target_mask is not None:
        depth_m = prs.agent.get_depth(0)
        tar_distance, view_angle = prs.agent.depth_estimation(target_mask, depth_m, field_of_view=90)
        if tar_distance > distance:
            point = prs.agent.target_direction(degree=camera_degree, distance=tar_distance, target_degree_view=view_angle)
            res = prs.agent.goto_target_goal(point, radius=2.5, position_mode=1, inflation=1)
            prs.agent.direction_adjust(point, pos_input=1)
        else:
            res = 1
    return res


def manipulate_target(prs, target_obj, degree, pitch=20):
    s_now = prs.agent.observation(degree, up_down=pitch)
    seg, result = object_detect_module(s_now, target_obj), None
    if seg is not None:
        result = prs.agent.object_interaction(input_matrix=seg, manipulaton=1, type=0)
    return result


if __name__ == "__main__":
    # Environment initialization
    prs = PrsEnv(is_print=1, rendering=1, start_up_mode=1)

    with open(os.path.join('task', 'dataset', 'deliver_task_test_set.json'), 'r') as file:
        task_data = json.load(file)
    tasks = list(task_data.keys())
    errors, error_num, task_results = [], 0, dict()
    for task_i, task_id in enumerate(tasks):
        print('task:', task_id)
        task = task_data[task_id]
        task_npc_id = task['npc_id']
        start_time = time.time()
        instruction, npc_information, data = prs.delivery_task_import(task)
        now = prs.env_time.current_date.strftime("%d %H:%M:%S")
        try:
            # ------------ baseline method -----------------
            time.sleep(0.5)
            delivery_execution(prs, instruction, npc_information)
        except Exception as e:
            print(e, 'error')
            break
        result = prs.delivery_task_evaluate(task, score=1, save=0)
        print(result['task_score'])
        # ====== if you want to save the result as json file to submission on Eval AI ==========
        # result_save = prs.delivery_task_evaluate(task, score=0, save=1)
        # task_results[task_id] = result_save
        # with open('task/result/deliver_task_result.json', 'w') as file:
        #     json.dump(task_results, file, indent=4)
        # ---------------------------------------------------------------------------------------
    time.sleep(3)
    prs.finish_env()