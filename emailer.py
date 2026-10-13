import logging
import os
import re
import smtplib
import textwrap
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ── Category metadata ──────────────────────────────────────────────────────────

CATEGORY_META = {
    "competitive_intelligence": ("Competitive Intel", "#ffe8e8", "#c00"),
    "partner_signals":          ("Partner Signal",   "#e8f5e9", "#2e7d32"),
    "advertiser_trends":        ("Advertiser Trend", "#e8f0fe", "#1a56db"),
    "social_media":             ("Social Media",     "#fce4ec", "#880e4f"),
    "uk_market":                ("UK Market",        "#e2e8f0", "#374151"),
    "policy_regulation":        ("Policy",           "#f3e5f5", "#6a1b9a"),
    "industry_trends":          ("Industry",         "#e0f7fa", "#006064"),
}

BU_META = {
    "Platform Partnerships": ("#6a1b9a", "#fff"),
}

COMPETITOR_LABELS = {
    "mntn":    "MNTN",
    "vibe_co": "Vibe.co",
    "tatari":  "Tatari",
    "roku":    "Roku",
    "amazon":  "Amazon",
    "nbcu":    "NBCU",
}

# ── Did You Know? ─────────────────────────────────────────────────────────────
# 261 NBC/TV history facts — one per weekday for a full year, no repeats.

