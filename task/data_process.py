import os
import re
import json
from zhipuai import ZhipuAI
client = ZhipuAI(api_key="1f2068c7882338638fd17aaaacfe0a70.NbQqxF36KaP6y3k5") # 请填写您自己的APIKey


def llm_interaction(content='Hello World!', temperature=0.9):
    # 值越大，会使输出更随机，更具创造性；值越小，输出会更加稳定或确定
    response = client.chat.completions.create(
    model="glm-4",  # 填写需要调用的模型名称
    #     glm-4   glm-3-turbo
    messages=[
        {"role": "user", "content": content}
    ],
        top_p=0.7,
        temperature=0.9
    )
    # print(response.choices[0].message.content)
    res = response.choices[0].message.content
    return res


def instruction_generation(directives, npc):
    context = '请你帮助机器人生成合适的语言指令，关于指定目标人物的物品运送任务，参照任务信息生成两条指令，分别是第一人称命令和第三人称的指挥命令（目的让机器人去帮助拿东西，不是对人发出指令）。希望根据指令，机器人可以准确帮助目标人物完成任务。任务的信息如下：'
    character = '目标人物的简单描述：'
    requirement = '依照上述的任务描述和人物信息，只需要生成两条英语命令（请注意第一人称的我和第三人称的他/她是指的同一个目标人物，在第一人称中不需要描述自己的名字和外观只发出任务的指令），内容包含在<>中，请不要加入与任务无关的信息，可以适当调换语序、语气、句法结构、说辞和用词让指令内容更加丰富多样，但不用输出解释或其他额外信息，只给我两条指令而格式请参考： <Retrieve the red apple from the kitchen and deliver it to Room 2 for me.>; <Bring the white cup that is on the kitchen table to Office 1, locate Sheldon who is wearing a white shirt, and hand it to him.>'
    no_time_first = directives[1].split(',')[1]
    new_string = directives[0].replace(".", ",")
    first = directives[2]
    third = new_string + no_time_first[:-3] + npc
    supplement = ''
    content_array = []
    for try_index in range(5):
        prompt = context + new_string + first + third + requirement + supplement
        # print(prompt)
        result = llm_interaction(prompt, temperature=0.99)
        # print(result)
        try:
            matches = re.findall(r'<(.*?)>', result)
            # matches现在是一个列表，包含每个<...>对中的内容
            # for match in matches: pass
                # print(match)  # 分别打印每个匹配项
            content_array = matches
            # print(content_array)
            if len(content_array) == 2:
                break
            else:
                supplement = '你上一次生成的内容格式错误，麻烦您重新生成一次符合标准格式的两条指令<ins1>; <ins2>.'
                continue
        except:
            continue
    if len(content_array) == 2:
        directives.extend(content_array)
        return directives
    else:
        return None


def new_generation(directives, npc):
    # context = '请你帮助机器人生成合适的语言指令，关于指定目标人物的物品运送任务，参照任务信息生成一条指令，作为对机器人的命令。希望根据指令，机器人可以准确完成任务（帮目标人物带去正确的物品）。任务的信息如下：'
    context = '请你帮助机器人生成合适的语言指令，关于指定目标人物的物品运送任务，参照任务信息生成两条指令（第一条指令是第一人称口吻发出给机器人，第二条指令要求将指导机器人去给指定人物拿东西），作为对机器人的命令。希望根据指令，机器人可以准确完成任务（帮目标人物带去正确的物品）。任务的信息如下：'
    character = '目标人物的简单描述：'
    # requirement = "依照上述的任务信息，只需要生成一条英语命令（请参考原有任务信息），内容包含在<>中，请不要加入与任务无关的信息，可以适当调换语序、语气、句法结构、说辞和用词让指令内容更加丰富多样，但不用输出解释或其他额外信息，只给我一条指令而格式请参考： <Bring the white cup that is on the kitchen table to Office 1, locate Sheldon who is wearing a white shirt, and hand it to him.>; <retrieve the red and white bagged cake from the living room's marble dinner counter and deliver it to Graham's bedroom for a white shirt man.>"
    requirement = "依照上述的任务信息，只需要生成两条英语命令（请参考原有任务信息和主语），内容包含在<>中，请不要加入与任务无关的信息，可以适当调换语序、语气、句法结构、风格、句式、说辞和用词让指令内容更加丰富多样，但不用输出解释或其他额外信息，只给我两条指令而格式请参考： <Retrieve the red apple from the kitchen and deliver it to room 2 for me.>; <Bring the red and white bagged cake from the living room's marble dinner counter and deliver it to Graham's bedroom for a white shirt man.>"
    no_time_first = directives[1].split(',')[1]
    new_string = directives[0].replace(".", ",")
    first = '第一条指令的参考: ' + directives[2]
    third = '第二条指令的参考: ' + new_string + no_time_first[:-3] + npc
    supplement = ''
    content_array = []
    for try_index in range(5):
        prompt = context + first + third + requirement + supplement
        # print(prompt)
        result = llm_interaction(prompt, temperature=0.99)
        # print(result)
        try:
            matches = re.findall(r'<(.*?)>', result)
            # matches现在是一个列表，包含每个<...>对中的内容
            # for match in matches: pass
                # print(match)  # 分别打印每个匹配项
            content_array = matches
            # print(content_array)
            if len(content_array) == 2:
                break
            else:
                supplement = '你上一次生成的内容格式错误，麻烦您重新生成一次符合标准格式的以条指令<ins1>.'
                continue
        except:
            continue
    if len(content_array) == 2:
        # directives[4] = content_array[0]
        directives.extend(content_array)
        return directives
    else:
        return None


with open(os.path.join('', 'deliver_task_5_18.json'), 'r') as file:
    task_data = json.load(file)
with open('./../data/npc_data.json', 'r') as file:
    npc_data = json.load(file)
tasks = list(task_data.keys())
print('task:', len(tasks))
error_list = []
for task_i, task_id in enumerate(tasks[:]):
    task = task_data[task_id]
    ins = task['directive']
    npc_id = task['npc_id']
    npc_information = npc_data["npc"][npc_id]
    npc_name = task['npc_name']
    # resume = npc_information["feature"].format_map({'name': npc_name})
    character = npc_name + ', ' + npc_information["character"]
    # print(ins)
    try:
        # new_ins = instruction_generation(ins, resume)
        print(task_i)
        new_ins = new_generation(ins, character)
        if new_ins is None:
            print(task_id)
            error_list.append(task_id)
        else:
            task_data[task_id]['directive'] = new_ins
    except Exception as e:
        print(e, task_id)
        error_list.append(task_id)
    # break
print(error_list)
with open('dataset/deliver_task_5_18_verification1.json', 'w') as file:
    json.dump(task_data, file, indent=4)