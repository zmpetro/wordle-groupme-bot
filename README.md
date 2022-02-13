# wordle-groupme-bot
groupme bot that tracks wordle statistics

wordle-groupme-bot is a GroupMe bot written in Python / Flask / SQLite that tracks Wordle scores over time. Participants in a GroupMe group simply copy and paste their score each day into the group, and the bot will track and display statistics about the players. It also has Microsoft's TrueSkill algorithm built in for the leaderboard function. To use the bot, create a GroupMe bot (https://dev.groupme.com/tutorials/bots) with the server:port you are running the bot on as the callback URL, set the Bot ID (the app looks for BOT_ID as an environment variable), and flask run app.py (systemd service file included). Screenshots:

`/wordle`:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/help.jpg" width="350"/>

`/wordle leaderboard`:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/leaderboard.jpg" width="350"/>

`/wordle daily`:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/daily.jpg" width="350"/>

`/wordle weekly`:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/weekly.jpg" width="350"/>

`/wordle my`:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/my.jpg" width="350"/>

At the start of a new day / Wordle:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/yesterday.jpg" width="350"/>

Screenshot not shown, but the bot also displays the same as directly above **for the start of a new week** (displays last week's winner).
