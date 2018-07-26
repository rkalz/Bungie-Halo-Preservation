from credentials import ES_URL
import json
import os
import random
import requests


def upload_to_elasticsearch():
    path_to_folder = "C:\\Users\\aleez\\Desktop\\Halo 2 Data\\fixed_files\\"
    files_to_upload = os.listdir(path_to_folder)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    for _ in range(9999):
        file = random.choice(files_to_upload)
        id = file[file.rfind('_')+1:file.rfind('.')]
        with open(path_to_folder + file, 'r') as f:
            data = json.loads(f.read())
            requests.post(ES_URL + "/h2/" + id, json=data, headers=headers)
            print(id)


upload_to_elasticsearch()