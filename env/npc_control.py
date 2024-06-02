import os
import json
import csv
import cv2
import time
import numpy as np
from heapq import heappop, heappush
import copy
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue, Value, Lock
import multiprocessing as mp
from PIL import Image
import io
# robot
from roboticstoolbox.robot.ERobot import ERobot
import roboticstoolbox as rtb
from math import pi
from spatialmath import SE3
from spatialmath.base import *
from collections import Counter
from datetime import datetime

def random_number(n):
    selected_number = np.random.randint(0, n)  # Generate a random number within the interval [0, n-1]
    return selected_number


class Env(object):
    def __init__(self, data, maps):
        self.data = data
        self.maps = maps
        self.height_f1 = -16.693447
        self.height_f2 = -5.2174
        self.height_f3 = -0.0499999
        f1, f2, f3 = self.height_f1, self.height_f2, self.height_f3
        self.location = dict()
        # self.room_process()
        # Align scene semantics, e.g. room12 may be the kitchen
        with open('env/data/room_sampling_points.json', 'r') as file:
            self.location = json.load(file)

    def room_process(self):
        for room in self.data.room_area:
            starting_coordinates = (0, self.maps.floors[room['floor']], 0)
            ind, p_i, p_j, _ = self.maps.get_point_info(starting_coordinates)
            room_map = self.maps.maps_info[room['floor']]['grid']
            dis_matrix = self.maps.dis_matrix(room_map, (p_i, p_j))
            # self.maps.search_route(room_map, (66, 198), (130, 132))
            minimum, position_i, position_j = 999999, 0, 0
            for i in range(room['x'][0], room['x'][1]+1):
                for j in range(room['y'][0], room['y'][1]+1):
                    if dis_matrix[i][j] < minimum:
                        minimum = dis_matrix[i][j]
                        position_i, position_j = i, j
            # location information: (floor, map_i, map_j)
            self.location[room['semantic_name']] = [(room['floor'], position_i, position_j)
                                                    , (room['position'][0], room['position'][1], room['position'][2])]

    def calculate_distance(self, point1, point2):
        # NumPy array
        try:
            point1_array = np.array([point1['x'], point1['y'], point1['z']], dtype=float)
        except:
            point1_array = np.array([point1[0], point1[1], point1[2]], dtype=float)
        try:
           point2_array = np.array([point2['x'], point2['y'], point2['z']], dtype=float)
        except:
            point2_array = np.array([point2[0], point2[1], point2[2]], dtype=float)
        try:
            distance = np.linalg.norm(point2_array - point1_array)
        except:
            # print(point1_array, point2_array)
            distance = np.linalg.norm(point2_array - point1_array)
        return distance


