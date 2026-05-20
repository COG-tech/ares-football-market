# ARES Soccer Market

ARES Soccer Market is a static soccer market board for ARES performance scores, market asset scores, player search, clubs, leagues, transfers, and watchlist records.

The current site is a placeholder-only build. It uses generic player and club names, initials/placeholders, and no scraped Transfermarkt, club logo, player photo, or protected commercial data.

## Preview Locally

From this folder:

```powershell
python -m http.server 8001 -d site
```

Then open:

```text
http://127.0.0.1:8001/
```

## Static Publishing Rule

Publish only:

```text
site/
```

Do not publish:

```text
data_raw/private/
data_raw/restricted/
D:\html
raw Metronic source package files
```

## Data Pipeline

Run:

```powershell
python src\run_pipeline.py
```

The pipeline keeps existing placeholder JSON if final CSV files are empty. Real soccer data ingestion has not been connected yet.
