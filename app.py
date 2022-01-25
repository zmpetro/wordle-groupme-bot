import os
import json
import re
import sqlite3
import requests

from datetime import datetime

from typing import Tuple

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from trueskill import TrueSkill, Rating, rate, expose

from flask import Flask, request

BOT_ID = os.environ['BOT_ID']

def setup_db(db_name: str) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE DAILY_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        SCORE INT NOT_NULL);
        ''')

    c.execute('''
        CREATE TABLE ALL_TIME_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        GAMES_PLAYED INT NOT_NULL,
        TOTAL_SCORE INT NOT_NULL,
        AVERAGE_SCORE REAL NOT_NULL,
        NUM_1S INT DEFAULT 0,
        NUM_2S INT DEFAULT 0,
        NUM_3S INT DEFAULT 0,
        NUM_4S INT DEFAULT 0,
        NUM_5S INT DEFAULT 0,
        NUM_6S INT DEFAULT 0,
        NUM_XS INT DEFAULT 0);
        ''')

    c.execute('''
        CREATE TABLE WEEKLY_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        GAMES_PLAYED INT NOT_NULL,
        TOTAL_SCORE INT NOT_NULL,
        AVERAGE_SCORE REAL NOT_NULL,
        NUM_1S INT DEFAULT 0,
        NUM_2S INT DEFAULT 0,
        NUM_3S INT DEFAULT 0,
        NUM_4S INT DEFAULT 0,
        NUM_5S INT DEFAULT 0,
        NUM_6S INT DEFAULT 0,
        NUM_XS INT DEFAULT 0);
        ''')

    c.execute('''
        CREATE TABLE NAMES
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        NAME TEXT NOT NULL);
        ''')

    c.execute('''
        CREATE TABLE GAME_NUMBER
        (GAME INT PRIMARY KEY NOT NULL);
        ''')

    c.execute('''
        CREATE TABLE WEEK_NUMBER
        (WEEK INT PRIMARY KEY NOT NULL);
        ''')

    c.execute('''
        CREATE TABLE PLAYER_RATINGS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        MU REAL NOT_NULL,
        SIGMA REAL NOT_NULL);
        ''')

    c.execute('''
        INSERT INTO GAME_NUMBER VALUES (0);
    ''')

    c.execute('''
        INSERT INTO WEEK_NUMBER VALUES (0);
    ''')
    conn.commit()
    conn.close()

db_name = "wordle.db"

if not (os.path.exists(db_name)):
    print("Database does not exist. Creating new database.")
    setup_db(db_name)

def send_message(text: str) -> None:
    msg = {
        "text": text,
        "bot_id": BOT_ID
    }
    msg = json.dumps(msg)
    print("Sending message:", text)
    resp = requests.post('https://api.groupme.com/v3/bots/post', data=msg)
    resp.raise_for_status()

def is_wordle_score(message: str) -> bool:
    found = re.search("^Wordle\s\d+\s[1-6X]\/\d", message)
    if (found):
        return True
    else:
        return False

def is_wordle_command(message: str) -> bool:
    found = re.search("^\/wordle", message)
    if (found):
        return True
    else:
        return False

def is_new_player_daily(player_id: str) -> bool:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT EXISTS(SELECT 1 FROM DAILY_STATS WHERE PLAYER_ID = ?);", (player_id,))
    rows = c.fetchall()
    conn.close()
    if (rows[0][0] == 0):
        return True
    else:
        return False

def is_new_player_all_time(player_id: str) -> bool:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT EXISTS(SELECT 1 FROM ALL_TIME_STATS WHERE PLAYER_ID = ?);", (player_id,))
    rows = c.fetchall()
    conn.close()
    if (rows[0][0] == 0):
        return True
    else:
        return False

def add_new_player_all_time(player_id: str) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO ALL_TIME_STATS VALUES (?,0,0,0.0,0,0,0,0,0,0,0);", (player_id,))
    conn.commit()
    conn.close()

def add_new_name(player_id: str, name: str) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO NAMES VALUES (?, ?);", (player_id,name,))
    conn.commit()
    conn.close()

def update_name(player_id: str, name: str) -> None:
    # Should probably add a check to see if the name has changed before updating it
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("UPDATE NAMES SET NAME = ? WHERE PLAYER_ID = ?;", (name,player_id,))
    conn.commit()
    conn.close()

def get_name(player_id: str) -> str:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT NAME FROM NAMES WHERE PLAYER_ID = ?;", (player_id,))
    rows = c.fetchall()
    conn.close()
    return rows[0][0]

def stats_available() -> bool:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM DAILY_STATS")
    rows = c.fetchall()
    conn.close()
    if (rows):
        return True
    else:
        return False

def personal_stats_available(player_id: str) -> bool:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM ALL_TIME_STATS WHERE PLAYER_ID = ?;", (player_id,))
    rows = c.fetchall()
    conn.close()
    if (rows):
        return True
    else:
        return False

def print_daily_stats() -> None:
    if (stats_available() == False):
        send_message("No stats available yet.")
        return
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT GAME FROM GAME_NUMBER;")
    game_number = str(c.fetchall()[0][0])
    c.execute("SELECT PLAYER_ID,SCORE FROM DAILY_STATS;")
    rows = c.fetchall()
    conn.close()
    rows = sorted(rows, key = lambda x: x[1])
    msg = "Wordle " + game_number + "\n\n"
    for row in rows:
        msg = msg + get_name(row[0]) + ": " 
        if (row[1] == 7):
            msg = msg + "X"
        else:
            msg = msg + str(row[1])
        msg = msg + "/6"
        if (row[1] == 7):
            msg = msg + " 💀"
        msg = msg + "\n"
    send_message(msg)

def print_weekly_stats() -> None:
    if (stats_available() == False):
        send_message("No stats available yet.")
        return
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT WEEK FROM WEEK_NUMBER;")
    week_number = str(c.fetchall()[0][0])
    c.execute("SELECT * FROM WEEKLY_STATS;")
    rows = c.fetchall()
    conn.close()
    rows = sorted(rows, key = lambda x: x[3])
    msg = "Wordle Week " + week_number + "\n\n"
    idx = 1
    for row in rows:
        msg = msg + str(idx) + ". " + get_name(row[0]) + "\n" 
        msg = msg + "Games played: " + str(row[1]) + "\n"
        msg = msg + "Total score: " + str(row[2]) + "\n"
        msg = msg + "Average score: " + str(row[3])[:5] + "/6\n\n"
        idx = idx + 1
    send_message(msg)

def print_all_time_stats() -> None:
    if (stats_available() == False):
        send_message("No stats available yet.")
        return
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM ALL_TIME_STATS;")
    rows = c.fetchall()
    conn.close()
    rows = sorted(rows, key = lambda x: x[3])
    msg = "All Time Stats\n\n"
    idx = 1
    for row in rows:
        msg = msg + str(idx) + ". " + get_name(row[0]) + "\n" 
        msg = msg + "Games played: " + str(row[1]) + "\n"
        msg = msg + "Total score: " + str(row[2]) + "\n"
        msg = msg + "Average score: " + str(row[3])[:5] + "/6\n\n"
        idx = idx + 1
    send_message(msg)

def print_my_stats(player_id: str) -> None:
    if (personal_stats_available(player_id) == False):
        send_message("No stats available yet.")
        return
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("SELECT * FROM ALL_TIME_STATS WHERE PLAYER_ID = ?;", (player_id,))
    rows = c.fetchall()
    msg = get_name(player_id) + "\n\nAll time stats\n\n"
    for row in rows:
        msg = msg + "Games played: " + str(row[1]) + "\n"
        msg = msg + "Total score: " + str(row[2]) + "\n"
        msg = msg + "Average score: " + str(row[3])[:5] + "/6\n"
        msg = msg + "# of 1/6: " + str(row[4]) + "\n"
        msg = msg + "# of 2/6: " + str(row[5]) + "\n"
        msg = msg + "# of 3/6: " + str(row[6]) + "\n"
        msg = msg + "# of 4/6: " + str(row[7]) + "\n"
        msg = msg + "# of 5/6: " + str(row[8]) + "\n"
        msg = msg + "# of 6/6: " + str(row[9]) + "\n"
        msg = msg + "# of X/6: " + str(row[10]) + "\n\n"

    c.execute("SELECT * FROM WEEKLY_STATS WHERE PLAYER_ID = ?;", (player_id,))
    rows = c.fetchall()
    conn.close()
    msg = msg + "Weekly stats\n\n"
    for row in rows:
        msg = msg + "Games played: " + str(row[1]) + "\n"
        msg = msg + "Total score: " + str(row[2]) + "\n"
        msg = msg + "Average score: " + str(row[3])[:5] + "/6\n\n"
        msg = msg + "# of 1/6: " + str(row[4]) + "\n"
        msg = msg + "# of 2/6: " + str(row[5]) + "\n"
        msg = msg + "# of 3/6: " + str(row[6]) + "\n"
        msg = msg + "# of 4/6: " + str(row[7]) + "\n"
        msg = msg + "# of 5/6: " + str(row[8]) + "\n"
        msg = msg + "# of 6/6: " + str(row[9]) + "\n"
        msg = msg + "# of X/6: " + str(row[10]) + "\n\n"

    send_message(msg)

def is_new_player_weekly(player_id: str) -> bool:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT EXISTS(SELECT 1 FROM WEEKLY_STATS WHERE PLAYER_ID = ?);", (player_id,))
    rows = c.fetchall()
    conn.close()
    if (rows[0][0] == 0):
        return True
    else:
        return False

def add_new_player_weekly(player_id: str) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO WEEKLY_STATS VALUES (?,0,0,0.0,0,0,0,0,0,0,0);", (player_id,))
    conn.commit()
    conn.close()

def get_game_number_and_score(text: str) -> Tuple[int, int]:
    print(text)
    found = re.search("\d+", text)
    game_number = found.group(0)
    found = re.search("[1-6X]\/\d", text)
    score = found.group(0)[0]
    if (score == 'X'):
        score = 7
    return int(game_number), int(score)

def get_weekly_winners() -> Tuple[str, str]:
    # Returns the player(s) with the highest average scores for the week
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT PLAYER_ID,AVERAGE_SCORE FROM WEEKLY_STATS;')
    rows = c.fetchall()
    conn.close()
    highest_avg = min(rows, key = lambda x: x[1])[1]
    winners = ""
    for row in rows:
        if (row[1] == highest_avg):
            winner_name = get_name(row[0])
            winners = winners + winner_name + "\n"
    return winners, str(highest_avg)

def update_week_number() -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT WEEK FROM WEEK_NUMBER;")
    rows = c.fetchall()
    cur_week = rows[0][0] + 1
    c.execute("UPDATE WEEK_NUMBER SET WEEK = ?;", (cur_week,))
    conn.commit()
    conn.close()
    msg = "Welcome to Wordle week " + str(cur_week) + "!\n\n"
    if (stats_available() == True):
        weekly_winners, avg_score = get_weekly_winners()
        msg = msg + "Last week's winner(s):\n\n"
        msg = msg + weekly_winners + "\nwith an average score of: " + avg_score[:5] + "/6"
        send_message(msg)
    else:
        send_message("No stats available yet.")
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DELETE FROM WEEKLY_STATS;")
    conn.commit()
    conn.close()

def get_daily_winners() -> Tuple[str, str]:
    # Returns the player(s) with the highest score for the day
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT PLAYER_ID,SCORE FROM DAILY_STATS;')
    rows = c.fetchall()
    conn.close()
    highest_score = min(rows, key = lambda x: x[1])[1]
    winners = ""
    for row in rows:
        if (row[1] == highest_score):
            winner_name = get_name(row[0])
            winners = winners + winner_name + "\n"
    return winners, str(highest_score)

def update_game_number(game_number: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT GAME FROM GAME_NUMBER;")
    rows = c.fetchall()
    conn.close()
    cur_game = rows[0][0]

    if (cur_game == game_number):
        return

    # If it is Monday, update the week number
    if (datetime.today().weekday() == 0):
        update_week_number()
    update_player_rankings()
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("UPDATE GAME_NUMBER SET GAME = ?;", (game_number,))
    conn.commit()
    conn.close()
    msg = "Welcome to Wordle " + str(game_number) + "!\n\n"
    if (stats_available() == True):
        daily_winners, score = get_daily_winners()
        msg = msg + "Yesterday's winner(s):\n\n"
        msg = msg + daily_winners + "\nwith a score of: " + score + "/6"
        send_message(msg)
    else:
        send_message("No stats available yet.")
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DELETE FROM DAILY_STATS;")
    conn.commit()
    conn.close()

def update_standings_daily(player_id: str, score: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO DAILY_STATS VALUES (?,?);", (player_id,score,))
    conn.commit()
    conn.close()

def update_standings_all_time(player_id: str, score: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("UPDATE ALL_TIME_STATS SET GAMES_PLAYED = GAMES_PLAYED + 1 WHERE PLAYER_ID = ?;", (player_id,))
    c.execute("UPDATE ALL_TIME_STATS SET TOTAL_SCORE = TOTAL_SCORE + ? WHERE PLAYER_ID = ?;", (score,player_id,))
    c.execute("UPDATE ALL_TIME_STATS SET AVERAGE_SCORE = TOTAL_SCORE*1.0 / GAMES_PLAYED WHERE PLAYER_ID = ?;", (player_id,))
    if (score == 1):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_1S = NUM_1S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 2):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_2S = NUM_2S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 3):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_3S = NUM_3S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 4):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_4S = NUM_4S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 5):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_5S = NUM_5S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 6):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_6S = NUM_6S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 7):
        c.execute("UPDATE ALL_TIME_STATS SET NUM_XS = NUM_XS + 1 WHERE PLAYER_ID = ?;", (player_id,))
    conn.commit()
    conn.close()

def update_standings_weekly(player_id: str, score: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("UPDATE WEEKLY_STATS SET GAMES_PLAYED = GAMES_PLAYED + 1 WHERE PLAYER_ID = ?;", (player_id,))
    c.execute("UPDATE WEEKLY_STATS SET TOTAL_SCORE = TOTAL_SCORE + ? WHERE PLAYER_ID = ?;", (score,player_id,))
    c.execute("UPDATE WEEKLY_STATS SET AVERAGE_SCORE = TOTAL_SCORE*1.0 / GAMES_PLAYED WHERE PLAYER_ID = ?;", (player_id,))
    if (score == 1):
        c.execute("UPDATE WEEKLY_STATS SET NUM_1S = NUM_1S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 2):
        c.execute("UPDATE WEEKLY_STATS SET NUM_2S = NUM_2S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 3):
        c.execute("UPDATE WEEKLY_STATS SET NUM_3S = NUM_3S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 4):
        c.execute("UPDATE WEEKLY_STATS SET NUM_4S = NUM_4S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 5):
        c.execute("UPDATE WEEKLY_STATS SET NUM_5S = NUM_5S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 6):
        c.execute("UPDATE WEEKLY_STATS SET NUM_6S = NUM_6S + 1 WHERE PLAYER_ID = ?;", (player_id,))
    elif (score == 7):
        c.execute("UPDATE WEEKLY_STATS SET NUM_XS = NUM_XS + 1 WHERE PLAYER_ID = ?;", (player_id,))
    conn.commit()
    conn.close()

def get_player_stats_all_time(player_id: str) -> Tuple[str, int, int, float]:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM ALL_TIME_STATS WHERE PLAYER_ID = ?;", (player_id,))
    rows = c.fetchall()
    conn.close()
    return rows[0]

def get_player_stats_weekly(player_id: str) -> Tuple[str, int, int, float]:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM WEEKLY_STATS WHERE PLAYER_ID = ?;", (player_id,))
    rows = c.fetchall()
    conn.close()
    return rows[0]

def add_new_player_ratings(player_id: str) -> None:
    rating = Rating()
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO PLAYER_RATINGS VALUES (?, ?, ?);", (player_id,rating.mu,rating.sigma,))
    conn.commit()
    conn.close()

def update_player_rankings() -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Get scores and ratings for players who played in the current game
    c.execute('''
        SELECT DAILY_STATS.PLAYER_ID, SCORE, MU, SIGMA
        FROM DAILY_STATS, PLAYER_RATINGS
        WHERE PLAYER_RATINGS.PLAYER_ID = DAILY_STATS.PLAYER_ID;
    ''')
    rows = c.fetchall()

    if (len(rows) == 0):
        return

    # Add to list as tuples ex: [(r1, ), (r1, ), ...] (needed for rate function)
    ratings = [(Rating(mu=row[2], sigma=row[3]),) for row in rows]
    scores = [row[1] for row in rows]
    rankings = [sorted(scores).index(score) for score in scores]
    if len(ratings) <= 1:
        print("Needs more than one player to rate.")
        return

    # Update with new ratings based on how a players score ranked for the current game
    new_ratings = rate(ratings, ranks=rankings)
    for i in range(len(rows)):
        player_id = rows[i][0]
        new_rating = new_ratings[i][0]
        c.execute("UPDATE PLAYER_RATINGS SET MU = ? WHERE PLAYER_ID = ?;", (new_rating.mu,player_id,))
        c.execute("UPDATE PLAYER_RATINGS SET SIGMA = ? WHERE PLAYER_ID = ?;", (new_rating.sigma,player_id,))
    conn.commit()
    conn.close()

def get_leaderboard() -> Tuple[str, int]:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM PLAYER_RATINGS;")
    rows = c.fetchall()
    ratings = [Rating(mu=row[1],sigma=row[2]) for row in rows]
    player_ids = [row[0] for row in rows]
    leaderboard = sorted(ratings, key=expose, reverse=True)
    player_leaderboard = []
    for rating in leaderboard:
        index = ratings.index(rating)
        player_leaderboard.append([player_ids[index], expose(ratings[index])])
    conn.close()
    return player_leaderboard

def process_score(message: str) -> None:
    # 1. Check to see if player is new all time
    if (is_new_player_all_time(message['sender_id']) == True):
        print("New player all time. Adding player to database.")
        add_new_player_all_time(message['sender_id'])
        add_new_player_ratings(message['sender_id'])
        # Add a new name for the player as well
        add_new_name(message['sender_id'], message['name'])
    # 2. Update player name in case it has changed
    update_name(message['sender_id'], message['name'])
    # 3. Get the Wordle game # and the score
    game_number, score = get_game_number_and_score(message['text'])
    print("Game number:", game_number, "Score:", score)
    # 4. Update the Wordle game #
    print("Updating the game number to", game_number)
    update_game_number(game_number)
    # 5. Check to see if player is new weekly
    if (is_new_player_weekly(message['sender_id']) == True):
        print("New player weekly. Adding player to table.")
        add_new_player_weekly(message['sender_id'])
    # 6. Update the daily scores table
    print("Updating daily score for player_id:", message['sender_id'], "score:", score)
    if (is_new_player_daily(message['sender_id']) == True):
        update_standings_daily(message['sender_id'], score)
        # msg = get_name(message['sender_id'])
        # msg = msg + " has submitted his Wordle for today. Beautiful."
        # send_message(msg)
    else:
        msg = get_name(message['sender_id'])
        msg = msg + " has already submitted a score for today. Not submitting score."
        send_message(msg)
    # 7. Update the all time standings
    print("Updating all time standings for player_id:", message['sender_id'], "score:", score)
    update_standings_all_time(message['sender_id'], score)
    # 8. Update the weekly standings
    print("Updating weekly standings for player_id:", message['sender_id'], "score:", score)
    update_standings_weekly(message['sender_id'], score)

def print_leaderboard():
    leaderboard = get_leaderboard()
    msg = 'Ranked Leaderboard:\n'
    for i in range(len(leaderboard)):
        msg += '\n' + str(i+1) +'. ' + get_name(leaderboard[i][0]) + ' 🔸 TrueSkill: ' + ('%.3f' % leaderboard[i][1])
        if (i == 0):
            msg += ' 🥇'
        elif (i == 1):
            msg += ' 🥈'
        elif (i == 2):
            msg += ' 🥉'
        if (i == len(leaderboard) - 1):
            msg += ' 💀'
        msg += '\n'
    msg += '\nThe leaderboard updates at the beginning of a new day\n\n'
    send_message(msg)

def print_help():
    msg = '''Available commands:

help - show help menu
daily - show daily stats
weekly - show weekly stats
all - show all time stats
my - show personal stats
leaderboard - show ranked leaderboard

'''
    send_message(msg)

def process_command(message: str) -> None:
    found = re.search("\s.*$", message['text'])
    if not found:
        print_help()
        return
    command = found.group(0).strip()
    if (command == "daily"):
        print_daily_stats()
    elif (command == "weekly"):
        print_weekly_stats()
    elif (command == "all"):
        print_all_time_stats()
    elif (command == "my"):
        print_my_stats(message['sender_id'])
    elif (command == "leaderboard"):
        print_leaderboard()
    else:
        print_help()

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    message = request.get_json()
    if (is_wordle_score(message['text']) == True):
        process_score(message)
    elif (is_wordle_command(message['text']) == True):
        process_command(message)
    return "ok", 200