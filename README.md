# Market and trade monitor

Office TV dashboard. Version 0.1.

A single web page showing exchange rates, MLA cattle and sheep indicators over 20 years, economic indicators for Australia and five Asian markets, industry news, and alerts when monitored web pages change. GitHub Actions refreshes the data every 30 minutes and publishes the page through GitHub Pages.

## How it works

- `fetch/` holds one Python script per data block. `fetch/run.py` runs whichever blocks are due and writes JSON into `data/`.
- `.github/workflows/update.yml` runs on a schedule (twice an hour), commits the new data and republishes the site.
- `index.html` reads the JSON files every five minutes. It is laid out at 1920 × 1080 and scales to any screen.

## Refresh intervals

| Block | Source | Interval |
|---|---|---|
| Exchange rates | fawazahmed0 currency API (daily reference rates, includes VND) | 1 hour |
| News | Beef Central RSS feed, eFeedLink front page | 30 minutes |
| Website changes | Pages listed in `fetch/config.py` | 1 hour |
| Economic indicators | IMF DataMapper (annual), BIS policy rates (monthly) | 1 day |
| MLA indicators | MLA Statistics API | 1 day |

GitHub's scheduler can run late at busy times, so expect gaps of up to an hour now and then.

## Changing what it shows

Everything configurable is in `fetch/config.py`.

- **News sources.** Add an entry to `NEWS_SOURCES`. Use `"type": "rss"` where the site has a feed, otherwise `"type": "scrape"` with the text that appears in its article links.
- **Monitored pages.** Add an entry to `MONITORED_PAGES`. The first check records a baseline and later checks raise an alert when the main text changes.
- **MLA indicators.** Each indicator is found by name. After the first run, `data/mla_indicators.json` lists every indicator the API offers. If one is matched wrongly or not found, put its number in the `id` field.
- **Vietnam policy rate.** BIS does not publish it, so it is entered by hand in `MANUAL_POLICY_RATES`.

Editing a file on github.com and committing it triggers a full refresh straight away.

## Running a refresh by hand

Actions tab › Update data and publish › Run workflow. Tick "Refresh every block now" to ignore the intervals.

## On the TV

Open the GitHub Pages address in Chrome in full-screen or kiosk mode. On a Raspberry Pi or mini PC running Linux:

```
chromium --kiosk --noerrdialogs --disable-session-crashed-bubble https://capnpat.github.io/office-dashboard/
```

The page reloads itself every six hours and hides the mouse pointer when it is not moving.

## Not yet connected

Bunker fuel prices. Most bunker price data is behind a subscription, so this panel is waiting on a source.
