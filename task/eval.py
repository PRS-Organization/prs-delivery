import random
import datetime
import numpy as np
import json
import math


def calculate_distance(point1, point2):
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
        # distance = np.linalg.norm(point2_array - point1_array)
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(point1_array, point2_array)))
    except:
        distance = 99999
    return distance


def delivery_task_score(result_data, task_id=0):
    task_res, res_grasp, res_find, human_find, res_deliver = 0, 0, 0, 0, 0
    start_t = datetime.datetime.fromisoformat(result_data['start_time'])
    end_t = datetime.datetime.fromisoformat(result_data['end_time'])
    time_cost = end_t - start_t
    seconds_cost = (end_t - start_t).total_seconds()
    minutes_cost = time_cost.total_seconds() / 60
    # 1. target find, 2. grasp target, 3. target object dis, 4. deliver
    if result_data['agent_object_name'] is not None:
        if result_data['tar_object_name'] == result_data['agent_object_name']:
            res_grasp = 1
        else:
            if result_data['target_object_type'] in result_data['agent_object_name']:
                res_grasp = 0.5
    hr_dis = calculate_distance(result_data['npc_position'], result_data['agent_position'])
    if hr_dis < 3:
        human_find = 1
    elif hr_dis < 5:
        human_find = 0.5
    res_deliver = human_find * res_grasp
    task_res = res_grasp + res_find + res_deliver + human_find
    task_result = {'sub_result': {'grasp': res_grasp, 'object_find': res_find,
                                  'deliver': res_deliver, 'human_find': human_find},
                   'result': task_res, 'time': minutes_cost}
    return task_result


def evaluate(test_annotation_file, user_submission_file, phase_codename, **kwargs):
    print("Starting Evaluation.....")
    """
    Evaluates the submission for a particular challenge phase and returns score
    Arguments:

        `test_annotations_file`: Path to test_annotation_file on the server
        `user_submission_file`: Path to file submitted by the user
        `phase_codename`: Phase to which submission is made

        `**kwargs`: keyword arguments that contains additional submission
        metadata that challenge hosts can use to send slack notification.
        You can access the submission metadata
        with kwargs['submission_metadata']

        Example: A sample submission metadata can be accessed like this:
        >>> print(kwargs['submission_metadata'])
        {
            'status': u'running',
            'when_made_public': None,
            'participant_team': 5,
            'input_file': 'https://abc.xyz/path/to/submission/file.json',
            'execution_time': u'123',
            'publication_url': u'ABC',
            'challenge_phase': 1,
            'created_by': u'ABC',
            'stdout_file': 'https://abc.xyz/path/to/stdout/file.json',
            'method_name': u'Test',
            'stderr_file': 'https://abc.xyz/path/to/stderr/file.json',
            'participant_team_name': u'Test Team',
            'project_url': u'http://foo.bar',
            'method_description': u'ABC',
            'is_public': False,
            'submission_result_file': 'https://abc.xyz/path/result/file.json',
            'id': 123,
            'submitted_at': u'2017-03-20T19:22:03.880652Z'
        }
    """
    with open(test_annotation_file, 'r') as file:
        task_data = json.load(file)
    with open(user_submission_file, 'r') as file:
        task_submission = json.load(file)
    task_r, grasp_r, human_r, time_used = 0, 0, 0, 0
    number, tasks = len(list(task_data)), []
    for task_id, task in task_submission.items():
        print(task_id)
        if task_id in tasks:
            continue
        else:
            tasks.append(task)
        task_result = delivery_task_score(task)
    #     task_result = {'sub_result': {'grasp': res_grasp, 'object_find': res_find,
    #                                   'deliver': res_deliver, 'human_find': human_find},
    #                    'result': task_res, 'time': minutes_cost}
        task_r += int(task_result['result']/4)
        grasp_r += task_result['sub_result']['grasp']
        human_r += task_result['sub_result']['human_find']
        time_used += task_result['time']
    print(number, len(tasks))
    task_r = task_r / float(number)
    grasp_r = grasp_r / float(number)
    human_r = human_r / float(number)
    time_used = time_used / float(len(tasks))

    output = {}
    if phase_codename == "dev":
        # print("Evaluating for Dev Phase")
        # ["Task SR", "Object Manipulation SR", "Human Search SR", "Time Used"]
        output["result"] = [
            {
                "train_split": {
                    "Task SR": task_r,
                    "Object Manipulation SR": grasp_r,
                    "Human Search SR": human_r,
                    "Time Used": time_used
                }
            }
        ]
        # To display the results in the result file
        output["submission_result"] = output["result"][0]["train_split"]
        print("Completed evaluation for Dev Phase")
    elif phase_codename == "test":
        # print("Evaluating for Test Phase")
        output["result"] = [
            {
                "test_split": {
                    "Task SR": task_r,
                    "Object Manipulation SR": grasp_r,
                    "Human Search SR": human_r,
                    "Time Used": time_used
                }
            }
        ]
        # To display the results in the result file
        output["submission_result"] = output["result"][0]["test_split"]
        print("Completed evaluation for Test Phase")
    return output


if __name__ == "__main__":
    res = evaluate('dataset/deliver_task_test_set.json',
             'D:\\code\\prs_develop\\prs_system_git_push_version\\task\\result\\deliver_task_5_19_result.json'
             , 'test')
    print(res)