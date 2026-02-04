# rates.py
import requests

COUNTRIES = {
    "USA": "https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS",
    "EU": "https://sdw.ecb.europa.eu/service/data/FM/M.U2.EUR.4F.KR.MRR_FR.LEV"
}

def fetch_rates():
    rates = {}
    for country, url in COUNTRIES.items():
        rates[country] = "Kaynak özel parse gerekir"
    return rates
