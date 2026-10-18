"""
AWS Lambda: fetch Monero, Zcash and Dash quotes from CoinMarketCap
and append them to a CSV file stored in S3.

Environment variables:
  CMC_API_KEY  - CoinMarketCap Pro API key from parameter store (required)
  BUCKET_NAME  - S3 bucket that holds the CSV (required)
  CSV_KEY      - object key for the CSV (default: crypto_data.csv)
  SLUGS        - comma-separated CoinMarketCap slugs (default: monero,zcash,dash)
"""

import csv
import io
import json
import logging
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CMC_URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
FIELDNAMES = [
    "timestamp", "name", "symbol", "price", "market_cap", "volume_24h",
    "percent_change_1h", "percent_change_24h", "percent_change_7d",
]

s3 = boto3.client("s3")
apikey = boto3.client("ssm").get_parameter(Name="/privacy-coins/cmc-api-key", WithDecryption=True)["Parameter"]["Value"]

def fetch_quotes(api_key, slugs):
    query = urllib.parse.urlencode({"slug": slugs})
    req = urllib.request.Request(
        f"{CMC_URL}?{query}",
        headers={"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def read_existing_csv(bucket, key):
    """Return the current CSV contents from S3, or None if it doesn't exist yet."""
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read().decode("utf-8")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise


def lambda_handler(event, context):
    api_key = apikey
    bucket = os.environ["BUCKET_NAME"]
    key = os.environ.get("CSV_KEY", "crypto_data.csv")
    slugs = os.environ.get("SLUGS", "monero,zcash,dash,tari")

    timestamp = datetime.now(timezone.utc).isoformat()
    response_json = fetch_quotes(api_key, slugs)

    rows = []
    for crypto_id, crypto_data in response_json["data"].items():
        usd = crypto_data["quote"]["USD"]
        row = {
            "timestamp": timestamp,
            "name": crypto_data["name"],
            "symbol": crypto_data["symbol"],
            "price": usd["price"],
            "market_cap": usd["market_cap"],
            "volume_24h": usd["volume_24h"],
            "percent_change_1h": usd["percent_change_1h"],
            "percent_change_24h": usd["percent_change_24h"],
            "percent_change_7d": usd["percent_change_7d"],
        }
        rows.append(row)
        logger.info(
            "%s (%s): $%.6f, Market Cap: $%.6f",
            row["name"], row["symbol"], row["price"], row["market_cap"],
        )

    # S3 objects can't be appended to, so read, append, and write back.
    existing = read_existing_csv(bucket, key)
    buffer = io.StringIO()
    if existing:
        buffer.write(existing)
        if not existing.endswith("\n"):
            buffer.write("\n")

    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES, lineterminator="\n")
    if not existing:
        writer.writeheader()
    writer.writerows(rows)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"timestamp": timestamp, "rows_written": len(rows), "s3_key": f"s3://{bucket}/{key}"}),
    }