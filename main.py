from dotenv import load_dotenv
from data_sources.markets import fetch_markets, fetch_us_stocks
from datetime import datetime, timedelta
import pandas as pd
import os
import glob
import requests

load_dotenv()

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

today_str = today.strftime("%Y-%m-%d")
yesterday_str = yesterday.strftime("%Y-%m-%d")

# 1️⃣ Bugünkü veriyi al
markets = fetch_markets()
stocks = fetch_us_stocks()

markets["Type"] = "Market"
stocks["Type"] = "Stock"

df_today = pd.concat([markets, stocks])
df_today["Date"] = today_str

today_file = f"{OUTPUT_DIR}/finance_{today_str}.csv"
df_today.to_csv(today_file)

# 2️⃣ Dünkü dosyayı bul
files = glob.glob(f"{OUTPUT_DIR}/finance_*.csv")
files.sort()

df_diff = None
if len(files) >= 2:
    df_yesterday = pd.read_csv(files[-2], index_col=0)
    df_today = pd.read_csv(files[-1], index_col=0)

    df_diff = df_today.copy()
    df_diff["PrevClose"] = df_yesterday["Close"]
    df_diff["Change_%"] = (
        (df_today["Close"] - df_yesterday["Close"]) / df_yesterday["Close"] * 100
    ).round(2)

# 3️⃣ Telegram mesajı
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:

    if df_diff is None:
        msg = f"📊 Finance Report ({today_str})\n\n"
        msg += "İlk veri toplandı. Yarın değişim raporu gönderilecek.\n\n"

        for idx, row in df_today.iterrows():
            msg += f"• {idx}: {row['Close']}\n"

    else:
        msg = f"📊 Finance Report ({today_str})\n\n"
        for idx, row in df_diff.iterrows():
            change = row["Change_%"]
            emoji = "🟢" if change >= 0 else "🔴"
            msg += f"{emoji} {idx}: {change}%\n"

    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    )

    print("Telegram response:", response.status_code, response.text)
    print("TOKEN:", bool(TELEGRAM_TOKEN))
    print("CHAT_ID:", bool(TELEGRAM_CHAT_ID))
    print("CSV SAYISI:", len(files))