class Npc(object):
    def __init__(self, person_id, sock, env_time, objects):
        self.object_data = objects
        self.person_id = person_id
        self.times = env_time
        self.server = sock
        self.env = Env(self.object_data, self.server.maps)
        self.running = 1
        self.action_state = 'stand'
        self.place_state = 'warehouse'
        self.information = self.object_data.characters[self.person_id]
        # self.
        # -----initialization------
        self.height_f1 = -16.693447
        self.height_f2 = -5.2174
        self.height_f3 = -0.0499999
        self.position = [0, 0, 0]
        # tar_action, number = 'sit', 0
        # 0 universal (parameters for turning, sitting, eating, and missing) 1performance 2expressions
        # 3go 4pick 5put  6turn 7manipulation component  8
        self.instruction_type = [{"requestIndex": 10, "npcId": 0, "actionId": 0, "actionPara": {}},
            {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": {"showType": -1}},
                                 {"requestIndex": 10, "npcId": 0, "actionId": 300, "actionPara": {"expressionType":100}},
                                 {"requestIndex": 10, "npcId": 0, "actionId": 1,"actionPara": {"destination":{"x":0.5,"y":1.0,"z":0}}},
                                 {"requestIndex": 10, "npcId": 0, "actionId": 100,"actionPara": {"handType":-1,"itemId":1}},
                                 {"requestIndex": 10, "npcId": 0, "actionId": 101,"actionPara": {"handType":-1,"position":{"x":5.0,"y":12.0,"z":5.0}}},
                                 {"requestIndex": 10, "npcId": 0, "actionId": 2, "actionPara": {"angle":50}},
                                 {"requestIndex": 10, "npcId": 0, "actionId": 204,"actionPara": {"handType":1,"itemId":8,"targetActiveState":True}}
                                 ]
        self.mapping_action_type = {0: 0, 1: 3, 2: 0, 10: 0, 100: 4, 101: 5, 102: 0, 300: 2,
                400: 1}
        self.actions = {
            'stand': [0],
            'walk': [1],
            'turn': [2],
            'sit': [10],
            'pick': [100],
            'put': [101],
            'eat': [102],
            'operateButton': [200],
            'operateKnob': [201],
            'operateSlider': [202],
            'operateLever': [203],
            'triggerButton': [204],
            'emoji': [300, 301, 302],
            # -------show play()----------
            'dance': [400, 100],
            'exercise': [400, 101],
            'playComputer': [400, 102],
            'playGame': [400, 103],
            'layingDownOnDoor': [400, 104],
            'standLookHandObject': [400, 105],
            'sitLookHandObject': [400, 106],
            'waveHandOverHead': [400, 200],
            'waveHandAtWaist': [400, 201],
            'streachHead': [400, 202],
            'interrupt': [400, -1]
        #      Dance = 100, Exercise = 101, PlayComputer = 102, PlayGame = 103, LayingDownOnDoor = 104, StandLookHandObject = 105, SitLookHandObject = 106,
            #     //Single animation
            #     WaveHandOverHead = 200, WaveHandAtWaist = 201, StreachHead = 202
        }
        self.obj_interaction_action = ['pick', 'put', 'eat', 'operateButton', 'operateKnob', 'operateSlider',
            'operateLever', 'triggerButton']
        self.continuous_animation = ['dance', 'exercise', 'playComputer', 'playGame', 'layingDownOnDoor',
                                     'standLookHandObject', 'sitLookHandObject', 'waveHandOverHead', 'waveHandAtWaist', 'streachHead']

    def change_id(self, n):
        self.person_id = n

    def go_to_here(self, pos, command=0):
        try:
            y = pos[1]
        except:
            pos = [pos['x'], pos['y'], pos['z']]
        person_id = self.person_id
        if not command:
            command = {"requestIndex": 10, "npcId": 0, "actionId": 1, "actionPara": {"destination": {"x": 0.5, "y": 1.0, "z": 0}}}
        command['npcId'] = person_id
        command['actionPara']['destination']['x'] = pos[0]
        command['actionPara']['destination']['y'] = pos[1]
        command['actionPara']['destination']['z'] = pos[2]
        command['actionPara'] = json.dumps(command['actionPara'])
        re_id = self.server.send_data(1, command, 1)
        return re_id

    def where_npc(self):
        for npc in range(3):
            request_id = self.server.send_data(2,  {"requestIndex": 0, "targetType": 0, "targetId": self.person_id}, 1)
            time.sleep(0.1)
            info = None
            for i in range(9):
                try:
                    info = self.server.notes[request_id]
                    break
                except :
                    time.sleep(0.1)
            if info:
                try:
                    info['statusDetail'] = info['statusDetail'].replace("false", "False")
                    inf = eval(info['statusDetail'])
                    pos = inf['position']
                    return pos, info
                except Exception as e:
                    print(e, info)
                    # return False, info
        return None, info

    def query_information(self):
        pos, info = self.where_npc()
        datas = None
        if pos:
            datas = eval(info['statusDetail'])
            obj_closed = datas['closeRangeItemIds']
        return pos, datas

    def goto_randomly(self, position_tar, radius=1.5, delete_dis=2, times=10, random=1):
        try:
            xx, yy, zz = position_tar[0], position_tar[1], position_tar[2]
        except:
            xx, yy, zz = position_tar['x'], position_tar['y'], position_tar['z']
        floor, point_list = self.server.maps.get_an_accessible_area(xx, yy, zz, radius)
        result_go = 0
        for i_try in range(times):
            if not self.running or self.server.stop_event.is_set() or not self.server.state:
                return 0
            length = len(point_list)
            if length < 1:
                break
            if result_go == 1:
                break
    #         choose a random point (p_i, p_j)
            if random:
                now = np.random.randint(0, length)
            else:
                now = 0
            p_i, p_j = point_list[now][0], point_list[now][1]
            # translate the grid pos to the world pos
            pos_i, pos_j = self.server.maps.get_an_aligned_world_coordinate_randomly(floor, p_i, p_j)
            position_go = (pos_i, self.server.maps.floors[floor], pos_j)
            # print(' now plan to {}'.format(position_go))
            for i in range(2):
                if not self.running or self.server.stop_event.is_set() or not self.server.state:
                    return 0
                action_id = self.go_to_here(position_go)
                result = 0
                while True:
                    time.sleep(0.5)
                    if not self.running or self.server.stop_event.is_set() or not self.server.state:
                        return 0
                    try:
                        if self.server.notes[action_id]['informResult'] == 2:
                            result = self.server.notes[action_id]['informResult']
                            break
                        elif self.server.notes[action_id]['informResult'] == 0:
                            time.sleep(0.5)
                            break
                    except: pass
                if result == 2:
                    pos, info = self.where_npc()
                    if pos:
                        dis = self.env.calculate_distance(pos, position_go)
                        if dis < 1:
                            result_go = 1
                            break
                time.sleep(1)
            if result_go == 0:
                # Reverse loop deletion of points with a distance of 2 (not meter)
                for i in range(len(point_list) - 1, -1, -1):
                    point = point_list[i]
                    if np.sqrt((point[0] - p_i) ** 2 + (point[1] - p_j) ** 2) < delete_dis:
                        del point_list[i]
            elif result_go == 1:
                # print('$$$$$ arrive at: ', position_go)
                return result_go
        if result_go == 0: pass
            # print('$$$$$not arrive: ', position_tar)
        return result_go

    def random_walk(self):
        for i in range(1000):
            if not self.server.state or self.server.stop_event.is_set() or not self.running:
                return 0
            random_key = np.random.choice(list(self.env.location.keys()))
            location_now = self.env.location[random_key]
            result = self.goto_randomly(location_now[1], 3.5, 2, 20)
            if result:
                res, obj = self.go_to_object('Seat')
                if res:
                    suc = self.npc_action('sit', obj)
                    if suc:
                        time.sleep(30)
                        self.npc_action('stand')
                        time.sleep(3)
                    else:
                        time.sleep(5)

    def go_to_object(self, target='Seat', name='None_target', random_mode=1):
        pos, npc_info = self.query_information()
        if not pos:
            return 0, 0
        items = npc_info['closeRangeItemIds']
        all_obj = []
        if len(items) != 0:
            for item_id in items:
                item_info = self.object_data.objects[item_id]
                if not item_info['isOccupied']:
                    if target in item_info['features'] or name.lower() in item_info['itemName'].lower() :
                        item_info = self.server.object_query(item_id)
                        all_obj.append(item_info)
        else:
            return 0, 0
        if len(all_obj) == 0:
            return 0, 0
        if random_mode == 1:
            target_obj = np.random.choice(all_obj)
        else:
            target_obj = all_obj[0]
        if target_obj == None:
            return 0, 0
        pos = target_obj['position']
        res = self.goto_randomly(pos, 1, 2, 10)
        return res, target_obj['itemId']

    def get_now_time(self):
        week = self.times.weekday_now()
        hour = self.times.current_date.hour
        minute = self.times.current_date.minute
        # second = self.times.current_date.second
        return week, hour, minute

    def behavior_perform(self):
        with open("data/npc_schedule.json", "r") as json_file:
            data = json.load(json_file)
        schedule = data[str(self.person_id)]['schedule']
        week, hour, minute = 99, 99, 99
        while 1:
            week_n, hour_n, min_n = self.get_now_time()
            if hour != hour_n:  # or min_n == 30
                week, hour, minute = week_n, hour_n, min_n
                if self.action_state == 'sit':
                    self.npc_action('stand')
                    time.sleep(2)
                elif self.actions[self.action_state][0] == 400:
                    self.npc_action('interrupt')
                    time.sleep(1)
                    self.npc_action('stand')
                    time.sleep(2)
                for i in range(10):
                    # print(schedule[str(round(hour))])
                    planning = np.random.choice(schedule[str(round(hour))])
                    location_now = self.env.location[planning['location']]
                    result = self.goto_randomly(location_now[1], 2, 2, 20)
                    if result:
                        action_random, action_now = np.random.choice(planning['action']), 'stand'
                        self.place_state = planning['location']
                        res, obj = self.go_to_object('Seat')
                        if res:
                            suc = self.npc_action('sit', obj)
                            if suc:
                                action_now = 'sit'
                        if action_random != 'stand':
                            r = self.npc_action(action_random)
                            if r:
                                action_now = action_random
                        now_time = self.times.current_date.strftime("%d %H:%M:%S")
                        print(now_time, ': {} goes to the {} and perform action - {}'.format(
                            self.person_id, planning['location'], action_now
                        ))


                if not self.server.state or self.server.stop_event.is_set() or not self.running:
                    return 0
                time.sleep(1)

    def directive_following(self, directive):
        if self.action_state != 'stand':
            self.npc_action('stand')
            time.sleep(0.5)
        self.server.object_transform(obj_type=0, target_id=self.person_id, pos=directive['npc_position'])
        if directive["npc_action"] != self.action_state:
            npc_action = directive["npc_action"]
            if npc_action == 'sit':
                res, obj = self.go_to_object('Seat')
                if res:
                    suc = self.npc_action('sit', obj)
                    if suc:
                        action_now = 'sit'
            else:
                #  perform other action, need to extend
                if npc_action != 'stand':
                    r = self.npc_action(npc_action)
                pos, info = self.query_information()
                if pos:
                    self.place_state = self.object_data.point_determine(pos)

        random_x, random_z = np.random.uniform(-0.05, 0.05), np.random.uniform(-0.05, 0.05)
        target_obj_pos = directive['target_object_pos']
        target_obj_pos['x'] += random_x
        target_obj_pos['z'] += random_z
        target_obj_name = directive['target_object_name']
        # target_id = self.object_data.grasp_items[target_obj_name]['id']
        target_info = self.object_data.get_info_from_name(target_obj_name)
        # print(target_obj_name, target_info)
        self.server.object_transform(obj_type=1, target_id=target_info['itemId'], pos=target_obj_pos)
        self.times.current_date = datetime.fromisoformat(directive['time'])
        # go_result = self.goto_randomly(directive['npc_position'], 1, 2, 20)

    def random_behavior(self, room, probability=6):
        random_action = np.random.randint(0, probability)
        if random_action == 0:
            rooms = list(self.env.location.keys())
            del rooms[rooms.index(room)]
            random_loc = np.random.choice(rooms)
            location_now = self.env.location[random_loc]
            random_pos_index = np.random.randint(1, len(location_now))
            random_pos = location_now[random_pos_index]
            self.server.object_transform(target_id=self.person_id, pos=random_pos)
            time.sleep(0.1)

    def npc_action(self, tar_action, tar_object=0):
        action_para = self.actions[tar_action]
        instruct = self.mapping_action_type[action_para[0]]
        ins_template = copy.deepcopy(self.instruction_type[instruct])
        ins_template['npcId'] = self.person_id
        if action_para[0] < 300:
            ins_template['actionId'] = action_para[0]
        if tar_action == 'stand':
            pass
        elif tar_action == 'sit':
            if tar_object:
                ins_template['actionPara']["itemId"] = tar_object
            # pos, info = self.where_npc()
            # if pos:
            #     tar = self.object_data.object_parsing(info)
            #     if tar:
            #         # tar = self.object_data.object_parsing(self.near_items, ['Stool'])
            #         ins_template['actionPara']["itemId"] = tar
            #     else:
            #         ins_template['actionPara']["itemId"] = 0

        elif tar_action == 'pick':
            if tar_object:
                ins_template['actionPara']["itemId"] = tar_object
            ins_template['actionPara']["handType"] = -1
        elif tar_action == 'put':
            ins_template['actionPara']["position"] = {"x": 1, "y": 1, 'z': 1}
            ins_template['actionPara']["handType"] = -1
        elif tar_action == 'eat':
            ins_template['actionPara']["handType"] = -1
        elif action_para[0] == 400:
            # print('show show show')
            ins_template['actionPara']["showType"] = action_para[1]
        res = self.action_execution(ins_template)
        if res > 0:
            if res == 1:
                time.sleep(0.5)
            self.action_state = tar_action
            # print('*********successfully: ', tar_action, ' - ')
        return res

    def action_execution(self, ins):
        ins['actionPara'] = json.dumps(ins['actionPara'])
        action_id = self.server.send_data(1, ins, 1)
        res = 0
        for ii in range(20):
            time.sleep(0.3)
            try:
                res = self.server.notes[action_id]['informResult']
                if res > 1:
                    break
                elif res == 0 or ii > 2:
                    break
            except Exception as e:
                pass
                # print('~~~~~~~~~~~~~~~~', e, '---', len(self.server.notes), action_id
        return res

    def check_object_status(self, target=1):
        for npc in range(3):
            request_id = self.server.send_data(2,  {"requestIndex": 0, "targetType": 1, "targetId": target}, 1)
            time.sleep(0.1)
            info = None
            for i in range(9):
                try:
                    info = self.server.notes[request_id]
                    break
                except :
                    time.sleep(0.1)
            if info:
                try:
                    info['statusDetail'] = info['statusDetail'].replace("false", "False")
                    fea = eval(info['statusDetail'])['features']
                    # 'position', 'diretion', 'itemName'
                    return info, fea
                except Exception as e:
                    print(e, info)
        return info, None

    def observation_surrounding(self):
        ins = {"requestIndex": 0, "targetType": 10, "targetId": self.person_id}
        action_id = self.server.send_data(2, ins, 1)
        for ii in range(30):
            time.sleep(0.3)
            try:
                res = self.server.notes[action_id]
                break
            except Exception as e: pass
        if not res:
            return res
        img = json.loads(res["statusDetail"])
        im = img["multiVisionBytes"][0]['bytes']
        byte_array = bytes(im)
        # Load and display PNG files
        nparr = np.frombuffer(byte_array, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image


class Agent(object):
    def __init__(self, sock, env_time, objects):
        self.object_data = objects
        self.times = env_time
        self.running = 1
        self.npcs = []

        self.is_grasp = None
        self.robot = PRS_IK()
        # robot ik algorithm
        self.server = sock
        self.env = Env(self.object_data, self.server.maps)
        self.agent_state = 1
        self.current_info = None
        self.check_for_MLLM = None
        self.temporary_data = None
        self.height_f1 = -16.693447
        self.height_f2 = -5.2174
        self.height_f3 = -0.0499999
        self.position_agent = None  # [0,0,0]
    #                                  x y z
        self.direction_degree = None
        self.direction_vector = {'x': None,'y': None}
        self.map_position_agent = {'x': None, 'y': None, 'floor': None}

    def request_interaction(self, type=0):
        # type=0 head camera, 1 shows hand camera, suggest not to use this function while moving
        ob_rgb = self.observation_camera(type)
        seg, tags = self.get_segmentation(type, 1)
        if isinstance(ob_rgb, np.ndarray) and isinstance(seg, np.ndarray) and tags:
            self.check_for_MLLM = {'seg_matrix': seg, 'tags': tags}
            return ob_rgb
        return 0

    def interaction(self, input_matrix, manipulaton=1):
        #  input_matrix, 0: None, 1: target
        #  manipulation=0 view for recognize, manipulation=1 grasp
        target_list = []
        if self.check_for_MLLM:
            for i in range(input_matrix.shape[0]):
                for j in range(input_matrix.shape[1]):
                    if input_matrix[i][j]:
                      target_list.append(self.check_for_MLLM['seg_matrix'][i][j])
            counter = Counter(target_list)
            try:
                most_common_element, occurrences = counter.most_common(1)[0]
            except:
                print('no object or target in the input matrix')
                return 0
            target_id = None
            if most_common_element and occurrences/len(target_list) > 0.5:
                target_obj = self.check_for_MLLM['tags'][int(most_common_element)]
                try:
                    split_list = target_obj.split('_')
                    target_id = int(split_list[1])
                    obj_n = split_list[0]
                except: pass
                if target_id is None: return 0
            print(target_id, most_common_element, occurrences)
            if manipulaton == 1:
                tar_obj_info = self.object_information_query(obj_id=target_id)
                if not tar_obj_info: return 0
                self.goto_target_goal(tar_obj_info['position'], 1, 1, position_mode=0)
                re = self.direction_adjust(position=tar_obj_info['position'])
                a = self.ik_calculation(tar_obj_info['position'])
                if a:
                    self.arm_control(a)
                self.grasp_object(target_id)
        return 0

    def object_interaction(self, input_matrix, manipulaton=1, type=0):
        # manipulation=0 view for recognize, manipulation=1 grasp, 2 approach,
        # camera type=0 head camera, 1 shows hand camera, suggest not to use this function while moving
        ob_rgb = self.observation_camera(type)
        seg, tags = self.get_segmentation(type, 1)
        if isinstance(ob_rgb, np.ndarray) and isinstance(seg, np.ndarray) and tags:
            check_for_LMM = {'seg_matrix': seg, 'tags': tags}
        else: return 0
        target_list = []
        if np.sum(input_matrix) == 0:
            return 0
        if check_for_LMM:
            for i in range(input_matrix.shape[0]):
                for j in range(input_matrix.shape[1]):
                    if input_matrix[i][j] > 0:
                        target_list.append(check_for_LMM['seg_matrix'][i][j])
            counter = Counter(target_list)
            element_list = []
            try:
                most_common_element, occurrences = counter.most_common(1)[0]
                num = min(len(counter), 3)
                element_list = counter.most_common(num)
            except:
                print('no object or target in the input matrix')
                return 0
            for element in element_list:
                most_common_element, occurrences = element
                target_id, is_npc = None, False
                if most_common_element and occurrences / len(target_list) > 0.33:
                    target_obj = check_for_LMM['tags'][int(most_common_element)]
                    try:
                        split_list = target_obj.split('_')
                        if split_list[0].lower() == 'npc':
                            target_id = int(split_list[2])
                            is_npc = True
                        else:
                            target_id = int(split_list[-1])
                            obj_n = split_list[0]
                    except:
                        pass
                    if target_id is None: return 0
                if target_id is None: return 0
                if is_npc:
                    pos, tar_obj_info = self.npcs[target_id].query_information()
                else:
                    tar_obj_info = self.object_information_query(obj_id=target_id)
                    if not tar_obj_info: return 0
                if manipulaton == 1:
                    try:
                        if "Grabable" not in tar_obj_info['features']: continue
                    except:
                        return 0
                    pos, info = self.pos_query()
                    if self.env.calculate_distance(tar_obj_info['position'], pos) > 3.0:
                        return 0
                    elif self.env.calculate_distance(tar_obj_info['position'], pos) > 1.0:
                        self.goto_target_goal(tar_obj_info['position'], 1, 1, position_mode=0)
                    re = self.direction_adjust(position=tar_obj_info['position'])
                    a = self.ik_calculation(tar_obj_info['position'])
                    if a:
                        self.arm_control(a)
                        time.sleep(1)
                    res = self.grasp_object(target_id)
                    self.joint_control(joint_id=5, target=0)
                    if res:
                        return res
                elif manipulaton == 2:
                    res = self.goto_target_goal(tar_obj_info['position'], 1.5, 1, position_mode=0)
                    return res
                return 0

    def get_room_area(self, target_room='kitchen room', inflation=1):
        room_info = None
        for room_i in self.object_data.room_area:
            if room_i['name'] == target_room:
                room_info = room_i
                break
        if room_info is None: return None
        room_accessible_area = []
        floor = room_info['floor']
        map_i_min, map_i_max, map_j_min, map_j_max = room_info['x'][0], room_info['x'][1], room_info['y'][0], room_info['y'][1]
        map = copy.deepcopy(self.object_data.sematic_map[floor])
        map = np.array(map)
        for ii in range(map_i_min, map_i_max + 1):
            for jj in range(map_j_min, map_j_max + 1):
                if map[ii][jj] == 1:
                    close_to_obstacle = False
                    if inflation:
                        for iii in range(max(0, ii - 1), min(map.shape[0], ii + 2)):
                            for jjj in range(max(0, jj - 1), min(map.shape[1], jj + 2)):
                                if map[iii, jjj] == 0:
                                    close_to_obstacle = True
                    else:
                        close_to_obstacle = True
                    if not close_to_obstacle:
                        room_accessible_area.append((ii, jj))
                        map[ii][jj] = 3
        return room_accessible_area

    def get_receptacles_within_room(self, room_name='kitchen room'):
        # room_receptacle = self.object_data.room_receptacles[room_name]['receptacles']
        # room_receptacles = [[i, rec['name']] for i, rec in enumerate(room_receptacle)]
        room_receptacles = None
        for room_i in self.object_data.room_area:
            if room_i['name'] == room_name:
                room_receptacles = room_i['receptacles_list']
        return room_receptacles

    def calculate_2D_distance(self, point1, point2):
        dis = np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
        return dis

    def goto_receptacle(self, room='kitchen room', recepacle=0, random=0):
        room_info = None
        for room_i in self.object_data.room_area:
            if room_i['name'] == room:
                room_info = room_i
                break
        if room_info is None: return None
        room_receptacle = room_info['receptacles'][recepacle]
        pos, info = self.pos_query()
        floor_robot, robot_i, robot_j = self.map_position_agent['floor'], self.map_position_agent['x'], self.map_position_agent['y']
        floor_receptacle, rec_i, rec_j, _ = self.server.maps.get_point_info(room_receptacle['position'])
        if floor_receptacle != floor_receptacle:
            print('robot and receptacle is not the same floor !')
            return 0, 0
        width = abs(room_receptacle['x'][1] - room_receptacle['x'][0])
        length = abs(room_receptacle['y'][1] - room_receptacle['y'][0])

        scale = self.server.maps.maps_info[floor_robot]['scale']
        ob_distance = np.sqrt(width ** 2 + length ** 2) * 1.5
        free_area = self.get_room_area(room)
        reasonable_points, ob_time = [], 6
        for n in range(ob_time):
            ob_distance -= (ob_distance / ob_time)
            reasonable_points = []
            for po in free_area:
                if self.calculate_2D_distance(po, (rec_i, rec_j)) < ob_distance:
                    reasonable_points.append(po)
            if len(reasonable_points) > 0:
                break
            else:
                print(ob_distance)
        if len(reasonable_points) == 0:
            # print(room_receptacle['position'])
            print('there is no space to observer')
            res = self.goto_target_goal((floor_robot, rec_i, rec_j), radius=2.5, delete_dis=1, position_mode=1)
            return res, 0
        distances = [np.sqrt((i - robot_i) ** 2 + (j - robot_j) ** 2) for i, j in reasonable_points]
        sorted_valid_points = [point for _, point in sorted(zip(distances, reasonable_points))]
        target_point = sorted_valid_points[0]
        # target_point = reasonable_points[0]
        if random:
            random_i = np.random.randint(0, len(reasonable_points))
            target_point = reasonable_points[random_i]
        res = self.goto_target_goal((floor_robot, target_point[0], target_point[1]), radius=1.5, delete_dis=1,
                                    position_mode=1)
        if res:
            # print(res, room_receptacle['position'])
            self.head_camera_look_at(room_receptacle['position'], accuracy=1)
        return res, room_receptacle

    def depth_estimation(self, matrix_target, depth, field_of_view=90):
        target_depth = np.multiply(matrix_target, depth)
        sum_non_zero = np.sum(target_depth)
        count_non_zero = np.count_nonzero(target_depth)
        average_depth = sum_non_zero / count_non_zero
        non_zero_indices = np.nonzero(target_depth)
        # non_zero_elements = target_depth[non_zero_indices]
        # average_non_zero = np.mean(non_zero_elements)
        x_indices, y_indices = non_zero_indices[0], non_zero_indices[1]
        average_x, average_y = np.mean(x_indices), np.mean(y_indices)
        y = matrix_target.shape[1]
        degree = ((average_y-150)/y) * 90
        return average_depth, degree

    def target_direction(self, degree=20, distance=1, target_degree_view=0):
        #   degree is the camera
        pos, info = self.pos_query()
        direction_degree = self.direction_degree
        # degree = info['jointJointTarget']
        camera_direction = - degree + direction_degree
        # print(camera_direction, direction_degree, self.direction_vector)
        floor_r, r_i, r_j = self.map_position_agent['floor'], self.map_position_agent['x'], self.map_position_agent['y']
        # FOV field of view = 90, target_degree_view: left -, right +
        camera_direction = camera_direction - target_degree_view
        scale = self.server.maps.maps_info[floor_r]['scale']
        target_dis = distance / scale
        map = copy.deepcopy(self.object_data.sematic_map[floor_r])
        camera_direction = np.deg2rad(camera_direction)
        target_i, target_j = r_i + np.cos(camera_direction)*target_dis, r_j + np.sin(camera_direction)*target_dis
        map[round(target_i)][round(target_j)] = 5
        # plt.imshow(map)
        # plt.grid(False)
        # plt.show()
        approximate_point = (round(floor_r), round(target_i), round(target_j))
        return approximate_point

    def observation(self, degree=0, camera=0, up_down=10):
        # Depression angle, camera 0 is head 1 is hand
        if camera == 0:
            self.joint_control(joint_id=4, target=up_down)
            self.joint_control(joint_id=14, target=degree)
            ob_rgb = self.observation_camera(camera)
        elif camera == 1:
            if abs(degree) > 150:
                return None
            self.joint_control(joint_id=5, target=degree)
            ob_rgb = self.observation_camera(camera)
        return ob_rgb

    def look360(self, pitch=0):
        m0 = self.observation(-90, up_down=pitch)
        m1 = self.observation(0, up_down=pitch)
        m2 = self.observation(90, up_down=pitch)
        m3 = self.observation(180, up_down=pitch)
        fig, axs = plt.subplots(nrows=1, ncols=4, figsize=(12, 4))

        axs[0].imshow(m0)
        axs[0].set_title('Matrix m0')
        axs[0].axis('off')

        axs[1].imshow(m1)
        axs[1].set_title('Matrix m1')
        axs[1].axis('off')

        axs[2].imshow(m2)
        axs[2].set_title('Matrix m2')
        axs[2].axis('off')

        axs[3].imshow(m3)
        axs[3].set_title('Matrix m3')
        axs[3].axis('off')

        plt.tight_layout()
        plt.show()
        return [m0, m1, m2, m3]

    def goto_and_grasp(self, obj_name=None, target_id=None):
        if target_id is None:
            tars = self.object_data.object_query([obj_name])
            if len(tars) == 0: return 0
            target_id = tars[0]
        tar_obj_info = self.object_information_query(obj_id=target_id)
        if not tar_obj_info: return 0
        print(tar_obj_info)
        self.goto_target_goal(tar_obj_info['position'], 1, 1, position_mode=0)
        re = self.direction_adjust(position=tar_obj_info['position'])
        a = self.ik_calculation(tar_obj_info['position'])
        if a:
            print('---------', a)
        else:
            a = [-0.2, 0, 0.4, 0.6, 0.3]
        self.arm_control(a)
        self.grasp_object(target_id)
        self.joint_control(joint_id=5, target=0)

    def object_information_query(self, obj_id=0):
        instruction = {"requestIndex": 0, "targetType": 1, "targetId": obj_id}
        r_id = self.server.send_data(2, instruction, 1)
        object_info = self.wait_for_respond(r_id, 60)
        if object_info:
            object_info = eval(object_info['statusDetail'])
        return object_info

    def ik_calculation(self, pos_world):
        try:
            x, y, z = pos_world['x'], pos_world['y'], pos_world['z']
            pos_world = {'position': {'x': x, 'y': y, 'z': z}}
        except:
            pos_world = {'position': {'x': pos_world[0], 'y': pos_world[1], 'z': pos_world[2]}}
        pos_transform = {"requestIndex": 1, "actionId": 201, "actionPara": json.dumps(pos_world)}
        # ----------------- get the object information-----------------
        r_id = self.server.send_data(5, pos_transform, 1)
        obj_info1 = self.wait_for_respond(r_id, 75)
        if not obj_info1:
            return 0
        pos_relative = eval(obj_info1['information'])['position']
        # print(obj_info1, '---------IK relative position---')
        joint_targets = self.ik_process(pos_relative['x'], 0, pos_relative['z'])
        return joint_targets

    def arm_control(self, joints_tar=[0, 0, 0, 0, 0]):
        target_execute = {"requestIndex": 1, "actionId": 3,
                          "actionPara": json.dumps({'result': 1, 'data': joints_tar})}
        r_id = self.server.send_data(5, target_execute, 1)
        robot_info1 = self.wait_for_respond(r_id, 300)
        # print(robot_info1, '======---------IK perform')
        return robot_info1

    def initial_pose(self):
        a = [-0.35, 0, 0.3, 0.3, 0.1]
        return self.arm_control(a)

    def grasp_object(self, obj_id):
        if not self.is_grasp:
            grasp_execute = {"requestIndex": 1, "actionId": 4, "actionPara": json.dumps({'itemId': obj_id})}
            r_id = self.server.send_data(5, grasp_execute, 1)
            robot_info2 = self.wait_for_respond(r_id, 60)
            if robot_info2:
                self.is_grasp = obj_id
            return robot_info2
        return None

    def release_object(self):
        if self.is_grasp:
            release_execute = {"requestIndex": 1, "actionId": 5}
            r_id = self.server.send_data(5, release_execute, 1)
            robot_info3 = self.wait_for_respond(r_id, 60)
            if robot_info3:
                # print(robot_info3, '======---------release')
                self.is_grasp = None
            result = self.joint_control(5, 0)
            return robot_info3
        return None

    def joint_control(self, joint_id, target, radian=1):
        if radian:
            target = np.radians(target)
        target_execute = {"requestIndex": 1, "actionId": 2, "actionPara": json.dumps({'jointId': joint_id, 'data': target})}
        r_id = self.server.send_data(5, target_execute, 1)
        robot_info = self.wait_for_respond(r_id, 100)
        if robot_info:
            return 1
        return 0

    def wait_for_respond(self, id, times=60):
        info = None
        for ii in range(int(times)):
            time.sleep(0.1)
            try:
                info = self.server.notes[id]
                break
            except Exception as e: pass
        return info

    def move_forward(self, dis=1.0):
        instruct = {"requestIndex": 0, "actionId": 0, "actionPara": {"distance": 1.0}}
        instruct["actionPara"]["distance"] = dis
        instruct['actionPara'] = json.dumps(instruct['actionPara'])
        r_id = self.server.send_data(5, instruct, 1)
        start_time = time.time()
        time.sleep(dis)
        while True:
            time.sleep(0.2)
            try:
                # {'requestIndex': 0, 'actionId': 0, 'result': 1}
                if self.server.notes[r_id]['result'] == 1:
                    break
            except Exception as e:
                print('~~~~~~~~~~~~~~~~', e, '---', len(self.server.notes), r_id)
        # Record End Time
        end_time = time.time()
        # Calculate the running time of movement
        execution_time = end_time - start_time
        # print("Move forward: ", execution_time, "s")
        return 1

    def rotate_right(self, degree=10):
        result = [degree / 2]
        for angle in result:
            ins = {"requestIndex": 1, "actionId": 1, "actionPara": {"degree": angle}}
            ins['actionPara'] = json.dumps(ins['actionPara'])
            r_id = self.server.send_data(5, ins, 1)
            res = self.wait_for_respond(r_id, 60)
            time.sleep(0.5)
        return res

    def get_all_map(self):
        for map_i in range(3):
            re_id = self.server.send_data(2, {"requestIndex": 101, "targetType": 2, "targetId": map_i}, 1)
            time.sleep(0.1)
            while True:
                try:
                    info = self.server.notes[re_id]
                    ma = info['statusDetail']
                    dict_ma = eval(ma)
                    self.server.maps.add_room(dict_ma)
                    break
                except Exception as e:
                    pass  # print('~~~~~~~~map~~~~~~~~', e)
                time.sleep(0.1)
        # print('get all map: ', type(self.server.maps.floor1), type(self.server.maps.floor2), type(self.server.maps.floor3))

    def pos_query(self):
        info, inf, pos = None, None, None
        for request_i in range(3):
            request_id = self.server.send_data(5, {"requestIndex": 10, "actionId": 10}, 1)
            time.sleep(0.1)
            info = None
            #  {'requestIndex': 10, 'actionId': 0, 'information': '{"position":{"x":-8.397454261779786,"y":0.0027088536880910398,"z":-1.1824144124984742},
            #  "diretion":{"x":0.9973454475402832,"y":-0.01950152963399887,"z":0.07015550881624222}}'}
            pos = None
            for i in range(6):
                try:
                    info = self.server.notes[request_id]
                    break
                except :
                    time.sleep(0.1)
            if info:
                inf = eval(info['information'])
                pos_dire = inf['direction']
                pos = inf['position']
                self.position_agent = pos
                x = pos_dire["x"]
                y = pos_dire["z"]
                self.direction_vector['x'], self.direction_vector['y'] = x, y
                # Calculate the angle (in radians) between the direction vector and the positive x-axis direction
                angle_rad = np.arctan2(y, x)
                # Convert radians to angles
                angle_degree = np.degrees(angle_rad)
                self.direction_degree = angle_degree
                flo, xx, yy, is_o = self.server.maps.get_point_info(pos)
                self.map_position_agent['x'], self.map_position_agent['y'], self.map_position_agent['floor'] = xx, yy, flo
                # print('dgree???????????????????//:', angle_degree)
                return pos, inf
        return pos, inf

    def go_to_there(self, pos, command=0):
        try:
            y = pos[1]
        except:
            pos = [pos['x'], pos['y'], pos['z']]
        if not command:
            command = {"requestIndex": 10, "actionId": 6, "actionPara": {'position': {"x": 0.5, "y": 1.0, "z": 0}}}
        command['actionPara']['position']['x'] = pos[0]
        command['actionPara']['position']['y'] = pos[1]
        command['actionPara']['position']['z'] = pos[2]
        command['actionPara'] = json.dumps(command['actionPara'])
        re_id = self.server.send_data(5, command, 1)
        return re_id

    def goto_target_goal(self, position_tar, radius=1, delete_dis=2, times=6, position_mode=0, accurate=0):
        # 0 (world pos) position_tar:(0.5, 0.1, 1.2), 1: (x=floor_n, y=map_i, z=map_j)
        try:
            xx, yy, zz = position_tar[0], position_tar[1], position_tar[2]
        except:
            xx, yy, zz = position_tar['x'], position_tar['y'], position_tar['z']
        floor, point_list = self.server.maps.get_an_accessible_area(xx, yy, zz, radius, position_mode)
        result_go = 0
        for i_try in range(times):
            if not self.running or self.server.stop_event.is_set() or not self.server.state:
                return 0
            length = len(point_list)
            if length < 1:
                break
            if result_go == 1:
                break
    #         choose a nearest point (p_i, p_j) now = np.random.randint(0, length)
            p_i, p_j = point_list[0][0], point_list[0][1]
            # translate the grid pos to the world pos
            pos_i, pos_j = self.server.maps.get_an_aligned_world_coordinate_randomly(floor, p_i, p_j)
            if accurate:
                pos_i, pos_j = p_i, p_j
            position_go = (pos_i, self.server.maps.floors[floor], pos_j)
            # print(' now plan to {}'.format(position_go))
            for i in range(2):
                if not self.running or self.server.stop_event.is_set() or not self.server.state:
                    return 0
                if accurate:
                    position_go = (xx, yy, zz)
                action_id = self.go_to_there(position_go)
                result = 0
                while True:
                    if not self.running or self.server.stop_event.is_set() or not self.server.state:
                        return 0
                    time.sleep(0.5)
                    try:
                        if self.server.notes[action_id]['result'] == 1:
                            result = self.server.notes[action_id]['result']
                            break
                        elif self.server.notes[action_id]['result'] < 1:
                            break
                    except: pass
                time.sleep(0.1)
                if result == 1:
                    pos, info = self.pos_query()
                    if pos:
                        dis = self.env.calculate_distance(pos, position_go)
                        if dis < 1:
                            result_go = 1
                            break
                time.sleep(2)
            if result_go == 0:
                accurate = 0
                # Reverse loop deletion of points with a distance of 2
                for i in range(len(point_list) - 1, -1, -1):
                    point = point_list[i]
                    if np.sqrt((point[0] - p_i) ** 2 + (point[1] - p_j) ** 2) < delete_dis:
                        del point_list[i]
            elif result_go == 1:
                # print('$$$$$ arrive at: ', position_go)
                return result_go
        if result_go == 0: pass
            # print('$$$$$not arrive: ', position_tar)
        return result_go

    def observation_camera(self, camera_type=0):
        #  0 head camera, 1 hand camera
        c_type = 13
        if camera_type == 0:
            c_type = 13
        elif camera_type == 1:
            c_type = 14
        ins = {"requestIndex": 1, "actionId": c_type, "actionPara": {'height': 640, 'width': 480}}
        # new instruction
        action_id = self.server.send_data(5, ins, 1)
        res = self.wait_for_respond(action_id, 60)
        if not res:
            return res
        img = json.loads(res["information"])
        im = img["multiVisionBytes"][0]['bytes']
        byte_array = bytes(im)
        # Display image loading and display PNG file
        np_arr = np.frombuffer(byte_array, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def get_depth(self, camera_type=0):
        #  0 head camera, 1 hand camera
        c_type = 17
        if camera_type == 0:
            c_type = 15
        elif camera_type == 1:
            c_type = 16
        ins = {"requestIndex": 1, "actionId": c_type, "actionPara": {'height': 300, 'width': 300}}
        ins['actionPara'] = json.dumps(ins['actionPara'])
        action_id = self.server.send_data(5, ins, 1)
        res = self.wait_for_respond(action_id, 60)
        if not res:
            return res
        img = json.loads(res["information"])
        im = img["multiVisionBytes"][0]['bytes']
        byte_array = bytes(im)
        nparr = np.frombuffer(byte_array, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # image = Image.open(io.BytesIO(byte_array))
        # image = image.convert('I;16')
        # pil_image = Image.fromarray(image.astype('uint8'), mode='L')
        depth_matrix = image/255*10
        return depth_matrix

    def get_segmentation(self, camera_type=0, decode=0, show=False):
        #  0 head camera, 1 hand camera
        c_type = 17
        if camera_type == 0:
            c_type = 17
        elif camera_type == 1:
            c_type = 18
        ins = {"requestIndex": 1, "actionId": c_type, "actionPara": {'height': 300, 'width': 300}}
        ins['actionPara'] = json.dumps(ins['actionPara'])
        action_id = self.server.send_data(5, ins, 1)
        res = self.wait_for_respond(action_id, 60)
        if not res:
            return res
        img = json.loads(res["information"])
        im = img["multiVisionBytes"][0]['bytes']
        byte_array = bytes(im)
        # Display image loading and display PNG file
        # image = Image.open(io.BytesIO(byte_array))
        nparr = np.frombuffer(byte_array, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Convert image byte stream to Image object
        if show:
            cv2.imshow('image', image)
            cv2.waitKey(10)
            cv2.destroyAllWindows()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if decode:
            im, tags = self.decode_segment(image)
            return im, tags
        return image

    def decode_segment(self, image):
        width, height = image.shape[1], image.shape[0]
        object_tag = self.object_data.segment_tag
        rgb_id = self.object_data.rgb_to_id
        target = {}
        seg_matrix = np.zeros((height, width))
        image = image / 255
        formatted_arr = np.array([f'{x:.2f}' for x in np.nditer(image)])
        image = formatted_arr.reshape(image.shape)
        # Traverse each pixel of the image
        for x in range(height):
            for y in range(width):
                # Obtain the RGB value of pixels
                pixel_value = image[x, y]
                r, g, b = pixel_value[0], pixel_value[1], pixel_value[2]
                rrggbb = (r, g, b)
                if rrggbb == self.object_data.background:
                    continue
                pixel_id = rgb_id.get(rrggbb, 0)
                if pixel_id is not None:
                    seg_matrix[x][y] = pixel_id
        values_set = set(np.unique(seg_matrix))
        for value in values_set:
            value = round(value)
            if value:
                target[value] = object_tag[value]['tag']
        return seg_matrix, target

    def query_near_objects(self):
        instruction = {"requestIndex": 0, "actionId": 12}
        r_id = self.server.send_data(5, instruction, 1)
        obj_info = self.wait_for_respond(r_id, 60)
        object_info = eval(obj_info['information'])
        return object_info["nearby"]

    def go_to_target_object(self, object_id=None, name='Apple_what_your_nee', feature='Grabable_what_your_need',
                            distance=1, random_mode=1):
        items = self.query_near_objects()
        if not items: return 0
        all_objs = []
        if len(items) != 0:
            for item_id in items:
                item_info = self.object_data.objects[item_id]
                if not item_info['isOccupied']:
                    obj_f = [n.lower() for n in item_info['features']]
                    check_id = 0
                    if object_id is not None:
                        if item_id['itemId'] == object_id:
                            check_id = 1
                    if feature.lower() in obj_f or name.lower() in item_info['itemName'].lower() or check_id:
                        item_info = self.server.object_query(item_id)
                        all_objs.append(item_info)
        else:
            return 0
        if len(all_objs) == 0:
            return 0
        if random_mode == 1:
            target_obj = np.random.choice(all_objs)
        else:
            target_obj = all_objs[0]
        if not target_obj: return 0
        pos = target_obj['position']
        res = self.goto_target_goal(pos, distance, 3, 10)
        return res

    def site_view(self, pos=(0, 0, 0)):
        try:
            x, y, z = pos['x'], pos['y'], pos['z']
        except:
            x, y, z = pos[0], pos[1], pos[2]
        if -0.2 < y:
            y = 3
        elif -5 < y:
            y = -2
        else:
            y = -10
        ins = {"requestIndex": 0,"targetType": 12,"siteVisionPos": {"x": x, "y": y, "z": z}}
        r_id = self.server.send_data(2, ins, 1)
        receive = self.wait_for_respond(r_id, 60)
        if not receive: return None
        img = json.loads(receive["statusDetail"])
        im = img["multiVisionBytes"][0]['bytes']
        byte_array = bytes(im)
        nparr = np.frombuffer(byte_array, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Convert image byte stream to Image object
        # cv2.imshow('image', image)
        # cv2.waitKey(15)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def go_to_destination(self, tar_location, ids=0):
        location_now, outcome = None, 0
        try:
            location_now = self.env.location[tar_location]
        except:
            locations = list(self.env.location.keys())
            for index, loc in enumerate(locations):
                if tar_location.lower() in loc.lower():
                    location_now = self.env.location[loc]
                    break
        if location_now:
            outcome = self.goto_target_goal(location_now[ids], 2, 2, 20)
        return outcome

    # def navigate(self, map_floor, goal):
    #     #  map of scene, goal to navigation
    #     path_map = copy.deepcopy(self.server.maps.maps_info[map_floor]['grid'])
    #     path_map = np.array(path_map)
    #     print(f"started 1 at {time.strftime('%X')}")
    #     self.pos_query()
    #     start = (self.map_position_agent['x'], self.map_position_agent['y'])
    #     # start_vector = (self.direction_vector['x'], self.direction_vector['y'])
    #     # Input initial vector, initial coordinate point, and facing coordinate point
    #     x0, y0 = 1, 0  # Initial vector
    #     x, y = 0, 0  # Initial coordinate point
    #     xx, yy = 0, 1  # Facing coordinate points
    #
    #     rotation_angle = self.calculate_rotation_angle(goal[0], goal[1])
    #     print('-----', rotation_angle, '-------')
    #     print(f"started 2 at {time.strftime('%X')}")
    #     # path, turns = self.astar(start, goal, path_map)
    #     # Plan the path to the goal
    #     queue1 = Queue()
    #     # shared_list1, shared_list2 = mp.Array('c', 0), mp.Array('c', 0)
    #     # print(shared_list1, shared_list2)
    #     process1 = Process(target=astar, args=(start, goal, path_map, [], [], queue1))
    #     process1.start()
    #     process1.join()
    #     print(f"started 3 at {time.strftime('%X')}")
    #     shared_list1 = queue1.get()
    #     shared_list2 = queue1.get()
    #     print(shared_list2)
    #     rotation_angle = self.calculate_rotation_angle(shared_list2[0][0], shared_list2[0][1])
    #     print('-----', rotation_angle, '-------')
    #     xxx, yyy, zzz = self.server.maps.get_world_position(map_floor, shared_list2[0][0], shared_list2[0][1])
    #     dis = self.calculate_distance(xxx, zzz)
    #     print('-----', dis, '-------')
    #     # self.move_forward(dis)
    #     print(f"started 5 at {time.strftime('%X')}")
    #     # print(mp.cpu_count()) 16

    def calculate_rotation_angle(self, xx, yy, accuracy=1):
        start = (self.map_position_agent['x'], self.map_position_agent['y'])
        if accuracy:
            start = (self.position_agent['x'], self.position_agent['z'])
        start_vector = (self.direction_vector['x'], self.direction_vector['y'])
        x0, y0, x, y = start_vector[0], start_vector[1], start[0], start[1]
        v1 = np.array([x0, y0])  # Initial vector
        v2 = np.array([xx - x, yy - y])  # The vector of the oriented coordinate point relative to the initial coordinate point
        dot_product = np.dot(v1, v2)
        det = np.linalg.det([v1, v2])
        angle_radians = np.arctan2(det, dot_product)
        angle_degrees = np.degrees(np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))))
        cross_product = np.cross(v1, v2)# Determine the direction of rotation
        if cross_product > 0:
            # left rotation
            angle_degrees = -angle_degrees
        elif cross_product < 0: pass
        #     right
        else: pass
        return angle_degrees

    def head_camera_look_at(self, position, accuracy=0):
        try:
            xx, yy = position['x'], position['z']
        except:
            xx, yy = position[0], position[2]
        # if world_position and accuracy == 0:
        #     flo, xx, yy, is_o = self.server.maps.get_point_info(position)
        self.pos_query()
        rotation_angle = self.calculate_rotation_angle(xx, yy, accuracy=accuracy)
        # print(rotation_angle)
        result = self.rotate_right(rotation_angle)
        self.pos_query()
        rotation_angle = self.calculate_rotation_angle(xx, yy, accuracy)
        result = self.joint_control(5, rotation_angle)
        return result

    def direction_adjust(self, position, pos_input=0, accuracy=1):
        # world_position = (22.38, 0.1, -0.17) or {'x': , 'y': , 'z': }
        if pos_input:
            flo, xx, yy = position[0], position[1], position[2]
            accuracy = 0
        else:
            flo, xx, yy, is_o = self.server.maps.get_point_info(position)
        if accuracy:
            try:
                xx, yy = position['x'], position['z']
            except:
                xx, yy = position[0], position[2]
        self.pos_query()
        rotation_angle = self.calculate_rotation_angle(xx, yy)
        result = self.rotate_right(rotation_angle)
        self.pos_query()
        rotation_angle = self.calculate_rotation_angle(xx, yy)
        result = self.joint_control(5, rotation_angle)
        return result

    def calculate_distance(self, x_x, y_y):
        point1 = np.array([self.position_agent['x'], self.position_agent['y']])
        point2 = np.array([x_x, y_y])
        distance = np.linalg.norm(point2 - point1)
        return distance

    def ik_process(self, x, y, z):
        res = self.input_pos(self.robot, x, y, z)
        if np.all(res == -1):
            return 0
        else:
            return res.tolist()

    def input_pos(self, robot, x, y, z, phi=0, theta=0, psi=0, plot=0):
        A = eul2r(phi, theta, psi)
        # Representing the rotational Euler angle
        # [0.5, 0, 1.87]
        t = [x, y, z]
        AT = SE3.Rt(A, t)
        if phi == 0 and theta == 0 and psi == 0:
            AT = self.rotation_matrix(t[0], t[1], t[2])
        # The rotation Euler angle represents the displacement on the x, y, and z axes
        # AT = SE3.Rt(A, t)
        # AT represents the 4 * 4 transformation matrix of the end effector
        sol = robot.ik(AT)
        # print(robot.fkine([-0.11530289, 0.3, 0.24709773, 0.42730769, 0.72559458]))
        if sol[1]:
            if plot:
                robot.arm.plot(sol[0])
                # If a feasible solution is calculated, visualize it (swift package)
                time.sleep(20)
            return sol[0]
        return np.array([-1])

    def rotation_matrix(self, x, y, z):
        # print('hypotenuse and length of robot arm limit')return None
        # print(x, y, z)
        if x < -0.4:
            x = -0.4
        elif x > 0.5:
            x = 0.5
        if 0.2 > z:
            z = 0.2
        elif 1.0 < z:
            z = 1.05
        if y < -0.5:
            y = -0.5
        elif y > 0.5:
            y = 0.5
        elif abs(y) < 0.03:
            y = 0
        hypotenuse = np.sqrt(y ** 2 + z ** 2)
        if hypotenuse > 1.01:
            z = np.sqrt(1.05 - y ** 2)
        a, b, c = -2.222439753175887, 0.7599754447016618, 1.981407645745737
        theta = a * z ** 2 + b * z + c
        phi = y * 4
        A = eul2r(phi, theta, 0)
        t = [x, y, z]
        AT = SE3.Rt(A, t)
        return AT


def astar(start, goal, map_matrix, list1, list2, queue, initial_direction=(1, 0)):

    def heuristic(node, is_start):
        # return abs(node[0] - goal[0]) + abs(node[1] - goal[1])
        if is_start:
            # Calculate the angle between the node and the initial direction
            direction_cost = abs(node[0] - start[0]) * initial_direction[0] + abs(node[1] - start[1]) * \
                             initial_direction[1]
        else:
            direction_cost = 0
        # Calculate the Manhattan distance from the node to the nearest obstacle
        node_np = np.array(node)
        obstacles = np.transpose(np.where(map_matrix == 0))
        min_dist_to_obstacle = np.min(np.sum(np.abs(obstacles - node_np), axis=1))
        # Calculate the angle between the node and the initial direction
        return abs(node[0] - goal[0]) + abs(node[1] - goal[1]) + min_dist_to_obstacle + direction_cost*3
        # return abs(node[0] - goal[0]) + abs(node[1] - goal[1])
        # node_np = np.array(node)
        # obstacles = np.transpose(np.where(map_matrix == 0))
        # min_dist_to_obstacle = np.min(np.sum(np.abs(obstacles - node_np), axis=1))
        # return abs(node[0] - goal[0]) + abs(node[1] - goal[1]) + min_dist_to_obstacle

    # representation of the point with goal
    # Heuristic value for initialization starting point
    start_heuristic = heuristic(start, True)
    open_set = [(start_heuristic, start)]
    # save current position, [1]updating with movement
    came_from = {}
    # save path
    g_score = {start: 0}
    # score for evaluate point
    while open_set:
        current_heuristic, current = heappop(open_set)

        # pos [x][y]
        if current == goal:
            break
        # pos all around [(x+1, y), (x, y+1), (x-1, y), (x, y-1)]
        for neighbor in [(current[0] - 1, current[1]), (current[0] + 1, current[1]),
                         (current[0], current[1] - 1), (current[0], current[1] + 1)]:
            # Boundary Check
            if 0 <= neighbor[0] < map_matrix.shape[0] and 0 <= neighbor[1] < map_matrix.shape[1]:
                if map_matrix[neighbor[0], neighbor[1]] == 0:
                    continue
                # Obstacle examination
                tentative_g_score = g_score[current] + 1
                # Choose the best neighbor point
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(neighbor, False)
                    heappush(open_set, (f_score, neighbor))
    #                 saving with the score of the point (n, (x,y))
    paths_p = []
    turns_p = []  # Store points that require turning
    previous_direction = None  # The forward direction of the previous point
    current = goal
    # Reverse search
    while current != start:
        paths_p.append(current)
        neighbors = [(current[0] - 1, current[1]), (current[0] + 1, current[1]),
                     (current[0], current[1] - 1), (current[0], current[1] + 1)]
        next_vertex = came_from[current]
        dx = next_vertex[0] - current[0]
        dy = next_vertex[1] - current[1]
        current_direction = (dx, dy)
        # Determine whether to turn
        if previous_direction is not None and previous_direction != current_direction:
            turns_p.append(current)  # the current point needing turning right/left
        previous_direction = current_direction
        current = next_vertex
    paths_p.append(start)
    paths_p.reverse()

    # -------------visualization------------
    path, turns, path_map = paths_p, turns_p, map_matrix
    list1, list2 = paths_p, turns_p
    print(len(list1), len(list2))
    queue.put(list1)
    queue.put(list2)
    for point in path:
        if point in turns:
            path_map[point[0], point[1]] = 3
        else:
            path_map[point[0], point[1]] = 2
    # turning
    print("turning here：", turns)
    # control agent to move according to path, Moving point by point
    # for point in turns:
    #     print(point)
    # Mark as 2 on the path
    for point in path:
        path_map[point[0], point[1]] = 2

    # Output the points that need to turn
    for point in turns:
        path_map[point[0], point[1]] = 3
    # Visual map
    print(f"started 4 at {time.strftime('%X')}")
    plt.imshow(path_map, cmap='viridis', interpolation='nearest')
    plt.colorbar(ticks=[0, 1, 2])
    plt.title('Path Planning using A* Algorithm')
    plt.show()

    return paths_p, turns_p, list1, list2


# IK server
class Planar3DOF(ERobot):
    """
    Class that imports a planar3DOF Robot
    """

    def __init__(self):
        args = super().URDF_read(
            "robot/PRS_Robot.urdf", tld="./")

        super().__init__(
            args[0],
            name=args[1])

        self.manufacturer = "Utadeo"
        # self.ee_link = self.ets[9]

        # zero angles, L shaped pose
        self.addconfiguration("qz", np.array([0, 0, 0, 0, 0]))

        # ready pose, arm up
        self.addconfiguration("qr", np.array([0, 0, 0, 0, 0]))
        # self.addconfiguration("qr", np.array([0, -pi / 2, pi / 2, 0, 0]))

        # straight and horizontal
        self.addconfiguration("qs", np.array([0, 0, 0, 0, 0]))
        # self.addconfiguration("qs", np.array([0, 0, pi / 2, 0, 0]))

        # nominal table top picking pose
        self.addconfiguration("qn", np.array([0, 0, pi / 4, pi/4, 0]))

        # # nominal table top picking pose
        # self.addconfiguration("qm", np.array([0, pi / 4, pi]))
        #

    @staticmethod
    def load_my_path():
        # print(__file__)
        os.chdir(os.path.dirname(__file__))



class PRS_IK(object):
    def __init__(self):
        self.arm = Planar3DOF()

    def ik(self, AT):
        sol = self.arm.ik_GN(AT, q0 = [0, 0, 0, 0, 0])
        return sol  # display joint angles

    def fkine(self, arr=[0, 0, 0, 0, 0]):
        return self.arm.fkine(arr)
    # print(robot.fkine(robot.configs['qz']))  # FK shows that desired end-effector pose was achieved

    def trajectory(self, p0, p1, step):
        qt = rtb.tools.trajectory.jtraj(self.arm.configs['qr'], self.arm.configs['qz'], 100)
        # qt = rtb.tools.trajectory.jtraj(sol.q, sol.q, 100)
        qt = rtb.tools.trajectory.jtraj(p0, p1, step)
        # print(qt.q)
        return qt

    def show(self, pose=[0,0,0,0,0], time=10):
        self.arm.plot(pose)
        time.sleep(time)

