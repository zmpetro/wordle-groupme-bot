import os
import json
import re
import sqlite3

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

def setup_db(db_name):
    # If DB exists, connect to it
    # Else, set up new DB
    if not (os.path.exists(db_name)):
        db = sqlite3.connect(db_name)
        db.execute('''
            CREATE TABLE ALL_TIME_STATS
            (PLAYER_ID INT PRIMARY KEY NOT NULL,
            GAMES_PLAYED INT NOT_NULL,
            TOTAL_SCORE INT NOT_NULL,
            AVERAGE_SCORE REAL NOT_NULL);
            ''')

        db.execute('''
            CREATE TABLE WEEKLY_STATS
            (PLAYER_ID INT PRIMARY KEY NOT NULL,
            GAMES_PLAYED INT NOT_NULL,
            TOTAL_SCORE INT NOT_NULL,
            AVERAGE_SCORE REAL NOT_NULL);
            ''')
        return db
    else:
        db = sqlite3.connect(db_name)
        return db

db = setup_db("wordle.db")

def is_wordle_message(message: str) -> bool:
    found = re.search("^Wordle\s\d+\s[1-5X]\/\d", message)
    if (found):
        return True
    else:
        return False

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    message = request.get_json()
    print(message)
    if(is_wordle_message(message['text']) == False):
        return "ok", 200
    # Message is a Wordle message

