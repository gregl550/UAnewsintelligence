RSS_FEEDS = {
    # Industry publications
    "AdExchanger":        "https://adexchanger.com/feed/",
    "AdWeek":             "https://www.adweek.com/feed/",
    "Digiday":            "https://digiday.com/feed/",
    "Marketing Brew":     "https://www.marketingbrew.com/feed.xml",
    "Modern Retail":      "https://www.modernretail.co/feed/",
    "Social Media Today": "https://feeds.feedburner.com/SocialMediaToday",
    "The Verge":          "https://www.theverge.com/rss/index.xml",
    "Variety":            "https://variety.com/feed/",
    "Deadline":           "https://deadline.com/feed/",
    "Next TV / B&C":      "https://www.nexttv.com/rss",
    "TVTech":             "https://www.tvtechnology.com/feeds.xml",
    "StreamTV Insider":   "https://www.streamtvinsider.com/rss.xml",
    # Competitor direct feeds — MNTN (mountain.com)
    "MNTN Blog":          "https://mountain.com/blog/feed/",
    "MNTN Press":         "https://mountain.com/press/feed/",
    # Competitor Google News monitors
    "Vibe.co News":       "https://news.google.com/rss/search?q=vibe.co+CTV+advertising&hl=en-US&gl=US&ceid=US:en",
    "MNTN News":          "https://news.google.com/rss/search?q=MNTN+Performance+TV+CTV+advertising&hl=en-US&gl=US&ceid=US:en",
    "MNTN Mountain News": "https://news.google.com/rss/search?q=mountain.com+advertising&hl=en-US&gl=US&ceid=US:en",
    # UK market
    "Advanced Television": "https://advanced-television.com/feed",
    "Mediatel News":       "https://mediatel.co.uk/newsline/?feed=rss2",
    "UK CTV News":         "https://news.google.com/rss/search?q=UK+CTV+advertising+Sky+AdSmart&hl=en-GB&gl=GB&ceid=GB:en",
    # Finance / earnings
    "CTV Earnings News":   "https://news.google.com/rss/search?q=CTV+advertising+earnings+revenue&hl=en-US&gl=US&ceid=US:en",
}

# Keywords that boost relevance during pre-filtering (case-insensitive)
RELEVANCE_KEYWORDS = [
    # Platform Partnerships — CTV / programmatic / ad tech
    # MNTN
    "MNTN", "mountain.com", "MNTN Performance TV", "MNTN CTV",
    "Ryan Reynolds MNTN", "Performance TV MNTN",
    # Vibe.co
    "Vibe.co", "Vibe CTV", "vibeads", "vibe.co ads",
    # Other competitors
    "Tatari", "Roku", "Amazon", "Fire TV",
    "NBCU", "NBCUniversal", "Peacock", "Comcast",
    "self-serve", "self serve", "CTV", "connected TV", "streaming TV",
    "programmatic", "performance TV", "OTT",
    "privacy", "signal loss", "identity", "cookie",
    "upfront", "scatter", "cord-cutting", "cord cutting",
    "ad-supported", "AVOD", "FAST", "SVOD",
    "measurement", "attribution", "incrementality",
    "The Trade Desk", "LiveRamp", "Nielsen", "iSpot",
    # UK market
    "Sky Media", "Sky AdSmart", "Channel 4", "ITV", "ITVX", "BBC iPlayer",
    "Channel 5", "BritBox", "UK CTV", "UK streaming", "UK advertising",
    "Ofcom", "UK programmatic", "addressable TV UK",
    # Finance / earnings
    "earnings", "quarterly results", "revenue", "ad revenue", "advertising revenue",
    "financial results", "EPS", "guidance", "analyst", "Wall Street", "stock",
    "quarterly earnings", "Q1", "Q2", "Q3", "Q4", "fiscal year", "annual report",
]

CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_CONTENT_CHARS = 900   # per article before truncation
MAX_ARTICLES_PER_CALL = 120