TV_FACTS: list[str] = [
    "NBC was founded in 1926, making it the oldest major broadcast network in the United States.",
    "The Today Show debuted on NBC in January 1952 and has aired continuously ever since.",
    "NBC's peacock logo was introduced in 1956 to encourage viewers to buy color television sets.",
    "Comcast acquired NBCUniversal in 2011 for $30 billion in one of the largest media deals in history.",
    "Seinfeld, which aired on NBC from 1989 to 1998, is still one of the highest-earning syndicated shows ever made.",
    "The first Super Bowl was broadcast simultaneously on NBC and CBS in January 1967.",
    "NBC was the first network to broadcast a coast-to-coast live television program, in 1951.",
    "Friends generated over $1 billion in syndication revenue for NBC within its first decade off air.",
    "Peacock reached 34 million paid subscribers by 2024, making it one of the fastest-growing streaming platforms.",
    "US CTV advertising spend is projected to exceed $40 billion by 2027, driven largely by premium publisher inventory.",
    "Saturday Night Live first aired on NBC on October 11, 1975, and remains the longest-running live sketch comedy show in television history.",
    "The Tonight Show with Steve Allen premiered on NBC in 1954 and has been on air for over 70 years.",
    "NBC's coverage of the 1964 Tokyo Olympics marked the first time the network broadcast the Summer Games.",
    "ER, which ran on NBC from 1994 to 2009, is one of the highest-rated drama series in television history.",
    "The first commercial color television broadcast in the US was made by NBC in 1954.",
    "NBC Universal was formed in 2004 when Vivendi Universal Entertainment merged with NBC.",
    "The West Wing won 26 Emmy Awards during its seven-season run on NBC from 1999 to 2006.",
    "NBC's Cheers ran for 11 seasons and produced one of the most-watched series finales in US TV history.",
    "The first paid television advertisement in history aired on NBC on July 1, 1941.",
    "NBC Sports holds broadcast rights to NFL Sunday Night Football, consistently the most-watched primetime program in America.",
    "Law & Order, which premiered on NBC in 1990, became the longest-running primetime drama in US television history.",
    "Universal Pictures, now part of NBCUniversal, was founded in 1912, making it one of Hollywood's oldest studios.",
    "The Tonight Show has been hosted by Steve Allen, Jack Paar, Johnny Carson, Jay Leno, Conan O'Brien, and Jimmy Fallon.",
    "NBC's The Blacklist launched in 2013 and became one of the most-watched dramas across linear and streaming platforms.",
    "GE owned NBC from 1986 to 2004, a period that included the launches of MSNBC and CNBC.",
    "CNBC launched in 1989 and has become the world's leading business and financial news network.",
    "MSNBC launched in 1996 as a joint venture between Microsoft and NBC.",
    "NBCUniversal operates over 30 television channels worldwide across cable, broadcast, and streaming.",
    "NBC's broadcast home at 30 Rockefeller Plaza in New York has been a landmark since 1933.",
    "The Office, NBC's adaptation of the British series, ran from 2005 to 2013 and remains one of the most-streamed shows ever.",
    "NBC's Parks and Recreation launched in 2009 and became a streaming cult hit long after its 2015 finale.",
    "Brooklyn Nine-Nine was rescued from cancellation by NBC in 2018 after Fox dropped it, running for three more seasons.",
    "The 2008 Beijing Olympics on NBC drew a record 215 million viewers over its 17-day run.",
    "NBC's Sunday Night Football has been the most-watched primetime show in the US for over a decade straight.",
    "Peacock launched in July 2020 and was one of the last major streaming platforms to enter the market.",
    "The Universal Studios theme parks, operated by NBCUniversal, attract over 50 million visitors per year globally.",
    "NBCUniversal's news division includes NBC News, MSNBC, CNBC, Today, and NBC News NOW.",
    "NBC Nightly News has aired since 1970 and remains one of the top-rated evening newscasts in the country.",
    "Dateline NBC, launched in 1992, is one of the longest-running prime-time news magazine programs on US television.",
    "NBC Sports covered every Summer Olympics from 1988 through 2024, a 36-year run.",
    "The 1994 figure skating rivalry between Tonya Harding and Nancy Kerrigan helped NBC attract its biggest sports audience at the time.",
    "NBC's Will & Grace, which ran from 1998 to 2006 and was revived from 2017 to 2020, was groundbreaking in its LGBT representation.",
    "30 Rock, loosely based on the production of Saturday Night Live, aired on NBC from 2006 to 2013 and won 16 Emmy Awards.",
    "NBC's Frasier ran for 11 seasons and won the Primetime Emmy for Outstanding Comedy Series five consecutive years.",
    "The Biggest Loser premiered on NBC in 2004 and spawned numerous international adaptations.",
    "NBCUniversal spent $7.65 billion to acquire broadcast rights to the 2032 and 2034 Olympic Games.",
    "The NBC chimes — three notes G-E-C — were first used in 1931 and became one of the most recognized audio logos in broadcast history.",
    "Television advertising in the US exceeded $60 billion in 2023, with CTV accounting for the fastest-growing segment.",
    "The first television remote control was introduced in 1950, the same year NBC launched its first regular news programming.",
    "CTV impressions grew more than 20% year-over-year in 2023 as viewers shifted from linear to streaming platforms.",
    "The average US household now receives over 100 channels but regularly watches fewer than 15 of them.",
    "NBC's Peacock has exclusive streaming rights to WWE programming, adding a large and loyal sports entertainment fanbase.",
    "Universal Pictures' Jurassic Park franchise has grossed over $6 billion globally, making it one of NBCUniversal's most valuable properties.",
    "The Emmy Awards ceremony was first broadcast on television by NBC in 1949.",
    "NBC aired the first-ever late-night talk show, Broadway Open House, in 1950.",
    "Connected TV households in the US surpassed 85% penetration by 2024.",
    "Programmatic CTV advertising allows buyers to purchase individual impressions in real time, similar to digital display advertising.",
    "Ad-supported streaming tiers have helped networks like Peacock monetize audiences who resist subscription fees.",
    "NBCUniversal's One Platform unifies linear, streaming, and digital ad inventory for cross-screen campaign buys.",
    "The upfront market, in which advertisers commit spending before the TV season begins, has existed since the early 1960s.",
    "Addressable TV advertising enables brands to serve different ads to different households watching the same program.",
    "The CPM for premium CTV inventory averaged between $25 and $40 in 2023, well above most digital display rates.",
    "Comcast's FreeWheel is one of the largest ad technology platforms for premium video advertising worldwide.",
    "NBCUniversal's advertising revenue exceeded $8 billion in 2022 across all of its platforms.",
    "The first TV advertisement in the UK aired in 1955, nearly 14 years after the US debuted paid TV ads.",
    "A 30-second Super Bowl ad cost approximately $7 million in 2024, up from $42,000 at the first Super Bowl in 1967.",
    "Nielsen ratings, the primary measurement currency for US TV advertising, have been used since 1950.",
    "The transition from traditional Nielsen ratings to impression-based measurement has been one of the biggest industry shifts of the 2020s.",
    "Streaming platforms collectively surpassed traditional broadcast and cable TV in total viewing time for the first time in 2022.",
    "NBC Sports Group was dissolved in 2022 when Comcast restructured, moving most of its sports content to Peacock.",
    "The Golf Channel, owned by NBCUniversal, reaches over 60 million US households.",
    "USA Network, part of NBCUniversal, was one of the first cable channels to invest heavily in original scripted programming.",
    "Suits, originally a USA Network show, became the most-streamed show in Netflix history in 2023.",
    "NBCUniversal owns Bravo, the cable network behind the long-running Real Housewives franchise.",
    "The Real Housewives franchise, launched by Bravo in 2006, has spawned over 20 different city-based editions.",
    "Oxygen, NBCUniversal's true crime cable network, consistently ranks among the top-rated cable networks in its genre.",
    "SYFY, owned by NBCUniversal, is one of the few cable networks dedicated exclusively to science fiction and fantasy programming.",
    "E! Entertainment, part of NBCUniversal, covers celebrity news and produces the Emmy red carpet show Live from the Red Carpet.",
    "Telemundo, acquired by NBC in 2001, is the second-largest Spanish-language broadcast network in the United States.",
    "Telemundo's digital reach across streaming and social platforms has grown more than 50% since 2019.",
    "NBC's Must See TV lineup in the 1990s — including Seinfeld, Friends, and ER — made Thursday night appointment television.",
    "Appointment television viewership has steadily declined as DVR and streaming give audiences control over when they watch.",
    "By 2024, over 50% of US adults watched some television exclusively through a streaming platform.",
    "This Is Us premiered on NBC in 2016 and became one of the most-watched broadcast dramas of the streaming era.",
    "NBC's Chicago franchise, produced by Dick Wolf, includes Chicago Fire, Chicago PD, and Chicago Med.",
    "Dick Wolf's Law & Order franchise across NBC and Peacock spans more than 30 years of continuous production.",
    "The Voice, NBC's singing competition, has aired since 2011 and helped revive the network's Monday night ratings.",
    "America's Got Talent, which airs on NBC, has been one of the most-watched summer shows since its 2006 premiere.",
    "The legendary talk show host Johnny Carson hosted The Tonight Show on NBC for 30 years, from 1962 to 1992.",
    "Jay Leno's first run as Tonight Show host ran from 1992 to 2009, making him the longest-tenured solo host in the show's history.",
    "Conan O'Brien hosted Late Night on NBC from 1993 to 2009 before his short-lived tenure on The Tonight Show.",
    "Jimmy Fallon took over The Tonight Show from Jay Leno in 2014, relocating production back to New York City.",
    "The 1969 moon landing broadcast was covered live by NBC, drawing one of the largest television audiences in history.",
    "NBC's coverage of the O.J. Simpson verdict in 1995 attracted over 100 million simultaneous US viewers.",
    "RCA, the parent company of NBC, introduced color television sets to the US market in 1954.",
    "David Sarnoff, who founded RCA and NBC, is widely regarded as the father of American broadcasting.",
    "The NBC Radio Network, launched in 1926, preceded the television network by over two decades.",
    "NBC Television launched its first regular programming schedule in 1939, broadcasting to a small number of households in New York.",
    "The Howdy Doody Show, which aired on NBC from 1947 to 1960, was one of the first successful children's programs in TV history.",
    "The 1960 presidential debate between Kennedy and Nixon, broadcast on all three networks, permanently changed the role of television in politics.",
    "Television advertising revenue in the US first exceeded $1 billion in 1955.",
    "The introduction of the VCR in the late 1970s was initially opposed by NBC and other networks as a threat to advertising revenue.",
    "TiVo, introduced in 1999, allowed viewers to skip commercials for the first time at scale, alarming the broadcast industry.",
    "DVR penetration in US households peaked at around 50% before streaming services began to replace the technology.",
    "The TV advertising market contracted sharply during the 2008 financial crisis, losing over 10% of revenue in a single year.",
    "The rise of mobile video viewing has expanded the definition of television to include smartphones and tablets.",
    "NBCUniversal's digital properties collectively reach over 200 million unique users per month.",
    "The 2020 Tokyo Olympics, delayed by COVID-19, was broadcast by NBC on Peacock alongside linear channels for the first time.",
    "The 2022 Beijing Winter Olympics saw NBC shift more live coverage to Peacock than any previous Olympic Games.",
    "Peacock offered more streaming hours of Olympic coverage in 2024 than any broadcaster had offered in previous Games.",
    "NBCUniversal's Paris 2024 Olympics coverage broke records for streaming consumption across Peacock.",
    "The Super Bowl has been the most-watched single event on US television every year since at least 1990.",
    "Super Bowl XLIX on NBC in 2015 drew over 114 million viewers, setting a US television record at the time.",
    "Super Bowl commercials are widely considered the most effective single-day brand-building opportunities in US advertising.",
    "NBC, CBS, ABC, and Fox together are known as the Big Four broadcast networks in the United States.",
    "Broadcast television reaches approximately 90% of US households via antenna, cable, or satellite.",
    "The share of primetime viewing attributed to Big Four networks fell from over 80% in 1980 to under 30% by 2020.",
    "Cable television surpassed broadcast in total primetime ratings share for the first time in 2008.",
    "Streaming platforms surpassed cable in total viewing minutes for the first time in July 2022.",
    "Netflix became the first streaming service to win the Primetime Emmy Award for Outstanding Drama Series in 2022.",
    "YouTube is now counted as a CTV inventory source alongside Peacock and Hulu by major media buyers.",
    "Amazon Prime Video launched an ad-supported tier in early 2024, adding significant new scale to the CTV marketplace.",
    "Disney+ added an ad-supported tier in 2022, marking a significant expansion of premium streaming ad inventory.",
    "Hulu pioneered the ad-supported streaming model beginning in 2008 and has been a Peacock competitor ever since.",
    "NBCUniversal sold its remaining stake in Hulu to Disney in 2023 as part of a pre-existing buyout agreement.",
    "Virtual MVPDs such as YouTube TV, Sling TV, and FuboTV grew to over 15 million US subscribers by 2023.",
    "Programmatic advertising for television began to gain traction in 2014 and has grown into a multi-billion dollar market.",
    "NBCUniversal's One Platform initiative, launched in 2019, was one of the first unified cross-screen ad buying systems from a major broadcaster.",
    "Frequency capping across screens has become one of the most-requested features from CTV advertisers.",
    "Identity resolution tools now allow advertisers to connect CTV ad exposures to outcomes like website visits and purchases.",
    "Clean room technology enables advertisers and publishers to match audience data without sharing personally identifiable information.",
    "Upfront commitments for streaming inventory surpassed $1 billion for the first time in 2022.",
    "The shift from guaranteed ratings to impression-based guarantees has been one of the most significant structural changes in TV buying.",
    "NBCUniversal introduced its Audience Targeting Platform to allow data-driven targeting across linear and streaming in a single buy.",
    "Contextual targeting has gained renewed interest in CTV as signal loss from mobile identifiers reduces behavioral targeting precision.",
    "Comcast Advertising's FreeWheel serves tens of billions of ad requests per year from premium video publishers.",
    "The IAB defines CTV as any television set connected to the internet through a built-in smart TV OS or an external streaming device.",
    "Roku is the leading CTV platform in the US by active accounts, with over 80 million accounts as of 2024.",
    "Amazon Fire TV is the second-largest CTV platform in the US, powered by deep integration with the Alexa voice ecosystem.",
    "Apple TV has positioned itself as a premium CTV device and operates the Apple TV+ streaming service.",
    "Samsung, LG, and Vizio are the largest manufacturers of smart TVs with built-in ad-supported streaming in the US.",
    "Vizio, acquired by Walmart in 2024, gives the retail giant direct access to SmartCast TV and first-party shopper purchase data.",
    "Walmart's acquisition of Vizio was widely seen as a direct challenge to Amazon's retail media and CTV advertising strategy.",
    "Retail media networks are increasingly integrating with CTV platforms to connect purchase data to television ad exposure.",
    "The Trade Desk's OpenPath initiative aims to create direct relationships between advertisers and premium publishers, bypassing intermediaries.",
    "Magnite is the largest independent omnichannel sell-side advertising platform, with a major focus on premium CTV inventory.",
    "Innovid provides measurement and personalization infrastructure for CTV campaigns across all major streaming platforms.",
    "iSpot.tv, VideoAmp, and Comscore have all launched as alternative measurement currencies to Nielsen for cross-platform TV.",
    "Nielsen's return following its 2021 MRC accreditation suspension was one of the most closely watched events in TV measurement history.",
    "The MRC, or Media Rating Council, is the body that accredits measurement services used as trading currencies in US media.",
    "Cross-platform measurement remains one of the most contested and unresolved issues in television advertising.",
    "Outcome-based buying, in which advertisers pay for results rather than impressions, is growing in popularity for CTV campaigns.",
    "Attention metrics, which measure how long viewers focus on an ad, have emerged as a complement to viewability metrics in CTV.",
    "Co-viewing — multiple people watching the same CTV screen — creates measurement challenges since smart TV data tracks household, not individuals.",
    "The average US adult watched approximately four hours and thirty minutes of television per day in 2023.",
    "Binge-watching, defined as three or more episodes in a single session, is now the dominant content consumption pattern on streaming.",
    "Short-form video on TikTok and YouTube Shorts is competing with long-form television for viewer attention, especially among Gen Z.",
    "Live sports remain the most powerful tool for driving simultaneous large-scale audiences on both linear and streaming platforms.",
    "The NFL accounted for 93 of the 100 most-watched television programs in the US in 2023.",
    "NBCUniversal holds a significant portion of NFL broadcast rights through a multi-year agreement worth billions of dollars.",
    "Sunday Night Football on NBC averaged over 18 million viewers per episode during the 2023 season.",
    "Peacock's exclusive NFL playoff game in January 2024 set a new record for the most-streamed live sports event in US history.",
    "NBCUniversal expanded its Big Ten college football coverage through a landmark long-term deal with the conference.",
    "NBCUniversal regained a share of NBA broadcast rights starting in the 2025 season, ending the ABC/ESPN exclusive.",
    "Golf content on NBC and the Golf Channel draws some of the most affluent audiences in US television advertising.",
    "The Kentucky Derby has been broadcast on NBC since 1952, making it one of the longest-running sports rights deals in television.",
    "Formula 1 racing has grown dramatically in US viewership since Netflix's Drive to Survive documentary launched in 2019.",
    "Sports betting integration with live TV broadcasts has become a significant new revenue opportunity for networks including NBCUniversal.",
    "Second-screen sports experiences — where viewers track stats and odds on a phone while watching TV — have driven companion app development.",
    "Live news events such as election nights consistently drive the largest simultaneous streaming audiences outside of sports.",
    "NBC News NOW, the network's free streaming news service, has expanded significantly as traditional cable news viewership has declined.",
    "Over-the-top TV and CTV are often used interchangeably, though OTT technically refers to the delivery mechanism and CTV to the device.",
    "Frequency management across linear and streaming has become a top priority for media buyers to avoid overexposing viewers to the same ad.",
    "Dynamic ad insertion allows streaming platforms to replace or augment ads in live and on-demand content in real time.",
    "Server-side ad insertion stitches ads directly into the video stream, reducing buffering and improving the viewer experience.",
    "Ad-supported video on demand is the fastest-growing segment of the streaming market by advertising revenue.",
    "Free, ad-supported TV channels — like Pluto TV and Tubi — are attracting cord-cutters who want free television without a subscription.",
    "NBCUniversal's FAST channel strategy is integrated into Peacock's free tier, funded entirely by advertising.",
    "Live linear streaming on FAST channels has seen surprising growth, suggesting viewers still want the lean-back experience of scheduled TV.",
    "The global CTV advertising market is projected to reach $100 billion by 2030 according to multiple industry forecasts.",
    "Video completion rate is one of the primary performance metrics for CTV advertising, typically exceeding 95% on premium platforms.",
    "Brand safety in CTV is generally considered stronger than in social or user-generated content because inventory comes from premium publishers.",
    "NBCUniversal's Peacock Advertising platform offers self-serve tools for mid-market advertisers to access premium CTV inventory.",
    "Streaming ad loads are generally lower than linear, typically 4 to 5 minutes per hour versus 16 minutes per hour on cable.",
    "Some research suggests that ads in streaming environments generate higher recall and brand lift than the same ads on linear television.",
    "Interactive CTV ads, which allow viewers to engage with content using their remote, are growing in adoption across major platforms.",
    "QR codes in TV commercials have seen a resurgence as a bridge between the television screen and mobile purchasing behavior.",
    "Attribution models for CTV typically rely on device graph matching to connect ad exposures to web, app, or in-store actions.",
    "Incrementality testing — running holdout groups — has become the gold standard for measuring the true causal impact of CTV advertising.",
    "Multi-touch attribution models assign fractional credit to each ad touchpoint in a consumer's path to conversion.",
    "Media mix modeling uses aggregate data to estimate the contribution of each channel, including CTV, to overall sales.",
    "The integration of multi-touch attribution and media mix modeling is known as unified measurement and is being adopted by sophisticated advertisers.",
    "NBCUniversal partnered with Accenture to build NBCUniversal Audience Insights, combining data science with media planning tools.",
    "The television industry trades in GRPs, or Gross Rating Points, a measure of ad exposure that has been used since the 1950s.",
    "The shift from GRP-based to impression-based trading is seen as foundational to true cross-platform measurement.",
    "Reach and frequency are the two most basic metrics in media planning, measuring how many people saw an ad and how many times.",
    "NBC's affiliate network includes over 200 local stations across the US, providing local news and national content distribution.",
    "Retransmission consent fees, paid by cable and satellite operators to carry broadcast networks, have become a major revenue source for NBC affiliates.",
    "Retransmission fees for the major broadcast networks collectively reached nearly $12 billion in 2022.",
    "Cord-cutting — the cancellation of cable or satellite subscriptions — has accelerated since 2016, reaching over 25 million US households.",
    "Pay TV subscribers in the US declined from a peak of over 100 million in 2012 to under 70 million by 2024.",
    "NBC's owned-and-operated stations are among the most valuable broadcast properties in their respective local markets.",
    "WNBC in New York is one of the most-watched local television stations in the United States.",
    "Local television advertising remains a significant revenue source, particularly during election years when political spending spikes.",
    "Political advertising on broadcast TV hit record levels in 2022 and 2024, with over $3 billion spent across local and national inventory.",
    "The FCC's equal time rule requires broadcast stations like NBC affiliates to give equal airtime to competing political candidates.",
    "Broadcast television is still subject to content regulations that do not apply to streaming platforms, including FCC decency standards.",
    "NBCUniversal has been a leading advocate for advertising industry standards through participation in the IAB and 4A's.",
    "The Coalition for Innovative Media Measurement was co-founded by NBCUniversal to advance cross-platform measurement standards.",
    "Project OAR is an industry initiative to standardize addressable advertising across smart TV manufacturers.",
    "NBCUniversal's One Platform data is built on a first-party identity graph drawn from over 200 million registered users.",
    "Contextual targeting by content genre, daypart, and program type remains widely used in CTV buying despite the growth of data-driven methods.",
    "Lookalike modeling uses seed audiences from first-party data to find statistically similar viewers across additional inventory.",
    "Audience extension allows buyers to reach audiences identified on one platform across additional inventory in a publisher's ecosystem.",
    "NBCUniversal's Campaign Suite provides measurement tools that track conversions tied to Peacock and linear ad exposure.",
    "The TV upfront season takes place each spring, with networks presenting their fall schedules to advertisers in elaborate presentations.",
    "NBCUniversal's upfront presentations are typically held at Radio City Music Hall in New York City.",
    "The scatter market — buying TV ads after the upfront season — typically commands significantly higher CPMs than upfront pricing.",
    "Programmatic guaranteed deals allow advertisers to lock in premium CTV inventory at a fixed price through automated systems.",
    "Private marketplace deals are negotiated between a specific buyer and seller, offering premium inventory with programmatic execution.",
    "Preferred deals give a single buyer first right of refusal on a publisher's inventory before it goes to open auction.",
    "Supply path optimization is a practice where buyers reduce intermediaries between their DSP and a publisher's inventory.",
    "DSPs such as The Trade Desk, DV360, and Amazon DSP are the primary tools through which agencies buy programmatic CTV inventory.",
    "SSPs such as Magnite, PubMatic, and FreeWheel manage the sale of CTV publisher inventory to multiple demand sources simultaneously.",
    "Ad verification in CTV has improved significantly with the adoption of VAST and VPAID standards across major platforms.",
    "IAB Tech Lab's Open Measurement SDK provides a standardized way for third-party vendors to verify CTV ad delivery.",
    "Invalid traffic in CTV, including ad spoofing and domain fraud, has become a growing concern for brand-safe inventory buyers.",
    "NBCUniversal has committed to ads.txt and app-ads.txt standards to help buyers verify the legitimacy of its inventory.",
    "The total addressable market for video advertising in the US is estimated at over $70 billion annually, with CTV taking an increasing share.",
    "NBCUniversal's Universal Ads platform is designed to make premium TV advertising more accessible to brands of all sizes.",
    "The broadcast TV upfront market transacts roughly $10 billion in advertising commitments each spring.",
    "NBCUniversal's data-driven linear product allows advertisers to layer audience targeting onto traditional broadcast buys.",
    "Streaming households watch an average of three to four streaming services simultaneously, creating a fragmented but rich ad environment.",
    "The average CTV ad campaign in 2023 reached audiences across more than five different streaming apps or devices.",
    "NBCUniversal's Peacock is the only major streaming platform that simulcasts live broadcast television.",
    "NBCSN, the NBC Sports cable channel, was shut down at the end of 2021 as Comcast consolidated sports rights onto Peacock.",
    "The Bravo network's Watch What Happens Live has aired over 2,000 episodes, making it one of cable's longest-running live late-night shows.",
    "Universal Music Group, spun off from Vivendi and later NBCUniversal's orbit, is the world's largest record label.",
    "The Universal lot in Universal City, California, has been used as a film production location since 1915.",
    "NBCUniversal operates Universal Studios Hollywood, Universal Orlando, and international theme parks in Japan and Beijing.",
    "Xfinity, Comcast's consumer brand, is the largest internet service provider in the United States.",
    "Comcast's cable business has been investing in converged advertising products that link household broadband data with TV ad delivery.",
    "The Peacock original series Bel-Air, a dramatic reimagining of The Fresh Prince of Bel-Air, debuted to strong streaming numbers in 2022.",
    "NBC's The Voice has featured coaches including Adam Levine, Blake Shelton, Kelly Clarkson, and John Legend.",
    "The Emmy Award for Outstanding Variety Talk Series has been won by NBC shows more than any other network over the past 30 years.",
    "NBCUniversal's portfolio includes Spanish-language streaming through Peacock and Telemundo's digital platforms.",
    "The One Platform Total Audience solution gives advertisers a single point of access to all NBCUniversal audience segments.",
    "Peacock's free ad-supported tier has been a key driver of total registered user growth since the platform's 2020 launch.",
    "CTV ad fraud rates are significantly lower than open web display advertising due to the walled-garden nature of most streaming platforms.",
    "The average US streaming subscriber now pays for 3.4 services, down from a peak of 4.2 in 2022 as subscription fatigue grows.",
    "NBCUniversal's news programming reaches more Americans daily than any other news organization in the country.",
    "Late Night with Seth Meyers on NBC has won multiple Writers Guild of America Awards for its comedy writing staff.",
    "The first televised presidential inauguration was broadcast by NBC in January 1949.",
    "NBC Sports broadcast the first live national coverage of an NBA game in 1954, helping launch professional basketball's television era.",
    "NBCU's Fandango, the movie ticketing and entertainment platform, reaches tens of millions of entertainment fans monthly.",
    "NBCUniversal's content licensing business distributes programming to broadcasters in over 200 countries worldwide.",
    "The NBCUniversal Media Village at 30 Rock in New York hosts studios, newsrooms, and broadcast facilities across multiple floors.",
    "Peacock's integration with Comcast's X1 cable platform gives subscribers seamless access to streaming and linear content from one interface.",
    "NBCUniversal's Digital Lab has launched dozens of ad technology pilots focused on measurement, targeting, and creative personalization.",
    "The Super Bowl LII halftime show on NBC in 2018, featuring Justin Timberlake, drew over 103 million live viewers.",
    "Universal Ads combines NBCUniversal's premium content reach with simplified buying tools to help local and regional advertisers compete nationally.",
]

