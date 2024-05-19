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

def random_number(n):
    selected_number = np.random.randint(0, n)  # Generate a random number within the interval [0, n-1]
    return selected_number

class Env(object):
    def __init__(self):
        self.height_f1 = -16.693447
        self.height_f2 = -5.2174
        self.height_f3 = -0.0499999
        f1, f2, f3 = self.height_f1, self.height_f2, self.height_f3
        self.landmark = {
            'warehouse': [(11.41, f1, -6.26, 'doorway'), (11.5, f1, -54, 'center')],
            'laboratory': [(5.02, f2, 1.52, 'doorway'), (16.17, f2, 6.82, 'center')],
            'clinic': [(-4.90, f2, -1.01, 'doorway'), (-3.14, f2, -5.02, 'center')],
            'meeting room': [(4.83, f3, -2.13, 'doorway'), (2, f3, -4.04, 'center')],
            'office': [(5.16, f3, 1.39, 'doorway'),(3.92, f3, 6.4, 'sit'), (7.43, f3, 7.35, 'center'), (8.7, f3, 6.3, 'center'), (4.83, f3, 3.11, 'center')],
            'kitchen': [(-15.44, f3, -1.81, 'doorway'), (-18.3, f3, -5.9, 'free'), (-14.77, f3, -7.07, 'center')],
            'restroom': [(-4.9, f3, 1.39, 'doorway'), (-7.08, f3, 8.01, 'center')],
            'bedroom': [(19.88, f2, -1.2, 'gate'), (13.4, f3, -22.74, 'center'), (17.68, f3, -22.03, 'doorway'), (11.73, f3, -21.04, 'center')],
            'lobby': [(23.94, f3, 3.1, 'doorway'), (23.12, f3, 7.19, 'center')],
            'mark': [(19.61, f3, -0.35, '0'), (15.5, f3, -4.55, 1), (19.61, f3, -9.47, '2')],
            'hallway': [(19.61, f3, -0.35, 'none'), (18.1, f3, 0.0, 'center')],
            'hall': [(19.61, f3, -0.35, 'none'), (24.1, f3, -4.9, 'center')],
            'wc': [(19.61, f3, -0.35, 'none'), (-12.9, f3, 2.1, 'center')],
            'elevator': [(19.61, f3, -0.35, 'none'), (27.5, f3, -0.8, 'center')]
        }
        self.landmark_list = [
            'warehouse',
            'laboratory',
            'clinic',
            'meeting room',
            'office',
            'kitchen',
            'restroom',
            'bedroom',
            'lobby',
            'mark',
            'hallway',
            'hall',
            'wc',
            'elevator'
        ]
        self.location = {
            "F1_EnergyRoom": [(21.65, -16.4, -24.8), (11.5, -16.4, -36.5)],
            "F1_ConveyorRoom": [(-0.4, -16.4, -2.8), (9.1, -16.4, -2.9)],
            "F1_StorageRoom01": [(10.4, -16.4, -54.1), (10.1, -16.4, -46.3)],
            "F1_StorageRoom02": [(1.5, -16.4, -14.1), (9.5, -16.4, -26.5)],
            "F2_LabRoom01": [(14.5, -5.1, 4.1), (14.4, -5.1, 7.3)],
            "F2_LabRoom02": [(4.8, -5.1, 3.9), (5.1, -5.1, 7.1)],
            "F2_LabRoom03": [(-4.9, -5.1, 3.5), (-3.4, -5.1, 6.2)],
            "F2_Restroom": [(-15.2, -5.1, 2.2), (-15.9, -5.1, 3.5)],
            "F2_WarmRoom": [(15.7, -5.1, -19.5), (15.4, -5.1, -17.1)],
            "F2_StorageRoom": [(-11.9, -5.1, 1.7), (-13.4, -5.1, 1.9)],
            "F2_ServerRoom": [(15.6, -5.1, -12.1), (14.5, -5.1, -13.1)],
            "F2_MedicalRoom01": [(4.8, -5.1, -3.2), (3.6, -5.1, -5.9)],
            "F2_MedicalRoom02": [(-4.9, -5.1, -3.6), (-8.5, -5.1, -6.8)],
            "F2_MedicalRoom03": [(-12.4, -5.1, -3.7), (-11.5, -5.1, -6.7)],
            # "F3_Bedroom": [(, 0.1,), (, 0.1,)],
            "F3_GymRoom": [(14.7, 0.1, 3.3), (17.7, 0.1, 4.4)],
            "F3_OfficeRoom01": [(-2.1, 0.1, -3.4), (-2.3, 0.1, -7.6)],
            "F3_OfficeRoom02": [(-7.2, 0.1, -3.3), (-7.8, 0.1, -7.1)],
            "F3_RestRoom": [(-15.5, 0.1, 2.8), (-15.9, 0.1, 3.8)],
            "F3_OfficeSpaceRoom": [(4.9, 0.1, 3.2), (3.3, 0.1, 6.1)],
            "F3_KitchenRoom": [(-14.7, 0.1, -3.2), (-15.9, 0.1, -6.9)],
            "F3_StorageRoom": [(-11.8, 0.1, 2.7), (-13.4, 0.1, 2.1)],
            "F3_LivingRoom": [(-4.9, 0.1, 3.3), (-3.1, 0.1, 8.1)],
            "F3_ConferenceRoom": [(4.9, 0.1, -3.2), (1.5, 0.1, -4.6)]

        }

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
            print(point1_array, point2_array)
            distance = np.linalg.norm(point2_array - point1_array)
        return distance


