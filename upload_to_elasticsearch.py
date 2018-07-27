from credentials import ES_URL
from math import floor
from requests import post
import json
import os
import random


def upload_to_elasticsearch():
    path_to_folder = "C:\\Users\\aleez\\Desktop\\Halo 2 Data\\fixed_files\\"
    files_to_upload = os.listdir(path_to_folder)
    for _ in range(9000):
        file = random.choice(files_to_upload)
        game_id = file[file.rfind('_')+1:file.rfind('.')]
        with open(path_to_folder + file, 'r') as f:
            match_data = json.loads(f.read())
            r = post(ES_URL + "/h2/_doc/" + game_id, json=match_data)
            print(game_id + ": " + str(r.status_code))
            if floor(r.status_code / 100) != 2:
                print(r.content)
                break


upload_to_elasticsearch()