# ── Shared style values ────────────────────────────────────────────────────────

_FONT = "'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"
_TEXT = f"font-family:{_FONT};color:#1a202c"

# ── HTML helpers ───────────────────────────────────────────────────────────────

_ABBREVS = [
    "Bros.", "Inc.", "Corp.", "Co.", "Ltd.", "LLC.", "U.S.", "vs.", "etc.",
    "e.g.", "i.e.", "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "St.", "Gov.",
    "Sen.", "Rep.", "Gen.", "Sgt.", "No.", "Vol.", "Dept.", "Ave.", "Blvd.",
]

def _split_sentences(text: str) -> list[str]:
    protected = text
    subs: list[tuple[str, str]] = []
    for i, abbr in enumerate(_ABBREVS):
        ph = f"\x00A{i}\x00"
        new = protected.replace(abbr, ph)
        if new != protected:
            subs.append((ph, abbr))
            protected = new
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected.strip())
    result = []
    for part in parts:
        s = part.strip()
        for ph, abbr in subs:
            s = s.replace(ph, abbr)
        if s:
            result.append(s)
    return result


def _cap_sentences(text: str, n: int) -> str:
    parts = _split_sentences(text)
    return ' '.join(parts[:n])


def _exec_summary_html(text: str) -> str:
    sentences = _split_sentences(text)
    if len(sentences) < 2:
        return (
            f'<p style="margin:0 0 8px;font-size:13px;line-height:1.5;'
            f'color:#3d4852;font-family:{_FONT}">{text}</p>'
        )
    items = "".join(
        f'<li style="font-size:13px;line-height:1.5;color:#3d4852;font-family:{_FONT};'
        f'margin-bottom:5px">'
        f'<span style="color:#f07030;font-weight:700;margin-right:6px">&bull;</span>{s}</li>'
        for s in sentences
    )
    return f'<ul style="margin:0 0 8px;padding-left:0;list-style:none">{items}</ul>'


