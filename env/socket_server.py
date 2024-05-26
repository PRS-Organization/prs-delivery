import copy
import sys
import time
import subprocess
# import atexit
from socket import *
import threading
import json
import struct
from enum import Enum
# from game_demo import *
import ast
from env.map_process import RoomMap
from env.npc_control import Npc, Agent
import datetime


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
    Server_Config_Inform = 12
    Client_Config_Response = 13


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
        tcp_address = ('localhost', serve_port)
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
                    if cmd < 15:
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
                    # print(e, n_client[0])
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
        dict_d = copy.deepcopy(dict_data)
        del dict_d['requestIndex']
        self.notes[dict_data['requestIndex']] = dict_d
        if cmd == "EXIT":
            self.state = 0
            print('0. Env is over, exit!')
            return
        elif cmd == "Result": pass
            # print('3、Execution results from Unity', dict_data)
        elif cmd == "State": pass
            # Storing parameter information
            # print('4、Detailed information obtained id: {}'.format(dict_data['requestIndex']))
        elif cmd == "Control": pass
        # IK is here
        elif cmd == "Information": pass
            # print("6、This is robot information", dict_data['requestIndex'], ', length- ', len(dict_data),)
        else:
            print("\nUnknown cmd: {0}".format(cmd))
        # Continue receiving messages
        #self._recv_bytes()

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
        for i in range(5):
            instruction = {"requestIndex": 0, "targetType": 1, "targetId": obj_id}
            r_id = self.send_data(2, instruction, 1)
            object_info = self.wait_for_respond(r_id, 60)
            if object_info is not None:
                break
            time.sleep(0.1)
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
        if object_info:
            object_info = eval(object_info['statusDetail'])
            try:
                return object_info['touchedIds']
            except:
                return None
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
        instruction['objectTransformHandles'].append(para)
        r_id = self.send_data(12, instruction, 1)
        object_info = self.wait_for_respond(r_id, 60)
        time.sleep(0.2)
        return object_info

    def env_finish(self, process, npcs):
        if process:
            process.terminate()
            # Waiting for the process to end (optional, but recommended)
            process.wait()
        self.send_data(0, {"requestIndex": 10, "actionId": 1}, 0)
        # movement demo
        self.state = 0
        for npc in npcs:
            npc.running = 0
        self.stop_event.set()
        self.sock.close()
        # print(self.state, type(self.state))
        print(threading.active_count(), ' ------ env is ready to end')
        time.sleep(3)
        print(threading.active_count(), ' ------ thank you for using')


