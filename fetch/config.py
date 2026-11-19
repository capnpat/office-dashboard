"""Dashboard configuration. Edit this file to add sources or monitored pages."""

# Currencies shown against AUD, in display order
FX_CURRENCIES = ["usd", "idr", "myr", "vnd", "thb", "cny"]

# MLA indicators. "match" is a list of phrases that must all appear in the
# indicator name returned by the MLA Statistics API. "id" overrides matching
# if set (see data/mla_indicators.json after the first run for the full list).
MLA_INDICATORS = [
    {"key": "eyci",   "short": "EYCI",              "match": ["eastern young cattle"], "id": None},
    {"key": "wyci",   "short": "WYCI",              "match": ["western young cattle"], "id": None},
    {"key": "hvystr", "short": "Heavy steer",       "match": ["heavy steer"],          "id": None},
    {"key": "fdrstr", "short": "Feeder steer",      "match": ["feeder steer"],         "id": None},
    {"key": "trdlmb", "short": "Trade lamb",        "match": ["trade lamb"],           "id": None},
    {"key": "hvylmb", "short": "Heavy lamb",        "match": ["heavy lamb"],           "id": None},
    {"key": "mutton", "short": "Mutton",            "match": ["mutton"],               "id": None},
    {"key": "lxstr",  "short": "Live export steer", "match": ["live export"],          "id": None},
]
MLA_START_YEAR = 2006

# Economic indicators (IMF DataMapper ISO3 codes, BIS ISO2 codes)
COUNTRIES = [
    {"name": "Australia", "iso3": "AUS", "iso2": "AU", "rate_name": "Cash rate"},
    {"name": "Indonesia", "iso3": "IDN", "iso2": "ID", "rate_name": "BI rate"},
    {"name": "Malaysia",  "iso3": "MYS", "iso2": "MY", "rate_name": "OPR"},
    {"name": "Vietnam",   "iso3": "VNM", "iso2": "VN", "rate_name": "Refinancing rate"},
    {"name": "Thailand",  "iso3": "THA", "iso2": "TH", "rate_name": "Policy rate"},
    {"name": "China",     "iso3": "CHN", "iso2": "CN", "rate_name": "1y LPR"},
]
# Policy rates not covered by the BIS series are entered here by hand
MANUAL_POLICY_RATES = {
    "VN": {"value": 4.50, "as_at": "2023-06"},
}

# News sources. type "rss" reads a feed. type "scrape" collects article links
# from a page whose URL contains link_contains.
NEWS_SOURCES = [
    {"name": "Beef Central", "type": "rss", "url": "https://www.beefcentral.com/feed/"},
    {"name": "eFeedLink", "type": "scrape", "url": "https://www.efeedlink.com/",
     "link_contains": "/contents/", "min_title": 25},
]
NEWS_KEEP = 40

# Web pages watched for changes. "selector" narrows the comparison to the
# main content so menus and footers do not cause false alerts.
MONITORED_PAGES = [
    {"key": "daff-parliament", "name": "DAFF reports to Parliament",
     "url": "https://www.agriculture.gov.au/biosecurity-trade/export/controlled-goods/live-animals/live-animal-export-statistics/reports-to-parliament",
     "selector": "main"},
    {"key": "daff-escas", "name": "DAFF ESCAS investigations",
     "url": "https://www.agriculture.gov.au/biosecurity-trade/export/controlled-goods/live-animals/livestock/compliance-investigations/investigations-escas",
     "selector": "main"},
    {"key": "livecorp-tenders", "name": "LiveCorp tenders",
     "url": "https://livecorp.com.au/tenders",
     "selector": "main"},
]

# Minimum hours between refreshes of each block
INTERVALS = {"fx": 1, "news": 0.4, "monitor": 1, "econ": 24, "mla": 20}
