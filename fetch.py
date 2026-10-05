import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

CMC_PRO_API_KEY = os.getenv("CMC_API_KEY")
url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"

response =requests.get(
    url,
    headers={
      "X-CMC_PRO_API_KEY": CMC_PRO_API_KEY
    },
    params={
      "slug": "monero,zcash,dash"
    }
)

response.raise_for_status()
response_json = response.json()

for crypto in response_json["data"]:
    crypto_data = response_json["data"][crypto]
    name = crypto_data["name"]
    symbol = crypto_data["symbol"]
    price = crypto_data["quote"]["USD"]["price"]
    mcap = crypto_data["quote"]["USD"]["market_cap"]
    print(f"{name} ({symbol}): ${price:.2f}, Market Cap: ${mcap:.2f}")