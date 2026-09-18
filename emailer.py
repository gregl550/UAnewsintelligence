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

# ── Word of the Day ────────────────────────────────────────────────────────────
# 261 words — exactly one per weekday for a full year, no repeats.
# Interleaved adjective / noun / verb so the part of speech rotates daily.

WORDS_OF_THE_DAY: list[dict] = [
    # index 0-2
    {"word": "ephemeral",     "pos": "adjective", "definition": "Lasting for a very short time; transitory.", "example": "CTV ad impressions are ephemeral by nature — a viewer sees the spot once and moves on."},
    {"word": "exigency",      "pos": "noun",      "definition": "An urgent need or demand requiring immediate action.", "example": "The exigency of the Q4 deadline forced every campaign manager to finalise budgets overnight."},
    {"word": "ruminate",      "pos": "verb",      "definition": "To think deeply and at length about something; to ponder.", "example": "She spent the afternoon ruminating on whether to shift the remaining budget from linear to CTV."},
    # index 3-5
    {"word": "laconic",       "pos": "adjective", "definition": "Using very few words; brief and concise in speech or expression.", "example": "Her laconic reply — a single nod — told the agency everything it needed to know about the creative direction."},
    {"word": "impetus",       "pos": "noun",      "definition": "A force or energy that makes something happen or happen faster.", "example": "The surge in streaming subscriptions gave brands the impetus they needed to shift budget from linear TV."},
    {"word": "galvanize",     "pos": "verb",      "definition": "To shock or excite someone into taking action; to stimulate into activity.", "example": "The announcement of Prime Video's ad-supported tier galvanised the industry to reassess CTV CPMs."},
    # index 6-8
    {"word": "pellucid",      "pos": "adjective", "definition": "Translucently clear; easily understood.", "example": "The best creative briefs are pellucid — every team member should be able to explain the campaign in one sentence."},
    {"word": "equanimity",    "pos": "noun",      "definition": "Mental calmness and composure, especially in difficult situations.", "example": "The media buyer faced the last-minute targeting changes with remarkable equanimity."},
    {"word": "coalesce",      "pos": "verb",      "definition": "To come together and form one mass or whole; to unite.", "example": "After months of fragmented signals, the cross-channel attribution data began to coalesce into a coherent picture."},
    # index 9-11
    {"word": "sanguine",      "pos": "adjective", "definition": "Optimistic or positive, especially in a difficult situation.", "example": "Despite rising CPMs, the programmatic team remained sanguine about the year's CTV performance."},
    {"word": "acumen",        "pos": "noun",      "definition": "The ability to make good judgments and quick decisions; shrewdness.", "example": "Her media buying acumen allowed her to identify underpriced streaming inventory before anyone else on the plan."},
    {"word": "exacerbate",    "pos": "verb",      "definition": "To make a problem, bad situation, or negative feeling worse.", "example": "Signal loss from cookie deprecation only exacerbated the measurement challenges already facing CTV advertisers."},
    # index 12-14
    {"word": "mellifluous",   "pos": "adjective", "definition": "Pleasingly smooth and musical in tone or sound.", "example": "Her mellifluous voice made even the most technical campaign debrief sound engaging to the room."},
    {"word": "gravitas",      "pos": "noun",      "definition": "Dignity, seriousness, and solemnity in manner or bearing.", "example": "The upfront presentation carried a gravitas that underlined how much revenue was at stake for both sides."},
    {"word": "prevaricate",   "pos": "verb",      "definition": "To speak or act evasively; to avoid stating the truth directly.", "example": "The platform representative prevaricated so long on the measurement question that the client lost confidence entirely."},
    # index 15-17
    {"word": "liminal",       "pos": "adjective", "definition": "Relating to a transitional or threshold state between two conditions.", "example": "The industry sits in a liminal state — caught between the old upfront model and the programmatic future."},
    {"word": "probity",       "pos": "noun",      "definition": "The quality of having strong moral principles; complete honesty and integrity.", "example": "His reputation for probity in reporting made him the obvious choice to lead the campaign measurement committee."},
    {"word": "mitigate",      "pos": "verb",      "definition": "To make something less severe, serious, or painful; to lessen the impact of.", "example": "Contextual targeting can help mitigate the impact of signal loss on CTV campaign performance."},
    # index 18-20
    {"word": "perspicacious", "pos": "adjective", "definition": "Having a ready insight into things; shrewd and perceptive.", "example": "The perspicacious media planner spotted the streaming platform's CPM arbitrage opportunity before any rival agency."},
    {"word": "verve",         "pos": "noun",      "definition": "Enthusiasm, energy, and vigor, especially in creative or artistic work.", "example": "She tackled the CTV pitch with a verve that won over the client before the deck was halfway through."},
    {"word": "evince",        "pos": "verb",      "definition": "To reveal the presence of a quality, feeling, or characteristic.", "example": "Her meticulous pre-campaign analysis evinced a level of preparation that immediately impressed the platform team."},
    # index 21-23
    {"word": "inimitable",    "pos": "adjective", "definition": "So good or unusual as to be impossible to copy; unique.", "example": "Peacock's inimitable combination of live sports and AVOD inventory made it a standout in the upfront."},
    {"word": "serendipity",   "pos": "noun",      "definition": "The occurrence of happy or beneficial events by chance; a pleasant surprise.", "example": "It was pure serendipity that the streaming platform launched its self-serve tool just as the brand's linear TV commitment expired."},
    {"word": "circumvent",    "pos": "verb",      "definition": "To find a clever way around an obstacle or rule; to bypass.", "example": "The advertiser found a smart way to circumvent cookie-based limitations by leaning into first-party CTV data."},
    # index 24-26
    {"word": "salient",       "pos": "adjective", "definition": "Most noticeable, important, or relevant; standing out prominently.", "example": "The most salient finding in the attribution report was that CTV was driving 40% of first-touch conversions."},
    {"word": "propensity",    "pos": "noun",      "definition": "A natural inclination or tendency to behave in a particular way.", "example": "Streaming viewers showed a higher propensity to search for products featured in connected TV ads than those seen on linear."},
    {"word": "burnish",       "pos": "verb",      "definition": "To polish by rubbing; to enhance or improve something, especially a reputation.", "example": "The brand used a well-timed CTV campaign to burnish its image ahead of the product launch."},
    # index 27-29
    {"word": "intrepid",      "pos": "adjective", "definition": "Fearless and adventurous; notably courageous.", "example": "The intrepid media buyer negotiated directly with the streaming network rather than routing through the programmatic stack."},
    {"word": "cacophony",     "pos": "noun",      "definition": "A harsh, discordant mixture of sounds.", "example": "The cacophony of competing attribution vendors made it nearly impossible for advertisers to agree on a single source of truth."},
    {"word": "inculcate",     "pos": "verb",      "definition": "To instill an attitude, habit, or idea by persistent instruction or repetition.", "example": "Great account managers inculcate performance discipline not by mandating it, but by walking clients through the data every week."},
    # index 30-32
    {"word": "verdant",       "pos": "adjective", "definition": "Green with grass or other rich vegetation; lush.", "example": "The verdant hillsides in the brand's CTV spot gave the campaign a visual identity that stood out on the streaming platform."},
    {"word": "confluence",    "pos": "noun",      "definition": "A coming together of people, ideas, or events; the junction of two rivers.", "example": "The platform's early success was a confluence of affordable CTV inventory, first-party data, and a brand eager to experiment."},
    {"word": "beguile",       "pos": "verb",      "definition": "To charm or enchant someone, sometimes in a deceptive way.", "example": "The platform tried to beguile prospects with eye-catching ROAS case studies that couldn't be independently verified."},
    # index 33-35
    {"word": "punctilious",   "pos": "adjective", "definition": "Showing great attention to detail or correct behavior; meticulous.", "example": "The punctilious trafficking manager caught every mismatched creative spec before a single impression was wasted."},
    {"word": "candor",        "pos": "noun",      "definition": "The quality of being open, honest, and direct in expression.", "example": "She appreciated the agency's candor about the CTV campaign's underperformance, even when the conversation was difficult."},
    {"word": "conflate",      "pos": "verb",      "definition": "To combine two or more ideas into one, often incorrectly or carelessly.", "example": "It's easy to conflate total reach with incremental reach in CTV reporting when the methodology isn't clearly defined."},
    # index 36-38
    {"word": "cogent",        "pos": "adjective", "definition": "Clear, logical, and convincing; powerfully persuasive.", "example": "She made a cogent case for shifting 30% of the linear TV budget into self-serve CTV."},
    {"word": "ennui",         "pos": "noun",      "definition": "A feeling of listlessness and boredom arising from lack of occupation or excitement.", "example": "A creeping ennui had settled over the linear TV buying team as another quarter passed without a major new client win."},
    {"word": "buttress",      "pos": "verb",      "definition": "To increase the strength of or give support to; to reinforce.", "example": "She used three independent measurement studies to buttress the case for CTV's incremental reach above linear."},
    # index 39-41
    {"word": "propitious",    "pos": "adjective", "definition": "Giving or indicating a good chance of success; favorable.", "example": "The surge in streaming viewership made it a propitious moment to negotiate long-term inventory commitments."},
    {"word": "panacea",       "pos": "noun",      "definition": "A solution or remedy supposed to cure all problems or difficulties.", "example": "Self-serve CTV is no panacea for every advertiser's media problems, but it does offer compelling reach at accessible minimums."},
    {"word": "elicit",        "pos": "verb",      "definition": "To draw out a response, answer, or reaction from someone.", "example": "The detailed post-mortem finally elicited an honest conversation about why the CTV creative hadn't resonated with the audience."},
    # index 42-44
    {"word": "redoubtable",   "pos": "adjective", "definition": "Formidable and inspiring respect, especially as an opponent.", "example": "The Trade Desk remained a redoubtable force in programmatic CTV, even as well-funded challengers entered the market."},
    {"word": "penchant",      "pos": "noun",      "definition": "A strong or habitual liking for something or tendency to do it.", "example": "The brand's penchant for 15-second spots translated surprisingly well into the connected TV environment."},
    {"word": "calibrate",     "pos": "verb",      "definition": "To carefully assess and adjust something for accuracy or effectiveness.", "example": "The team carefully calibrated their CTV frequency caps to avoid overexposing the same household multiple times per day."},
    # index 45-47
    {"word": "incisive",      "pos": "adjective", "definition": "Intelligently analytical and clear-thinking; cutting straight to the point.", "example": "Her incisive questions during the platform demo cut straight through the vendor's sales narrative."},
    {"word": "rectitude",     "pos": "noun",      "definition": "Morally correct behavior or thinking; righteousness.", "example": "His reputation for rectitude in measurement reporting made him the obvious choice to chair the agency's transparency task force."},
    {"word": "iterate",       "pos": "verb",      "definition": "To repeat a process, making improvements or adjustments with each cycle.", "example": "The creative team iterated on the CTV ad format for six weeks before the completion rate metrics finally improved."},
    # index 48-50
    {"word": "evanescent",    "pos": "adjective", "definition": "Soon passing out of sight, memory, or existence; quickly fading.", "example": "The evanescent nature of streaming audiences — constantly churning across platforms — makes long-term loyalty hard to measure."},
    {"word": "hubris",        "pos": "noun",      "definition": "Excessive pride or self-confidence, often leading to one's downfall.", "example": "The network's hubris about its upfront dominance blinded it to the self-serve CTV threat building beneath."},
    {"word": "dissemble",     "pos": "verb",      "definition": "To conceal or disguise one's true motives, feelings, or beliefs.", "example": "She had no talent for dissembling; her frustration with the platform's opaque delivery reporting was plain to everyone in the room."},
    # index 51-53
    {"word": "mercurial",     "pos": "adjective", "definition": "Subject to sudden or unpredictable changes of mood; volatile.", "example": "CTV CPMs proved mercurial throughout Q4, spiking and dropping within the same week as scatter demand surged."},
    {"word": "alacrity",      "pos": "noun",      "definition": "Brisk and cheerful readiness to do something.", "example": "The programmatic team accepted the new attribution framework with alacrity, eager to prove incrementality to the CMO."},
    {"word": "inveigh",       "pos": "verb",      "definition": "To speak or write about something with great hostility or vehement criticism.", "example": "The trade press inveighed against the lack of standardised CTV measurement as the single biggest obstacle to advertiser scale."},
    # index 54-56
    {"word": "tenacious",     "pos": "adjective", "definition": "Holding firmly to something; very determined and persistent.", "example": "The tenacious ad ops manager refused to sign off on the campaign until every creative had cleared brand safety review."},
    {"word": "perspicacity",  "pos": "noun",      "definition": "A ready insight into things; the quality of having a sharp, discerning mind.", "example": "The buyer's perspicacity allowed her to identify the underperforming CTV placements before the client's weekly report surfaced them."},
    {"word": "enumerate",     "pos": "verb",      "definition": "To mention or list a number of things one by one.", "example": "The post-mortem enumerated every creative format tested across the six-week CTV campaign."},
    # index 57-59
    {"word": "recondite",     "pos": "adjective", "definition": "Not known by many people; abstruse or dealing with obscure subject matter.", "example": "His knowledge of the recondite details of the MRC's CTV measurement standards impressed everyone in the review."},
    {"word": "tenacity",      "pos": "noun",      "definition": "The quality of being very determined and persistent; not giving up.", "example": "It was the team's tenacity in pursuing outcome-based measurement that finally won over the most sceptical client."},
    {"word": "disambiguate",  "pos": "verb",      "definition": "To remove uncertainty or confusion about the meaning of something.", "example": "The analytics team spent an hour disambiguating the client's vague definition of a 'conversion' before building the attribution report."},
    # index 60-62
    {"word": "affable",       "pos": "adjective", "definition": "Friendly and easy to talk to; warmly approachable.", "example": "The new account manager's affable manner made even the most difficult CPM conversation feel collaborative."},
    {"word": "aberration",    "pos": "noun",      "definition": "A departure from what is normal or expected; an anomaly.", "example": "The 90% completion rate on the 30-second CTV spot was an aberration — the platform average was closer to 72%."},
    {"word": "abdicate",      "pos": "verb",      "definition": "To fail to fulfill a responsibility; to give up power or a position.", "example": "By outsourcing every media decision to the agency, the brand had effectively abdicated its own data strategy."},
    # index 63-65
    {"word": "ardent",        "pos": "adjective", "definition": "Enthusiastic or passionate; strongly felt or expressed.", "example": "She was an ardent advocate for outcome-based CTV measurement long before the rest of the industry caught up."},
    {"word": "acrimony",      "pos": "noun",      "definition": "Bitterness or ill feeling; sharp hostility in speech or manner.", "example": "The merger talks collapsed under the weight of personal acrimony between the two executive teams."},
    {"word": "abjure",        "pos": "verb",      "definition": "To solemnly renounce a belief, claim, or course of action.", "example": "Under industry pressure, the platform was eventually forced to abjure its earlier position on third-party audience data."},
    # index 66-68
    {"word": "assiduous",     "pos": "adjective", "definition": "Showing great care, attentiveness, and effort; diligent.", "example": "Her assiduous analysis of the viewership data revealed a targeting gap the entire media team had missed."},
    {"word": "adage",         "pos": "noun",      "definition": "A short statement expressing a general truth; a proverb or maxim.", "example": "The old adage 'half my advertising is wasted' rings less true in CTV, where every impression is measurable and attributable."},
    {"word": "accede",        "pos": "verb",      "definition": "To agree to a demand or request; to assume a position or office.", "example": "After months of pushback, the publisher finally acceded to the advertiser's request for household-level frequency data."},
    # index 69-71
    {"word": "astute",        "pos": "adjective", "definition": "Having an ability to accurately assess situations; shrewd and clever.", "example": "The astute media buyer spotted the underpriced streaming inventory before any other agency on the media plan."},
    {"word": "aegis",         "pos": "noun",      "definition": "The protection, support, or sponsorship of a particular person or organization.", "example": "The pilot CTV campaign ran under the aegis of the agency's innovation lab before a full market rollout."},
    {"word": "accentuate",    "pos": "verb",      "definition": "To make a feature more noticeable or prominent; to emphasize.", "example": "The creative was redesigned to accentuate the product's visual appeal on large-screen streaming devices."},
    # index 72-74
    {"word": "audacious",     "pos": "adjective", "definition": "Showing a willingness to take bold, daring risks.", "example": "The audacious proposal — to move the entire linear TV budget to self-serve CTV in a single quarter — somehow got approved."},
    {"word": "affinity",      "pos": "noun",      "definition": "A natural liking or sympathy for someone or something; a connection.", "example": "Research confirmed a strong consumer affinity for brands that advertised consistently during live sports on streaming platforms."},
    {"word": "adjudicate",    "pos": "verb",      "definition": "To make a formal judgment on a disputed matter.", "example": "A neutral measurement vendor was brought in to adjudicate the discrepancy between the two attribution reports."},
    # index 75-77
    {"word": "blithe",        "pos": "adjective", "definition": "Showing a casual and cheerful indifference; carefree or unconcerned.", "example": "The media planner made the audience assumption with a blithe disregard for how significantly CTV CPMs had shifted since the plan was written."},
    {"word": "anecdote",      "pos": "noun",      "definition": "A short, amusing or interesting story about a real incident or person.", "example": "The CEO opened every agency pitch with an anecdote about a small DTC brand that had scaled profitably on self-serve CTV."},
    {"word": "ameliorate",    "pos": "verb",      "definition": "To make something bad or unsatisfactory better; to improve a situation.", "example": "The new frequency cap logic was designed to ameliorate the household overexposure problem that had been hurting ad recall scores."},
    # index 78-80
    {"word": "candid",        "pos": "adjective", "definition": "Truthful and straightforward; not afraid to speak one's mind.", "example": "His candid assessment of the CTV platform's measurement gaps was exactly what the client needed to hear before committing budget."},
    {"word": "anomaly",       "pos": "noun",      "definition": "Something that deviates from what is standard, normal, or expected.", "example": "The spike in CTV completion rates during the holiday week was flagged as an anomaly by the platform's delivery monitoring system."},
    {"word": "amplify",       "pos": "verb",      "definition": "To make larger, louder, or more significant; to expand upon.", "example": "Connected TV's large-screen format tends to amplify both the creative's strengths and its weaknesses in equal measure."},
    # index 81-83
    {"word": "circumspect",   "pos": "adjective", "definition": "Wary and careful; unwilling to take risks without due consideration.", "example": "A circumspect approach to the new identity-based targeting methodology saved the campaign from a compliance issue."},
    {"word": "aphorism",      "pos": "noun",      "definition": "A pithy observation that contains a general truth; a concise maxim.", "example": "The media team had adopted 'reach first, then optimise' as its unofficial aphorism for every new CTV campaign."},
    {"word": "annul",         "pos": "verb",      "definition": "To declare invalid; to cancel an official decision or legal arrangement.", "example": "The court moved to annul the data licensing agreement on the grounds of material misrepresentation."},
    # index 84-86
    {"word": "dauntless",     "pos": "adjective", "definition": "Showing fearlessness and determination; undaunted by difficulty.", "example": "The dauntless programmatic trader continued optimising the CTV campaign through three consecutive nights of poor delivery."},
    {"word": "aplomb",        "pos": "noun",      "definition": "Self-confidence and poise, especially when dealing with difficult situations.", "example": "She handled the client's pointed questions about brand safety adjacencies with remarkable aplomb."},
    {"word": "appease",       "pos": "verb",      "definition": "To pacify or relieve by making concessions; to satisfy a demand.", "example": "The revised measurement framework was designed to appease both the brand and the agency without fully satisfying either."},
    # index 87-89
    {"word": "deferential",   "pos": "adjective", "definition": "Showing respect and courteous submission to another's opinion or wishes.", "example": "The junior planner was deferential in client meetings but direct and confident in her written media recommendations."},
    {"word": "approbation",   "pos": "noun",      "definition": "Approval or praise, especially from an official source.", "example": "The CTV strategy launched to broad approbation from a leadership team that had spent months resisting the shift from linear."},
    {"word": "ascertain",     "pos": "verb",      "definition": "To find out for certain; to establish or determine something definitively.", "example": "Before committing the budget, the team needed to ascertain whether the platform's reach claims were independently verified."},
    # index 90-92
    {"word": "diffident",     "pos": "adjective", "definition": "Modest or shy due to a lack of self-confidence; hesitant to assert oneself.", "example": "Despite her deep expertise in programmatic buying, she remained diffident in large client presentations."},
    {"word": "archetype",     "pos": "noun",      "definition": "A very typical example; a universally recognized original model.", "example": "The performance-focused DTC brand is the archetype customer that self-serve CTV platforms were built to serve."},
    {"word": "assimilate",    "pos": "verb",      "definition": "To take in and fully understand information; to integrate into a larger group.", "example": "New media buyers were given four weeks to assimilate the platform's attribution methodology before running their first live campaign."},
    # index 93-95
    {"word": "discerning",    "pos": "adjective", "definition": "Having or showing good taste, judgment, or understanding; perceptive.", "example": "The discerning media planner will notice the gap between a platform's claimed reach and its independently verified audience figures."},
    {"word": "ardor",         "pos": "noun",      "definition": "Enthusiasm or passion; a great warmth or intensity of feeling.", "example": "The team's ardor for the CTV product more than compensated for their lack of experience in the streaming advertising space."},
    {"word": "atone",         "pos": "verb",      "definition": "To make amends for a wrong or injury; to reconcile a past failing.", "example": "The agency spent the next quarter trying to atone for the mismanaged campaign that had burned through the client's upfront budget."},
    # index 96-98
    {"word": "ebullient",     "pos": "adjective", "definition": "Cheerful and full of energy; enthusiastically exuberant.", "example": "Her ebullient pitch about CTV's incremental reach left even the most sceptical client leaning forward in their seat."},
    {"word": "artifice",      "pos": "noun",      "definition": "Clever devices or expedients used to trick someone; cunning or trickery.", "example": "Beneath the polished programmatic dashboard was a great deal of artifice and very little transparency into actual delivery."},
    {"word": "augment",       "pos": "verb",      "definition": "To make something greater by adding to it; to supplement or enhance.", "example": "The brand decided to augment its traditional linear TV buy with a self-serve CTV layer specifically targeting cord-cutters."},
    # index 99-101
    {"word": "effusive",      "pos": "adjective", "definition": "Expressing feelings of gratitude, pleasure, or approval in an unrestrained way.", "example": "The effusive case study buried the critical caveat — results were from a 90-day test, not a full campaign cycle."},
    {"word": "axiom",         "pos": "noun",      "definition": "A statement regarded as self-evidently true; an established principle or rule.", "example": "In CTV advertising, the axiom 'what gets measured gets optimised' is finally starting to have real meaning."},
    {"word": "bolster",       "pos": "verb",      "definition": "To support or strengthen; to boost confidence, morale, or a position.", "example": "The new measurement partnership was announced specifically to bolster the platform's credibility with performance-focused advertisers."},
    # index 102-104
    {"word": "fastidious",    "pos": "adjective", "definition": "Very attentive to accuracy, detail, and propriety; meticulous.", "example": "The fastidious trafficking manager verified every creative spec and tag before a single CTV impression was served."},
    {"word": "bastion",       "pos": "noun",      "definition": "A projecting part of a fortification; something that strongly defends a principle.", "example": "Premium streaming inventory remained a bastion of brand-safe ad environments in an otherwise fragmented digital landscape."},
    {"word": "broach",        "pos": "verb",      "definition": "To raise a sensitive or difficult topic for discussion for the first time.", "example": "The account manager had been waiting for the right moment to broach the subject of shifting remaining linear budget to CTV."},
    # index 105-107
    {"word": "fervent",       "pos": "adjective", "definition": "Having or displaying a passionate intensity; earnest and heartfelt.", "example": "The CMO delivered a fervent defence of the CTV investment that persuaded even the most sceptical board member."},
    {"word": "brevity",       "pos": "noun",      "definition": "Concise and exact use of words; shortness of time or duration.", "example": "The one-page campaign brief's brevity was its greatest virtue — the creative agency knew exactly what was being asked."},
    {"word": "catalyze",      "pos": "verb",      "definition": "To cause or accelerate a process or series of events.", "example": "The streaming boom catalysed a complete rethinking of how DTC brands approach upper-funnel media investment."},
    # index 108-110
    {"word": "forthright",    "pos": "adjective", "definition": "Direct and outspoken; going straight to the point without evasion.", "example": "A forthright assessment of the platform's reach limitations early on saved the brand from an embarrassing overpromise to stakeholders."},
    {"word": "cachet",        "pos": "noun",      "definition": "The state of being respected or admired; a mark of prestige or quality.", "example": "Running campaigns on premium AVOD inventory carried a cachet that generic programmatic placements simply couldn't match."},
    {"word": "censure",       "pos": "verb",      "definition": "To express severe official disapproval of someone or something.", "example": "The IAB moved to formally censure the data vendor for failing to disclose its audience measurement methodology."},
    # index 111-113
    {"word": "garrulous",     "pos": "adjective", "definition": "Excessively talkative, especially on trivial or irrelevant subjects.", "example": "The garrulous vendor representative turned a scheduled fifteen-minute demo into a ninety-minute product tour."},
    {"word": "catalyst",      "pos": "noun",      "definition": "Something that precipitates an event or accelerates a process; an agent of change.", "example": "The collapse of third-party cookies proved to be the catalyst for the industry's long-overdue pivot to first-party CTV data."},
    {"word": "codify",        "pos": "verb",      "definition": "To arrange laws, rules, or principles into a systematic code or structure.", "example": "The measurement team finally codified its attribution methodology into a document that any client or partner could review."},
    # index 114-116
    {"word": "genial",        "pos": "adjective", "definition": "Friendly and cheerful; pleasantly warm and good-natured.", "example": "The new account director's genial manner made even tense CPM renegotiations feel constructive rather than adversarial."},
    {"word": "caveat",        "pos": "noun",      "definition": "A warning or proviso about the conditions or limits of something.", "example": "The agency recommended the CTV strategy, with the caveat that results would require a three-month learning period to interpret."},
    {"word": "compel",        "pos": "verb",      "definition": "To force or oblige someone to do something; to drive irresistibly.", "example": "The incrementality data was compelling enough to compel even the most linear-loyal media directors to reconsider their budget split."},
    # index 117-119
    {"word": "haughty",       "pos": "adjective", "definition": "Arrogantly superior and disdainful; having a high opinion of oneself.", "example": "The haughty DSP representative spent more time dismissing competitors than explaining his own platform's actual capabilities."},
    {"word": "chasm",         "pos": "noun",      "definition": "A deep fissure; a profound difference between people, views, or groups.", "example": "There remained a chasm between what CTV platforms promised in terms of measurement transparency and what they could actually deliver."},
    {"word": "concede",       "pos": "verb",      "definition": "To admit that something is true; to yield a point or cede territory.", "example": "The VP conceded that the original CTV budget allocation had been far too conservative given the platform's measurable incrementality."},
    # index 120-122
    {"word": "imperious",     "pos": "adjective", "definition": "Assuming power or authority without justification; domineering and arrogant.", "example": "His imperious style during the upfront negotiation put the network's sales team on edge from the opening minute."},
    {"word": "chicanery",     "pos": "noun",      "definition": "The use of trickery, deception, or sharp practice to achieve a goal.", "example": "The audit revealed years of impression inflation that amounted to financial chicanery buried deep in the delivery reports."},
    {"word": "confound",      "pos": "verb",      "definition": "To cause surprise or confusion in someone; to prove an expectation wrong.", "example": "The self-serve CTV startup confounded every analyst by out-growing the established DSPs in its first year of operation."},
    # index 123-125
    {"word": "implacable",    "pos": "adjective", "definition": "Unable to be appeased, satisfied, or placated; relentlessly determined.", "example": "She faced implacable resistance from the linear TV buying team as she pushed to redirect budget toward streaming."},
    {"word": "corollary",     "pos": "noun",      "definition": "A practical consequence that follows naturally from something else.", "example": "A natural corollary of the streaming boom is that the linear TV scatter market has become structurally weaker."},
    {"word": "consolidate",   "pos": "verb",      "definition": "To combine several things into a single more effective whole; to make secure.", "example": "The platform consolidated its four separate DSP integrations into a single self-serve buying interface."},
    # index 126-128
    {"word": "impudent",      "pos": "adjective", "definition": "Not showing due respect; boldly rude or impertinent.", "example": "The impudent junior planner cc'd the CMO on his reply to the agency lead's media recommendation."},
    {"word": "crucible",      "pos": "noun",      "definition": "A place or situation of severe test or trial; a melting pot.", "example": "The first open beta was a crucible that exposed every weak point in the platform's self-serve campaign workflow."},
    {"word": "contemplate",   "pos": "verb",      "definition": "To think carefully and at length about something; to look thoughtfully at.", "example": "She spent the morning contemplating whether to add a retargeting layer or let the CTV campaign run to a clean prospecting pool."},
    # index 129-131
    {"word": "inveterate",    "pos": "adjective", "definition": "Having a particular habit or interest firmly established; habitual or deeply ingrained.", "example": "As an inveterate early riser, she was always the first to spot overnight delivery anomalies in the campaign dashboard."},
    {"word": "decorum",       "pos": "noun",      "definition": "Behavior or language in keeping with good taste, propriety, and dignity.", "example": "The moderator struggled to maintain decorum as the measurement debate between the two competing vendors grew increasingly heated."},
    {"word": "contend",       "pos": "verb",      "definition": "To struggle to surmount a difficulty; to assert or maintain a position.", "example": "The programmatic team had to contend with three separate measurement discrepancies before the campaign could officially close."},
    # index 132-134
    {"word": "judicious",     "pos": "adjective", "definition": "Having or showing good judgment; sensible and prudent.", "example": "A judicious mix of CTV and social retargeting drove full-funnel results that neither channel could have achieved alone."},
    {"word": "deluge",        "pos": "noun",      "definition": "A severe flood; an overwhelming quantity or amount of something.", "example": "The self-serve platform's launch triggered a deluge of support tickets that took the customer success team two weeks to clear."},
    {"word": "corroborate",   "pos": "verb",      "definition": "To confirm or give support to a statement or theory with evidence.", "example": "The incrementality study corroborated the attribution platform's claim that CTV was driving 25% incremental conversions above the base."},
    # index 135-137
    {"word": "lachrymose",    "pos": "adjective", "definition": "Tearful or given to weeping; mournful and sad.", "example": "The lachrymose tone of the year-end agency review accurately reflected how difficult the measurement conversations had been."},
    {"word": "desideratum",   "pos": "noun",      "definition": "Something that is needed or wanted; an essential requirement.", "example": "Independent, cross-platform reach deduplication is the primary desideratum for any serious CTV media plan."},
    {"word": "crystallize",   "pos": "verb",      "definition": "To make a plan or idea clear and definite; to assume a fixed and clear form.", "example": "The head-to-head platform test helped crystallize which CTV partner would earn the lion's share of the upfront commitment."},
    # index 138-140
    {"word": "loquacious",    "pos": "adjective", "definition": "Tending to talk a great deal; very talkative or rambling.", "example": "The loquacious vendor rep ran the platform demo thirty minutes over time and still hadn't reached the reporting section."},
    {"word": "diatribe",      "pos": "noun",      "definition": "A forceful and bitter verbal attack or tirade against someone or something.", "example": "What started as a constructive campaign debrief quickly became a diatribe about the platform's persistent measurement opacity."},
    {"word": "cultivate",     "pos": "verb",      "definition": "To develop a quality or skill; to nurture a relationship or environment.", "example": "She had spent years cultivating publisher relationships that proved invaluable when premium streaming inventory became scarce."},
    # index 141-143
    {"word": "magnanimous",   "pos": "adjective", "definition": "Generous or forgiving, especially toward rivals or those less powerful.", "example": "The magnanimous agency lead shared her team's CTV playbook with a smaller competitor, knowing a rising tide lifts all boats."},
    {"word": "dichotomy",     "pos": "noun",      "definition": "A division or contrast between two opposing things.", "example": "The study highlighted a stark dichotomy between what CTV platforms claimed in terms of unique reach and what independent vendors verified."},
    {"word": "delineate",     "pos": "verb",      "definition": "To describe or indicate something precisely; to portray clearly.", "example": "The campaign brief delineated each channel's role precisely: CTV for reach, social for retargeting, search for conversion."},
    # index 144-146
    {"word": "obdurate",      "pos": "adjective", "definition": "Stubbornly refusing to change one's opinion or course of action.", "example": "Despite compelling incrementality data, the obdurate CMO refused to reduce the linear TV budget by even ten percent."},
    {"word": "dissonance",    "pos": "noun",      "definition": "A lack of harmony; tension or conflict between two elements.", "example": "There was uncomfortable dissonance between the platform's brand-safety promises and the actual content adjacencies logged during the campaign."},
    {"word": "demarcate",     "pos": "verb",      "definition": "To set the boundaries or limits of something; to mark a clear distinction.", "example": "The new measurement framework clearly demarcated which conversions could be attributed to CTV and which remained statistically unresolved."},
    # index 147-149
    {"word": "officious",     "pos": "adjective", "definition": "Asserting authority in an annoyingly overbearing or domineering way; meddlesome.", "example": "The officious brand safety officer rejected three creatives on technicalities that had no bearing on actual audience risk."},
    {"word": "dossier",       "pos": "noun",      "definition": "A collection of documents about a particular person, subject, or event.", "example": "Before the upfront meeting, the agency assembled a detailed dossier on each publisher's audience overlap, CPM trends, and delivery history."},
    {"word": "deprecate",     "pos": "verb",      "definition": "To express disapproval of; to strongly criticize or belittle.", "example": "The platform deprecated its legacy pixel-based tracking system in favour of a server-side attribution approach."},
    # index 150-152
    {"word": "perfidious",    "pos": "adjective", "definition": "Deceitful and untrustworthy; guilty of betrayal.", "example": "The perfidious data vendor had been selling overlapping audience segments to competing clients without disclosing the conflict."},
    {"word": "efficacy",      "pos": "noun",      "definition": "The ability to produce a desired or intended result; effectiveness.", "example": "The study measured the efficacy of CTV retargeting by comparing conversion rates against a matched holdout group."},
    {"word": "diffuse",       "pos": "verb",      "definition": "To spread over a wide area; to reduce tension or concentration gradually.", "example": "The account director stepped in to diffuse the tension between the client and the platform's measurement team."},
    # index 153-155
    {"word": "pertinacious",  "pos": "adjective", "definition": "Holding firmly to an opinion or a course of action; stubbornly persistent.", "example": "The pertinacious media buyer refused to accept the platform's default reporting until she had received the underlying delivery logs."},
    {"word": "elegance",      "pos": "noun",      "definition": "The quality of being pleasingly refined, tasteful, and ingeniously simple.", "example": "The solution's elegance lay in combining CTV viewership data with first-party purchase signals to build a single high-intent audience."},
    {"word": "discern",       "pos": "verb",      "definition": "To recognize or find out; to perceive something that is not immediately obvious.", "example": "It took careful analysis to discern whether the CTV lift was real or an artefact of the attribution methodology."},
    # index 156-158
    {"word": "phlegmatic",    "pos": "adjective", "definition": "Having an unemotional, calm, and stoic temperament; not easily excited.", "example": "His phlegmatic reaction to the unexpected CPM spike allowed him to reallocate budget rationally while the rest of the team panicked."},
    {"word": "eloquence",     "pos": "noun",      "definition": "Fluent, persuasive, and expressive speech or writing.", "example": "The brevity and eloquence of the campaign brief left the creative agency with no excuse for an off-strategy execution."},
    {"word": "dispel",        "pos": "verb",      "definition": "To make a doubt, fear, or misconception disappear; to drive away.", "example": "A well-designed incrementality test was enough to dispel most of the board's scepticism about CTV's contribution to revenue."},
    # index 159-161
    {"word": "querulous",     "pos": "adjective", "definition": "Complaining in a petulant or whining manner; habitually complaining.", "example": "The querulous tone of the client's weekly emails made it clear the campaign performance was not meeting expectations."},
    {"word": "emissary",      "pos": "noun",      "definition": "A person sent as a diplomatic agent on a special mission.", "example": "The holding company sent a senior emissary to negotiate more favourable programmatic rates ahead of the upfront commitments."},
    {"word": "distill",       "pos": "verb",      "definition": "To extract the most important aspects; to purify through concentration.", "example": "The analyst's job was to distill three months of CTV performance data into a single executive slide the CMO could act on."},
    # index 162-164
    {"word": "reticent",      "pos": "adjective", "definition": "Not revealing one's thoughts or feelings readily; reserved and restrained.", "example": "He was uncharacteristically reticent in the platform debrief, offering only short answers to the team's direct questions."},
    {"word": "epiphany",      "pos": "noun",      "definition": "A moment of sudden and great revelation or insight.", "example": "The epiphany came during a routine attribution review — the brand's CTV and social audiences overlapped by less than 12%."},
    {"word": "diverge",       "pos": "verb",      "definition": "To develop in a different direction from another; to differ.", "example": "The two CTV strategies had started from the same brief but diverged significantly after the first round of in-flight creative testing."},
    # index 165-167
    {"word": "sagacious",     "pos": "adjective", "definition": "Having or showing good judgment; wise and discerning.", "example": "The sagacious media director resisted the temptation to chase raw reach and focused instead on household frequency control."},
    {"word": "ethos",         "pos": "noun",      "definition": "The characteristic spirit of a culture, era, or community; its guiding beliefs.", "example": "The team's ethos — 'measure everything, assume nothing' — made it a natural fit for a performance-driven CTV brief."},
    {"word": "edify",         "pos": "verb",      "definition": "To instruct or improve someone morally or intellectually.", "example": "The workshop was designed less to sell the platform than to genuinely edify clients about the principles of CTV measurement."},
    # index 168-170
    {"word": "sycophantic",   "pos": "adjective", "definition": "Behaving in an obsequious, servile way to gain favor; fawning.", "example": "The sycophantic applause for every new platform feature made it hard for the product team to receive genuine critical feedback."},
    {"word": "exuberance",    "pos": "noun",      "definition": "The quality of being full of energy, excitement, and cheerfulness.", "example": "The team's exuberance about the platform's new self-serve targeting tools masked some legitimate concerns about scale in smaller markets."},
    {"word": "embellish",     "pos": "verb",      "definition": "To make more attractive by adding detail; to exaggerate for effect.", "example": "The vendor's case study had been so embellished that the actual campaign performance bore little resemblance to the headline ROAS figure."},
    # index 171-173
    {"word": "taciturn",      "pos": "adjective", "definition": "Reserved; saying little; not inclined to talk or share opinions.", "example": "The taciturn data scientist said almost nothing in the meeting, but her single question about the holdout methodology stopped the room cold."},
    {"word": "fallacy",       "pos": "noun",      "definition": "A mistaken belief; a failure in reasoning that undermines an argument.", "example": "The report exposed the central fallacy in the argument that linear TV reach was interchangeable with streaming audience delivery."},
    {"word": "embolden",      "pos": "verb",      "definition": "To give someone the courage or confidence to do something.", "example": "Early strong results on the self-serve platform emboldened the brand to triple its CTV investment in the following quarter."},
    # index 174-176
    {"word": "truculent",     "pos": "adjective", "definition": "Eager or quick to argue or fight; aggressively defiant.", "example": "The truculent client turned every weekly optimisation call into a debate about the campaign's fundamental strategy."},
    {"word": "finesse",       "pos": "noun",      "definition": "Intricate and refined skill in handling a delicate or difficult situation.", "example": "Negotiating premium CTV inventory during the upfront requires a certain finesse that not every media buyer develops quickly."},
    {"word": "emulate",       "pos": "verb",      "definition": "To match or surpass someone by imitation; to follow as a model.", "example": "The challenger brand openly set out to emulate the streaming advertising playbook of its category-leading rival."},
    # index 177-179
    {"word": "unflappable",   "pos": "adjective", "definition": "Having or showing calmness in a crisis; not easily agitated or alarmed.", "example": "The unflappable campaign manager kept the team on track even as creative revisions doubled the trafficking workload overnight."},
    {"word": "foible",        "pos": "noun",      "definition": "A minor weakness or eccentricity in someone's character; a small failing.", "example": "His habit of checking delivery reports at midnight was a well-known foible, but it had saved more than one campaign from going dark."},
    {"word": "encapsulate",   "pos": "verb",      "definition": "To express the essential features of something succinctly; to enclose.", "example": "The single-sentence creative brief perfectly encapsulated what the CTV spot needed to achieve in its first three seconds."},
    # index 180-182
    {"word": "venerable",     "pos": "adjective", "definition": "Accorded a great deal of respect, especially because of age, wisdom, or character.", "example": "The venerable broadcast network was adapting slowly but seriously to the self-serve streaming advertising model."},
    {"word": "fortitude",     "pos": "noun",      "definition": "Courage and resilience in the face of pain or adversity; mental strength.", "example": "It took real fortitude to push the all-in CTV strategy through in the face of sustained pushback from the linear TV buying team."},
    {"word": "engender",      "pos": "verb",      "definition": "To cause or give rise to a situation, feeling, or condition.", "example": "The shift to outcome-based CTV buying engendered genuine collaboration between the media, data science, and creative teams."},
    # index 183-185
    {"word": "verbose",       "pos": "adjective", "definition": "Using or expressed in more words than are needed; wordy.", "example": "The verbose platform specification document made it nearly impossible to identify which campaign settings actually mattered."},
    {"word": "fruition",      "pos": "noun",      "definition": "The realization or fulfillment of a plan or project; coming to maturity.", "example": "After two years of product development, the self-serve CTV vision finally came to fruition at the annual upfront presentation."},
    {"word": "entrench",      "pos": "verb",      "definition": "To establish something so firmly that change is difficult; to embed deeply.", "example": "Years of reliance on GRP-based metrics had entrenched habits that the new outcome-focused CTV framework struggled to displace."},
    # index 186-188
    {"word": "vigilant",      "pos": "adjective", "definition": "Keeping careful watch for possible danger or difficulties; alert.", "example": "Staying vigilant about brand safety adjacencies in streaming content is a daily operational responsibility, not a one-time platform setting."},
    {"word": "gambit",        "pos": "noun",      "definition": "An action intended to gain an advantage, especially at the outset of a situation.", "example": "Opening the upfront negotiation with an extreme rate anchor was a classic gambit, and both sides knew exactly what was happening."},
    {"word": "epitomize",     "pos": "verb",      "definition": "To be a perfect example of a quality or type; to summarize or exemplify.", "example": "The DTC brand's performance CTV strategy epitomised exactly the outcome-based approach the platform had been built to enable."},
    # index 189-191
    {"word": "wistful",       "pos": "adjective", "definition": "Having or showing a feeling of vague, tender longing; yearningly nostalgic.", "example": "The veteran buyer cast a wistful glance at the old upfront order form, remembering when the entire market could be planned on a single spreadsheet."},
    {"word": "genesis",       "pos": "noun",      "definition": "The origin or beginning of something; the point at which it came into being.", "example": "The genesis of the platform lay in the founders' deep frustration with the opacity and inefficiency of traditional TV buying."},
    {"word": "espouse",       "pos": "verb",      "definition": "To adopt or support a cause or belief; to advocate strongly for.", "example": "She had espoused outcome-based CTV buying for years before the rest of the industry finally caught up."},
    # index 192-194
    {"word": "zealous",       "pos": "adjective", "definition": "Having or showing great energy or enthusiasm in pursuit of a cause or goal.", "example": "The zealous new campaign manager had already optimised the audience segments before the creative had even been approved."},
    {"word": "harbinger",     "pos": "noun",      "definition": "A person or thing that announces or signals the approach of another.", "example": "The sharp multi-quarter decline in linear TV ratings was the harbinger of the budget migration to streaming that followed."},
    {"word": "exhort",        "pos": "verb",      "definition": "To strongly encourage or urge someone to do something.", "example": "The agency VP exhorted the media team to develop CTV expertise before their clients found the platform without them."},
    # index 195-197
    {"word": "acerbic",       "pos": "adjective", "definition": "Sharp and forthright; having a bitter, cutting quality in speech or manner.", "example": "His acerbic commentary on the walled-garden data practices was entertaining to the trade press, though considerably less so to the platforms."},
    {"word": "hegemony",      "pos": "noun",      "definition": "Leadership or dominance of one group over others in a particular domain.", "example": "The new entrant's rapid growth threatened the incumbent DSP's long-standing hegemony in programmatic CTV buying."},
    {"word": "expedite",      "pos": "verb",      "definition": "To make an action or process happen sooner; to speed up or accelerate.", "example": "The immovable Q4 launch date meant every effort was made to expedite the creative approval and trafficking process."},
    # index 198-200
    {"word": "apposite",      "pos": "adjective", "definition": "Apt in the circumstances or in relation to something; highly pertinent.", "example": "His remark about diminishing returns on reach was oddly apposite given the frequency-cap debate that erupted immediately after."},
    {"word": "impasse",       "pos": "noun",      "definition": "A situation in which no progress is possible; a deadlock.", "example": "The upfront negotiation reached an impasse when neither the agency nor the streaming network would move on CPM floors."},
    {"word": "explicate",     "pos": "verb",      "definition": "To analyze and develop an idea in detail; to explain clearly and fully.", "example": "The data scientist spent thirty minutes explicating the difference between multi-touch attribution and incrementality testing for the client."},
    # index 201-203
    {"word": "auspicious",    "pos": "adjective", "definition": "Giving or indicating a good chance of success; favorable.", "example": "Closing the largest self-serve CTV deal in the company's history on day one was an auspicious start for the new VP of Sales."},
    {"word": "imperative",    "pos": "noun",      "definition": "An essential or urgent thing; an authoritative command or rule.", "example": "In a fragmented streaming landscape, a first-party data strategy is a competitive imperative, not an optional future initiative."},
    {"word": "extrapolate",   "pos": "verb",      "definition": "To extend a conclusion or trend to an unknown situation beyond the data.", "example": "You can't safely extrapolate from three months of CTV data what the full-year incrementality picture will look like."},
    # index 204-206
    {"word": "capacious",     "pos": "adjective", "definition": "Having a lot of space inside; roomy; able to hold a great deal.", "example": "The capacious war room was commandeered for the final two weeks of Q4 campaign trafficking."},
    {"word": "largesse",      "pos": "noun",      "definition": "Generosity in bestowing money, gifts, or favors; liberality.", "example": "The streaming network's year-end largesse extended to bonus impressions for every client who had met their upfront commitments."},
    {"word": "facilitate",    "pos": "verb",      "definition": "To make an action, process, or interaction easier or smoother.", "example": "The new integration was designed to facilitate seamless audience syncing between the brand's CRM and the CTV buying platform."},
    # index 207-209
    {"word": "caustic",       "pos": "adjective", "definition": "Sarcastic in a scathing way; able to destroy or damage through sharp speech.", "example": "The caustic trade press review of the platform's new targeting product was pointed, but its core technical criticism was accurate."},
    {"word": "lexicon",       "pos": "noun",      "definition": "The vocabulary of a person, language, or branch of knowledge.", "example": "The onboarding guide introduced new advertisers to the platform's extensive lexicon — from 'completion rate' to 'household frequency cap.'"},
    {"word": "fathom",        "pos": "verb",      "definition": "To understand something after much thought; to comprehend fully.", "example": "She couldn't fathom why the team had launched the CTV campaign without setting household frequency caps from day one."},
    # index 210-212
    {"word": "clandestine",   "pos": "adjective", "definition": "Kept secret, especially because illicit or potentially damaging.", "example": "The clandestine data-sharing arrangement between the two publishers was uncovered during a routine compliance audit."},
    {"word": "lore",          "pos": "noun",      "definition": "A body of traditions, knowledge, or stories held by a particular group.", "example": "Every long-tenured programmatic trader at the agency carried irreplaceable institutional lore about which streaming publishers actually delivered on their guarantees."},
    {"word": "forestall",     "pos": "verb",      "definition": "To prevent something from happening by taking action in advance; to preempt.", "example": "The detailed pre-campaign FAQ was written specifically to forestall the attribution questions that always emerged mid-flight."},
    # index 213-215
    {"word": "contentious",   "pos": "adjective", "definition": "Causing or likely to cause argument or controversy; disputed.", "example": "The contentious decision to move 40% of the linear budget to self-serve CTV divided the media planning team for months."},
    {"word": "maelstrom",     "pos": "noun",      "definition": "A powerful whirlpool; a situation of confused, violent, or turbulent activity.", "example": "The ad tech consolidation wave dropped the agency into a maelstrom of renegotiated contracts and competing platform claims."},
    {"word": "formulate",     "pos": "verb",      "definition": "To create or prepare a strategy, plan, or idea in a systematic way.", "example": "The strategist spent two weeks formulating a competitive response to the rival platform's self-serve product announcement."},
    # index 216-218
    {"word": "decorous",      "pos": "adjective", "definition": "In keeping with good taste, propriety, and dignity; proper and seemly.", "example": "The handover between the outgoing and incoming media agency was decorous and professional, even given the difficult circumstances."},
    {"word": "malaise",       "pos": "noun",      "definition": "A general feeling of discomfort, unease, or lack of wellbeing; dissatisfaction.", "example": "A subtle malaise had settled over the linear TV sales team after three consecutive quarters of declining upfront commitments."},
    {"word": "fortify",       "pos": "verb",      "definition": "To make stronger or more resistant; to strengthen mentally or physically.", "example": "The pre-brief session was designed to fortify the team's confidence before a high-stakes review of six months of CTV performance."},
    # index 219-221
    {"word": "dilatory",      "pos": "adjective", "definition": "Slow to act; intended to cause delay; not prompt.", "example": "The publisher's dilatory response to the frequency cap request allowed the campaign's household overexposure to worsen significantly."},
    {"word": "manifesto",     "pos": "noun",      "definition": "A public declaration of intentions, policies, or views issued by a person or group.", "example": "The programmatic team published a short manifesto setting out its principles for transparent, outcome-based CTV buying."},
    {"word": "foment",        "pos": "verb",      "definition": "To instigate or stir up trouble, rebellion, or discord.", "example": "The anonymous trade post was widely seen as an attempt to foment distrust between advertisers and the streaming measurement platforms."},
    # index 222-224
    {"word": "doleful",       "pos": "adjective", "definition": "Expressing sorrow or misery; mournful and sad.", "example": "The doleful tone of the mid-campaign report accurately reflected how far performance had fallen short of the initial projections."},
    {"word": "minutiae",      "pos": "noun",      "definition": "The small, precise, or trivial details of something; fine points.", "example": "He was so absorbed in the minutiae of the insertion order that he missed the problematic CPM floor buried in the headline clause."},
    {"word": "garner",        "pos": "verb",      "definition": "To gather or collect; to acquire or earn something, especially gradually.", "example": "The self-serve CTV platform had garnered over a thousand active advertisers before it officially exited beta."},
    # index 225-227
    {"word": "eclectic",      "pos": "adjective", "definition": "Deriving ideas, style, or taste from a broad and diverse range of sources.", "example": "Her eclectic background — spanning linear TV, programmatic display, and performance marketing — made her uniquely suited for the head of CTV role."},
    {"word": "nexus",         "pos": "noun",      "definition": "A connection or series of connections; the central and most important point.", "example": "The demand-side platform had positioned itself as the nexus through which an entire ecosystem's CTV inventory and audience data would flow."},
    {"word": "glean",         "pos": "verb",      "definition": "To obtain information or understanding bit by bit from various sources.", "example": "From the sparse delivery logs, she was able to glean that the campaign had been consistently pacing behind its daily impression target."},
    # index 228-230
    {"word": "egregious",     "pos": "adjective", "definition": "Outstandingly bad; shocking in its severity or magnitude.", "example": "The egregious brand safety failure — ads served adjacent to extremist content — had been sitting in the delivery logs undetected for a full week."},
    {"word": "nuance",        "pos": "noun",      "definition": "A subtle difference in meaning, expression, or tone; a fine distinction.", "example": "The best measurement partners were the ones who could grasp the nuance between reach overlap and truly incremental, unduplicated reach."},
    {"word": "grapple",       "pos": "verb",      "definition": "To struggle to overcome a problem or difficulty; to wrestle with.", "example": "The ad tech team had been grappling with the same cross-device identity resolution problem for two consecutive quarters."},
    # index 231-233
    {"word": "elusive",       "pos": "adjective", "definition": "Difficult to find, catch, or achieve; tending to evade grasp or understanding.", "example": "True cross-platform, deduplicated reach measurement remained elusive despite dozens of industry-led attempts to standardise it."},
    {"word": "onus",          "pos": "noun",      "definition": "Something that is one's duty or responsibility; a burden.", "example": "The onus to prove CTV's incremental contribution to revenue fell squarely on the team that had recommended the budget shift."},
    {"word": "impede",        "pos": "verb",      "definition": "To delay or block the progress or action of; to obstruct.", "example": "Misaligned KPIs between the brand and the agency impeded progress on the shared CTV measurement framework for weeks."},
    # index 234-236
    {"word": "enigmatic",     "pos": "adjective", "definition": "Difficult to interpret or understand; mysterious and puzzling.", "example": "The CEO's enigmatic comments about the platform's forthcoming measurement product left analysts and advertisers with more questions than answers."},
    {"word": "paradigm",      "pos": "noun",      "definition": "A typical example or pattern; a framework of ideas, assumptions, or practices.", "example": "The shift from appointment viewing to on-demand streaming fundamentally changed the paradigm within which media planners had operated for two decades."},
    {"word": "infer",         "pos": "verb",      "definition": "To deduce or conclude something from evidence and reasoning rather than explicit statement.", "example": "From the sharp drop in delivery volume, she inferred that the audience segment had been exhausted well ahead of the campaign's scheduled end."},
    # index 237-239
    {"word": "equivocal",     "pos": "adjective", "definition": "Open to more than one interpretation; ambiguous or uncertain.", "example": "The platform's equivocal response to questions about third-party measurement access left agency buyers uncertain how to proceed."},
    {"word": "paradox",       "pos": "noun",      "definition": "A seemingly contradictory statement that may nonetheless be true; a self-contradiction.", "example": "The CTV paradox — that premium, brand-safe inventory often underperforms on short-term direct-response metrics — is well documented but rarely discussed openly."},
    {"word": "instigate",     "pos": "verb",      "definition": "To bring about or initiate an action or event, especially a problematic one; to provoke.", "example": "Nobody could agree on who had instigated the move from GRP-based to outcome-based measurement, but everyone agreed it was long overdue."},
    # index 240-242
    {"word": "esoteric",      "pos": "adjective", "definition": "Intended for or understood by only a small, specialized group; highly specialized.", "example": "Her knowledge of the esoteric details of the MRC's viewability and invalid traffic standards proved invaluable during the platform audit."},
    {"word": "prerogative",   "pos": "noun",      "definition": "A right or privilege exclusive to a particular person or group.", "example": "Setting the KPI framework before the campaign goes live is the client's prerogative; hitting it is the agency's."},
    {"word": "invoke",        "pos": "verb",      "definition": "To cite or appeal to something as an authority or justification; to call upon.", "example": "The media buyer invoked the platform's contractual make-good clause when the end-of-month delivery reports came in significantly short."},
    # index 243-245
    {"word": "immutable",     "pos": "adjective", "definition": "Unchanging over time or incapable of being changed; permanent.", "example": "The one immutable rule on the team was that no CTV campaign could go live without an independent third-party measurement tag in place."},
    {"word": "provenance",    "pos": "noun",      "definition": "The place of origin or source of something; a record of ownership or history.", "example": "Knowing the provenance of the audience segment data was essential before any targeting decision could be made with confidence."},
    {"word": "marshal",       "pos": "verb",      "definition": "To arrange or organize people, arguments, or resources effectively and efficiently.", "example": "She marshaled every available piece of incrementality evidence before presenting the CTV business case to a sceptical board."},
    # index 246-248
    {"word": "incongruous",   "pos": "adjective", "definition": "Not in harmony with the surrounding or other elements; out of place.", "example": "The formal upfront contract language felt incongruous on a self-serve platform that prided itself on accessibility and speed."},
    {"word": "rapprochement", "pos": "noun",      "definition": "The reestablishment of harmonious relations after a period of conflict or estrangement.", "example": "The joint measurement initiative served as a rapprochement after two years of public tension between the agency coalition and the streaming publishers."},
    {"word": "navigate",      "pos": "verb",      "definition": "To plan or direct a route through a complex environment; to find a way through.", "example": "Learning to navigate the self-serve platform's audience targeting and frequency control tools was a skill that took most buyers several weeks to develop."},
    # index 249-251
    {"word": "ineffable",     "pos": "adjective", "definition": "Too great or extreme to be expressed in words; defying description.", "example": "There is an ineffable satisfaction in watching a CTV campaign's incrementality numbers come back exactly as the team had predicted."},
    {"word": "rancor",        "pos": "noun",      "definition": "Bitterness or resentfulness that has built up over time; long-standing ill will.", "example": "The rancor from the original attribution dispute never fully dissipated, even after the joint measurement framework was formally agreed."},
    {"word": "obviate",       "pos": "verb",      "definition": "To remove a need or difficulty; to prevent a problem from arising.", "example": "A clear measurement plan agreed before launch would have obviated the entire attribution argument at the campaign's close."},
    # index 252-254
    {"word": "inexorable",    "pos": "adjective", "definition": "Impossible to stop or prevent; continuing without any possibility of being changed.", "example": "The inexorable shift of viewing hours from linear TV to streaming has made CTV investment a strategic necessity rather than an experiment."},
    {"word": "recourse",      "pos": "noun",      "definition": "A source of help in a difficult situation; the right to take legal action.", "example": "Without a clear escalation process, advertisers had no meaningful recourse when a platform's delivery fell consistently short of its guarantees."},
    {"word": "ostracize",     "pos": "verb",      "definition": "To exclude from a society, group, or activity; to shun or banish.", "example": "The agency informally ostracised any vendor caught misrepresenting delivery data, regardless of how competitive their rates were."},
    # index 255-257
    {"word": "insipid",       "pos": "adjective", "definition": "Lacking flavor, vigor, or interest; dull and unexciting.", "example": "The insipid 30-second spot — a direct lift from the linear version — failed to hold attention past the first five seconds on streaming devices."},
    {"word": "reprieve",      "pos": "noun",      "definition": "A cancellation or postponement of a punishment or difficulty; temporary relief.", "example": "The Q4 budget extension was a welcome reprieve for the CTV team, but the pressure to show measurable results was unrelenting."},
    {"word": "interpolate",   "pos": "verb",      "definition": "To insert something between existing elements; to estimate values between known data points.", "example": "The measurement model was designed to interpolate viewership estimates for small audience segments where direct measurement data was unavailable."},
    # index 258-260
    {"word": "lucid",         "pos": "adjective", "definition": "Expressed clearly and easily understood; mentally clear and rational.", "example": "The most lucid explanation of the platform's attribution model came not from the documentation but from a ten-minute walkthrough with the data team."},
    {"word": "resonance",     "pos": "noun",      "definition": "The quality of evoking a response; the ability to evoke significance or meaning.", "example": "The campaign's resonance with cord-cutting households surprised even the creative team that had produced the spot."},
    {"word": "kindle",        "pos": "verb",      "definition": "To light a fire; to arouse or inspire a feeling or quality.", "example": "The streaming platform's entry into self-serve advertising kindled a competitive intensity the market hadn't seen since the early days of programmatic."},
]

