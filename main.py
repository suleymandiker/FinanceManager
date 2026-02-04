# main.py
from data_sources.markets import fetch_markets,fetch_us_stocks
from datetime import datetime
import pandas as pd
import os

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

today = datetime.utcnow().strftime("%Y-%m-%d")

markets = fetch_markets()
stocks = fetch_us_stocks()

markets["Type"] = "Market"
stocks["Type"] = "Stock"

df = pd.concat([markets, stocks])
df["Date"] = today

file_path = f"{OUTPUT_DIR}/finance_{today}.csv"
df.to_csv(file_path)

print(f"Saved: {file_path}")
print(df)

