import json
import os
from collections import OrderedDict


def find_bad_files():
    folder_path = "C:\\Users\\aleez\\Desktop\\Halo 2 Data\\"
    file_names = os.listdir(folder_path)
    bad_files = []

    for name in file_names:
        with open(folder_path + name, 'r') as file:
            match = None
            try:
                match = json.loads(file.read())
            except Exception:
                bad_files.append(name)
                continue

            if "players" in match:
                for player in match["players"]:
                    if player == "Red Team" or player == "Blue Team" or player == "Green Team" \
                            or player == "Orange Team" or player == "Brown Team" or player == "Yellow Team" \
                            or player == "Pink Team":
                        print(str(match["id"]))
                        bad_files.append(name)
                        break

    print(str(len(bad_files)) + " bad files found")
    with open(os.getcwd() + "\\files_to_fix.txt", 'w') as file:
        for bad_file in bad_files:
            file.write(bad_file + '\n')


def fix_bad_files():
    bad_files = None
    with open("files_to_fix.txt", 'r') as f:
        bad_files = f.read().splitlines()

    folder_path = "C:\\Users\\aleez\\Desktop\\Halo 2 Data\\"
    fixed_folder_path = os.curdir + "\\fixed_files\\"
    for file in bad_files:
        with open(folder_path + file, 'r') as f:
            try:
                match = json.loads(f.read(), object_pairs_hook=OrderedDict)
                players = match["players"]
                match.pop("players", None)
                match["teams"] = dict()
                last_team_name = None
                last_team_data = None
                for player in players:
                    if player == "Red Team" or player == "Blue Team" or player == "Green Team" \
                            or player == "Orange Team" or player == "Brown Team" or player == "Yellow Team" \
                            or player == "Pink Team":
                        if last_team_name is not None:
                            match["teams"][last_team_name] = last_team_data
                        last_team_name = player
                        last_team_data = players[player]
                        last_team_data["players"] = dict()
                    else:
                        last_team_data["players"][player] = players[player]
                if last_team_name is not None:
                    match["teams"][last_team_name] = last_team_data
                with open(fixed_folder_path + file, 'w') as fi:
                    json.dump(match, fi)
                print(match["id"])
            except Exception as e:
                continue


fix_bad_files()
