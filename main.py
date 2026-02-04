from dotenv import load_dotenv
from data_sources.markets import fetch_all_markets
from datetime import datetime, timedelta
import pandas as pd
import os
import glob
import requests

# ======================================================
# ENV
# ======================================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ======================================================
# PATHS & DATES
# ======================================================

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

today_str = today.strftime("%Y-%m-%d")
yesterday_str = yesterday.strftime("%Y-%m-%d")

today_file = f"{OUTPUT_DIR}/finance_{today_str}.csv"

# ======================================================
# 1️⃣ FETCH TODAY DATA (LONG FORMAT)
# ======================================================

df_today = fetch_all_markets()
df_today["Date"] = today_str

df_today.to_csv(today_file, index=False)

# ======================================================
# 2️⃣ LOAD YESTERDAY (IF EXISTS)
# ======================================================

files = sorted(glob.glob(f"{OUTPUT_DIR}/finance_*.csv"))
df_diff = None

if len(files) >= 2:
    df_yesterday = pd.read_csv(files[-2])
    df_today = pd.read_csv(files[-1])

    df_diff = df_today.merge(
        df_yesterday[["Group", "Asset", "Close"]],
        on=["Group", "Asset"],
        how="left",
        suffixes=("", "_Prev")
    )

    df_diff["Change_%"] = (
        (df_diff["Close"] - df_diff["Close_Prev"])
        / df_diff["Close_Prev"] * 100
    ).round(2)

# ======================================================
# 3️⃣ TELEGRAM MESSAGE
# ======================================================

if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:

    msg = f"📊 Finance Report ({today_str})\n\n"

    if df_diff is None:
        msg += "İlk veri toplandı. Yarın değişim raporu gönderilecek.\n\n"
        sample = df_today.head(10)

        for _, row in sample.iterrows():
            msg += f"• {row['Asset']}: {row['Close']}\n"

    else:
        # Sadece anlamlı olanları gönderelim
        df_show = df_diff.dropna(subset=["Change_%"]).sort_values(
            "Change_%", ascending=False
        )

        top_up = df_show.head(5)
        top_down = df_show.tail(5)

        msg += "🟢 En Çok Yükselenler:\n"
        for _, row in top_up.iterrows():
            msg += f"{row['Asset']}: {row['Change_%']}%\n"

        msg += "\n🔴 En Çok Düşenler:\n"
        for _, row in top_down.iterrows():
            msg += f"{row['Asset']}: {row['Change_%']}%\n"

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        }
    )

    print("Telegram status:", resp.status_code)
    print("Telegram response:", resp.text)

else:
    print("Telegram env vars missing, skipping notification")

print("DONE")
