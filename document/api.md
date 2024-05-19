# PRS API
We provide **API** that includes various functions:
- [Environment API](#environment-api)
- [Task API](#task-api)
- [Robot API](#robot-api)
- [Map API](#map-and-position-api)
- [NPC API](#npc-api)

## Environment API
Operations: Accelerate, Terminate, Initiate

Instantiate environment class
```
prs = PrsEnv()
```
Start autonomous activities for NPCs, specifying the number of activated NPCs
```
prs.npc_start(3)
```
Accelerate the scene simulation by specifying the speed multiplier
```
prs.sim_speed(2)
```
set environment time
```
prs.env_time.set_time(2024, 6, 1, 9, 0)
```
Terminate the environment and end the process
```
prs.finish_env()
```

## Task API

Initialize the task program, 0 stands for searching and delivery tasks
```
prs.task_choice(0)
```
Evaluate the task result
```
prs.task_evaluate()
```
## Robot API

Retrieve vision data, specifying the camera type (0 for head, 1 for hand)
```
prs.agent.observation_camera(camera_type=0)
```
Move the robot to a target location, specifying the position mode (0 for world, 1 for grid map)
```
prs.agent.goto_target_goal((2, 130, 120), position_mode=1)
```
Retrieve robot position information, returning position (pos) and detailed information (info)
```
prs.agent.pos_query()
```
Rotate the robot, specifying the degree of rotation (positive for right, negative for left)
```
prs.agent.rotate_right(degree=30)
```
Control robot joints, specifying the joint ID and target
```
prs.agent.joint_control(joint_id=1, target=20)
```
Adjust robot direction alignment based on input coordinates
```
prs.agent.direction_adjust(position=(22.38, 0.1, -0.17))
```
Perform inverse kinematics (IK) for the robot, specifying relative coordinates
```
prs.agent.ik_process(x=0, y=1, z=0.1)
```
Calculate 6 Degrees of Freedom (6-DoF) IK for the robot, specifying the target coordinates and rotation matrix (yaw, pitch, roll)
```
prs.agent.input_pos(prs.agent.robot, x=0.2, y=0, z=0.75, phi=0, theta=1.25, psi=0, plot=0)
```
Move the robot forward by specifying the distance
```
prs.agent.move_forward(dis=1.0)
```
Navigate to a specific destination, specifying the location name
```
prs.agent.go_to_destination('kitchen')
```
Retrieve the latest map
```
prs.agent.get_all_map()
```
Calculate IK for relative coordinates and target values, specifying world coordinates
```
prs.agent.ik_calculation((-10.1, 0.1, 1.6))
```
Calculate IK target, specifying relative coordinates
```
prs.agent.ik_process(0.25, 0.1, 0.79)
```
Control robot arms, specifying joint target values
```
prs.agent.arm_control([0, 0, 0, 0, 0])
```
Grab an object, specifying the object's ID
```
prs.agent.grasp_object(17)
```
Move towards the vicinity of an object, specifying the object ID or functional feature
```
prs.agent.go_to_target_object(feature='Seat')
```
Walk towards and grab the target object
```
prs.agent.goto_and_grasp('apple')
```
Release the held object
```
depth_m = prs.agent.get_depth(0)
```
Retrieve depth information, specifying mode (0 for head camera, 1 for hand camera)
```
prs.agent.get_depth()
```
Retrieve camera semantic segmentation, specifying mode (0 for head camera, 1 for hand camera), tags contain object information
```
seg, tags = prs.agent.get_segmentation(0)
```
Head camera twisted downwards
```
prs.agent.joint_control(joint_id=4, target=20)
```
Using the camera to observe the surroundings with the given angle
```
prs.agent.observation(degree=0, camera=0)
```
    prs.agent.observation(camera=0, degree=0)
Request Visual Interaction

```
prs.agent.request_interaction()
```
This function requests an interaction with the visual system.
Input: A two-dimensional matrix marking the target and the operation type:
0: recognize
1: grasp
2: approach target
3, etc.
```
prs.agent.interaction()
```

## Map and Position API

Determine the area based on world coordinates, returning the room or None
```
prs.objs_data.point_determine((15.7, -5.1, -19.5))
```
Retrieve information from the 2D grid map, specifying world coordinates [-10.1, 0.1, -6.1], output includes floor, map_i, map_j, and obstacle status
```
prs.server.maps.get_point_info({'x': -10.1, 'y': 0.1, 'z': -6.1})
```
Retrieve world position based on floor, map_i, and map_j coordinates
```
prs.server.maps.get_world_position(1, 89, 108)
```
Retrieve 2D grid maps for floors 1, 2, and 3
```
map1, map2, map3 = prs.server.maps.floor1, prs.server.maps.floor2, prs.server.maps.floor3
```
Retrieve the latest map
```
prs.agent.get_all_map()
```
Parse object information based on instructions, querying a specific object
```
obj_list = prs.objs_data.object_parsing(instruction, ['apple'])
```
Global query for an object's ID, specifying the object's name
```
obj_list = prs.objs_data.object_query(['apple'])
```
Query object information based on ID
```
prs.object_query(obj_id=100)
```

## NPC API

Execute actions for NPCs based on action IDs, including looping actions, interactive actions, and performance actions
```
prs.npcs[0].npc_action(tar_action='stand')
```
Retrieve photos around the NPC, from the camera perspective above the head
```
prs.npcs[0].observation_surrounding()
```
Retrieve the current NPC's position, returning position and detailed NPC information
```
prs.npcs[0].where_npc()
```
NPC move to a specific place based on preset location lists
```
prs.npcs[0].go_to_place()
```
Retrieve detailed information about the NPC, including position and other information
```
pos, npc_info = prs.npcs[0].query_information()
```
Move towards the vicinity of an object, specifying the distance range to the target
```
res, obj = prs.npcs[0].go_to_object('Seat')
```