import copy
import asyncio
import numpy as np
import os
import sys
import time
import subprocess
# import atexit

from socket import *
import threading
import json
import struct
from enum import Enum
from game_demo import *
import ast
import pickle
from map_process import RoomMap
from npc_control import Npc, Agent
import datetime
from multiprocessing import Process, Queue, Value, Lock


class EnvTime(object):
    def __init__(self, speed=120, year=2025, month=3, day=12, hour=6, minute=50, second=0, end=2050):
        # Define start date. At a rate of speed(120) times
        self.start_date = datetime.datetime(year, month, day, hour, minute, second)
        # Define time multiplier
        self.time_multiplier = speed
        self.running = 1
        self.end = end
        # Simulation time
        self.current_date = self.start_date
        self.start_time = self.start_date
        # self.current_date.isoweekday()
        self.week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def set_time(self, year=2025, month=3, day=12, hour=6, minute=50, second=0, end=2050):
        self.current_date = datetime.datetime(year, month, day, hour, minute, second)
        print(self.current_date)

    def time_simulation(self, stop_event):
        while True:
            # print(stop_event.is_set())
            if not self.running or stop_event.is_set():
                break
            # print("Current Date:", self.current_date)
            # Accelerate at 120 times the speed
            time_delta = datetime.timedelta(seconds=1)  # Add one more day
            self.current_date += time_delta * self.time_multiplier
            # Control simulation speed
            time.sleep(1)  # Update every second
            # Termination conditions can be added, such as stopping simulation when a specific date is reached
            if self.current_date.year > self.end:
                break

    def time_difference(self):
        time_diff = self.current_date - self.start_time
        hours = time_diff.total_seconds() // 3600
        # print("The time difference is% d hours" % hours)
        return time_diff.days

    def weekday_now(self):
        return self.week[self.current_date.weekday()]

    def simulation_start(self):
        self.start_time = self.current_date


# message define
class MsgCmd(Enum):
    # 0 disconnects, 1 server sends behavior instructions, 2 servers send status requests, 3 clients reply with behavior callbacks,
    # 4 clients reply with target status, 5 instructions to robots, 6 requests/feedback about robot clients
    EXIT = 0
    Instruction = 1
    Request = 2
    Result = 3
    State = 4
    Control = 5
    Information = 6
    Server_Update_Config = 7
    Server_Device_Create_Request = 8
    Server_Device_Inform_Request = 9
    Server_Device_Status_Request = 10
    Client_Device_Status_Response = 11