class ObjectsData(object):
    def __init__(self):
        with open('unity/PRS_Data/StreamingAssets/itemInfo.json', 'r') as file:
            json_data = json.load(file)
        with open('unity/PRS_Data/StreamingAssets/roomInfo.json', 'r') as file:
            room_data = json.load(file)
        with open('unity/PRS_Data/StreamingAssets/segmentationTagColorInfo.json', 'r') as file:
            seg_tag_data = json.load(file)
        with open('../data/npc_data.json', 'r') as file:
            json_npc = json.load(file)
        with open('/EmbodiedAI02/VerticleSlice/Assets/StreamingAssets/receptacleInfo.json', 'r') as file:
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
            if item_tag['tag'] == "Untagged":
                self.background = rgb

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
        buliding_rooms = [dict(), dict(), dict()]
        for ro in env_rooms:
            y = ro['roomCenter']['y']
            if y > -0.8:
                buliding_rooms[2][ro['roomName']] = ro
            elif y > -10:
                buliding_rooms[1][ro['roomName']] = ro
            else:
                buliding_rooms[0][ro['roomName']] = ro
        self.buliding_rooms = buliding_rooms
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
        receptacles_information = {'F3_KitchenRoom': {'receptacles': [
            {'name': 'Small Table (3)', 'feature': 'yellow', 'pos': {'x': -15.496, 'y': 0.0, 'z': -8.361}},
            {'name': 'Table', 'feature': 'wooden dining', 'pos': {'x': -15.996, 'y': 0.0, 'z': -5.042}},
            {'name': 'Kitchen Counter', 'feature': 'left', 'pos': {'x': -10.483, 'y': 0.0, 'z': -4.688}},
            {'name': 'Kitchen Wardrobe', 'feature': 'wooden high', 'pos': {'x': -10.527, 'y': 0.0, 'z': -6.603}},
            {'name': 'Dinner Counter', 'feature': 'middle', 'pos': {'x': -13.109, 'y': 0.0, 'z': -6.124}}]},
            'F3_Bedroom_5': {'receptacles': [{'name': 'Table', 'feature': 'sturdy',
                                              'pos': {'x': 13.58, 'y': 0.01, 'z': -27.902}},
                                             {'name': 'Bed', 'feature': 'stylish',
                                              'pos': {'x': 14.683, 'y': 0.01, 'z': -28.336}}]},
            'F2_HallRoom02': {'receptacles': [{'name': 'Table (1)', 'feature': '',
                                               'pos': {'x': 26.88, 'y': -5.167, 'z': -7.638}},
                                              {'name': 'Table (2)', 'feature': '',
                                               'pos': {'x': 26.88, 'y': -5.167, 'z': -5.174}}]},
            'F2_HallRoom03': {'receptacles': [{'name': 'Table (1)', 'feature': '',
                                               'pos': {'x': 26.073, 'y': -5.167, 'z': 4.748}},
                                              {'name': 'Reception Counter', 'feature': '',
                                               'pos': {'x': 21.354, 'y': -5.167, 'z': 5.55}},
                                              {'name': 'Table (3)', 'feature': '',
                                               'pos': {'x': 28.461, 'y': -5.167, 'z': 4.516}},
                                              {'name': 'Table (2)', 'feature': '',
                                               'pos': {'x': 27.206, 'y': -5.167, 'z': 5.7}},
                                              {'name': 'Table (4)', 'feature': '',
                                               'pos': {'x': 28.461, 'y': -5.167, 'z': 6.89}}]},
            'F3_HallRoom02': {'receptacles': [{'name': 'Table (1)', 'feature': 'wall-adjacent',
                                               'pos': {'x': 26.88, 'y': 0.0, 'z': -7.638}},
                                              {'name': 'Table (2)', 'feature': 'light brown',
                                               'pos': {'x': 26.88, 'y': 0.0, 'z': -5.174}}]},
            'F3_OfficeSpaceRoom': {'receptacles': [{'name': 'Desk (8)', 'feature': 'rectangular',
                                                    'pos': {'x': 2.841, 'y': -0.002,
                                                            'z': 3.755}},
                                                   {'name': 'Desk (3)', 'feature': 'compact',
                                                    'pos': {'x': 7.973, 'y': -0.002,
                                                            'z': 7.732}},
                                                   {'name': 'Desk (4)', 'feature': 'modern',
                                                    'pos': {'x': 1.812, 'y': -0.003,
                                                            'z': 3.755}},
                                                   {'name': 'Desk (6)', 'feature': 'wooden',
                                                    'pos': {'x': 2.836, 'y': -0.002,
                                                            'z': 7.745}},
                                                   {'name': 'Desk (2)', 'feature': 'functional',
                                                    'pos': {'x': 7.978, 'y': -0.002,
                                                            'z': 3.784}},
                                                   {'name': 'Desk (1)', 'feature': 'office',
                                                    'pos': {'x': 6.949, 'y': -0.003,
                                                            'z': 3.784}},
                                                   {'name': 'Side Table', 'feature': 'tall',
                                                    'pos': {'x': 4.838, 'y': 0.0, 'z': 5.93}},
                                                   {'name': 'Desk (7)', 'feature': 'office',
                                                    'pos': {'x': 6.944, 'y': -0.003,
                                                            'z': 7.732}},
                                                   {'name': 'Desk (5)', 'feature': 'work',
                                                    'pos': {'x': 1.807, 'y': -0.003,
                                                            'z': 7.745}}]}, 'F3_Bedroom_3': {
                'receptacles': [
                    {'name': 'Table', 'feature': 'wall-mounted', 'pos': {'x': 13.58, 'y': 0.01, 'z': -20.22}},
                    {'name': 'Bed', 'feature': 'modern', 'pos': {'x': 14.683, 'y': 0.01, 'z': -20.654}}]},
            'F3_HallRoom01': {'receptacles': [{'name': 'Polygon Table', 'feature': 'stone',
                                               'pos': {'x': 12.727, 'y': 0.0, 'z': -5.639}}]},
            'F3_GymRoom': {'receptacles': [{'name': 'Furniture_Gym_Desk', 'feature': 'dark gray',
                                            'pos': {'x': 10.945, 'y': 0.0, 'z': 3.209}}]},
            'F3_Bedroom_4': {'receptacles': [{'name': 'Table', 'feature': 'minimalist',
                                              'pos': {'x': 25.7, 'y': 0.01, 'z': -29.25}},
                                             {'name': 'Bed', 'feature': 'dark',
                                              'pos': {'x': 24.597, 'y': 0.01, 'z': -28.816}}]},
            'F3_OfficeRoom01': {'receptacles': [{'name': 'Desk 4', 'feature': 'versatile',
                                                 'pos': {'x': -3.505, 'y': 0.0, 'z': -6.917}}]},
            'F3_LivingRoom': {'receptacles': [{'name': 'Dinner Counter', 'feature': 'marble',
                                               'pos': {'x': -3.09, 'y': 0.0, 'z': 5.787}},
                                              {'name': 'Coffee table', 'feature': 'low',
                                               'pos': {'x': -6.92, 'y': 0.041, 'z': 6.23}}]},
            'F3_HallRoom03': {'receptacles': [{'name': 'Table (4)', 'feature': 'square',
                                               'pos': {'x': 28.461, 'y': 0.0, 'z': 6.89}},
                                              {'name': 'Reception Counter',
                                               'feature': 'marmoreal',
                                               'pos': {'x': 21.354, 'y': 0.0, 'z': 5.55}},
                                              {'name': 'Table (2)', 'feature': 'rectangular',
                                               'pos': {'x': 27.206, 'y': 0.0, 'z': 5.7}},
                                              {'name': 'Table (3)', 'feature': 'small',
                                               'pos': {'x': 28.461, 'y': 0.0, 'z': 4.516}},
                                              {'name': 'Table (1)', 'feature': 'dark',
                                               'pos': {'x': 26.073, 'y': 0.0, 'z': 4.748}}]},
            'F3_Bedroom_9': {'receptacles': [{'name': 'Table', 'feature': 'elegant',
                                              'pos': {'x': 13.58, 'y': 0.01, 'z': -43.28}},
                                             {'name': 'Bed', 'feature': 'comfortable',
                                              'pos': {'x': 14.683, 'y': 0.01, 'z': -43.714}}]},
            'F3_Bedroom_2': {'receptacles': [{'name': 'Table', 'feature': 'rectangular',
                                              'pos': {'x': 25.7, 'y': 0.01, 'z': -21.56}},
                                             {'name': 'Bed', 'feature': 'simple',
                                              'pos': {'x': 24.597, 'y': 0.01, 'z': -21.126}}]},
            'F3_Bedroom_0': {'receptacles': [{'name': 'Table', 'feature': 'wooden',
                                              'pos': {'x': 25.7, 'y': 0.01, 'z': -13.878}},
                                             {'name': 'Bed', 'feature': 'wonderful',
                                              'pos': {'x': 24.597, 'y': 0.01, 'z': -13.444}}]},
            'F3_Bedroom_7': {'receptacles': [{'name': 'Table', 'feature': 'brown',
                                              'pos': {'x': 13.58, 'y': 0.01, 'z': -35.59}},
                                             {'name': 'Bed', 'feature': 'dark colored',
                                              'pos': {'x': 14.683, 'y': 0.01, 'z': -36.024}}]},
            'F3_Bedroom_6': {'receptacles': [{'name': 'Table', 'feature': 'decorative',
                                              'pos': {'x': 25.7, 'y': 0.01, 'z': -36.938}},
                                             {'name': 'Bed', 'feature': 'contemporary',
                                              'pos': {'x': 24.597, 'y': 0.01, 'z': -36.504}}]},
            'F3_ConferenceRoom': {'receptacles': [
                {'name': 'Meeting Table Large', 'feature': 'elongated',
                 'pos': {'x': 4.88, 'y': 0.0, 'z': -5.752}}]}, 'F3_Bedroom_1': {'receptacles': [
                {'name': 'Table', 'feature': 'rectangular', 'pos': {'x': 13.58, 'y': 0.01, 'z': -12.53}},
                {'name': 'Bed', 'feature': 'tidy', 'pos': {'x': 14.683, 'y': 0.01, 'z': -12.964}}]}, 'F3_Bedroom_11': {
                'receptacles': [{'name': 'Table', 'feature': 'wooden', 'pos': {'x': 13.58, 'y': 0.01, 'z': -50.962}},
                                {'name': 'Bed', 'feature': 'dark', 'pos': {'x': 14.683, 'y': 0.01, 'z': -51.396}}]},
            'F3_Bedroom_8': {'receptacles': [{'name': 'Table', 'feature': 'personal',
                                              'pos': {'x': 25.7, 'y': 0.01, 'z': -44.62}},
                                             {'name': 'Bed', 'feature': 'single',
                                              'pos': {'x': 24.597, 'y': 0.01, 'z': -44.186}}]},
            'F2_HallRoom01': {'receptacles': [{'name': 'Polygon Table', 'feature': '',
                                               'pos': {'x': 12.727, 'y': -5.167, 'z': -5.639}}]},
            'F2_MedicalRoom03': {'receptacles': [{'name': 'Desk 4', 'feature': '',
                                                  'pos': {'x': -13.347, 'y': -5.172,
                                                          'z': -6.917}}]}, 'F3_OfficeRoom02': {
                'receptacles': [{'name': 'Desk 3', 'feature': 'office', 'pos': {'x': -6.415, 'y': 0.0, 'z': -6.654}}]},
            'F3_Bedroom_10': {'receptacles': [{'name': 'Table', 'feature': 'wooden',
                                               'pos': {'x': 25.7, 'y': 0.01, 'z': -52.31}},
                                              {'name': 'Bed', 'feature': 'square',
                                               'pos': {'x': 24.597, 'y': 0.01, 'z': -51.876}}]}}
        self.receptacles_information = receptacles_information
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
        return res

    def object_parsing(self, ins, target=['Chair','Stool']):
        datas = eval(ins['statusDetail'])
        obj_closed = datas['closeRangeItemIds']
        object = None
        for i, obj in enumerate(obj_closed):
            name = self.objects[obj]['itemName']
            for ttt in target:
                if ttt.lower() in name.lower():
                    print("The target: ", name, obj, self.objects[obj])
                    return obj
        # print('There is no {}'.format(target))
        return object
        # return None

    def object_query(self, target=['Chair', 'Stool']):
        tar = []
        for i, obj in enumerate(self.objects):
            obj_i = obj['itemId']
            obj_full_name = obj['itemName']
            obj_now = ''.join([char for char in obj_full_name if not char.isdigit()])
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
        # agent_thread = threading.Thread(target=agent_plan, args=(self.server, self.agent))
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
        with open('../data/npc_data.json', 'r') as file:
            npc_data = json.load(file)
        self.npc_data = npc_data
        time.sleep(0.1)

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
        action_id = self.server.send_data(12, instruction, 0)
        # print(self.env_time.time_multiplier, speed)
        res = self.server.wait_for_respond(action_id, 10)
        self.env_time.time_multiplier = speed
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

    # ---------------- delivery task - ------------------------

    def delivery_task_import(self, task_setup):
        target_npc_id = task_setup['npc_id']
        if self.time_running == 0:
            self.env_time.time_multiplier = 1
            time_thread = threading.Thread(target=self.env_time.time_simulation, args=(self.stop_event,))
            time_thread.start()
            # self.sim_speed(1)
            self.time_running = 1
        if self.npc_running:
            return False
        else:
            for npc_i, npc in enumerate(self.npcs):
                if npc_i == target_npc_id:
                    continue
                # npc.random_behavior(task_setup['npc_location'], 1)
        self.npcs[target_npc_id].directive_following(task_setup)
        #     此处生成任务指令和数据
        instructions = [
            'Grasp the black console gaming pad from the low coffee table in the living room and take it to the bedroom.',
            'Retrieve the black console gaming pad on the low coffee table in the living room and bring it to the bedroom for Brian, the one in the light-colored jacket.']
        basic_information, name_dict = self.npc_data["npc"][target_npc_id]["description"], {
            'name': task_setup['npc_name']}
        npc_information = basic_information.format_map(name_dict)
        try:
            instruction = task_setup['directive'][4]
        except:
            instruction = task_setup['directive'][0] + task_setup['directive'][1]
        data = task_setup
        return instruction, npc_information, data

    def delivery_task_evaluate(self, task_data, score=0, save=0):
        now_time = self.env_time.current_date.isoformat()
        time.sleep(0.3)
        tar_npc_id, tar_obj = task_data['npc_id'], task_data['target_object_name']
        tar_obj_inf = self.objs_data.get_info_from_name(tar_obj)
        tar_obj_id = tar_obj_inf['itemId']
        npc_pos, npc_info = self.npcs[tar_npc_id].query_information()
        obj_info = self.server.object_query(tar_obj_id)
        try:
            obj_pos = obj_info['position']
        except Exception as e:
            print(tar_obj_inf)
            print(e, tar_obj_id, obj_info)
            obj_pos = obj_info['position']
        agent_pos, agent_info = self.agent.pos_query()
        agent_obj_id = self.agent.is_grasp
        if agent_obj_id is not None:
            agent_obj_info = self.server.object_query(agent_obj_id)
            agent_obj_pos = agent_obj_info['position']
            agent_obj_name = agent_obj_info['itemName']
        else:
            agent_obj_pos, agent_obj_name = None, None
        result = {'task_id': task_data['task_id'], 'tar_object_position': obj_pos, 'tar_object_name': tar_obj,
                  'target_object_type': task_data['target_object_type'],
                  'agent_object_name': agent_obj_name, 'agent_object_position': agent_obj_pos,
                  'npc_position': npc_pos, 'npc_id': tar_npc_id, 'agent_position': agent_pos,
                  'start_time': task_data['time'], 'end_time': now_time}
        if agent_obj_id is not None:
            self.agent.release_object()
            pos_original = self.objs_data.objects[agent_obj_id]['position']
            self.server.object_transform(obj_type=1, target_id=agent_obj_id, pos=pos_original)
        # if save:
        # return result
        if score:
            grade = self.delivery_task_score(result)
            result['task_score'] = grade
            return result
        return result

    def delivery_task_score(self, result_data, task_id=0):
        task_res, res_grasp, res_find, human_find, res_deliver = 0, 0, 0, 0, 0
        start_t = datetime.datetime.fromisoformat(result_data['start_time'])
        end_t = datetime.datetime.fromisoformat(result_data['end_time'])
        time_cost = end_t - start_t
        seconds_cost = (end_t - start_t).total_seconds()
        minutes_cost = time_cost.total_seconds() / 60
        # 1. target find, 2. grasp target, 3. target object dis, 4. deliver
        if result_data['agent_object_name'] is not None:
            if result_data['tar_object_name'] == result_data['agent_object_name']:
                res_grasp, res_find = 1, 1
            else:
                if result_data['target_object_type'] in result_data['agent_object_name']:
                    res_find = 0.5
        hr_dis = self.agent.env.calculate_distance(result_data['npc_position'], result_data['agent_position'])
        if hr_dis < 3:
            human_find = 1
        elif hr_dis < 5:
            human_find = 0.5
        res_deliver = human_find * res_grasp
        #   计算距离，判断手上物品，计算时间
        task_res = res_grasp + res_find + res_deliver + human_find
        task_result = {'sub_result': {'grasp': res_grasp, 'object_find': res_find,
                                      'deliver': res_deliver, 'human_find': human_find},
                       'result': task_res, 'time': minutes_cost}
        # task_result = {'sub_result': [res_grasp, res_find, res_deliver, human_find],
        #                'result': task_res, 'time': minutes_cost}
        return task_result


if __name__ == '__main__':  # pragma nocover
    server = Server()



'''
-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"requestIndex":11, "result":1}


-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"result":1}
'''
