import os
import json
import re
import sqlite3

from typing import Tuple

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

def setup_db(db_name: str) -> None:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE ALL_TIME_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        GAMES_PLAYED INT NOT_NULL,
        TOTAL_SCORE INT NOT_NULL,
        AVERAGE_SCORE REAL NOT_NULL);
        ''')

    c.execute('''
        CREATE TABLE WEEKLY_STATS
        (PLAYER_ID TEXT PRIMARY KEY NOT NULL,
        GAMES_PLAYED INT NOT_NULL,
        TOTAL_SCORE INT NOT_NULL,
        AVERAGE_SCORE REAL NOT_NULL);
        ''')
    conn.commit()
    conn.close()

db_name = "wordle.db"

if not (os.path.exists(db_name)):
    print("Database does not exist. Creating new database.")
    setup_db(db_name)

def is_wordle_message(message: str) -> bool:
    found = re.search("^Wordle\s\d+\s[1-5X]\/\d", message)
    if (found):
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
    c.execute("INSERT INTO ALL_TIME_STATS VALUES (?, 0, 0, 0.0);", (player_id,))
    conn.commit()
    conn.close()

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
    c.execute("INSERT INTO WEEKLY_STATS VALUES (?, 0, 0, 0.0);", (player_id,))
    conn.commit()
    conn.close()

def get_game_number_and_score(text: str) -> Tuple[int, int]:
    print(text)
    found = re.search("\d+", text)
    game_number = found.group(0)
    found = re.search("[1-5X]\/\d", text)
    score = found.group(0)[0]
    if (score == 'X'):
        score = 6
    return game_number, score

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

def process_message(message: str) -> None:
    # 1. Check to see if player is new all time
    if (is_new_player_all_time(message['sender_id']) == True):
        print("New player all time. Adding player to database.")
        add_new_player_all_time(message['sender_id'])
    # 2. Check to see if player is new weekly
    if (is_new_player_weekly(message['sender_id']) == True):
        print("New player weekly. Adding player to table.")
        add_new_player_weekly(message['sender_id'])
    # 3. Get the Wordle game # and the score
    # Game number is not being used for anything yet
    game_number, score = get_game_number_and_score(message['text'])
    print("Game number:", game_number, "Score:", score)
    # 4. Update the all time standings
    print("Updating all time standings for player_id:", message['sender_id'], "score:", score)
    update_standings_all_time(message['sender_id'], score)
    stats = get_player_stats_all_time(message['sender_id'])
    print(stats)

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    message = request.get_json()
    if (is_wordle_message(message['text']) == False):
        return "ok", 200
    # Message is a Wordle message
    process_message(message)
    return "ok", 200