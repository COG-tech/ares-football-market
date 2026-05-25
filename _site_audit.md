# ARES Football Market Site Audit

Static site build is now a seeded Public Beta Demo football market terminal preview.

Public copy avoids old sample wording, the homepage shows active seeded boards, player and ranking tables use ARES-owned generated player images, club boards use generated club badges, and league boards use generated league badges. Asia, MLS, North America, AFC, and CONCACAF are visible as first-class market sections.

Visual audit result: the previous build had seeded rows but still looked too generic because player `photo_url` fields were empty and club/league boards had no badge layer. This pass adds local generated assets under `assets/media/public-beta/`:

- 28 ARES-owned generated player images
- 12 ARES-owned generated club badges
- 38 ARES-owned generated league badges

All seeded rows remain clearly marked `data_mode: "public_beta_demo"`. No restricted feed, scraped player photo, protected club mark, or external image search result is used.

Remaining work: connect approved live football player, transfer, contract, and provider image feeds before presenting the product as a real market database.

Compactness note: the default player profile overview and the `view=stats` tab were tightened to fit a 1366x768 viewport, with the overview trimmed to the core summary cards and the lower detail cards moved behind the dedicated tabs.