def _tag_html(categories: list[str]) -> str:
    parts = []
    for cat in categories:
        label, bg, fg = CATEGORY_META.get(cat, (cat.replace("_", " ").title(), "#edf2f7", "#4a5568"))
        parts.append(
            f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
            f'font-size:10px;font-weight:600;margin-right:3px;'
            f'background:{bg};color:{fg}">{label}</span>'
        )
    return "".join(parts)


def _region_tags_html(regions: list[str]) -> str:
    return "".join(
        f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
        f'font-size:10px;font-weight:600;margin-right:3px;'
        f'background:#374151;color:#fff">{r}</span>'
        for r in regions
    )


def _bu_tags_html(business_units: list[str]) -> str:
    parts = []
    for bu in business_units:
        bg, fg = BU_META.get(bu, ("#4a5568", "#fff"))
        parts.append(
            f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
            f'font-size:10px;font-weight:600;margin-right:3px;'
            f'background:{bg};color:{fg}">{bu}</span>'
        )
    return "".join(parts)


def _score_badge(score: int) -> str:
    bg = {5: "#c00", 4: "#e65100"}.get(score, "#003087")
    return (
        f'<span style="display:inline-block;width:16px;height:16px;border-radius:50%;'
        f'font-size:9px;font-weight:800;text-align:center;line-height:16px;'
        f'margin-right:5px;vertical-align:middle;background:{bg};color:#fff">{score}</span>'
    )


