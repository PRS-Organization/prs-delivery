from env.socket_server import *
import os
from robot.baseline import *

# Environment initialization
prs = PrsEnv(is_print=1)

with open(os.path.join('task', 'dataset', 'deliver_task_5_19_test_set.json'), 'r') as file:
    task_data = json.load(file)
tasks = list(task_data.keys())
print('task:', len(tasks))
for task_i, task_id in enumerate(tasks):
    task = task_data[task_id]
    task_npc_id = task['npc_id']
    start_time = time.time()
    instruction, npc_information, data = prs.delivery_task_import(task)
    # ------------ robot execution method -----------------
    # delivery_execution(prs, instruction, npc_information)

    # ------------ robot execution method -----------------
    time.sleep(0.5)
    result = prs.delivery_task_evaluate(task, score=1, save=0)
    print(result['task_score'])
    # break