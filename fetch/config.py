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
# Years of history fetched per run while the 20-year backfill completes
MLA_MAX_CHUNKS_PER_RUN = 40

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
# Commodity futures and freight proxy (Yahoo Finance symbols)
MARKETS = [
    {"sym": "ZC=F", "name": "Corn",          "unit": "USc/bu",  "group": "Grains"},
    {"sym": "ZW=F", "name": "Wheat",         "unit": "USc/bu",  "group": "Grains"},
    {"sym": "ZS=F", "name": "Soybeans",      "unit": "USc/bu",  "group": "Grains"},
    {"sym": "ZM=F", "name": "Soybean meal",  "unit": "US$/st",  "group": "Grains"},
    {"sym": "BZ=F", "name": "Brent crude",   "unit": "US$/bbl", "group": "Energy and freight"},
    {"sym": "BDRY", "name": "Dry bulk freight (BDRY)", "unit": "US$", "group": "Energy and freight"},
]

# Weather locations (Open-Meteo). ytd=True adds rainfall to date against the 1991 to 2020 average.
WEATHER = [
    {"name": "Dandaragan", "lat": -30.67, "lon": 115.70, "ytd": True},
    {"name": "Fremantle",  "lat": -32.05, "lon": 115.75},
    {"name": "Darwin",     "lat": -12.46, "lon": 130.84},
    {"name": "Townsville", "lat": -19.26, "lon": 146.82},
]

# WOAH WAHIS animal disease events. Countries are matched by name.
DISEASE_COUNTRIES = ["Australia", "Indonesia", "Malaysia", "Viet Nam", "Thailand", "China (People's Rep. of)",
                     "Philippines", "Brunei", "Israel", "Kuwait", "Qatar", "Jordan", "United Arab Emirates",
                     "Saudi Arabia", "Oman", "Timor-Leste", "Papua New Guinea", "Cambodia", "Lao", "Myanmar"]
DISEASE_DAYS = 120
# Diseases shown with a red flag
DISEASE_PRIORITY = ["foot and mouth", "lumpy skin", "african swine fever", "peste des petits", "sheep pox", "goat pox",
                    "bluetongue", "anthrax", "rinderpest", "contagious bovine pleuropneumonia", "highly pathogenic avian influenza",
                    "rift valley", "screwworm", "surra", "haemorrhagic septicaemia"]

# DAFF all livestock exports by market (monthly spreadsheet)
EXPORTS_PAGE = "https://www.agriculture.gov.au/biosecurity-trade/export/controlled-goods/live-animals/live-animal-export-statistics/livestock-exports-by-market"

# AusTender approaches to market. Items whose title or description contains any keyword are kept.
TENDERS_FEED = "https://www.tenders.gov.au/public_data/rss/rss.xml"
TENDER_KEYWORDS = ["livestock", "animal welfare", "cattle", "sheep", "goat", "live export", "biosecurity", "veterinar",
                   "traceability", "abattoir", "meat", "agricultur", "animal health", "export certification", "feedlot"]

# Livestock carriers tracked on the map (names as broadcast on AIS, case-insensitive).
# Needs the AISSTREAM_API_KEY repository secret. Positions come from shore-based
# receivers, so a ship far offshore shows its last position heard.
VESSELS = ["OCEAN DROVER", "OCEAN UTE", "OCEAN SWAGMAN", "OCEAN KELPIE", "OCEAN OUTBACK", "OCEAN SHEARER",
           "BRAHMAN EXPRESS", "GALLOWAY EXPRESS", "GELBRAY EXPRESS", "ANGUS EXPRESS", "DEVON EXPRESS",
           "BISON EXPRESS", "GLOUCESTER EXPRESS", "YANGTZE FORTUNE", "AL KUWAIT", "MAYSORA", "BAHIJAH", "JAWAN"]
# Area listened to (south-west lat, lon; north-east lat, lon) and listening time per run
VESSEL_BOX = [[-45, 30], [35, 160]]
VESSEL_LISTEN_SECONDS = 120

INTERVALS = {"fx": 1, "news": 0.4, "monitor": 1, "econ": 24, "mla": 20, "markets": 1, "weather": 1,
             "disease": 3, "exports": 24, "tenders": 6, "vessels": 0.4}
