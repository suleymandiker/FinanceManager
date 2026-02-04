# markets.py
import yfinance as yf
import pandas as pd

SYMBOLS = {
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DAX": "^GDAXI",
    "NIKKEI": "^N225",
    "GOLD": "GC=F",
    "SILVER": "SI=F"
}

# ABD Hisseleri
US_STOCKS = {
    "TESLA": "TSLA",
    "NVIDIA": "NVDA",
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT"
}

def _get_last_close(symbol: str):
    """
    Tek bir sembol için son kapanış fiyatını getirir.
    Hata alırsa None döner (script patlamaz).
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"[WARN] {symbol} alınamadı: {e}")
        return None

def fetch_markets():
    data = {}
    for name, symbol in SYMBOLS.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        data[name] = hist["Close"].iloc[-1]
    return pd.DataFrame.from_dict(data, orient="index", columns=["Close"])

def fetch_us_stocks():
    """
    ABD hisseleri (Tesla, Nvidia vs.)
    """
    data = {}
    for name, symbol in US_STOCKS.items():
        data[name] = _get_last_close(symbol)

    return pd.DataFrame.from_dict(
        data, orient="index", columns=["Close"]
    )
