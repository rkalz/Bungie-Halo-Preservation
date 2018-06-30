import json
import os


def find_bad_files():
    folder_path = "C:\\Users\\aleez\\Desktop\\Halo 2 Data\\"
    file_names = os.listdir(folder_path)
    bad_files = []

    for name in file_names:
        with open(folder_path + name, 'r') as file:
            match = None
            try:
                match = json.loads(file.read())
            except Exception as e:
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


find_bad_files()