def _source_link(url: str) -> str:
    if not url:
        return ""
    return f' <a href="{url}" style="font-size:11px;color:#003087;text-decoration:none">[source]</a>'


def _story_html(story: dict, is_last: bool = False) -> str:
    score = story.get("relevance_score", 3)
    title = story.get("title", "Untitled")
    url = story.get("url", "#")
    source = story.get("source", "")
    pub = story.get("published", "")
    summary = _cap_sentences(story.get("summary", ""), 2)
    impl = _cap_sentences(story.get("ua_implications", ""), 1)
    cats    = story.get("categories", [])
    bus     = story.get("business_units", [])
    regions = story.get("regions", [])

    title_color = "#c00" if score >= 5 else "#1a202c"
    link_color  = "#c00" if score >= 5 else "#003087"
    row_border  = "none" if is_last else "1px solid #f7fafc"

    impl_html = ""
    if impl:
        impl_html = (
            f'<div style="background:#fef9e7;border:1px solid #f6d860;border-radius:4px;'
            f'padding:6px 10px;margin-top:6px;font-size:12px;color:#5a4400;line-height:1.4;'
            f'font-family:{_FONT}">'
            f'<b style="color:#b8860b">UA Signal:</b> {impl}</div>'
        )

    all_tags = _tag_html(cats) + _bu_tags_html(bus) + _region_tags_html(regions)

    return (
        f'<div style="padding:10px 32px;border-bottom:{row_border}">'
        f'<div style="font-size:14px;font-weight:600;line-height:1.3;color:{title_color};'
        f'font-family:{_FONT}">'
        f'{_score_badge(score)}'
        f'<a href="{url}" style="color:{link_color};text-decoration:none">{title}</a>'
        f'</div>'
        f'<div style="color:#8895a7;font-size:11px;margin-top:2px;font-family:{_FONT}">'
        f'{source} &bull; {pub}</div>'
        f'<div style="margin-top:4px">{all_tags}</div>'
        f'<div style="font-size:13px;line-height:1.45;margin-top:5px;color:#3d4852;'
        f'font-family:{_FONT}">{summary}</div>'
        f'{impl_html}'
        f'</div>'
    )


