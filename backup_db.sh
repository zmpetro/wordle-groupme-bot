#!/bin/bash
rsync -a /home/zmpetro/wordle_bot_prod/wordle.db /home/zmpetro/wordle_bot_prod/db_backups/wordle.db.$(date +%Y%m%d)
