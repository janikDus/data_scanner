from csv import DictReader
from datetime import datetime
import json
import os

TIME_DIFF_SAMPLE = 10

path_to_status = '/Users/dusanjanik/Documents/TASKY/Domaci_ukol/DroneTag/sample-data-01-status.csv'
path_to_telemetry = '/Users/dusanjanik/Documents/TASKY/Domaci_ukol/DroneTag/sample-data-01-telemetry.csv'
processed_file = '/Users/dusanjanik/Documents/TASKY/Domaci_ukol/DroneTag/processed_{}.json'

format = '%Y-%m-%d %H:%M:%S'


def getAvgTimeDiff(data: list):
    '''
    '''

    time_diff_sum = 0
    for index in range(1, TIME_DIFF_SAMPLE + 1):
        old_one_time = datetime.strptime(data[index - 1]['time'][:19], format)
        current_one_time = datetime.strptime(data[index]['time'][:19], format)
        time_diff = int((current_one_time - old_one_time).seconds)

        time_diff_sum += time_diff

    print('time_diff_sum: {}'.format(time_diff_sum))
    time_diff_avg = time_diff_sum // TIME_DIFF_SAMPLE

    return time_diff_avg


def processData(data: list, file_path: str):
    '''
    '''

    default_time_diff = getAvgTimeDiff(data)
    print('type: {}, default_time_diff: {}'.format(type(default_time_diff), default_time_diff))

    data[0]['event'] = False
    for index in range(1, len(data)):
        old_one = data[index - 1]
        current_one = data[index]

        old_one_time = datetime.strptime(old_one['time'][:19], format)
        current_one_time = datetime.strptime(current_one['time'][:19], format)

        time_diff = int((current_one_time - old_one_time).seconds)

        if time_diff > default_time_diff:
            print('old_one id: {}, current_one id {}'.format(old_one['id'], current_one['id']))
            print('old_one time: {}, current_one time {}'.format(old_one['time'], current_one['time']))
            print('type: {}, diff: {}'.format(type(time_diff), time_diff))
            data[index]['event'] = True
        else:
            data[index]['event'] = False

    file_name, _ = os.path.basename(file_path).rsplit('.', 1)
    json.dump(data, open(processed_file.format(file_name), 'w', encoding='utf8'), indent=2)


telemetry_data = []
with open(path_to_telemetry, 'r') as file:
    telemetry_data = list(DictReader(file))

processData(telemetry_data, path_to_telemetry)

status_data = []
with open(path_to_status, 'r') as file:
    status_data = list(DictReader(file))

processData(status_data, path_to_status)
