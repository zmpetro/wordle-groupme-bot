# wordle-groupme-bot
groupme bot that tracks wordle statistics

wordle-groupme-bot is a GroupMe bot written in Python / Flask / SQLite that tracks Wordle scores over time. Participants in a GroupMe group simply copy and paste their score each day into the group, and the bot will track and display statistics about the players. It also has Microsoft's TrueSkill algorithm built in for the leaderboard function. To use the bot, create a GroupMe bot (https://dev.groupme.com/tutorials/bots) with the server:port you are running the bot on as the callback URL, set the Bot ID (the app looks for BOT_ID as an environment variable), and flask run app.py (systemd service file included). Screenshots:

`/wordle`:

<img src="https://raw.githubusercontent.com/zmpetro/wordle-groupme-bot/main/screenshots/help.jpg" alt="/wordle" width="200"/>

`/wordle leaderboard`:

![/wordle leaderboard](/screenshots/leaderboard.jpg)

`/wordle daily`:

![/wordle daily](/screenshots/daily.jpg)

`/wordle weekly`:

![/wordle weekly](/screenshots/weekly.jpg)

`/wordle my`:

![/wordle my](/screenshots/my.jpg)

At the start of a new day / Wordle:

![New day / Wordle](/screenshots/yesterday.jpg)

Screenshot not shown, but the bot also does the same as directly above for the start of a new week (displays last week's winner).
