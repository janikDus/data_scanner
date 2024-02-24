from csv import DictReader
from datetime import datetime
import json
import os
import matplotlib.pyplot as plt
import operator

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

    time_diff_avg = time_diff_sum // TIME_DIFF_SAMPLE

    return time_diff_avg


def processData(data: list, file_path: str):
    '''
    '''

    default_time_diff = getAvgTimeDiff(data)

    data[0]['event'] = False
    for index in range(1, len(data)):
        old_one = data[index - 1]
        current_one = data[index]

        old_one_time = datetime.strptime(old_one['time'][:19], format)
        current_one_time = datetime.strptime(current_one['time'][:19], format)

        time_diff = int((current_one_time - old_one_time).seconds)

        if time_diff > default_time_diff:
            data[index]['event'] = True
        else:
            data[index]['event'] = False

    file_name, _ = os.path.basename(file_path).rsplit('.', 1)
    json.dump(data, open(processed_file.format(file_name), 'w', encoding='utf8'), indent=2)


telemetry_data = []
with open(path_to_telemetry, 'r') as file:
    telemetry_data = list(DictReader(file))
    # telemetry_data.sort(key=operator.itemgetter('id'))

processData(telemetry_data, path_to_telemetry)

status_data = []
with open(path_to_status, 'r') as file:
    status_data = list(DictReader(file))
    # status_data.sort(key=operator.itemgetter('id'))

processData(status_data, path_to_status)

axes_x = []
axes_y = []
events = []

for telemetry_item in telemetry_data:
    axes_x.append(telemetry_item['time'][12:19])
    # axes_y.append(float(telemetry_item['height']))
    axes_y.append(float(telemetry_item['pressure']))
    if telemetry_item['event']:
        events.append(telemetry_item['time'][12:19])

plt.plot(axes_x, axes_y)
for event in events:
    plt.axvspan(event, event, color='red', alpha=1.0)

ticks = list(axes_x[0::10])
plt.xticks(ticks, rotation=90)

plt.show()


'''
for status_item in status_data:
    axes_x.append(status_item['time'][12:19])
    # axes_y.append(float(telemetry_item['battery']))
    axes_y.append(float(status_item['satellites']))
    if status_item['event']:
        events.append(status_item['time'][12:19])

plt.plot(axes_x, axes_y)
for event in events:
    plt.axvspan(event, event, color='red', alpha=1.0)

ticks = list(axes_x)
plt.xticks(ticks, rotation=90)

plt.show()
'''