def _section_wrap(heading: str, body: str) -> str:
    return (
        f'<div style="background:#fff;margin-top:8px">'
        f'<div style="padding:9px 32px;border-bottom:1px solid #edf2f7">'
        f'<h2 style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
        f'color:#003087;font-weight:700;font-family:{_FONT}">{heading}</h2>'
        f'</div>'
        f'{body}'
        f'</div>'
    )


def _comp_intel_html(comp: dict) -> str:
    sections = []

    landscape = comp.get("landscape", "")
    if landscape:
        sections.append(
            f'<div style="font-size:12px;color:#6b7280;line-height:1.5;'
            f'margin-bottom:10px;padding:8px 10px;background:#fafafa;'
            f'border-radius:4px;font-family:{_FONT}">'
            f'<span style="font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:.5px;margin-right:6px">Landscape</span>'
            f'{landscape}</div>'
        )

    for key, label in COMPETITOR_LABELS.items():
        items = comp.get(key, [])
        if not items:
            continue
        name_html = (
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.4px;color:#c00;margin:10px 0 3px;font-family:{_FONT}">'
            f'{label}</div>'
        )
        rows = ""
        for i in items:
            badge_html = ""
            tags = _bu_tags_html(i.get("business_units", [])) + _region_tags_html(i.get("regions", []))
            if tags:
                badge_html = f'<div style="margin-top:3px">{tags}</div>'
            rows += (
                f'<div style="font-size:13px;color:#3d4852;line-height:1.4;'
                f'padding-left:8px;border-left:2px solid #ffd0d0;margin-bottom:4px;'
                f'font-family:{_FONT}">'
                f'{i.get("insight","")}{_source_link(i.get("url",""))}{badge_html}</div>'
            )
        sections.append(name_html + rows)

    if not sections:
        return (
            f'<p style="padding:12px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No direct competitor mentions today.</p>'
        )
    return f'<div style="padding:2px 32px 10px">{"".join(sections)}</div>'


