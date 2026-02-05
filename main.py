from dotenv import load_dotenv
from data_sources.markets import fetch_all_markets
from datetime import datetime
import pandas as pd
import os
import glob
import requests
from openai import OpenAI

# ======================================================
# ENV
# ======================================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ======================================================
# PATHS & DATE (LOCAL TIME)
# ======================================================

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

today = datetime.now().date()
today_str = today.strftime("%Y-%m-%d")

today_file = os.path.join(OUTPUT_DIR, f"finance_{today_str}.csv")

# ======================================================
# 1️⃣ FETCH TODAY DATA
# ======================================================

print("Fetching market data...")
df_today = fetch_all_markets()

if df_today.empty:
    raise RuntimeError("fetch_all_markets returned EMPTY dataframe")

df_today["Date"] = today_str
df_today.to_csv(today_file, index=False)

print("CSV written:", os.path.exists(today_file))
print("CSV path:", os.path.abspath(today_file))

# ======================================================
# 2️⃣ LOAD YESTERDAY & CALCULATE CHANGE
# ======================================================

files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "finance_*.csv")))
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
# 3️⃣ CORE MACRO SNAPSHOT
# ======================================================

KEY_ASSETS = {
    "SP500": "S&P 500",
    "VIX": "VIX",
    "BRENT": "Brent Oil",
    "DXY": "DXY",
    "US_10Y": "US 10Y",
}

df_core = None
macro_text = ""

if df_diff is not None:
    df_core = df_diff[df_diff["Asset"].isin(KEY_ASSETS.keys())]

    # Sabit sıra
    order_map = {"SP500": 1, "VIX": 2, "BRENT": 3, "DXY": 4, "US_10Y": 5}
    df_core["order"] = df_core["Asset"].map(order_map)
    df_core = df_core.sort_values("order")

    for _, r in df_core.iterrows():
        macro_text += f"{r['Asset']}: Close={r['Close']}, Change={r['Change_%']}%\n"

# ======================================================
# 4️⃣ RISK LABEL (DETERMINISTIC)
# ======================================================

def calculate_risk_label(df):
    score = 0

    for _, r in df.iterrows():
        asset = r["Asset"]
        close = r["Close"]
        change = r["Change_%"]

        if asset == "SP500":
            score += 1 if change > 0 else -1

        elif asset == "VIX":
            if close < 18:
                score += 1
            elif close > 25:
                score -= 1

        elif asset == "US_10Y":
            score += 1 if change > 0 else -1

        elif asset == "DXY":
            score += 1 if change < 0 else -1

        elif asset == "BRENT":
            score += 1 if change > 0 else -1

    if score >= 3:
        return "🟢 RISK-ON"
    elif score >= 1:
        return "🟡 RISK-ON (zayıf)"
    elif score == 0:
        return "⚪ NEUTRAL"
    elif score >= -2:
        return "🟠 RISK-OFF (yumuşak)"
    else:
        return "🔴 RISK-OFF"

risk_label = "⚪ NEUTRAL"
if df_core is not None and not df_core.empty:
    risk_label = calculate_risk_label(df_core)

# ======================================================
# 5️⃣ CHATGPT – SHORT MACRO COMMENT
# ======================================================

macro_comment = "Makro yorum üretilemedi."

if OPENAI_API_KEY and macro_text:

    prompt = f"""
Aşağıdaki finansal verileri analiz et:

{macro_text}

Kurallar:
- En fazla 3 kısa cümle
- Teknik ama sade
- Risk-on / Risk-off perspektifi
- Yatırım tavsiyesi verme
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional macro market analyst."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=120,
        temperature=0.3
    )

    macro_comment = response.choices[0].message.content.strip()

# ======================================================
# 6️⃣ TELEGRAM MESSAGE (4096 SAFE)
# ======================================================

MAX_LEN = 3800

if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:

    msg = f"🌍 Makro Özet ({today_str})\n{risk_label}\n\n"
    msg += "📊 Çekirdek Göstergeler\n"

    for _, r in df_core.iterrows():
        name = KEY_ASSETS[r["Asset"]]
        close = r["Close"]
        change = r["Change_%"]
        emoji = "🟢" if change >= 0 else "🔴"

        if r["Asset"] in ["VIX", "US_10Y"]:
            line = f"{emoji} {name}: {close}\n"
        else:
            line = f"{emoji} {name}: {close} ({change}%)\n"

        msg += line

    comment_block = f"\n🧠 Makro Yorum\n{macro_comment}"

    if len(msg) + len(comment_block) <= MAX_LEN:
        msg += comment_block
    else:
        short = macro_comment[:500].rsplit(".", 1)[0] + "."
        msg += f"\n🧠 Makro Yorum\n{short}"

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
