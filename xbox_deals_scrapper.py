#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from dotenv import load_dotenv
load_dotenv()


def get_exch_rate():
    from currency_converter import CurrencyConverter

    cr = CurrencyConverter(fallback_on_wrong_date=True)
    rate = cr.convert(1, "TRY", "IDR")

    return rate


def clean_price(str_price):
    import re

    clean_price = re.sub("[₺,]", "", str_price)
    price = float(clean_price)

    return price


def scraping():
    import time
    import json
    import requests
    import pandas as pd
    from datetime import datetime
    from bs4 import BeautifulSoup as bs

    print("\n" + datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
    print("Starting Xbox Deals Scrapper...")

    # get and parse data from website
    page = 1
    next = True
    session = requests.Session()

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
            time.sleep(10)
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

            original_price_idr = clean_price(original_price) * get_exch_rate()
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

                sale_price_idr = clean_price(sale_price) * get_exch_rate()
                print(sale_price_idr)
                game_sale.append(sale_price_idr)

            except AttributeError:
                game_sale.append(None)
                game_sale.append(None)
                game_sale.append(None)

            # game service bonus type
            try:
                bonus_service = game_item.find("img", class_="game-collection-item-icon-bonus", alt=True)['alt']
                print("EA" if bonus_service=="ea" else "GAMEPASS" if bonus_service=="pass" else bonus_service)
                game_sale.append("EA" if bonus_service=="ea" else "GAMEPASS" if bonus_service=="pass" else bonus_service)
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
                    bonus_price_idr = clean_price(bonus_price) * get_exch_rate()
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
    data_sales.columns = json.loads(os.getenv("XBOX_SHEET_COLUMNS"))

    return data_sales


def write_to_sheet(data):
    import gspread
    from gspread_dataframe import set_with_dataframe

    # sorting data
    data.sort_values(by=['Bonus','Valid Until','Discount'], na_position='first', inplace=True, ignore_index=True)

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