def _ua_partners_section(items: list[dict]) -> str:
    header = (
        f'<div style="background:#0d1b4b;padding:9px 32px">'
        f'<h2 style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
        f'color:#fff;font-weight:700;font-family:{_FONT}">UA Partners in the News</h2>'
        f'</div>'
    )
    if not items:
        return (
            f'<div style="background:#fff;margin-top:8px">'
            f'{header}'
            f'<p style="padding:12px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No partner news today.</p>'
            f'</div>'
        )

    rows = ""
    for idx, item in enumerate(items):
        partner  = item.get("partner", "")
        headline = item.get("headline", "")
        insight  = item.get("insight", "")
        url      = item.get("url", "")
        border   = "none" if idx == len(items) - 1 else "1px solid #f0f4ff"

        label = (
            f'<span style="display:inline-block;padding:2px 7px;border-radius:3px;'
            f'font-size:10px;font-weight:700;background:#1e3a8a;color:#fff;'
            f'text-transform:uppercase;letter-spacing:.3px;margin-right:8px;'
            f'vertical-align:middle;font-family:{_FONT}">{partner}</span>'
        )
        hed = (
            f'<a href="{url}" style="font-size:13px;font-weight:600;color:#1a202c;'
            f'text-decoration:none;vertical-align:middle;font-family:{_FONT}">{headline}</a>'
            if url else
            f'<span style="font-size:13px;font-weight:600;color:#1a202c;'
            f'vertical-align:middle;font-family:{_FONT}">{headline}</span>'
        )
        insight_html = (
            f'<div style="font-size:12px;color:#6b7280;line-height:1.4;'
            f'margin-top:5px;font-family:{_FONT}">'
            f'<span style="font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:.4px;margin-right:5px">Partnership signal:</span>'
            f'{insight}</div>'
        ) if insight else ""

        rows += (
            f'<div style="padding:10px 32px;border-bottom:{border}">'
            f'<div style="line-height:1.5">{label}{hed}</div>'
            f'{insight_html}'
            f'</div>'
        )

    return f'<div style="background:#fff;margin-top:8px">{header}{rows}</div>'


def _insight_list_html(items: list[dict]) -> str:
    if not items:
        return (
            f'<p style="padding:10px 32px 14px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'Nothing notable today.</p>'
        )
    rows = []
    for idx, i in enumerate(items):
        is_last = idx == len(items) - 1
        border = "none" if is_last else "1px solid #f7fafc"
        tags = _bu_tags_html(i.get("business_units", [])) + _region_tags_html(i.get("regions", []))
        badge_html = f'<div style="margin-top:3px">{tags}</div>' if tags else ""
        rows.append(
            f'<div style="font-size:13px;color:#3d4852;line-height:1.4;'
            f'padding:5px 0;border-bottom:{border};font-family:{_FONT}">'
            f'{i.get("insight","")}{_source_link(i.get("url",""))}{badge_html}</div>'
        )
    return f'<div style="padding:6px 32px 10px">{"".join(rows)}</div>'


