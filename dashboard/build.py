"""Build a static HTML page of charts from the CSV written by lambda_function.py.

Usage: python dashboard/build.py <csv_path> <output_dir>
"""

import html
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px

MARKET_CAP_NOTE = (
    "Minotari shows 0 because CoinMarketCap doesn't publish its circulating supply."
)


def load(csv_path):
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="ISO8601")
    return df.sort_values("timestamp")


def growth_chart(df):
    parts = []
    for symbol, g in df.groupby("symbol"):
        g = g.dropna(subset=["price"])
        if g.empty or g["price"].iloc[0] == 0:
            continue
        parts.append(
            pd.DataFrame(
                {
                    "timestamp": g["timestamp"],
                    "label": f"{g['name'].iloc[0]} ({symbol})",
                    "index": g["price"] / g["price"].iloc[0] * 100,
                }
            )
        )
    idx = (
        pd.concat(parts)
        if parts
        else pd.DataFrame(columns=["timestamp", "label", "index"])
    )
    fig = px.line(
        idx,
        x="timestamp",
        y="index",
        color="label",
        title="Growth comparison (price indexed to 100 at first data point)",
    )
    fig.update_layout(yaxis_title="Index", xaxis_title=None, legend_title=None)
    return fig


def per_coin_chart(df, column, title, yaxis_title):
    """One small subplot per coin, each with its own y-axis."""
    fig = px.line(
        df,
        x="timestamp",
        y=column,
        facet_col="symbol",
        facet_col_wrap=2,
        facet_col_spacing=0.08,
        facet_row_spacing=0.15,
        hover_name="name",
        title=title,
    )
    fig.update_yaxes(matches=None, showticklabels=True, title_text=None)
    fig.update_xaxes(matches=None, title_text=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    n_rows = -(-df["symbol"].nunique() // 2)
    fig.update_layout(height=max(300, 280 * n_rows), yaxis_title=yaxis_title)
    return fig


def build(csv_path, output_dir):
    df = load(csv_path)
    last_updated = df["timestamp"].max().strftime("%Y-%m-%d %H:%M UTC")

    figs = [
        (growth_chart(df), None),
        (per_coin_chart(df, "price", "Price (USD)", "USD"), None),
        (per_coin_chart(df, "volume_24h", "24h volume (USD)", "USD"), None),
        (per_coin_chart(df, "market_cap", "Market cap (USD)", "USD"), MARKET_CAP_NOTE),
    ]

    sections = []
    for i, (fig, note) in enumerate(figs):
        body = fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False)
        note_html = f'<p class="note">{html.escape(note)}</p>' if note else ""
        sections.append(f"<section>{body}{note_html}</section>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Coin Charts</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: 0 auto; padding: 1rem; }}
.note {{ color: #555; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>Privacy Coin Charts</h1>
<p>Last updated: {html.escape(last_updated)}</p>
{"".join(sections)}
</body>
</html>
"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    return out / "index.html"


def main(argv):
    if len(argv) != 3:
        print(
            "usage: python dashboard/build.py <csv_path> <output_dir>", file=sys.stderr
        )
        return 2
    print(f"Wrote {build(argv[1], argv[2])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
