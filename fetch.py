from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import requests
import json
import csv

load_dotenv()

CMC_PRO_API_KEY = os.getenv("CMC_API_KEY")
url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"

response =requests.get(
    url,
    headers={
      "X-CMC_PRO_API_KEY": CMC_PRO_API_KEY
    },
    params={
      "slug": "monero,zcash,dash,tari"
    }
)

timestamp = datetime.now(timezone.utc).isoformat()
response.raise_for_status()
response_json = response.json()

for crypto in response_json["data"]:
    crypto_data = response_json["data"][crypto]
    name = crypto_data["name"]
    symbol = crypto_data["symbol"]
    price = crypto_data["quote"]["USD"]["price"]
    mcap = crypto_data["quote"]["USD"]["market_cap"]
    print(f"{name} ({symbol}): ${price:.6f}, Market Cap: ${mcap:.6f}")

file_exists = os.path.exists("crypto_data.csv")

with open("crypto_data.csv", "a", newline="") as csvfile:
    fieldnames = ["timestamp", "name", "symbol", "price", "market_cap", "volume_24h", "percent_change_1h", "percent_change_24h", "percent_change_7d"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    if not file_exists:
        writer.writeheader()
    
    for crypto in response_json["data"]:
        crypto_data = response_json["data"][crypto]
        writer.writerow({
            "timestamp": timestamp,
            "name": crypto_data["name"],
            "symbol": crypto_data["symbol"],
            "price": crypto_data["quote"]["USD"]["price"],
            "market_cap": crypto_data["quote"]["USD"]["market_cap"],
            "volume_24h": crypto_data["quote"]["USD"]["volume_24h"],
            "percent_change_1h": crypto_data["quote"]["USD"]["percent_change_1h"],
            "percent_change_24h": crypto_data["quote"]["USD"]["percent_change_24h"],
            "percent_change_7d": crypto_data["quote"]["USD"]["percent_change_7d"]
        })