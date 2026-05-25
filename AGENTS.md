# ARES Football Market Agent Notes

## Visual QA

- Always inspect the deployed GitHub Pages site when judging page appearance:
  `https://cog-tech.github.io/ares-football-market/`
- Do not use localhost screenshots for visual approval unless the user explicitly asks for local-only debugging.
- Before taking a screenshot, wait for the page to finish rendering live data. For player pages, the screenshot is not valid while the page still shows placeholder text such as `Player Profile` or `Player intelligence view will render from the selected profile record.`
- For player profile screenshots, wait until `#player-name` contains the actual player name and key fields such as `#ares-score` are populated. If those fields do not populate on GitHub Pages, report the load failure instead of taking or relying on a screenshot.
- GitHub Pages is served from the configured Pages branch. If a PR branch is not deployed to Pages, do not claim the PR visuals are visible on GitHub Pages until the branch is merged or a preview deployment exists.
- Save screenshots under `D:\ARES\` with names that clearly say they are from GitHub Pages, for example `github_pages_profile_after.png`.