def _finance_corner_html(items: list[dict]) -> str:
    if not items:
        return (
            f'<p style="padding:12px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No earnings or financial news today.</p>'
        )
    rows = ""
    for idx, item in enumerate(items[:4]):
        row_bg = "#fff" if idx % 2 == 0 else "#e8f5e9"
        url = item.get("url", "")
        headline = item.get("headline", "")
        metric = item.get("metric", "")
        headline_html = (
            f'<a href="{url}" style="color:#1b5e20;text-decoration:none;font-size:12px;'
            f'font-weight:600;line-height:1.4;font-family:{_FONT}">{headline}</a>'
            if url else
            f'<span style="font-size:12px;font-weight:600;color:#3d4852;font-family:{_FONT}">{headline}</span>'
        )
        metric_html = (
            f'<div style="font-size:11px;color:#8895a7;margin-top:2px;font-family:{_FONT}">{metric}</div>'
            if metric else ""
        )
        rows += (
            f'<tr style="background:{row_bg}">'
            f'<td style="padding:5px 8px;border:1px solid #c8e6c9;font-size:12px;font-weight:700;'
            f'color:#1b5e20;white-space:nowrap;vertical-align:top;font-family:{_FONT}">'
            f'{item.get("company","")}</td>'
            f'<td style="padding:5px 8px;border:1px solid #c8e6c9;vertical-align:top">'
            f'{headline_html}{metric_html}</td>'
            f'</tr>'
        )
    table = (
        f'<div style="padding:8px 32px 12px">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:#1b5e20">'
        f'<th style="padding:5px 8px;text-align:left;font-size:11px;font-weight:700;'
        f'color:#fff;font-family:{_FONT};border:1px solid #1b5e20;white-space:nowrap">Company</th>'
        f'<th style="padding:5px 8px;text-align:left;font-size:11px;font-weight:700;'
        f'color:#fff;font-family:{_FONT};border:1px solid #1b5e20">Headline &amp; Key Metric</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )
    return table


def _finance_corner_section(items: list[dict]) -> str:
    body = _finance_corner_html(items)
    return (
        f'<div style="background:#f1f8e9;margin-top:8px">'
        f'<div style="padding:9px 32px;border-bottom:1px solid #c8e6c9;background:#1b5e20">'
        f'<h2 style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
        f'color:#fff;font-weight:700;font-family:{_FONT}">Gino&#8217;s Finance Corner &#128200;</h2>'
        f'</div>'
        f'{body}'
        f'</div>'
    )


def build_html(briefing: dict, article_count: int, run_date: str, sources: list[str]) -> str:
    _today = datetime.now().date()
    _jan1 = _today.replace(month=1, day=1)
    _weekday_index = sum(
        1 for d in range((_today - _jan1).days + 1)
        if (_jan1 + timedelta(days=d)).weekday() < 5
    ) - 1
    tv_fact = TV_FACTS[_weekday_index % len(TV_FACTS)]
    word_block_inner = (
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;'
        f'color:#f07030;font-family:{_FONT}">Did You Know?</div>'
        f'<div style="color:#c9d1d9;font-size:14px;line-height:1.6;margin-top:10px;'
        f'font-family:{_FONT}">{tv_fact}</div>'
    )
    exec_summary = briefing.get("executive_summary", "No summary available.")
    key_themes   = briefing.get("key_themes", [])
    top_stories  = briefing.get("top_stories", [])

    # ── Stories ──
    if top_stories:
        stories_html = "".join(
            _story_html(s, is_last=(idx == len(top_stories) - 1))
            for idx, s in enumerate(top_stories)
        )
    else:
        stories_html = (
            f'<p style="padding:16px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No highly-relevant stories today.</p>'
        )

    # ── Key themes list ──
    themes_html = "".join(
        f'<li style="font-family:{_FONT}">{t}</li>'
        for t in key_themes
    )

    # ── Other insight sections ──
    other_sections = ""
    for key, heading in [
        ("partner_signals",   "Partner &amp; Integration Signals"),
        ("advertiser_trends", "Advertiser Trends"),
        ("social_media",      "Meanwhile, in Social Media&#8230;"),
        ("uk_market",         "UK Market"),
    ]:
        items = briefing.get(key, [])
        if items:
            other_sections += _section_wrap(heading, _insight_list_html(items))

    # ── Policy compact block ──
    policy_items = briefing.get("policy_regulation", [])
    if policy_items:
        notes = " &bull; ".join(_cap_sentences(i.get("insight", ""), 1) for i in policy_items)
        policy_block = (
            f'<div style="background:#fff;padding:10px 32px 14px;font-size:12px;'
            f'color:#6b7280;line-height:1.55;margin-top:8px;font-family:{_FONT}">'
            f'<span style="font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:.5px;margin-right:5px">Policy notes:</span>'
            f'{notes}</div>'
        )
    else:
        policy_block = ""

    source_str = " &bull; ".join(sources)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Universal Ads Intelligence Brief &#8212; {run_date}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:{_FONT};color:#1a202c">
<div style="max-width:680px;margin:0 auto">

  <!-- Header -->
  <div style="background:#0a0a0f;padding:22px 32px 16px">
    <h1 style="color:#fff;margin:0;font-size:30px;font-weight:800;letter-spacing:-.5px;font-family:{_FONT}">Universal Ads</h1>
    <div style="height:4px;background:linear-gradient(90deg,#e8402a 0%,#f07030 50%,#4a7fd4 100%);border-radius:3px;margin:10px 0 9px"></div>
    <div style="color:#9ca3af;font-size:13px;font-weight:400;margin:0 0 5px;font-family:{_FONT}">Daily Intelligence Briefing</div>
    <div style="color:#6b7280;font-size:12px;margin-top:4px;font-family:{_FONT}">{run_date} &bull; {article_count} articles analyzed</div>
  </div>

  <!-- Did You Know? -->
  <div style="background:#1a1a2e;padding:16px 32px 18px">
    {word_block_inner}
  </div>

  <!-- Executive summary -->
  <div style="background:#fff;border-left:4px solid #003087;padding:14px 32px">
    <p style="font-size:14px;font-weight:600;color:#003087;margin:0 0 6px;font-family:{_FONT}">Today&#8217;s Briefing</p>
    {_exec_summary_html(exec_summary)}
    <div style="font-size:12px;font-weight:700;color:#5a6472;text-transform:uppercase;letter-spacing:.5px;font-family:{_FONT}">Key Themes</div>
    <ul style="margin:3px 0 0;padding-left:16px;font-size:13px;line-height:1.65;color:#3d4852">{themes_html}</ul>
  </div>

  <!-- Top Stories -->
  {_section_wrap("Top Stories", stories_html)}

  <!-- Competitive Intelligence -->
  {_section_wrap("Competitive Intelligence Detail",
    _comp_intel_html(briefing.get("competitive_intel", {}))
  )}

  <!-- UA Partners in the News -->
  {_ua_partners_section(briefing.get("ua_partners", []))}

  <!-- Finance Corner -->
  {_finance_corner_section(briefing.get("finance_corner", []))}

  <!-- Other sections: Partner, Advertiser, Social, UK Market -->
  {other_sections}

  <!-- Policy notes -->
  {policy_block}

  <!-- Footer -->
  <div style="background:#edf2f7;padding:10px 32px;font-size:11px;color:#8895a7;text-align:center;margin-top:8px;font-family:{_FONT}">
    Universal Ads Intelligence Brief &bull; Powered by Claude AI ({run_date})<br>
    Sources monitored: {source_str}
  </div>

</div>
</body>
</html>"""


def build_plaintext(briefing: dict, run_date: str) -> str:
    lines = [
        f"UNIVERSAL ADS INTELLIGENCE BRIEF — {run_date}",
        "=" * 60,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        briefing.get("executive_summary", ""),
        "",
        "KEY THEMES",
        "-" * 40,
    ]
    for t in briefing.get("key_themes", []):
        lines.append(f"• {t}")
    lines += ["", "TOP STORIES", "-" * 40]
    for s in briefing.get("top_stories", []):
        lines += [
            f"[{s.get('relevance_score',0)}/5] {s.get('title','')}",
            f"  {s.get('source','')} | {s.get('published','')}",
            f"  {s.get('url','')}",
            f"  {s.get('summary','')}",
            f"  UA Signal: {s.get('ua_implications','')}",
            "",
        ]
    return "\n".join(lines)


# ── Sending ────────────────────────────────────────────────────────────────────

_PRIMARY_RECIPIENT = "greglieber@gmail.com"


def send_briefing(briefing: dict, article_count: int) -> None:
    gmail_addr = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipients_raw = os.environ.get("RECIPIENT_EMAILS", gmail_addr)
    all_recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    sender_name = os.environ.get("SENDER_NAME", "Universal Ads Intelligence")

    # Primary recipient always goes in To; everyone else goes in Bcc
    bcc = [r for r in all_recipients if r.lower() != _PRIMARY_RECIPIENT]

    run_date = datetime.now().strftime("%A, %B %-d, %Y")
    subject = f"Universal Ads Intel Brief — {datetime.now().strftime('%b %-d, %Y')}"

    from config import RSS_FEEDS
    sources = list(RSS_FEEDS.keys())

    html_body = build_html(briefing, article_count, run_date, sources)
    text_body = build_plaintext(briefing, run_date)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{gmail_addr}>"
    msg["To"] = _PRIMARY_RECIPIENT
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    smtp_recipients = [_PRIMARY_RECIPIENT] + bcc
    logger.info(f"  To: {_PRIMARY_RECIPIENT}" + (f"  Bcc: {', '.join(bcc)}" if bcc else ""))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_addr, app_password)
        server.sendmail(gmail_addr, smtp_recipients, msg.as_string())
    logger.info("  Email sent successfully")
