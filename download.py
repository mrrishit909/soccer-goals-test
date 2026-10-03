"""Step 1: international football results, men's and women's, from the martj42 'international results' CC0 datasets on GitHub.

    ./venv/bin/python download.py   -> data/men.csv, data/women.csv (not committed), results/pull.json
"""
import csv
import io
import json
import ssl
import urllib.request
from datetime import date
from pathlib import Path

import certifi

HERE = Path(__file__).parent
CTX = ssl.create_default_context(cafile=certifi.where())
SOURCES = {"men": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
           "women": "https://raw.githubusercontent.com/martj42/womens-international-results/master/results.csv"}


def main():
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "results").mkdir(exist_ok=True)
    meta = {"pulled": date.today().isoformat()}
    for name, url in SOURCES.items():
        raw = urllib.request.urlopen(url, context=CTX, timeout=120).read()
        (HERE / "data" / f"{name}.csv").write_bytes(raw)
        rows = list(csv.DictReader(io.StringIO(raw.decode())))
        meta[name] = {"url": url, "matches": len(rows), "first": min(r["date"] for r in rows), "last": max(r["date"] for r in rows)}
    (HERE / "results" / "pull.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