class Server(object):
    def __init__(self, stop_event):
        self.stop_event = stop_event
        self.state = 1
        self.clients = []
        self.messages = []
        self.information = ''
        # 1.Create a socket
        self.sock = socket(AF_INET, SOCK_STREAM)
        # 2. Prepare to connect to the server and establish a connection
        serve_ip = 'localhost'
        serve_port = 8000  # search for available port starting from 8000
        # tcp_socket.connect((serve_ip,serve_port))
        # Connect to the server, establish a connection, with parameters in tuple form
        tcp_address = ('localhost', 8000)
        # Provide a mechanism for checking ports
        sock_result = 0
        while not sock_result:
            try:
                self.sock.bind(tcp_address)
                sock_result = 1
            except:
                serve_port += 1
                tcp_address = ('localhost', serve_port)
        with open('unity/PRS_Data/StreamingAssets/config.json', 'r') as file:
            env_data = json.load(file)
        env_data["serverConnectionPort"] = serve_port
        with open('unity/PRS_Data/StreamingAssets/config.json', 'w') as file:
            json.dump(env_data, file)
        print('server started: ', str(tcp_address))
        MAX_CONNECTION = 100
        # Start listening for connections
        self.sock.listen(MAX_CONNECTION)
        self.headerSize = 12
        self.count = 0
        # self.robot = PRS_IK()
        # robot ik algorithm
        self.maps = RoomMap()
        self.notes = {}
        self.byte_stream = bytes()
        self.header_length = 0
        self.sock.settimeout(10)

    def wait_for_connection(self):
        while True:
            try:
                now_client, addr = self.sock.accept()
                print('Connected by', now_client)
                self.state = 2
                now_client.settimeout(300)
                self.clients.append([addr, now_client])
            except: pass
            for index_client, n_client in enumerate(self.clients):
                # result = self.sock.connect_ex(n_client)
                try:
                    result = n_client[1].getsockname()
                    r = n_client[1].getpeername()
                    # print('===========perfect connection============')
                except Exception as e:
                    print(e, n_client[0], 'Connected Closed Now')
                    try:
                        self.clients.remove(n_client)
                        if len(self.clients) == 0 and self.state == 2:
                            self.state = 0
                            self.stop_event.set()
                    except:
                        pass
            if not self.state or self.stop_event.is_set():
                print(self.state, 'No waiting for connection')
                self.sock.close()
                break
            if len(self.clients):
                time.sleep(0.5)
            else:
                time.sleep(0.01)

    def check_connection(self):
        pass
    #     for index_client, n_client in enumerate(self.clients):
    #         # result = self.sock.connect_ex(n_client)
    #         rrr = n_client[1].recv(1024)
    #         result = n_client[1].getsockname()
    #         r = n_client[1].getpeername()

    def handle_data(self, n_client):
        # receive message from client -> information process
        data = n_client.recv(10240000)
        if not data:
            return 0
        else:
            self.messages.append(data)
        # print('---------------------------------'， 'Received: msg')
        # ------------------parsing info from unity---------------------
        # self.messages.append(data.decode())
        try:
            # self.unpack(data)
            pass
        except Exception as e:
            print(data)
            print(e)
        # self.send_back({'result': 1})
        return 1

    def message_process(self):
        while True:
            if not self.state or self.stop_event.is_set():
                self.state = 0
                print(self.state, 'Processing Completed')
                break
            if len(self.messages) > 0:
                for msg_i, msg in enumerate(self.messages):
                    try:
                        self.unpack(msg)
                    except Exception as e:
                        print('.........parsing error............', e, type(msg))
                        self.state = 0
                    finally:
                        del self.messages[msg_i]
            else:
                time.sleep(0.005)

    def receive_data(self):
        while True:
            # self.check_connection()
            for n_client in self.clients:
                try:
                    # Processing received message
                    res = self.handle_data(n_client[1])
                except Exception as e:
                    print(e, n_client[0], 'Connected closed')
                    try:
                        self.clients.remove(n_client)
                        if len(self.clients) == 0 and self.state == 2:
                            self.state = 0
                            self.stop_event.set()
                    except:
                        pass
            time.sleep(0.005)
            if not self.state or self.stop_event.is_set():
                print(self.state, 'Connection closed')
                self.sock.close()
                break

    def send_data(self, cmd=1, data={"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}, recv=0):
        send_finish = 0
        while not send_finish:
            if len(self.clients)==0: break
            for n_client in self.clients:
                self.check_connection()
                try:
                    if cmd < 8:
                        data['requestIndex'] = self.count
                        self.count = self.count + 1
                    elif cmd == 0:
                        self.state = 0
                    msg, msg_data = self.pack(cmd, data, recv)
                    n_client[1].send(msg)
                    send_finish = 1
                    return data['requestIndex']
                    break
                except Exception as e:
                    print(e, n_client[0])
                    try:
                        self.clients.remove(n_client)
                        if len(self.clients) == 0:
                            self.state = 0
                    except: pass
        return False

    def send_back(self, response={'result': 0}):
        f = 0
        while not f:
            for n_client in self.clients:
                self.check_connection()
                try:
                    info = json.dumps(response)
                    n_client[1].send(info.encode("utf8"))
                    print('Sent: ', info.encode("utf8"))
                    f = 1
                    return 1
                except Exception as e:
                    print(e, n_client[0])
                    try:
                        self.clients.remove(n_client)
                    except: pass

    def pack(self, cmd, _body, _recv=0):
        body = json.dumps(_body)
        # Convert the message body to Json format and convert it to byte encoding
        header = [body.__len__(), cmd, _recv]
        # Form a list of message headers in order
        headPack= struct.pack("3I", *header)
        #  Use struct to package message headers and obtain byte encoding
        sendData = headPack+body.encode("utf8")
        # Combine message header bytes and message body bytes together
        return sendData, body

    def handle_msg(self, headPack ,body):
        """Classify and process received message strings"""
        # data processing
        cmd= 'ad'
        try:
            cmd = MsgCmd(headPack[1]).name  # Get the value of Code\
        except Exception as e:
            print(headPack[1])
        # print('python get================cmd is', cmd)
        is_recv = headPack[2]
        # print("Received 1 packet->bodySize:{}, cmd:{}, recv:{}".format(headPack[0], cmd, is_recv))
        body = body.replace("false", "False")
        body = body.replace("true", "True")
        body = body.replace("none", "None")
        p = json.loads(body)  # Decode and deserialize strings into JSON objects
        dict_data = ast.literal_eval(p)
        # self.information += str(cmd) + str(body)
        # Check the message type
        # Instruction = 1
        # Request = 2
        # Result = 3
        # State = 4
        # Control = 5
        # Information = 6
        dict_d = copy.deepcopy(dict_data)
        del dict_d['requestIndex']
        self.notes[dict_data['requestIndex']] = dict_d
        if cmd == "EXIT":
            self.state = 0
            print('0、Env is over, exit!')
            return
        elif cmd == "Result": pass
            # print('3、Execution results from Unity', dict_data)
        elif cmd == "State": pass
            # Storing parameter information
            # print('4、Detailed information obtained id: {}'.format(dict_data['requestIndex']))
            # # dict_map = ast.literal_eval(dict_ma["points"])
        elif cmd == "Control":
            pass
        # IK is here
        elif cmd == "Information": pass
            # print("6、This is robot information", dict_data['requestIndex'], ', length- ', len(dict_data),)
        else:
            print("\nUnknown cmd:{0}".format(cmd))
        # Continue receiving messages
        #self._recv_bytes()
        # print(self.notes)

    def unpack(self, data):
        headPack = struct.unpack('3I', bytearray(data[:self.headerSize]))
        bodySize = headPack[0]
        body = data[self.headerSize:self.headerSize + bodySize]
        try:
            self.handle_msg(headPack, body.decode("utf8"))
        except ValueError:
            if not self.header_length or len(self.byte_stream) == 0:
                self.header_length = headPack
                self.byte_stream += body
            else:
                self.byte_stream += data
                if len(self.byte_stream) >= self.header_length[0]:
                    # data_byte = self.byte_stream.decode("utf8")
                    self.handle_msg(self.header_length, self.byte_stream.decode())
                    self.byte_stream = bytes()
                    self.header_length = 0
        return 1

    def unpack_pro(self, data, msgHandler):
        dataBuffer = bytes()
        if data:
            self.dataBuffer += data
            while True:
                # Jump out of the function to continue receiving data when there is insufficient data in the message header
                if len(self.dataBuffer) < self.headerSize:
                    # print("Packet (% s Byte) is smaller than the length of the message header, causing a small loop to break out" % len(self.dataBuffer))
                    break
                # struct: represent Network order，3I represents 3个unsigned int
                # msg_length = struct.unpack("I", bytearray(msg[:4]))[0]
                # Obtain information length
                headPack = struct.unpack('3I', bytearray(self.dataBuffer[:self.headerSize]))
                # Decode the message header
                # Get message body length
                bodySize = headPack[0]
                # Handling subcontracting situations, jumping out of the function to continue receiving data
                if len(self.dataBuffer) < self.headerSize + bodySize:
                    # print("Packet (% s Byte) incomplete (total of% s Bytes), skipping small loop“ % (len(self.dataBuffer), self.headerSize + bodySize))
                    break
                # Read the content of the message body
                body = self.dataBuffer[self.headerSize:self.headerSize + bodySize]
                self.handle_msg(headPack, body.decode("utf8"))
                # Handling of packet sticking and obtaining the next part of the data packet
                self.dataBuffer = self.dataBuffer[self.headerSize + bodySize:]
            if len(self.dataBuffer) != 0:
                return True  # Continue receiving messages
            else:
                return False  # No longer receiving messages
        else:
            return False  # No longer receiving messages

    def wait_for_respond(self, id, times=60):
        info = None
        for ii in range(int(times)):
            time.sleep(0.1)
            try:
                info = self.notes[id]
                break
            except Exception as e:
                pass
        return info

    def object_query(self, obj_id=0):
        instruction = {"requestIndex": 0, "targetType": 1, "targetId": obj_id}
        r_id = self.send_data(2, instruction, 1)
        object_info = self.wait_for_respond(r_id, 60)
        if object_info:
            object_info = eval(object_info['statusDetail'])
        return object_info

    def object_nearby_detect(self, obj_id=0):
        instruction = {"requestIndex": 1, "targetType": 20, "targetId": obj_id}
        r_id = self.send_data(2, instruction, 1)
        object_info = self.wait_for_respond(r_id, 60)
        if object_info:
            object_info = eval(object_info['statusDetail'])
            return object_info['touchedIds']
        return None

    def object_transform(self, obj_type=0, target_id=4, pos=(0, 0, 0), rotation=0):
        # obj_type = 0: npc, obj_type = 1: items in the env
        try:
            position = {"x": pos[0], "y": pos[1], "z": pos[2]}
        except:
            position = {"x": pos['x'], "y": pos['y'], "z": pos['z']}
        instruction = {"requestIndex": 1, "objectTransformHandles": []}
        para = {"objectType": obj_type, "objectId": target_id, "objectPos": position, "objectDir":
            {"x": 0, "y": 90, "z": 0}}
        # para = json.dumps(para)
        instruction['objectTransformHandles'].append(para)
        #       {"objectType":1,"objectId":10,"objectPos":{"x":5,"y":3,"z":5},"objectDir":{"x":90,"y":0,"z":0}}
        r_id = self.send_data(7, instruction, 1)
        object_info = self.wait_for_respond(r_id, 60)
        return object_info

    def env_finish(self, process, npcs):
        if process:
            process.terminate()
            # Waiting for the process to end (optional, but recommended)
            process.wait()
        self.send_data(0, {"requestIndex": 10, "actionId": 1}, 0)
        # movement demo
        # print('00100')
        self.state = 0
        for npc in npcs:
            npc.running = 0
        self.stop_event.set()
        self.sock.close()
        # print(self.state, type(self.state))
        print(threading.active_count(), ' ------ env is ready to end')
        time.sleep(3)
        print(threading.active_count(), ' ------ thank you for using')


class Command(object):

    def __init__(self, ser, game, per, objects):
        self.id = 0
        self.web = game
        self.server = ser
        self.tar = [0, 1]
        self.near_items = None
        self.object_data = objects
        # 0 disconnects, 1 server sends behavior instructions, 2 servers send status requests, 3 clients reply with behavior callbacks, 4 clients reply with target status, 5 instructions to robots, 6 requests/feedback about robot clients
        self.instruction = [
            [0, {'this is': 'an example for python command to unity API'}, 0],

            [1, {"requestIndex": 10, "npcId": 0, "actionId": 10, "actionPara": "{\"itemId\":177}"}, 1],
            # [1, {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}, 1],
            #    python ins index,  npc,
            # [[0,npc_john,position],[]]
            # info -> items.json   id->name

            # 1  npc stand
            # [1, {"requestIndex":10,"npcId":0,"actionId":10,"actionPara":"{\"itemId\":177}"}, 1],
            #   npc sit
            [1, {"requestIndex":10,"npcId":0,"actionId":1,"actionPara":"{\"destination\":{\"x\":-14.56,\"y\":0.0,\"z\":-4.3}}"}, 1],
            # # 2  npc walk to (x,y,z)
            # [1, {"requestIndex":10,"npcId":0,"actionId":2,"actionPara":"{\"angle\":50}"}, 1],
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 0, "actionPara": ""}, 1],
            # 3  npc turn n degrees
            [1, {"requestIndex":10,"npcId":0,"actionId":100,"actionPara": "{\"handType\":-1,\"itemId\":1}"}, 1],
            # 4  npc pick
            [1, {"requestIndex":10,"npcId":0,"actionId":101,"actionPara":"{\"handType\":-1,\"position\":{\"x\":5.0,\"y\":12.0,\"z\":5.0}}"}, 1],
            # 5  npc put
            [1, {"requestIndex":10,"npcId":0,"actionId":300,"actionPara":"{\"expressionType\":100}"}, 1],
            # 6  npc emoji
            [1, {"requestIndex":10,"npcId":0,"actionId":300,"actionPara":"{\"expressionType\":101}"}, 1],
            # 7  npc stand
            # [1, {"requestIndex":10,"npcId":0,"actionId":300,"actionPara":"{\"expressionType\":102}"}, 1],
            [1, {"requestIndex":10,"npcId":0,"actionId":102,"actionPara":"{\"handType\":-1}"},1],
            # 8  npc stand
            [2,  {"requestIndex":0,"targetType":0,"targetId":0}, 1],
            # [2, {"requestIndex": 0, "targetType": 1, "targetId": 2}, 1],
            # 9  npc information query
            # [2,  {"requestIndex":0,"targetType":1,"targetId":3}, 1],
            [2, {"requestIndex": 101, "targetType": 2, "targetId": 1}, 1],
            # 10 object information query
            [5, {"requestIndex": 0, "actionId": 0, "actionPara": "{\"distance\":1.0}"}, 1],
            # 11 robot move forward
            [5, {"requestIndex": 1, "actionId": 1, "actionPara": "{\"degree\":90}"}, 1],
            # 12 robot turn
            [5, {"requestIndex": 2, "actionId": 2, "actionPara": "{\"degree\":90}"}, 1],
            # 13 robot turn
            [5, {"requestIndex": 10, "requireId": 0}, 1],
            # 14 robot position
            [5, {"requestIndex": 11, "requireId": 1}, 1],
            # 15 robot joint

            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":100}"}, 1],
            # 16
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":101}"}, 1],
            # 17
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":102}"}, 1],
            # 18
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":103}"}, 1],
            # 19
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":104}"}, 1],
            # 20
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":-1}"}, 1],
            # 21
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":105}"}, 1],
            # 22
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":106}"}, 1],
            # 23
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":200}"}, 1],
            # 24
            # [1, {"requestIndex": 10, "npcId": 3, "actionId": 400, "actionPara": "{\"showType\":201}"}, 1],
            [1, {"requestIndex":0,"targetType":10,"targetId":0}, 1]
            # 25
        ]
        self.npc = per

    def chioce(self, index):
        print("click the Button ", index)
        # Convert strings to dictionaries
        data = self.instruction[index]
        if index == 2:
            # data = self.instruction[2]
            action_dict = json.loads(data[1]["actionPara"])

            # 设置 x 和 y 的随机值
            # action_dict["destination"]["x"] = round(np.random.uniform(-1, 1), 2)
            # action_dict["destination"]["z"] = round(np.random.uniform(-1, 1), 2)

            # 更新 actionPara 字符串
            data[1]["actionPara"] = json.dumps(action_dict)
            self.instruction[index] = data

        elif index == 3:
            # [1, {"requestIndex": 10, "npcId": 0, "actionId": 2, "actionPara": "{\"angle\":50}"}, 1],
            for ii in range(10):
                data[1]["npcId"] = ii
                self.send_to_client(data)
        elif index == 4:
            action_dict = json.loads(data[1]["actionPara"])
            action_dict["itemId"] = self.tar[1]
            data[1]["actionPara"] = json.dumps(action_dict)
            self.instruction[index] = data
        elif index == 1:
            action_dict = json.loads(data[1]["actionPara"])
            tar = self.object_data.object_parsing(self.near_items, ['Stool', 'Chair'])
            action_dict["itemId"] = tar
            data[1]["actionPara"] = json.dumps(action_dict)
            self.instruction[index] = data
        #  ---------instruction send----------
        ins_id = self.send_to_client(self.instruction[index])
        # print(ins_id, 'sended')
        if index == 9:
            ins = self.object_data.check_feedback(self.server, ins_id)
            self.near_items = ins
            self.tar[0] = self.object_data.object_parsing(ins, ['Stool'])
            self.tar[1] = self.object_data.object_parsing(ins, ['Apple'])
    #   get response of unity from server messages
        self.web.text = self.server.information

    def send_to_client(self, inf):
        res = self.server.send_data(inf[0], inf[1], inf[2])