# ── Shared style values ────────────────────────────────────────────────────────

_FONT = "'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"
_TEXT = f"font-family:{_FONT};color:#1a202c"

# ── HTML helpers ───────────────────────────────────────────────────────────────

def _cap_sentences(text: str, n: int) -> str:
    parts = re.split(r'(?<=[.!?])\s+', text.strip(), maxsplit=n)
    return ' '.join(parts[:n])


def _exec_summary_html(text: str) -> str:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
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
    word_entry = WORDS_OF_THE_DAY[_weekday_index % len(WORDS_OF_THE_DAY)]
    word_block_inner = (
        f'<div style="font-size:22px;font-weight:800;color:#f07030;letter-spacing:-.3px;'
        f'font-family:{_FONT}">{word_entry["word"]}</div>'
        f'<div style="font-style:italic;color:#6b7280;font-size:11px;margin-top:4px;'
        f'font-family:{_FONT}">{word_entry["pos"]}</div>'
        f'<div style="color:#c9d1d9;font-size:13px;line-height:1.55;margin-top:9px;'
        f'font-family:{_FONT}">{word_entry["definition"]}</div>'
        f'<div style="font-style:italic;color:#8895a7;font-size:12px;line-height:1.5;'
        f'margin-top:8px;font-family:{_FONT}">&ldquo;{word_entry["example"]}&rdquo;</div>'
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

  <!-- Word of the Day -->
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