class Npc(object):
    def __init__(self, person_id, sock, env_time, objects):
        self.object_data = objects
        self.person_id = person_id
        self.env = Env()
        self.times = env_time
        self.server = sock
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
        person_id = self.person_id
        if not command:
            command = {"requestIndex": 10, "npcId": 0, "actionId": 1, "actionPara": {"destination": {"x": 0.5, "y": 1.0, "z": 0}}}
        command['npcId'] = person_id
        # print(command)
        # print(type(command['actionPara']))
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
            # else:
        return False, info

    def query_information(self):
        pos, info = self.where_npc()
        datas = None
        if pos:
            datas = eval(info['statusDetail'])
            obj_closed = datas['closeRangeItemIds']
        return pos, datas

    def goto_randomly(self, position_tar, radius=1.5, delete_dis=3, times=10):
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
            now = np.random.randint(0, length)
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
                time.sleep(1.5)
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

    def go_to_place(self, tar, specific=1, rad=2, del_d=2, times=20):
        destination = self.env.landmark[tar][specific]
        print('^^^^^^^^^^^^ here will be ', destination)
        result = 0
        result = self.goto_randomly(destination, rad, del_d, times)
        return result

    def random_walk(self):
        for i in range(1000):
            if not self.server.state or self.server.stop_event.is_set() or not self.running:
                return 0
            random_key = np.random.choice(list(self.env.location.keys()))
            location_now = self.env.location[random_key]
            result = self.goto_randomly(location_now[1], 2, 2, 20)
            if result:
                res, obj = self.go_to_object('Seat')
                if res:
                    suc = self.npc_action('sit', obj)
                    if suc:
                        time.sleep(10)
                        self.npc_action('stand')
                        time.sleep(3)
                    else:
                        time.sleep(5)

    def walk_around(self):
        time.sleep(1)
        for i in range(1000):
            if not self.server.state or self.server.stop_event.is_set() or not self.running:
                return 0
            if i < 3 and False:
                continue
            n = random_number(13)
            # n = i
            time.sleep(3)
            # print('############### now go to {} -'.format(self.env.landmark_list[n]), i)
            destination = self.env.landmark[self.env.landmark_list[n]][1]
            print(n, destination)
            go_res = self.go_to_place(self.env.landmark_list[n], 1)
            # if go_res:
            #     print('good good good for {} -'.format(self.env.landmark_list[n]), i)
            # action_id = self.go_to_here(destination)
            # while True:
            #     time.sleep(1)
            #     try:
            #         if self.server.notes[action_id]['informResult'] == 2:
            #             break
            #     except Exception as e:
            #         print('~~~~~~~~~~~~~~~~', e,'---', len(self.server.notes), action_id)
            # pos, info = self.where_npc()
            # print('$$$$$arrive: ', pos)
            time.sleep(0.5)

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

    def continuous_simulation(self, length=10):
        npc_day = {0: [
            # 'id': 0, "schedule":
            ['exercise', 'hallway'], ['stand', 'bedroom'], ['stand', 'bedroom'], ['stand', 'bedroom'],
            ['stand', 'bedroom'], ['stand', 'bedroom'], ['stand', 'bedroom'], ['stand', 'bedroom'],
            #  -> 0-8h: room    ->   9-11h: office  ->   12-13h: kitchen
            ['sit', 'office'], ['playComputer', 'office'], ['playComputer', 'office'], ['playComputer', 'office'],
            ['sitLookHandObject', 'office'],
            #  -> 14-15h: dating   16-17h: meetingroom   18-19h: kitchen
            ['layingDownOnDoor', 'office'], ['playComputer', 'office'], ['playComputer', 'office'],
            ['playComputer', 'office'], ['layingDownOnDoor', 'office'], ['sitLookHandObject', 'office'],
            # 20-21h: lobby   22-23h: bedroom
            ['playComputer', 'office'], ['playComputer', 'office'], ['layingDownOnDoor', 'office'], ['playComputer', 'office'], ['playComputer', 'office']
        ], -1: [
            # 'id': 0, "schedule":
            ['stand', 'bedroom'], ['stand', 'bedroom'], ['stand', 'bedroom'], ['stand', 'bedroom'],
            ['stand', 'bedroom'], ['stand', 'hallway'], ['stand', 'bedroom'], ['stand', 'bedroom'],
            #  -> 0-8h: room    ->   9-11h: office  ->   12-13h: kitchen
            ['sit', 'office'], ['playComputer', 'office'], ['playComputer', 'office'], ['sit', 'kitchen'],
            ['sit', 'kitchen'],
            #  -> 14-15h: dating   16-17h: meetingroom   18-19h: kitchen
            ['sit', 'mark'], ['playGame', 'mark'], ['waveHandAtWaist', 'meeting room'],
            ['waveHandOverHead', 'meeting room'], ['sit', 'kitchen'], ['sitLookHandObject', 'kitchen'],
            # 20-21h: lobby   22-23h: bedroom
            ['exercise', 'lobby'], ['dance', 'lobby'], ['stand', 'bedroom'], ['stand', 'bedroom'], ['stand', 'bedroom']
        ], 1:
         [
            # 'id': 0, "schedule":

            #  -> 0-8h: room    ->   9-11h: office  ->   12-13h: kitchen
            ['sit', 'office'], ['playComputer', 'office'], ['playComputer', 'office'], ['sit', 'kitchen'], ['exercise', 'hall'],
            ['sit', 'kitchen'],
            #  -> 14-15h: dating   16-17h: meetingroom   18-19h: kitchen
            ['sit', 'mark'], ['exercise', 'mark'], ['waveHandAtWaist', 'meeting room'],
            ['waveHandOverHead', 'meeting room'], ['sit', 'kitchen'], ['sitLookHandObject', 'kitchen'],
            # 20-21h: lobby   22-23h: bedroom
            ['exercise', 'lobby'], ['dance', 'lobby'], ['stand', 'bedroom'], ['stand', 'laboratory'], ['stand', 'laboratory'],
            ['stand', 'laboratory'], ['stand', 'mark'], ['stand', 'bedroom'],
            ['stand', 'mark'], ['exercise', 'mark'], ['stand', 'restroom'], ['dance', 'restroom']
        ], 2:
        [
            # 'id': 0, "schedule":
            ['sit', 'mark'], ['playGame', 'mark'], ['waveHandAtWaist', 'meeting room'],
            ['waveHandOverHead', 'hallway'], ['waveHandAtWaist', 'hall'], ['stand', 'lobby'], ['stand', 'restroom'],
            ['streachHead', 'restroom'], ['stand', 'bedroom'], ['dance', 'bedroom'], ['streachHead', 'hall'],
            #  -> 0-8h: room    ->   9-11h: office  ->   12-13h: kitchen
            ['stand', 'clinic'], ['stand', 'clinic'], ['playComputer', 'clinic'], ['playComputer', 'clinic'],
            ['stand', 'kitchen'], ['waveHandOverHead', 'hallway'], ['exercise', 'hall'], ['stand', 'lobby'],
            #  -> 14-15h: dating   16-17h: meetingroom   18-19h: kitchen
            ['waveHandOverHead', 'meeting room'], ['sit', 'kitchen'], ['sitLookHandObject', 'kitchen'],
            # 20-21h: lobby   22-23h: bedroom
            ['waveHandOverHead', 'hallway'], ['dance', 'meeting room']
        ]
        }
        for day_i in range(length):
            week, hour, min = self.get_now_time()
            print('############ now is {} '.format(week), hour, min)
            self.one_day(npc_day[self.person_id])
            if not self.server.state or self.server.stop_event.is_set() or not self.running:
                return 0
            while True:
                week_n, hour_n, min_n = self.get_now_time()
                if week != week_n:
                    print('---------hey folks, new day is coming --------')
                    break

    def one_day(self, a_day):
        # Get hours, minutes, and seconds
        week, hour, min = self.get_now_time()
        print('############now ', hour, min)
        while hour < 23:
            week, hour_now, min = self.get_now_time()
            if not self.server.state or self.server.stop_event.is_set() or not self.running:
                return 0
            if hour_now != hour or min > 55:
                hour = hour_now
                tar_action, tar_place = a_day[hour][0], a_day[hour][1]
                print('@@@@@@@ now is : {} {} {}'.format(hour, tar_action, tar_place))
                print(self.action_state, '++++++++++', self.place_state)
                if tar_action != self.action_state or tar_place != self.place_state:
                    if self.action_state == 'sit':
                        action_id = self.mapping_action_type[self.actions['stand'][0]]
                        ins = copy.deepcopy(self.instruction_type[action_id])
                        ins['actionId'] = 0
                        ins['npcId'] = self.person_id
                        self.action_execution(ins)
                    elif self.actions[self.action_state][0] == 400:
                        print('should iiiiiiiiiiiiiinterrupt')
                        action_id = self.mapping_action_type[self.actions['interrupt'][0]]
                        ins = copy.deepcopy(self.instruction_type[action_id])
                        ins['actionPara']["showType"] = -1
                        ins['npcId'] = self.person_id
                        print(action_id, 'interrupt', ins)
                        self.action_execution(ins)

                if tar_place != self.place_state:
                    res = self.go_to_place(tar_place)
                    if res:
                        self.place_state = tar_place
                if tar_action != self.action_state:

                    action_para = self.actions[tar_action]
                    instruct = self.mapping_action_type[action_para[0]]
                    print(action_para,'oooooooooo',instruct)
                    ins_template = copy.deepcopy(self.instruction_type[instruct])

                    # 先打断，先坐下------------
                    ins_template['npcId'] = self.person_id
                    if action_para[0]<300:
                        ins_template['actionId'] = action_para[0]
                    if tar_action == 'stand':
                        pass
                    elif tar_action == 'sit':
                        pos, info = self.where_npc()
                        if pos:
                            tar = self.object_data.object_parsing(info)
                            if tar:
                                print(self.check_object_status(tar))
                                # tar = self.object_data.object_parsing(self.near_items, ['Stool'])
                                ins_template['actionPara']["itemId"] = tar
                            else:
                                ins_template['actionPara']["itemId"] = 1
                                # sit fail
                                # continue
                    elif tar_action == 'pick':
                        ins_template['actionPara']["itemId"] = 1
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
                        self.action_state = tar_action
                        # print('*********successfully: ', tar_action, ' - ', tar_place)
                        time.sleep(2)
            time.sleep(0.5)
        return 1

    def npc_action(self, tar_action, tar_object=0):
        action_para = self.actions[tar_action]
        instruct = self.mapping_action_type[action_para[0]]
        # print(action_para, 'oooooooooo', instruct)
        ins_template = copy.deepcopy(self.instruction_type[instruct])
        # ------------
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
                # print('~~~~~~~~~~~~~~~~', e, '---', len(self.server.notes), action_id)
        # pos = self.where_npc()
        # print('$$$$$arrive: ', pos)
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
        # image = Image.open(io.BytesIO(byte_array))
        # print(image.size)
        # Display Image
        # image.show()
        # image.save('img1.png')
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
        self.env = Env()
        self.server = sock
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

    def object_information_query(self, obj_id=0):
        instruction = {"requestIndex": 0, "targetType": 1, "targetId": obj_id}
        r_id = self.server.send_data(2, instruction, 1)
        object_info = self.wait_for_respond(r_id, 60)
        if object_info:
            object_info = eval(object_info['statusDetail'])
        return object_info

    def ik_control(self, tar=['apple']):
        obj_n = self.object_data.object_query(tar)
        if len(obj_n) == 0:
            return 0
        obj = obj_n[0]
        # ----------------- read the id of the target object
        pos_request = {"requestIndex": 0, "targetType": 1, "targetId": obj}
        r_id = self.server.send_data(2, pos_request, 1)
        obj_info = self.wait_for_respond(r_id, 15)
        if obj_info:
            pos_world = eval(obj_info['statusDetail'])
            # the world position of the target object
        else:
            # return 0
            pos_world = {'position': {'x': 28.81, 'y': 1.01, 'z': -2.997}}

        self.direction_adjust(pos_world['position'])
        # -----------------------pose adjustment-----------------

        pos_transform = {"requestIndex": 1, "actionId": 201, "actionPara": json.dumps(pos_world)}
        # ----------------- get the object information-----------------
        r_id = self.server.send_data(5, pos_transform, 1)
        obj_info1 = self.wait_for_respond(r_id, 15)
        if not obj_info1:
            return 0
        pos_relative = eval(obj_info1['information'])['position']
        print(obj_info1, '---------------------------IK relative position----------------------')
        joint_targets = self.ik_process(pos_relative['x'], 0, pos_relative['z'])
        #
        # --------------- calculate the relative position for IK estimate-----------------
        target_execute = {"requestIndex": 1, "actionId": 3, "actionPara": json.dumps({'result': 1, 'data': joint_targets})}
        r_id = self.server.send_data(5, target_execute, 1)
        robot_info1 = self.wait_for_respond(r_id, 30)
        print(robot_info1, '-===-=---------IK perform')
        time.sleep(5)
        # --------------- execute the joint targets for arrive the object-----------------

        grasp_execute = {"requestIndex": 1, "actionId": 4, "actionPara": json.dumps({'itemId': obj})}
        r_id = self.server.send_data(5, grasp_execute, 1)
        robot_info2 = self.wait_for_respond(r_id, 30)
        print(robot_info2, '-===-=---------grasp')
        time.sleep(3)
        # --------------- grasping begin-----------------

        tars = joint_targets
        if 0:
            try:
                # tars[0] -= 0.2
                target_execute = {"requestIndex": 1, "actionId": 3,
                                  "actionPara": json.dumps({'result': 1, 'data': tars})}
                r_id = self.server.send_data(5, target_execute, 1)
                robot_info1 = self.wait_for_respond(r_id, 30)
                print(robot_info1, '-===-=---------high')
                time.sleep(5)
            except: pass
        # target_execute = {"requestIndex": 1, "actionId": 3,
        #                   "actionPara": json.dumps({'result': 1, 'data': tars})}
        # r_id = self.server.send_data(5, target_execute, 1)
        # robot_info1 = self.wait_for_respond(r_id, 30)
        # print(robot_info1, '-===-=---------adjkwdna')
        # time.sleep(5)
        return 1

        self.rotate_right(30)

        release_execute = {"requestIndex": 1, "actionId": 5}
        r_id = self.server.send_data(5, release_execute, 1)
        robot_info3 = self.wait_for_respond(r_id, 20)
        print(robot_info3, '-===-=---------release')

        self.rotate_right(20)

        # normal pose for robot arm
        tars = [-0.5,0,0.4,0.6,0.3]
        target_execute = {"requestIndex": 1, "actionId": 3,"actionPara": json.dumps({'result': 1, 'data': tars})}
        r_id = self.server.send_data(5, target_execute, 1)
        robot_info1 = self.wait_for_respond(r_id, 30)
        print(robot_info1, '-===-=---------normal pose')

        self.pos_query()

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

    def joint_control(self, joint_id, target):
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
        time.sleep(dis*3)
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
        # Calculate the running time of function A
        execution_time = end_time - start_time
        print("Move forward: ", execution_time, "s")
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
        # self.server.ma
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
        print('get all map: ', type(self.server.maps.floor1), type(self.server.maps.floor2), type(self.server.maps.floor3))

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

    def move_to(self, n=9):
        destination = self.env.landmark[self.env.landmark_list[n]][0]
        return destination

    def go_to_there(self, pos, command=0):
        if not command:
            command = {"requestIndex": 10, "actionId": 6, "actionPara": {'position': {"x": 0.5, "y": 1.0, "z": 0}}}
        command['actionPara']['position']['x'] = pos[0]
        command['actionPara']['position']['y'] = pos[1]
        command['actionPara']['position']['z'] = pos[2]
        command['actionPara'] = json.dumps(command['actionPara'])
        re_id = self.server.send_data(5, command, 1)
        return re_id

    def goto_target_goal(self, position_tar, radius=1, delete_dis=3, times=6, position_mode=0, accurate=0):
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
        for ii in range(60):
            time.sleep(0.2)
            try:
                res = self.server.notes[action_id]
                break
            except: pass
        if not res:
            return res
        # with open('data.json', 'w') as file:
        #     json.dump(res, file)
        img = json.loads(res["information"])
        im = img["multiVisionBytes"][0]['bytes']
        byte_array = bytes(im)
        # Display image loading and display PNG file
        np_arr = np.frombuffer(byte_array, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # image = Image.open(io.BytesIO(byte_array))
        # Display Image
        # image.show()
        # image.save('img2.png')
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
        # cv2.imshow('image', image)
        # cv2.waitKey(0)
        # Display image loading and display PNG file
        # image = Image.open(io.BytesIO(byte_array))
        # image = image.convert('I;16')
        # pil_image = Image.fromarray(image.astype('uint8'), mode='L')
        # pil_image.show()
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
                if pixel_id:
                    seg_matrix[x][y] = pixel_id
        values_set = set(np.unique(seg_matrix))
        for value in values_set:
            value = int(value)
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

    def navigate(self, map_floor, goal):
        #  map of scene, goal to navigation
        path_map = copy.deepcopy(self.server.maps.maps_info[map_floor]['grid'])
        path_map = np.array(path_map)
        print(f"started 1 at {time.strftime('%X')}")
        self.pos_query()
        start = (self.map_position_agent['x'], self.map_position_agent['y'])
        # start_vector = (self.direction_vector['x'], self.direction_vector['y'])
        # Input initial vector, initial coordinate point, and facing coordinate point
        x0, y0 = 1, 0  # Initial vector
        x, y = 0, 0  # Initial coordinate point
        xx, yy = 0, 1  # Facing coordinate points

        rotation_angle = self.calculate_rotation_angle(goal[0], goal[1])
        print('-----', rotation_angle, '-------')
        print(f"started 2 at {time.strftime('%X')}")
        # path, turns = self.astar(start, goal, path_map)
        # Plan the path to the goal
        # manager = mp.Manager()
        # shared_list1 = manager.list()
        # shared_list2 = manager.list()
        queue1 = Queue()
        # shared_list1, shared_list2 = mp.Array('c', 0), mp.Array('c', 0)
        # print(shared_list1, shared_list2)
        process1 = Process(target=astar, args=(start, goal, path_map, [], [], queue1))
        process1.start()
        process1.join()
        print(f"started 3 at {time.strftime('%X')}")
        # for point in path:
        #     if point in turns:
        #         path_map[point[0], point[1]] = 3
        #     else:
        #         path_map[point[0], point[1]] = 2
        # # turning
        # print("turning here：", turns)
        # # control agent to move according to path, Moving point by point
        # for point in turns:
        #     print(point)
        # # Mark as 2 on the path
        # for point in path:
        #     path_map[point[0], point[1]] = 2
        #
        # # Output the points that need to turn
        # print("Output the points that need to turn：")
        # for point in turns:
        #     # print(point)
        #     path_map[point[0], point[1]] = 3
        # # Visual map
        # print(f"started 4 at {time.strftime('%X')}")
        # plt.imshow(path_map, cmap='viridis', interpolation='nearest')
        # plt.colorbar(ticks=[0, 1, 2])
        # plt.title('Path Planning using A* Algorithm')
        # plt.show()
        # print(shared_list2, shared_list1)
        shared_list1 = queue1.get()
        shared_list2 = queue1.get()
        print(shared_list2)
        rotation_angle = self.calculate_rotation_angle(shared_list2[0][0], shared_list2[0][1])
        print('-----', rotation_angle, '-------')
        xxx, yyy, zzz = self.server.maps.get_world_position(map_floor, shared_list2[0][0], shared_list2[0][1])
        dis = self.calculate_distance(xxx, zzz)
        print('-----', dis, '-------')
        # self.move_forward(dis)
        print(f"started 5 at {time.strftime('%X')}")
        # print(mp.cpu_count()) 16

    def calculate_rotation_angle(self, xx, yy, accuracy=1):
        start = (self.map_position_agent['x'], self.map_position_agent['y'])
        if accuracy:
            start = (self.position_agent['x'], self.position_agent['z'])
        start_vector = (self.direction_vector['x'], self.direction_vector['y'])
        # print(xx,yy,'=====', start, '=====', start_vector)
        x0, y0, x, y = start_vector[0], start_vector[1], start[0], start[1]
        v1 = np.array([x0, y0])  # Initial vector
        v2 = np.array([xx - x, yy - y])  # The vector of the oriented coordinate point relative to the initial coordinate point
        # print('-----------------',v1,'-------',v2)
        # 计算向量夹角
        dot_product = np.dot(v1, v2)
        det = np.linalg.det([v1, v2])
        angle_radians = np.arctan2(det, dot_product)
        # angle_degrees = np.degrees(angle_radians)
        angle_degrees = np.degrees(np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))))
        cross_product = np.cross(v1, v2)# Determine the direction of rotation
        if cross_product > 0:
            # left rotation
            angle_degrees = -angle_degrees
        elif cross_product < 0: pass
        #     right
        else: pass
        # print(angle_degrees)
        return angle_degrees

    def direction_adjust(self, position, accuracy=1):
        # world_position = (22.38, 0.1, -0.17) or {'x': , 'y': , 'z': }
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
        # print(point2, point1)
        distance = np.linalg.norm(point2 - point1)
        return distance

    def ik_process(self, x, y, z):
        res = self.input_pos(self.robot, x, y, z)
        # print(x, y, z, res)
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
        # print(sol)
        # print(robot.fkine([-0.11530289, 0.3, 0.24709773, 0.42730769, 0.72559458]))
        # print(eul2r(0.3, 1.4, 0.02))
        if sol[1]:
            if plot:
                robot.arm.plot(sol[0])
                # If a feasible solution is calculated, visualize it (swift package)
                time.sleep(20)
            return sol[0]
        return np.array([-1])

    def rotation_matrix(self, x, y, z):
        # print('hypotenuse and length of robot arm limit')return None
        print(x, y, z)
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
        # print(x, y, z, '!!!', phi, theta)
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
    print("需要转弯的点：")
    for point in turns:
        # print(point)
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

