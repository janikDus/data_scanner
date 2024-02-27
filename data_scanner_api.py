# main.py

from csv import DictReader
from datetime import datetime
import json
import os
import matplotlib.pyplot as plt
import sys
import traceback

from fastapi import FastAPI
from pydantic import BaseModel

TIME_DIFF_SAMPLE = 20
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MESSAGES_TO_SHOW = {
    'telemetry': ['latitude', 'geo_altitude', 'height', 'speed_accuracy', 'pressure'],
    'status': ['battery', 'snr', 'tac', 'satellites']
}
EXPECTED_FILE_TYPES = ['csv']
EXPECTED_FILE_SUBNAMES = ['telemetry', 'status']

processed_file = 'processed_{}.json'
png_file = '{}_graph_{}.png'


def getAvgTimeDiff(data: list):
    '''
    Function getAvgTimeDiff calculate the average difference in time column sample of data (size of the sample is defined in TIME_DIFF_SAMPLE).

    Input: Csv data in structure list of dictionries
    Output: Average difference in time column
    '''

    time_diff_avg = 0
    time_diff_sum = 0
    # fix same time value for the following lines
    zero_count = 0
    for index in range(1, TIME_DIFF_SAMPLE + 1):
        # cut time zone offset
        old_one_time = datetime.strptime(data[index - 1]['time'][:19], DATE_FORMAT)
        current_one_time = datetime.strptime(data[index]['time'][:19], DATE_FORMAT)
        time_diff = int((current_one_time - old_one_time).seconds)

        if time_diff > 0:
            time_diff_sum += time_diff
        else:
            zero_count += 1

    time_diff_count = TIME_DIFF_SAMPLE - zero_count
    if time_diff_count > 0:
        time_diff_avg = round(time_diff_sum / time_diff_count)

    return time_diff_avg


def processData(data: list, file_name: str, result_path: str):
    '''
    Function processData determine message events which are not equal to default time difference. 
    The events are marked and save to the json file into result folder.

    Input: Csv data in structure list of dictionries, csv file name, path to the result folder
    Output: Path to result json file
    '''

    result_json_file = ''

    default_time_diff = getAvgTimeDiff(data)

    if default_time_diff > 0:
        # expectation: the event will not be on the first line of data
        data[0]['event'] = False
        for index in range(1, len(data)):
            old_one = data[index - 1]
            current_one = data[index]

            # cut time zone offset
            old_one_time = datetime.strptime(old_one['time'][:19], DATE_FORMAT)
            current_one_time = datetime.strptime(current_one['time'][:19], DATE_FORMAT)

            time_diff = int((current_one_time - old_one_time).seconds)

            if time_diff == default_time_diff:
                data[index]['event'] = False
            else:
                data[index]['event'] = True

        processed_json_file = os.path.join(result_path, processed_file.format(file_name))
        json.dump(data, open(processed_json_file, 'w', encoding='utf8'), indent=2)
        result_json_file = processed_json_file
    else:
        sys.stdout.write('Exception for file: {} : default_time_diff was not set.\n'.format(file_name))

    return result_json_file


def showProcessedData(data: list, message_name: str, file_name: str, result_path: str):
    '''
    Function showProcessedData visualize data colum defined in message_name and save the graph as image into result folder.

    Input: Csv data in structure list of dictionries, data colum name, csv file name, path to the result folder
    Output: Path to png graph file
    '''

    axes_x = []
    axes_y = []
    events = []

    for item in data:
        # show only HH:MM:SS
        axes_x.append(item['time'][10:19])
        try:
            axes_y.append(float(item[message_name]))
        except ValueError:
            axes_y.append(item[message_name])
        if item['event']:
            events.append(item['time'][10:19])

    plt.plot(axes_x, axes_y)
    for event in events:
        plt.axvspan(event, event, color='red', alpha=1.0)

    plt.xlabel('time')
    plt.ylabel(message_name)

    plt.xticks(events, rotation=30)

    message_graph_file = os.path.join(result_path, png_file.format(file_name, message_name))
    plt.savefig(message_graph_file)
    plt.close()

    return message_graph_file


def processDataFolder(message_data_path: str, result_path: str):
    '''
    Function processDataFolder walk through the given folder and process expected scv files.

    Input: Path to scv file folder, path to the result folder
    Output: Lits of path to result files collected in dictionary
    '''

    process_folder_status = {
        'json_files': [],
        'graphs': []
    }

    for dir_path, _, file_basenames in os.walk(message_data_path):
        for file_basename in file_basenames:
            try:
                path_to_messages_data = os.path.join(dir_path, file_basename)
                file_name, file_ext = file_basename.rsplit('.', 1)

                if file_ext in EXPECTED_FILE_TYPES:

                    for subname in EXPECTED_FILE_SUBNAMES:
                        if subname in file_basename:

                            result_fullpath = os.path.join(result_path, file_name)
                            os.makedirs(result_fullpath, exist_ok=True)

                            message_data = []
                            with open(path_to_messages_data, 'r') as file:
                                message_data = list(DictReader(file))

                            json_file = processData(message_data, file_name, result_fullpath)
                            process_folder_status['json_files'].append(json_file)

                            if json_file:
                                for message_name in MESSAGES_TO_SHOW[subname]:
                                    png_file = showProcessedData(message_data, message_name, file_name, result_fullpath)
                                    process_folder_status['graphs'].append(png_file)
                            else:
                                raise Exception('Exception in processData: default_time_diff was not set.')

            except Exception as e:
                process_folder_status = False
                sys.stdout.write('Exception for file: {} : {}\n'.format(file_name, traceback.format_exc()))

    return process_folder_status


class Configuration(BaseModel):
    pathToMessageData: str
    pathToResult: str


app = FastAPI()


@app.post("/process_data/")
async def create_item(config: Configuration):

    item_dict = {}

    if config.pathToMessageData and config.pathToResult:
        folder_status = processDataFolder(config.pathToMessageData, config.pathToResult)
        if folder_status:
            item_dict['folder_status'] = folder_status

    return item_dict