#         def send_data(self, cmd=1, data={"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}, recv=0):
        return res


class ObjectsData(object):

    def __init__(self):
        with open('unity/PRS_Data/StreamingAssets/itemInfo.json', 'r') as file:
            json_data = json.load(file)
        with open('unity/PRS_Data/StreamingAssets/roomInfo.json', 'r') as file:
            room_data = json.load(file)
        with open('unity/PRS_Data/StreamingAssets/segmentationTagColorInfo.json', 'r') as file:
            seg_tag_data = json.load(file)
        with open('data/npc_data.json', 'r') as file:
            json_npc = json.load(file)
        with open('D:\\github\\EmbodiedAI02\\VerticleSlice\\Assets\\StreamingAssets\\receptacleInfo.json', 'r') as file:
            json_receptcle = json.load(file)
        rece = json_receptcle['receptacleItemBounds']
        # decode JSON
        seg_data = []
        rgb_id = dict()
        for index_tag, item_tag in enumerate(seg_tag_data['TagColors']):
            # data_i = json.loads(item_tag)
            seg_data.append(item_tag)
            r_n, g_n, b_n = float(item_tag['color']['r']), float(item_tag['color']['g']), float(item_tag['color']['b'])
            r_n, g_n, b_n = '{:.2f}'.format(r_n), '{:.2f}'.format(g_n), '{:.2f}'.format(b_n)
            rgb = (r_n, g_n, b_n)
            rgb_id[rgb] = index_tag

        env_objects = []
        for json_i in json_data['statusDetails']:
            data = json.loads(json_i)
            env_objects.append(data)

        env_rooms = []
        for json_i in room_data['statusDetails']:
            data = json.loads(json_i)
            env_rooms.append(data)
        room_index = []
        for room_i, roo in enumerate(env_rooms):
            # print()
            xx, zz = [], []
            for point in roo['roomBoudaryPoints']:
                xx.append(point['x'])
                zz.append(point['z'])
            name = roo['roomName']
            # na = name.split('_')
            room_index.append({'name': name, 'x': [min(xx), max(xx)], 'y': roo['roomCenter']['y'], 'z': [min(zz), max(zz)]})
            # print('----------------')

        self.room_area = room_index

        self.objects = env_objects
        self.rooms = env_rooms
        self.segment_tag = seg_data
        self.rgb_to_id = rgb_id
        self.characters = json_npc['npc']
        self.room_receptacles = None
        self.sematic_map = [None, None, None]
        # print(env_rooms)
        grab_obj = [
            'BoxedChocolate01', 'InjectableMedicationBottle_2', 'InjectableMedicationBottle_1', 'Apple_2', 'Kiwi',
            'BoxedCake02', 'ButterSauce', 'PlasticBottle03', 'BoxedCake01', 'PlasticBottle03WithGreenLid',
            'WaterBottle_Blue_3',
            'WaterBottle_Blue_1', 'PlasticBottle03WithYellowLid', 'TomatoSauce', 'Spoon_2', 'Tomato', 'Cup_3', 'Cup_2',
            'RedBeansCan', 'BaggedCake02', 'RedChill', 'MeatCan03', 'MeatCan01', 'PeaCan01', 'Cup_1', 'MeatCan02',
            'ChocolateSauce', 'BaggedCake01', 'Spoon_1', 'MobilePhone_3', 'PlasticBottle03WithRedLid',
            'ChiliSauce', 'MobilePhone_1', 'ConsolegamingPad', 'MobilePhone_2', 'Spoon_3', 'BoxedCake03', 'HoneySauce',
            'Apple_1', 'Banana', 'BaggedCake03', 'BoxedChocolate02', 'InjectableMedicationBottle_3',
            'WaterBottle_Blue_2',
            'PeaCan02', 'PlasticBottle03WithBlueLid', 'Apple_3', 'PeanutSauce']
        items = dict()
        for obj in self.objects:
            name = obj['itemName']
            fea = obj['features']
            if "Grabable" in fea and name in grab_obj:
                items[name] = dict()
                items[name]["id"] = obj['itemId']
                items[name]['position'] = obj['position']
        # print(items)
        self.grasp_items = items
        self.receptacle_mark(rece)

    def receptacle_mark(self, obj_rec):
        recp = []
        for rec in obj_rec:
            id = rec['itemId']
            obj = self.objects[id]
            name, id = obj['itemName'], obj['itemId']
            position = obj['position']
            lis = rec['receptacleBounds']
            x_max, x_min = lis[0]['x'], lis[0]['x']
            z_max, z_min = lis[0]['z'], lis[0]['z']
            for item in lis:
                x_max = max(x_max, item['x'])
                x_min = min(x_min, item['x'])
                z_max = max(z_max, item['z'])
                z_min = min(z_min, item['z'])
            recp.append({'name': name, 'id': id, 'x_max': x_max, 'y': lis[0]['y'],
                         'x_min': x_min, 'z_max': z_max, 'z_min': z_min, 'position': position})
        self.receptacles = recp

    def point_determine(self, pos):
        point_P = {}
        try:
            point_P['x'], point_P['y'], point_P['z'] = pos['x'], pos['y'], pos['z']
        except:
            point_P['x'], point_P['y'], point_P['z'] = pos[0], pos[1], pos[2]
        res = None
        for room_i in self.room_area:
            if (room_i['x'][0] <= point_P['x'] <= room_i['x'][1]) and (
                    room_i['z'][0] <= point_P['z'] <= room_i['z'][1]):
                if abs(point_P['y']-room_i['y']) < 3:
                    res = room_i['name']
                    # print ("Point P is in room F3_Bedroom")
        return res

    def object_parsing(self, ins, target=['Chair','Stool']):
        print('near items: ', ins)
        datas = eval(ins['statusDetail'])
        obj_closed = datas['closeRangeItemIds']
        objec = None
        for i, obj in enumerate(obj_closed):
            name = self.objects[obj]['itemName']
            for ttt in target:
                if ttt.lower() in name.lower():
            # if target in name:
                    print("The target: ", name, obj, self.objects[obj])
                    return obj
        print('There is no {}'.format(target))
        return objec
        # return None

    def object_query(self, target=['Chair', 'Stool']):
        tar = []
        for i, obj in enumerate(self.objects):
            obj_i = obj['itemId']
            obj_full_name = obj['itemName']
            obj_now = ''.join([char for char in obj_full_name if not char.isdigit()])
            # print(name)
            for name in target:
                if name.lower() == obj_now.lower():
                    tar.append(obj_i)
        return tar

    def get_object_name(self, object_id=1):
        name = None
        for obj in self.objects:
            id = obj['itemId']
            if id == object_id:
                name = obj['itemName']
        return name

    def get_info_from_name(self, object_name):
        result = None
        for obj in self.objects:
            for obj in self.objects:
                na = obj['itemName']
                if na == object_name:
                    result = obj
            return result

    def check_feedback(self, server, id):
        time.sleep(0.1)
        info = None
        for i in range(30):
            try:
                info = server.notes[id]
                break
            except Exception as e:
                print(len(server.notes))
                time.sleep(0.1)
        return info


