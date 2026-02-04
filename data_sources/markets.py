# markets.py
import yfinance as yf
import pandas as pd
from datetime import datetime

# ======================================================
# SYMBOL GROUPS (FULL SET)
# ======================================================

SYMBOL_GROUPS = {
    "US_INDICES": {
        "SP500": "^GSPC",
        "DOW": "^DJI",
        "NASDAQ100": "^NDX",
        "RUSSELL2000": "^RUT",
        "VIX": "^VIX",
    },
    "EUROPE": {
        "FTSE100": "^FTSE",
        "DAX": "^GDAXI",
        "CAC40": "^FCHI",
        "EUROSTOXX50": "^STOXX50E",
    },
    "ASIA": {
        "NIKKEI225": "^N225",
        "HANGSENG": "^HSI",
        "SSE_COMP": "000001.SS",
        "ASX200": "^AXJO",
    },
    "CRYPTO": {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "BNB": "BNB-USD",
        "SOL": "SOL-USD",
        "XRP": "XRP-USD",
        "USDT": "USDT-USD",
    },
    "COMMODITIES": {
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "CRUDE_OIL": "CL=F",
        "BRENT": "BZ=F",
        "NAT_GAS": "NG=F",
        "COPPER": "HG=F",
    },
    "FX": {
        "EURUSD": "EURUSD=X",
        "USDJPY": "JPY=X",
        "GBPUSD": "GBPUSD=X",
        "USDCAD": "CAD=X",
        "USDAUD": "AUD=X",
        "USDMXN": "MXN=X",
    },
    "BONDS": {
        "US_13W": "^IRX",
        "US_5Y": "^FVX",
        "US_10Y": "^TNX",
        "US_30Y": "^TYX",
    }
}

# ======================================================
# CORE HELPERS
# ======================================================

def _get_last_two_closes(symbol: str):
    """
    Son iki kapanış fiyatını döner.
    Change_% hesaplamak için zorunlu.
    """
    try:
        hist = yf.Ticker(symbol).history(period="2d")
        if hist.empty or len(hist) < 2:
            return None, None
        return float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
    except Exception as e:
        print(f"[WARN] {symbol} alınamadı: {e}")
        return None, None


# ======================================================
# PUBLIC API
# ======================================================

def fetch_all_markets():
    """
    LONG FORMAT output:
    Group | Asset | Symbol | Close | Change_% | Date
    """
    rows = []
    today = datetime.utcnow().strftime("%Y-%m-%d")

    for group, symbols in SYMBOL_GROUPS.items():
        for asset, symbol in symbols.items():
            close, prev = _get_last_two_closes(symbol)

            if close is None or prev is None:
                change_pct = None
            else:
                change_pct = round(((close - prev) / prev) * 100, 2)

            rows.append({
                "Group": group,
                "Asset": asset,
                "Symbol": symbol,
                "Close": round(close, 4) if close is not None else None,
                "Change_%": change_pct,
                "Date": today
            })

    return pd.DataFrame(rows)
