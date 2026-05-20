# ARES Soccer Market Site Audit

## Status

Static site build is complete for a placeholder-only soccer preview.

## Pages Created

- `site/index.html`
- `site/rankings/ares.html`
- `site/rankings/market.html`
- `site/players/index.html`
- `site/players/player-template.html`
- `site/clubs/index.html`
- `site/clubs/club-template.html`
- `site/leagues/index.html`
- `site/leagues/league-template.html`
- `site/transfers/index.html`
- `site/watchlist/index.html`
- `site/methodology.html`
- `site/about.html`
- `site/.nojekyll`

## Data Files

- `site/data/ares_rankings.json`
- `site/data/market_rankings.json`
- `site/data/player_search.json`
- `site/data/clubs.json`
- `site/data/leagues.json`
- `site/data/transfers.json`
- `site/data/watchlist.json`
- `site/data/top_cards.json`
- `site/data/player_profile_sample.json`
- `site/data/club_profile_sample.json`
- `site/data/league_profile_sample.json`
- `site/data/player_value_history.json`

## Verification

- JSON syntax: passed.
- Internal static links: passed.
- GitHub Pages static readiness: passed.
- Backend requirement: none.
- React/Vue/Angular/Laravel/PHP requirement: none.
- Public data status: placeholder-only.

## Scores

- Visual consistency: 8/10
- User navigation: 8/10
- Static hosting readiness: 10/10
- Data safety: 10/10
- Real data readiness: 5/10

## Remaining Issues

- Real soccer ingestion is not connected.
- Player, club, and league template pages currently render one sample profile each.
- Generated individual player pages are not created yet.
- Advanced Metronic chart widgets are available but not wired to real soccer time-series data yet.

## Public Upload Rule

Only upload `site/` for GitHub Pages unless the repository is kept private and raw data has been reviewed. Do not upload `data_raw/private`, `data_raw/restricted`, or the raw Metronic source package.
