import cProfile
import json
import os
import re
import multiprocessing
import threading
import urllib.request
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool


def get_metadata(map_and_gametype):
    gametype, mapname, playlist, date, time, duration = \
        None, None, None, None, None, None

    for line in map_and_gametype.text.split('\n'):
        line = line.strip()
        if line.find(" on ") != -1:
            gametype = line[:line.find(" on")]
            mapname = line[line.find("n ") + 2:]
        elif line.find('-') != -1:
            playlist = line[line.find('- ') + 2:]
        elif ',' in line:
            split = line.split(", ")
            date = split[0]
            time = split[1]
        elif "Length" in line:
            split = line.split(": ")
            if len(split) == 2:
                duration = split[1]

    return gametype, mapname, playlist, date, time, duration


def get_medals(medal_rows):
    medals = dict()
    for medal_row in medal_rows:
        title = medal_row.find("div", {"class": "title"})
        count = medal_row.find("div", {"class": "number"})
        if title is not None and count is not None and title.text not in medals:
            medals[title.text] = count.text
    return medals


def get_team_data(rows, carnage_rows):
    teams = dict()
    ranked = dict()
    has_teams = False
    last_team = None
    columns = None
    for i in range(rows):
        total_row = []
        if carnage_rows is not None:
            row = carnage_rows[i]
            cols = row.find_all("td")
            for col in cols:
                text = col.text.strip()
                if text == "K/D Spread":
                    text = "Spread"
                total_row.append(text)
                exp_bar = col.find("div", {"class": "ExpBar"})
                if exp_bar is not None:
                    style = exp_bar.find("span").get("style")
                    progress = style[style.find(':') + 1:style.find("px")]
                    ranked[total_row[0][:total_row[0].find('\n')]] = str(int(progress) * 2.5)
        if i is 0:
            columns = total_row
        else:
            is_team = False
            for j in range(len(columns)):
                col_name = columns[j]
                item = total_row[j]
                player_newline_indent = total_row[0].find('\n')
                if col_name == "Players":
                    if item == "Red Team" \
                            or item == "Blue Team" \
                            or item == "Green Team" \
                            or item == "Orange Team" \
                            or item == "Brown Team" \
                            or item == "Yellow Team" \
                            or item == "Pink Team":
                        last_team = item
                        has_teams = True
                        is_team = True
                        teams[item] = dict()
                        teams[item]["players"] = dict()
                    elif has_teams:
                        if player_newline_indent != -1:
                            player = item[:player_newline_indent]
                            rank = item[player_newline_indent + 1:]
                            teams[last_team]["players"][player] = dict()
                            teams[last_team]["players"][player]["rank"] = rank
                            teams[last_team]["players"][player]["progress"] = ranked[player]
                        else:
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
                        if player_newline_indent != -1:
                            player = item[:player_newline_indent]
                            rank = item[player_newline_indent + 1:]
                            teams[player] = dict()
                            teams[player]["rank"] = rank
                            teams[player]["progress"] = ranked[player]
                        else:
                            teams[item] = dict()

                elif has_teams and not is_team:
                    if player_newline_indent != -1:
                        teams[last_team]["players"][total_row[0][:player_newline_indent]][col_name.lower()] = item
                    else:
                        teams[last_team]["players"][total_row[0]][col_name.lower()] = item

                else:
                    if player_newline_indent != -1:
                        teams[total_row[0][:player_newline_indent]][col_name.lower()] = item
                    else:
                        teams[total_row[0]][col_name.lower()] = item

    return teams, has_teams


def get_data(game_id):

    url = 'http://halo.bungie.net/Stats/GameStatsHalo2.aspx?gameid=' + str(game_id)
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, "html.parser")
    pool = multiprocessing.pool.ThreadPool(3)

    output = dict()
    output["id"] = game_id

    rows = 0
    carnage_rows = soup.find("div", {"id": "ctl00_mainContent_bnetpgd_pnlKills"}) \
        .find("table", {"class": "stats"})
    if carnage_rows is not None:
        carnage_rows = carnage_rows.find_all("tr")
        rows = len(carnage_rows)

    async_team_data = \
        pool.apply_async(get_team_data, [rows, carnage_rows])

    map_and_gametype = soup.find("div", {"class": "stats_overview"})\
        .find("ul", {"class": "summary"})
    async_metadata = pool.apply_async(get_metadata, [map_and_gametype])

    medal_rows = soup.find("div", {"class": "ranked_medals_row"}).find_all("div")
    async_medals = pool.apply_async(get_medals, [medal_rows])

    gametype, mapname, playlist, date, time, duration = async_metadata.get()
    output["gametype"] = gametype
    output["map"] = mapname
    output["playlist"] = playlist
    output["date"] = date
    output["time"] = time
    if duration is not None:
        output["duration"] = duration

    medals = async_medals.get()
    if len(medals) is not 0:
        output["medals"] = medals

    teams, has_teams = async_team_data.get()
    if has_teams:
        output["teams"] = teams
    else:
        output["players"] = teams

    with open("halo_2_game_" + str(game_id) + ".json", 'w') as file:
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


START = 6066
END = 803138050
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

get_data(6066)