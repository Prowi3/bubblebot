#!/usr/bin/env bash

git_sync () {
	git branch sub
	git checkout sub
	git add --all
	git config --global user.email ${EMAIL}
	git config --global user.name "Prowi3"
	git commit -am 'remote sync'
	git push https://prowi3:${GIT}@github.com/${REPO}.git sub
}

touch BOTCONDITION
izuku () {
	while [ -f BOTCONDITION ]
	  do
	  mkdir -p logs
	  git pull
	  python3 src/main.py >> logs/$RUNNUM.log
	  git_sync
	  done
}
pip install discord.py
pip install random
pip install os
pip install io
pip install httpx
pip install requests
pip install math
pip install asyncio
pip install pillow
pip install discord-py-slash-command
izuku
