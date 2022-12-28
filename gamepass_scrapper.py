#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import gspread
import requests
import traceback
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from gspread_dataframe import set_with_dataframe
load_dotenv()


print("\n" + datetime.now())
print("Starting Gamepass Scrapper...")

# load worksheet
gc = gspread.service_account(filename=os.getenv("CREDENTIALS_FILE"))
sh = gc.open_by_key(os.getenv("SPREADSHEET_KEY"))
worksheet = sh.worksheet(os.getenv("GAMEPASS_SHEET"))
worksheet.resize(1)

# get and parse data from website
session = requests.Session()
resp = session.get(os.getenv("GAMEPASS_URL"))
doc = bs(resp.text, "html.parser")

# loop through each row and section
data = pd.DataFrame()
for i in range(1, 10):
    print(f"\nRow {i}")
    row = doc.find("div", id=f"row{i}")
    sections = row.find_all("div", class_="et_pb_with_border")

    for j in range(0, len(sections), 2):
        section = sections[j]
        title = section.find("h3").text
        print(title)
        games = section.find_all("li")
        print(len(games))

        # create list of games
        list_games = []
        for game in games:
            list_games.append(game.text)

        # concat dataframe
        df = pd.DataFrame(pd.Series(list_games))
        df.rename(columns={0: title}, inplace=True)
        data = pd.concat([data, df], axis=1)

# save data to worksheet
set_with_dataframe(worksheet, data)
