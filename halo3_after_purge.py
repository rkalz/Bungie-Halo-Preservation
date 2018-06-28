import json
import os
import multiprocessing
import threading
import urllib.request
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool


def get_metadata(metadata):
    gametype, mapname, playlist, date, time = \
        None, None, None, None, None

    for line in metadata.text.split('\n'):
        line = line.strip()
        if line.find(" on ") != -1:
            gametype = line[:line.find(" on")]
            mapname = line[line.find("n ") + 2:]
        elif line.find('-') != -1:
            playlist = line[line.find('- ') + 2:]
        elif line.find(',') != -1:
            date = line[:line.find(',')]
            time = line[line.find(',') + 2:]

    return gametype, mapname, playlist, date, time


def get_team_data(carnage_rows):
    teams = dict()
    has_teams = False
    last_team = None
    columns = None
    for i in range(len(carnage_rows)):
        total_row = []
        row = carnage_rows[i]
        cols = row.find_all("td")
        for col in cols:
            text = col.text.strip()
            if text == "K/D Spread":
                text = "Spread"
            total_row.append(text)
        if i is 0:
            columns = total_row
        else:
            is_team = False
            for j in range(len(columns)):
                # Identify this column's attribute and add to appropriate target
                col_name = columns[j]
                item = total_row[j]
                player_front_newline_indent = total_row[0].find('\n')
                player_back_newline_indent = total_row[0].rfind('\n')
                if col_name == "Players":
                    # Every name in here is either a team name or a gamertag
                    if item == "Red Team" or item == "Blue Team" or item == "Green Team" \
                            or item == "Orange Team" or item == "Brown Team" or item == "Yellow Team" \
                            or item == "Pink Team":
                        # All possible team names (If there's an 8th, I haven't found it)
                        last_team = item
                        has_teams = True
                        is_team = True
                        teams[item] = dict()
                        teams[item]["players"] = dict()
                    elif has_teams:
                        if player_front_newline_indent != -1 and player_back_newline_indent != -1:
                            # Indicates that this was a ranked game
                            # Player\n \nRank
                            player = item[:player_front_newline_indent]
                            rank = item[player_back_newline_indent + 1:]
                            teams[last_team]["players"][player] = dict()
                            teams[last_team]["players"][player]["rank"] = rank
                        else:
                            # Check for guests (not allowed in ranked play)
                            # All guests are reported as Gamertag(G), even if multiple
                            # Append number for additional guests (should only be 2, 3, or 4)
                            if item not in teams[last_team]["players"]:
                                teams[last_team]["players"][item] = dict()
                            else:
                                number = 2
                                item_copy = item + '(' + str(number) + ')'
                                while item_copy in teams[last_team]["players"]:
                                    number += 1
                                    item_copy = item + '(' + str(number) + ')'
                                item = item_copy
                                total_row[j] = item
                                teams[last_team]["players"][item] = dict()
                    else:
                        # FFA ranked game
                        if player_front_newline_indent != -1 and player_back_newline_indent != -1:
                            player = item[:player_front_newline_indent]
                            rank = item[player_back_newline_indent + 1:]
                            teams[player] = dict()
                            teams[player]["rank"] = rank
                        else:
                            teams[item] = dict()

                elif has_teams and not is_team:
                    # Assign attribute to player, located in team dict
                    if player_front_newline_indent != -1:
                        teams[last_team]["players"][total_row[0][:player_front_newline_indent]][col_name.lower()] = item
                    else:
                        teams[last_team]["players"][total_row[0]][col_name.lower()] = item

                else:
                    # Free for all game
                    if player_front_newline_indent != -1:
                        teams[total_row[0][:player_front_newline_indent]][col_name.lower()] = item
                    else:
                        teams[total_row[0]][col_name.lower()] = item

    return teams, has_teams


def get_data(game_id):

    url = 'http://halo.bungie.net/Stats/GameStatsHalo3.aspx?gameid=' + str(game_id)
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, "html.parser")
    pool = multiprocessing.pool.ThreadPool(2)

    output = dict()
    output["id"] = str(game_id)

    # The carnage tab essentially has all the remaining data
    carnage_rows = soup.find("div", {"id": "ctl00_mainContent_bnetpgd_pnlKills"}) \
        .find("table", {"class": "stats"}).find_all("tr")
    async_team_data = pool.apply_async(get_team_data, [carnage_rows])

    # Get information about the map, gametype, playlist, and other metadata
    metadata = soup.find("div", {"class": "stats_overview"})\
        .find("ul", {"class": "summary"})
    async_metadata = pool.apply_async(get_metadata, [metadata])

    gametype, mapname, playlist, date, time = async_metadata.get()
    output["gametype"] = gametype
    output["map"] = mapname
    output["playlist"] = playlist
    output["date"] = date
    output["time"] = time

    teams, has_teams = async_team_data.get()
    # JSON tag based on if team game or FFA
    if has_teams:
        output["teams"] = teams
    else:
        output["players"] = teams

    with open("halo_3_game_" + str(game_id) + ".json", 'w') as file:
        json.dump(output, file)


stdio_lock = threading.Lock()


def work(start, end):
    started = False
    for i in range(start, end):
        if started:
            try:
                get_data(i)
            except Exception as e:
                stdio_lock.acquire()
                print(str(os.getpid()) + ": " + str(e))
                stdio_lock.release()
                continue

        elif i not in generated:
            if not started:
                stdio_lock.acquire()
                print(str(os.getpid()) + " starting at " + str(i))
                stdio_lock.release()
                started = True
            try:
                get_data(i)
            except Exception as e:
                stdio_lock.acquire()
                print(str(os.getpid()) + ": " + str(e))
                stdio_lock.release()
                continue


START = 1
END = 1917736473
SUM = END-START
WORK_PER_THREAD = int(SUM / 24)

'''
file_list = os.listdir("E:/Halo 2 Data/")
generated = set()

for file in file_list:
    file = file[file.rfind('_')+1:file.find('.')]
    generated.add(int(file))

st = START
for i in range(24):
    t = multiprocessing.Process(target=work, args=[st, st + WORK_PER_THREAD])
    t.start()
    st += WORK_PER_THREAD

main_thread = threading.current_thread()
for t in threading.enumerate():
    if t is not main_thread:
        t.join()
'''

get_data(1889748906)