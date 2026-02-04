# main.py
from data_sources.markets import fetch_markets,fetch_us_stocks
import schedule
import time

def daily_job():
    print("Markets:")
    print(fetch_markets())
    print("US Stocks:")
    print(fetch_us_stocks())


daily_job()