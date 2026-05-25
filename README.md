# ARES Football Market

Professional Demo Mode market terminal build for the global football asset board.

The site now uses demo-mode language instead of public old sample language, keeps the scoring framework visible, and exposes the product structure for player search, ARES rankings, market rankings, clubs, leagues, transfers, and watchlists. Live player, transfer, contract, and provider image feeds are not connected yet.

## Data safety

- Player images must come from provider-supplied API URLs, TheSportsDB artwork, properly licensed Wikimedia Commons files with attribution, or the ARES branded fallback avatar.
- Do not scrape Transfermarkt, Google Images, club websites, media-agency previews, Getty/AP/Reuters/Imago, or social media.
- Expanded league rows include MLS, USL, Liga MX, Japan, Korea, Saudi Arabia, China, Australia, India, Southeast Asia, and AFC competition coverage targets.

## Current status

- Open match rows: connected where local public CSV exports exist.
- Open club rows: connected from the local match dataset.
- Live player data: not connected.
- Asia, MLS, North America, AFC, and CONCACAF sections: visible as first-class market boards.
- Live transfer data: not connected.
- ARES model output: formula defined, not live.
- Market model output: formula defined, not live.

## Open match cache

The website cache is built from `D:\aRES\football\open_match_csv`.

- Rebuild once per day: `python "D:\aRES\ares-football-market\scripts\integrate_open_match_data.py"`
- Force a rebuild: `python "D:\aRES\ares-football-market\scripts\integrate_open_match_data.py" --force`
- Rebuild, commit, and push to GitHub Pages: `python "D:\aRES\ares-football-market\scripts\integrate_open_match_data.py" --publish`
- Daily runner for upload: `powershell -ExecutionPolicy Bypass -File "D:\aRES\ares-football-market\scripts\run_daily_open_match_cache.ps1"`
