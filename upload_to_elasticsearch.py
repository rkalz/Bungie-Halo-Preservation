from collections import OrderedDict
from credentials import ES_URL
from math import floor
from requests import post
import json
import os
import random


def upload_to_elasticsearch():
    # Can't be parallelized due to server side rate limiting
    path_to_folder = "C:\\Users\\aleez\\Desktop\\Halo 2 Data\\fixed_files\\"
    files_to_upload = os.listdir(path_to_folder)
    for i in range(10000):
        file = random.choice(files_to_upload)
        game_id = file[file.rfind('_')+1:file.rfind('.')]
        with open(path_to_folder + file, 'r') as f:
            match_data = json.loads(f.read(), object_pairs_hook=OrderedDict)
            match_data["id"] = str(match_data["id"])
            if "teams" in match_data:
                for team in match_data["teams"]:
                    if "winner" not in match_data:
                        match_data["winner"] = team
                    match_data["teams"][team]["kills"] = int(match_data["teams"][team]["kills"])
                    match_data["teams"][team]["assists"] = int(match_data["teams"][team]["assists"])
                    match_data["teams"][team]["deaths"] = int(match_data["teams"][team]["deaths"])
                    match_data["teams"][team]["spread"] = int(match_data["teams"][team]["spread"])
                    match_data["teams"][team]["suicides"] = int(match_data["teams"][team]["suicides"])
                    match_data["teams"][team]["betrayals"] = int(match_data["teams"][team]["betrayals"])
            r = post(ES_URL + "/h2/_doc/" + game_id, json=match_data)
            print(game_id + ": " + str(r.status_code))
            if floor(r.status_code / 100) != 2:
                print(r.content)
                print(str(10000-i) + " files remaining")
                break


upload_to_elasticsearch()