def cleanup_function(stop_event):
    stop_event.set()
    # stop the loop


def agent_plan(server, agent):
    agent.get_all_map()
    p, information = agent.pos_query()
    ob = agent.observation_camera_head()
    return 1
    flo, xx, yy, is_o = server.maps.get_point_info((20.9, 1, -44))
    print(flo, xx, yy, is_o)
    print(server.maps.maps_info[0]['x0'], server.maps.maps_info[0]['z0'])
    # server.maps.draw(19.2, 1, -44)
    des = agent.move_to(4)
    flo, xx, yy, is_o = server.maps.get_point_info(des)
    # agent.navigate(flo, (xx, yy))
    # Physical navigation
    # agent.move_forward(0.3)
    # agent.pos_query()
    # Robot position request

    # agent.goto_target_goal((18.0, 0.1, -2.99))
    agent.goto_target_goal((-13.9, 0.1, -7.5))
    flo, xx, yy, is_o = server.maps.get_point_info((-2.5, 0.1, -2.8))
    # adjustment
    flo, xx, yy, is_o = server.maps.get_point_info((-12.8, 0.1, 1.7))
    rotation_angle = agent.calculate_rotation_angle(xx, yy)
    # print(information)
    # print('-+++++++++++++++++++++++=', rotation_angle)
    # agent.joint_control(5, rotation_angle)
    # return
    # agent.rotate_right(rotation_angle)
    time.sleep(1)
    # agent.go_to_there((-2.0, 0.1, 0))
    # agent.go_to_there((12.5, 0.1, 0))
    # agent.goto_target_goal((27.0, 0.1, -2.99))
    agent.ik_control()
    time.sleep(2)
    agent.goto_target_goal((3.38, 0.1, 5.99))
    # Item location information
