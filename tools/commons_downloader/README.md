# ARES Wikimedia Commons Image Downloader

This tool searches Wikimedia Commons for entity images, downloads only candidates that pass a conservative first-pass license filter, and writes a rights/attribution registry for ARES.

It is for targeted lists of players, teams, leagues, coaches, stadiums, or other entities. It is not a bulk Wikimedia scraper.

## What It Creates

```text
ares_commons_output/
  images/
  metadata/
    image_rights_registry.csv
    image_rights_registry.json
    rejected_candidates.csv
    download_log.csv
```

## Required Input CSV

```csv
entity_id,entity_name,sport,league,team
soc_001,Lionel Messi,soccer,MLS,Inter Miami
grid_001,Patrick Mahomes,gridiron,NFL,Kansas City Chiefs
```

Optional columns:

```csv
commons_title,wikidata_qid
```

When `commons_title` is present, the downloader checks that exact Commons file before falling back to text search. For large player batches, prefer exact Commons titles from Wikidata and run with `--exact-only`.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python ares_commons_image_downloader.py ^
  --input ares_entities_sample.csv ^
  --output ares_commons_output ^
  --contact jesse777crown@gmail.com ^
  --max-results 5
```

## Top 10 Leagues, Top Level + Second Level

Build a Wikimedia-backed entity CSV first:

```bash
python build_wikidata_top_league_entities.py ^
  --output runs/top10_two_levels/entities.csv ^
  --contact jesse777crown@gmail.com ^
  --scope top10 ^
  --players-per-league 100
```

Then download only exact Commons files from that CSV:

```bash
python ares_commons_image_downloader.py ^
  --input runs/top10_two_levels/entities.csv ^
  --output runs/top10_two_levels/commons_output ^
  --contact jesse777crown@gmail.com ^
  --thumb-width 480 ^
  --sleep-seconds 0.3 ^
  --exact-only
```

Default league scope:

```text
Premier League / EFL Championship
La Liga / LaLiga 2
Bundesliga / 2. Bundesliga
Serie A / Serie B
Ligue 1 / Ligue 2
Eredivisie / Eerste Divisie
Liga Portugal / Liga Portugal 2
Campeonato Brasileiro Serie A / Serie B
Major League Soccer / USL Championship
Liga MX / Liga de Expansion MX
```

## Next 10 Markets, Top Level + Second Level

```bash
python build_wikidata_top_league_entities.py ^
  --output runs/next10_two_levels/entities.csv ^
  --contact jesse777crown@gmail.com ^
  --scope next10 ^
  --no-limit

python ares_commons_image_downloader.py ^
  --input runs/next10_two_levels/entities.csv ^
  --output runs/next10_two_levels/commons_output ^
  --contact jesse777crown@gmail.com ^
  --thumb-width 480 ^
  --sleep-seconds 0.3 ^
  --exact-only
```

Next scope:

```text
Argentine Primera Division / Primera Nacional
Super Lig / TFF First League
Belgian Pro League / Challenger Pro League
Scottish Premiership / Scottish Championship
Swiss Super League / Swiss Challenge League
J1 League / J2 League
K League 1 / K League 2
Saudi Pro League / Saudi First Division League
A-League Men / National Premier Leagues
Indian Super League / I-League
```

## ARES Approval Rule

Only use an image on the public or premium site when the registry row has:

```text
display_allowed = True
commercial_use_allowed = True
paid_site_display_allowed = True
attribution_text is filled
license_url is filled
```

If `image_status` is `rights_pending`, do not show the image.

## Important

This is a first-pass metadata filter, not legal approval. Before using images on paid pages, ads, emails, or sales pages, manually review the Wikimedia file page and license terms.

This tool does not scrape Google Images, Transfermarkt, ESPN, PFF, NFL, MLS, club websites, Getty, Reuters, AP, or social media.
