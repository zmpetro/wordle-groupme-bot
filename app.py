import os
import json
import re
import sqlite3
import requests

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
        SCORE INT NOT_NULL,
        RANK INT NOT_NULL);
        ''')

    c.execute('''
        CREATE TABLE ALL_TIME_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        GAMES_PLAYED INT NOT_NULL,
        TOTAL_SCORE INT NOT_NULL,
        AVERAGE_SCORE REAL NOT_NULL,
        RANK INT NOT NULL);
        ''')

    c.execute('''
        CREATE TABLE WEEKLY_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        GAMES_PLAYED INT NOT_NULL,
        TOTAL_SCORE INT NOT_NULL,
        AVERAGE_SCORE REAL NOT_NULL,
        RANK INT NOT NULL);
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
        CREATE TABLE PLAYER_RATINGS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        MU REAL NOT_NULL,
        SIGMA REAL NOT_NULL);
        ''')

    c.execute('''
        INSERT INTO GAME_NUMBER VALUES (0);
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
    found = re.search("^Wordle\s\d+\s[1-5X]\/\d", message)
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
    c.execute("INSERT INTO ALL_TIME_STATS VALUES (?, 0, 0, 0.0, 0);", (player_id,))
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
    c.execute("INSERT INTO WEEKLY_STATS VALUES (?, 0, 0, 0.0, 0);", (player_id,))
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

def update_game_number(game_number: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT GAME FROM GAME_NUMBER;")
    rows = c.fetchall()
    cur_game = rows[0][0]
    if (cur_game != game_number):
        update_player_rankings()
        msg = "Welcome to Wordle " + str(game_number) + "!"
        send_message(msg)
        c.execute("UPDATE GAME_NUMBER SET GAME = ?;", (game_number,))
        c.execute("DELETE FROM DAILY_STATS;")
        conn.commit()
    conn.close()

def update_standings_daily(player_id: str, score: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("INSERT INTO DAILY_STATS VALUES (?, ?, 0);", (player_id,score,))
    conn.commit()
    conn.close()

def update_standings_all_time(player_id: str, score: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("UPDATE ALL_TIME_STATS SET GAMES_PLAYED = GAMES_PLAYED + 1 WHERE PLAYER_ID = ?;", (player_id,))
    c.execute("UPDATE ALL_TIME_STATS SET TOTAL_SCORE = TOTAL_SCORE + ? WHERE PLAYER_ID = ?;", (score,player_id,))
    c.execute("UPDATE ALL_TIME_STATS SET AVERAGE_SCORE = TOTAL_SCORE*1.0 / GAMES_PLAYED WHERE PLAYER_ID = ?;", (player_id,))
    conn.commit()
    conn.close()

def update_standings_weekly(player_id: str, score: int) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("UPDATE WEEKLY_STATS SET GAMES_PLAYED = GAMES_PLAYED + 1 WHERE PLAYER_ID = ?;", (player_id,))
    c.execute("UPDATE WEEKLY_STATS SET TOTAL_SCORE = TOTAL_SCORE + ? WHERE PLAYER_ID = ?;", (score,player_id,))
    c.execute("UPDATE WEEKLY_STATS SET AVERAGE_SCORE = TOTAL_SCORE*1.0 / GAMES_PLAYED WHERE PLAYER_ID = ?;", (player_id,))
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
    # 2. Check to see if player is new weekly
    if (is_new_player_weekly(message['sender_id']) == True):
        print("New player weekly. Adding player to table.")
        add_new_player_weekly(message['sender_id'])
    # 3. Update player name in case it has changed
    update_name(message['sender_id'], message['name'])
    # 4. Get the Wordle game # and the score
    game_number, score = get_game_number_and_score(message['text'])
    print("Game number:", game_number, "Score:", score)
    # 5. Update the Wordle game #
    print("Updating the game number to", game_number)
    update_game_number(game_number)
    # 6. Update the daily scores table
    print("Updating daily score for player_id:", message['sender_id'], "score:", score)
    if (is_new_player_daily(message['sender_id']) == True):
        update_standings_daily(message['sender_id'], score)
        msg = get_name(message['sender_id'])
        msg = msg + " has submitted his score for today. Beautiful."
        send_message(msg)
    else:
        msg = get_name(message['sender_id'])
        msg = msg + " has already submitted a score for today. Not submitting score."
        send_message(msg)
    # 6. Update the all time standings
    print("Updating all time standings for player_id:", message['sender_id'], "score:", score)
    update_standings_all_time(message['sender_id'], score)
    # 7. Update the weekly standings
    print("Updating weekly standings for player_id:", message['sender_id'], "score:", score)
    update_standings_weekly(message['sender_id'], score)

def print_daily_stats():
    send_message("Placeholder")

def print_weekly_stats():
    send_message("Placeholder")

def print_all_time_stats():
    send_message("Placeholder")

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