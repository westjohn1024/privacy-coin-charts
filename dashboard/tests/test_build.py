import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build

SAMPLE = Path(__file__).parent / "sample.csv"


def test_build_writes_page_with_every_coin(tmp_path):
    path = build.build(SAMPLE, tmp_path / "out")
    assert path == tmp_path / "out" / "index.html"
    page = path.read_text(encoding="utf-8")
    for name in pd.read_csv(SAMPLE)["name"].unique():
        assert name in page
    assert "Last updated: 2026-01-01 06:00 UTC" in page
    assert "cdn.plot.ly" in page
    assert "Minotari shows 0 because CoinMarketCap" in page
