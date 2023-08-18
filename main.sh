#!/usr/bin/env bash

git_sync () {
	git branch sub
	git checkout sub
	git add --all
	git config --global user.email "hakurei@asia.com"
	git config --global user.name "hakureii"
	git commit -am 'remote sync'
	git push https://hakureii:${GIT}@github.com/${REPO}.git sub
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
pip install -r requirements.txt
izuku
