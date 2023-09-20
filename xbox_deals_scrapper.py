#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import re
import gspread
import requests
import traceback
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from gspread_dataframe import set_with_dataframe
load_dotenv()


def get_exch_rate(cur, base_cur='USD', date=None):
    assert len(cur) == 3, f'Not valid currency: {cur}'
    assert len(base_cur) == 3, f'Not valid base currency: {base_cur}'

    date_str = 'latest' if date is None else str(date)
    url = f'http://api.exchangeratesapi.io/v1/{date_str}'  # HTTPS only for paid subscriptions
    params = {
        'access_key' : os.getenv("ACCESS_KEY_CURRENCY_CONVERTER"),
        'symbols' : f'{cur},{base_cur}',
    }

    resp = requests.get(url, params=params)
    if not resp.ok:
        resp.raise_for_status()

    data = resp.json()
    rates = data['rates']

    rate = rates[cur] / rates[base_cur]

    return rate


def clean_price(str_price):

    clean_price = re.sub("[$,]", "", str_price)
    price = float(clean_price)

    return price


def scraping():
    print("\n" + datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
    print("Starting Xbox Deals Scrapper...")

    # get and parse data from website
    page = 1
    next = True
    session = requests.Session()

    # game_types, game_titles, original_prices, sale_discounts, sale_prices, bonus_services, bonus_discounts, bonus_prices, valid_dates, ends_in, ratings, rating_counts = [], [], [] , [], [], [], [], [], [], [], [], []
    game_sales = []
    while next:
        response = session.get(os.getenv("XBOX_DEALS_URL").format(str(page)))
        doc = bs(response.text, "html.parser")

        # check pagination
        pagination = doc.find("ul", class_="pagination")
        all_pages = pagination.find_all("li", class_=True)
        pages = [page['class'] for page in all_pages]

        # extract all game attributes
        game_links = doc.find_all("a", class_="game-collection-item-link")

        for game_link in game_links:
            game_sale = []
            print("\n==================")

            # game type
            game_container = game_link.find("div", class_="game-collection-item-container")
            game_type = game_container.find("div", class_="game-collection-item-type").text
            print(game_type)
            game_sale.append(game_type)
            
            # game details
            game_item = game_link.find("div", class_="game-collection-item-details")

            # game title
            game_title = game_item.find("span", class_="game-collection-item-details-title").text
            print(game_title)
            game_sale.append(game_title)

            # game original price
            original_price = game_item.find("span", class_="game-collection-item-price").text
            print(original_price)
            game_sale.append(original_price)

            original_price_idr = clean_price(original_price) * get_exch_rate("IDR", "ARS")
            print(original_price_idr)
            game_sale.append(original_price_idr)

            # game discount and discount price
            try:
                sale_discount = game_item.find("span", class_="game-collection-item-discount").text
                print(sale_discount)
                game_sale.append(sale_discount)

                sale_price = game_item.find("span", class_="game-collection-item-price-discount").text
                print(sale_price)
                game_sale.append(sale_price)

                sale_price_idr = clean_price(sale_price) * get_exch_rate("IDR", "ARS")
                print(sale_price_idr)
                game_sale.append(sale_price_idr)

            except AttributeError:
                game_sale.append(None)
                game_sale.append(None)
                game_sale.append(None)

            # game service bonus type
            try:
                bonus_service = game_item.find("img", class_="game-collection-item-icon-bonus", alt=True)['alt']
                print("EA" if bonus_service=="ea" else "GAMEPASS")
                game_sale.append("EA" if bonus_service=="ea" else "GAMEPASS")
            except TypeError:
                game_sale.append(None)

            # game discount bonus and discount price bonus
            try:
                bonus_discount = game_item.find("span", class_="game-collection-item-discount-bonus").text
                print(bonus_discount)
                game_sale.append(bonus_discount)

                bonus_price = game_item.find("span", class_="game-collection-item-price-bonus").text
                print(bonus_price)
                game_sale.append(bonus_price)

                if bonus_price != "FREE":
                    bonus_price_idr = clean_price(bonus_price) * get_exch_rate("IDR", "ARS")
                    print(bonus_price_idr)
                    game_sale.append(bonus_price_idr)
                else:
                    game_sale.append(None)

            except AttributeError:
                game_sale.append(None)
                game_sale.append(None)
                game_sale.append(None)

            # game sale period
            try:
                price_valid_until = game_item.find("span", itemprop="priceValidUntil").text
                print(price_valid_until)
                game_sale.append(price_valid_until)

                price_end_date = game_item.find("span", class_="game-collection-item-end-date").text
                print(price_end_date)
                game_sale.append(price_end_date)
            except AttributeError:
                game_sale.append(None)
                game_sale.append(None)

            # game rating
            try:
                rating = game_item.find("span", itemprop="ratingValue").text
                print(rating)
                game_sale.append(rating)

                rating_count = game_item.find("span", itemprop="ratingCount").text
                print(rating_count)
                game_sale.append(rating_count)
            except AttributeError:
                game_sale.append(None)
                game_sale.append(None)
            
            game_sales.append(game_sale)

        if pages[-1] == ['next', 'disabled']:
            next = False
        else:
            page += 1


    data_sales = pd.DataFrame(game_sales)
    data_sales.columns = os.getenv("XBOX_SHEET_COLUMNS").split(",")

    return data_sales


def write_to_sheet(data):
    # load worksheet
    gc = gspread.service_account(filename=os.getenv("CREDENTIALS_FILE"))
    sh = gc.open_by_key(os.getenv("SPREADSHEET_KEY"))
    worksheet = sh.worksheet(os.getenv("XBOX_DEALS_SHEET"))
    worksheet.resize(1)

    # save data to worksheet
    set_with_dataframe(worksheet, data)


if __name__=="__main__":
    data_sales = scraping()
    write_to_sheet(data_sales)