#       {"requestIndex":10,"actionId":6,"result":1,"positionOffset":0.0,"directionOffset":0.0}
# def server_initialization(output_queue):


class DevNull:
    def write(self, msg):
        pass


class PrsEnv(object):
    def __init__(self, is_print=1, rendering=1, start_up_mode=0):
        # is_print: 0 without print, 1 print information to screen;
        # rendering=1 with unity render, 0 is headless mode;   start_up_mode: 0 manual, 1 automatic
        print("PRS environment beta is starting without interaction")
        print('Please open the Unity program (start.sh)')
        print('PRS challenge task and benchmark come soon!')
        self.original_stdout = sys.stdout
        if not is_print:
            dev_null = DevNull()
            sys.stdout = dev_null
        self.stop_event = threading.Event()
        self.server = Server(self.stop_event)
        self.npc_running, self.time_running, self.agent_running = 0, 0, 0
        connection_thread = threading.Thread(target=self.server.wait_for_connection, args=())
        receive_thread = threading.Thread(target=self.server.receive_data, args=())
        parsing_thread = threading.Thread(target=self.server.message_process, args=())
        connection_thread.start()
        receive_thread.start()
        parsing_thread.start()
        # ---------------server begin-------------------
        self.env_time = EnvTime()
        # ---------------time system ready-------------------
        self.process = 0
        # executable_path = 'start.sh'
        executable_path = './unity/PRS.x86_64'
        if rendering:
            command_args = [executable_path]
        else:
            command_args = [executable_path, '-batchmode']
        try:
            if start_up_mode:
                # Start the Shell script using subprocess.Popen and capture stdout and stderr
                self.process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("Starting Unity process...")
                # If needed, you can add more processing logic here, such as waiting for the process to finish, etc.
        except Exception as e:
            # Catch any exceptions that occur during startup and print the error message
            print(f"An error occurred during beginning: {e}")
        # --- unity exe start ---
        while True:
            time.sleep(0.3)
            state = self.server.state
            if state == 2 : break
        self.objs_data = ObjectsData()
        # --------------agent begin---------------
        self.agent = Agent(self.server, self.env_time, self.objs_data)
        agent_thread = threading.Thread(target=agent_plan, args=(self.server, self.agent))
        # 启动线程 机器人
        self.agent.get_all_map()
        # agent_thread.start()
        # ----------------------- npc coming----------------------
        npc_0 = Npc(0, self.server, self.env_time, self.objs_data)
        npc_1 = Npc(1, self.server, self.env_time, self.objs_data)
        npc_2 = Npc(2, self.server, self.env_time, self.objs_data)
        npc_3 = Npc(3, self.server, self.env_time, self.objs_data)
        npc_4 = Npc(4, self.server, self.env_time, self.objs_data)
        npc_5 = Npc(5, self.server, self.env_time, self.objs_data)
        npc_6 = Npc(6, self.server, self.env_time, self.objs_data)
        npc_7 = Npc(7, self.server, self.env_time, self.objs_data)
        npc_8 = Npc(8, self.server, self.env_time, self.objs_data)
        npc_9 = Npc(9, self.server, self.env_time, self.objs_data)

        print('start')
        self.task = {'type': None, 'npc': None, 'object': None, 'target': None, 'state': 0, 'result': None}
        self.npcs = [npc_0, npc_1, npc_2, npc_3, npc_4, npc_5, npc_6, npc_7, npc_8, npc_9]
        self.agent.npcs = self.npcs
        self.receptacle_mark()
        time.sleep(1)

        # # --------------------------robot ----------------------

    def npc_start(self, number=1):
        if not self.time_running:
            time_thread = threading.Thread(target=self.env_time.time_simulation, args=(self.stop_event,))
            time_thread.start()
            self.time_running = 1
        if not self.npc_running:
            for npc_i, npc in enumerate(self.npcs):
                if npc_i == number:
                    break
                # running_thread = threading.Thread(target=npc.continuous_simulation, args=())
                running_thread = threading.Thread(target=npc.random_walk, args=())
                running_thread.start()
                time.sleep(2)
            self.npc_running = 1

    def finish_env(self):
        print('========== Env end ==========')
        self.stop_event.set()
        self.agent.running = 0
        self.server.env_finish(self.process, self.npcs)
        sys.stdout = self.original_stdout
        exit(0)

    def sim_speed(self, speed):
        instruction = {"requestIndex": 1, "timeScale": speed}
        action_id = self.server.send_data(7, instruction, 1)
        self.env_time.time_multiplier *= speed
        return self.env_time.time_multiplier

    def object_query(self, obj_id=0):
        instruction = {"requestIndex": 0, "targetType": 1, "targetId": obj_id}
        r_id = self.server.send_data(2, instruction, 1)
        object_info = self.agent.wait_for_respond(r_id, 60)
        if object_info:
            object_info = eval(object_info['statusDetail'])
        return object_info

    def receptacle_mark(self):
        # maps_0 = copy.deepcopy(self.server.maps.maps_info[0]['grid'])
        # maps_1 = copy.deepcopy(self.server.maps.maps_info[1]['grid'])
        for floor_i in range(3):
            maps_2 = copy.deepcopy(self.server.maps.maps_info[floor_i]['grid'])
            record = dict()
            for rece in self.objs_data.receptacles:
                # {'name': name, 'id': id, 'x_max': x_max,'x_min': x_min, 'z_max': z_max, 'z_min': z_min}
                x_max, x_min, z_max, z_min, y = rece['x_max'], rece['x_min'], rece['z_max'], rece['z_min'], rece['y']
                floor, map_i1, map_j1, iso = self.server.maps.get_point_info((x_max, y, z_max))
                floor, map_i2, map_j2, iso = self.server.maps.get_point_info((x_min, y, z_min))
                map_i_min, map_i_max = min(map_i1, map_i2), max(map_i1, map_i2)
                map_j_min, map_j_max = min(map_j1, map_j2), max(map_j1, map_j2)
                for ii in range(map_i_min, map_i_max + 1):
                    for jj in range(map_j_min, map_j_max + 1):
                        if maps_2[ii][jj] == 0:
                            maps_2[ii][jj] = 2
                loc = self.objs_data.point_determine((x_min, floor, z_max))
                rece['location'], rece['floor'] = loc, floor
                rece['map_i_min'], rece['map_i_max'] = map_i_min, map_i_max
                rece['map_j_min'], rece['map_j_max'] = map_j_min, map_j_max
                try:
                    record[loc]['num'] += 1
                    record[loc]['receptacles'].append(rece)
                except:
                    record[loc] = {'num': 1}
                    record[loc]['receptacles'] = [rece]
            self.objs_data.room_receptacles = record
            self.objs_data.sematic_map[floor_i] = maps_2


if __name__ == '__main__':  # pragma nocover
    server = Server()



'''
-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"requestIndex":11, "result":1}


-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"result":1}
'''
