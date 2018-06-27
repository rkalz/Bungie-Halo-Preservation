import json
import os
import re
import threading
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path


def get_data(game_id):

    url = 'http://halo.bungie.net/Stats/GameStatsHalo2.aspx?gameid=' + str(game_id)
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, "html.parser")

    output = dict()
    output["id"] = game_id

    map_and_gametype = soup.find("div", {"class": "stats_overview"})\
        .find("ul", {"class": "summary"})

    for line in map_and_gametype.text.split('\n'):
        line = line.strip()
        if " on " in line:
            split = line.split(" on ")
            output["gametype"] = split[0]
            output["map"] = split[1]
        elif '-' in line:
            split = line.split(" - ")
            output["playlist"] = split[1]
        elif ',' in line:
            split = line.split(", ")
            output["date"] = split[0]
            output["time"] = split[1]
        elif "Length" in line:
            split = line.split(": ")
            if len(split) == 2:
                output["duration"] = split[1]

    medals = dict()
    medal_rows = soup.find("div", {"class": "ranked_medals_row"}).find_all("div")
    for medal_row in medal_rows:
        title = medal_row.find("div", {"class": "title"})
        count = medal_row.find("div", {"class": "number"})
        if title is not None and count is not None and title.text not in medals:
            medals[title.text] = count.text

    if len(medals) is not 0:
        output["medals"] = medals

    rows = 0
    carnage_rows = soup.find("div", {"id": "ctl00_mainContent_bnetpgd_pnlKills"})\
        .find("table", {"class": "stats"})
    if carnage_rows is not None:
        carnage_rows = carnage_rows.find_all("tr")
        rows = len(carnage_rows)

    breakdown_rows = soup.find("div", {"id": "ctl00_mainContent_bnetpgd_pnlBreakdown"})\
        .find("table", {"class": "stats"})
    if breakdown_rows is not None:
        breakdown_rows = breakdown_rows.find_all("tr")

    field_stat_rows = soup.find("div", {"id": "ctl00_mainContent_bnetpgd_pnlFieldStats"})\
        .find("table", {"class": "stats"})
    if field_stat_rows is not None:
        field_stat_rows = field_stat_rows.find_all("tr")

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
                    progress = style[style.find(':')+1:style.find("px")]
                    ranked[total_row[0][:total_row[0].find('\n')]] = str(int(progress) * 2.5)
        if breakdown_rows is not None:
            row = breakdown_rows[i]
            cols = row.find_all("td")
            if len(total_row) == 0:
                total_row.append(cols[0].text.strip())
                exp_bar = cols[0].find("div", {"class": "ExpBar"})
                if exp_bar is not None:
                    style = exp_bar.find("span").get("style")
                    progress = style[style.find(':'):style.find("px")]
                    ranked[total_row[0][:total_row[0].find('\n')]] = progress
            for j in range(1, len(cols)):
                total_row.append(cols[j].text.strip())
        if field_stat_rows is not None:
            row = field_stat_rows[i]
            cols = row.find_all("td")
            if len(total_row) == 0:
                total_row.append(cols[0].text.strip())
                exp_bar = cols[0].find("div", {"class": "ExpBar"})
                if exp_bar is not None:
                    style = exp_bar.find("span").get("style")
                    progress = style[style.find(':'):style.find("px")]
                    ranked[total_row[0][:total_row[0].find('\n')]] = progress
            for j in range(1, len(cols)):
                total_row.append(cols[j].text.strip())
        if i is 0:
            columns = total_row
        else:
            is_team = False
            for j in range(len(columns)):
                col_name = columns[j]
                item = total_row[j]
                if col_name == "Players":
                    if item is "Red Team"\
                        or item is "Blue Team"\
                        or item is "Green Team"\
                        or item is "Orange Team"\
                        or item is "Brown Team"\
                        or item is "Yellow Team"\
                    or item is "Pink Team":
                        last_team = item
                        has_teams = True
                        is_team = True
                        teams[item] = dict()
                        teams[item]["players"] = dict()
                    elif has_teams:
                        if item.find('\n') != -1:
                            player = item[:item.find('\n')]
                            rank = item[item.find('\n')+1:]
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
                        if item.find('\n') != -1:
                            player = item[:item.find('\n')]
                            rank = item[item.find('\n')+1:]
                            teams[player] = dict()
                            teams[player]["rank"] = rank
                            teams[player]["progress"] = ranked[player]
                        else:
                            teams[item] = dict()

                elif col_name == "Tool of Destruction":
                    if item != '-':
                        item = re.split(r'\s+', item)
                        tools = dict()
                        weapon = ""
                        for k in range(3, len(item)):
                            word = item[k]
                            if word.isdigit() and weapon is not "":
                                tools[weapon.lower()] = word
                                weapon = ""
                            elif word.find('(') == -1:
                                weapon += word
                        player = total_row[0]
                        if player.find('\n') != -1:
                            player = player[:player.find('\n')]
                        if has_teams:
                            teams[last_team]["players"][player]["tools"] = tools
                        else:
                            teams[player]["tools"] = tools

                elif col_name == "Most Killed":
                    if item != '-':
                        item = re.split(r'\s+', item)
                        killed = dict()
                        player = ""
                        for k in range(2, len(item)):
                            word = item[k]
                            if word.isdigit() and k is not len(item) - 1:
                                if player not in killed:
                                    killed[player] = word
                                else:
                                    number = 2
                                    name = player + '(' + str(number) + ')'
                                    while name in killed:
                                        number += 1
                                        name = player + '(' + str(number) + ')'
                                    killed[name] = word
                            elif word.find(':') != -1:
                                player = word[:word.find(':')]
                        player = total_row[0]
                        if player.find('\n') != -1:
                            player = player[:player.find('\n')]
                        if has_teams:
                            teams[last_team]["players"][player]["most killed"] = killed
                        else:
                            teams[player]["most killed"] = killed

                elif col_name == "Most Killed By":
                    if item != '-':
                        item = re.split(r'\s+', item)
                        killed_by = dict()
                        player = ""
                        for k in range(2, len(item)):
                            word = item[k]
                            if word.isdigit() and k is not len(item) - 1:
                                if player not in killed_by:
                                    killed_by[player] = word
                                else:
                                    number = 2
                                    name = player + '(' + str(number) + ')'
                                    while name in killed_by:
                                        number += 1
                                        name = player + '(' + str(number) + ')'
                                    killed_by[name] = word
                            elif word.find(':') != -1:
                                player = word[:word.find(':')]
                        player = total_row[0]
                        if player.find('\n') != -1:
                            player = player[:player.find('\n')]
                        if has_teams:
                            teams[last_team]["players"][player]["most killed by"] = killed_by
                        else:
                            teams[player]["most killed by"] = killed_by

                elif has_teams and not is_team:
                    if total_row[0].find('\n') != -1:
                        teams[last_team]["players"][total_row[0][:total_row[0].find('\n')]][col_name.lower()] = item
                    else:
                        teams[last_team]["players"][total_row[0]][col_name.lower()] = item

                else:
                    if total_row[0].find('\n') != -1:
                        teams[total_row[0][:total_row[0].find('\n')]][col_name.lower()] = item
                    else:
                        teams[total_row[0]][col_name.lower()] = item

    if has_teams:
        output["teams"] = teams
    else:
        output["players"] = teams

    with open("E:/Halo 2 Data/halo_2_gameid_" + str(game_id) + ".json", 'w') as file:
        json.dump(output, file)

lock = threading.Lock()


def work(start, end):
    started = False
    for i in range(start, end):
        if started:
            try:
                get_data(i)
            except Exception as e:
                lock.acquire()
                print(threading.current_thread().getName() + ": " + str(e))
                lock.release()
                continue

        elif i not in generated:
            if not started:
                lock.acquire()
                print(threading.current_thread().getName() + " starting at " + str(i))
                lock.release()
                started = True
            try:
                get_data(i)
            except Exception as e:
                lock.acquire()
                print(threading.current_thread().getName() + ": " + str(e))
                lock.release()
                continue

START = 6066
END = 803138050
SUM = END-START
WORK_PER_THREAD = int(SUM / 24)

file_list = os.listdir("E:/Halo 2 Data/")
generated = set()

for file in file_list:
    file = file[file.rfind('_')+1:file.find('.')]
    generated.add(int(file))

st = START
for i in range(24):
    t = threading.Thread(target=work, args=[st, st + WORK_PER_THREAD])
    t.start()
    st += WORK_PER_THREAD

main_thread = threading.current_thread()
for t in threading.enumerate():
    if t is not main_thread:
        t.join()
