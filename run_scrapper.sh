#!/bin/bash -f -x

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

python /app/gamepass_scrapper.py
sleep 60
python /app/xbox_deals_scrapper.py