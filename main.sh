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
pip install random
pip install httpx
pip install aiohttp
pip install requests
pip install pillow
pip install beautifulsoup4
pip install pet-pet-gif
pip install google-api-python-client==1.8.0
pip install pycord
pip install discord.py selenium chromedriver-autoinstaller
izuku
