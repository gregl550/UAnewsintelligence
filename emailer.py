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
    {"word": "ephemeral",     "pos": "adjective", "definition": "Lasting for a very short time; transitory.", "example": "The morning mist was ephemeral, burning off within an hour of sunrise."},
    {"word": "exigency",      "pos": "noun",      "definition": "An urgent need or demand requiring immediate action.", "example": "The exigency of the situation demanded an immediate response from leadership."},
    {"word": "ruminate",      "pos": "verb",      "definition": "To think deeply and at length about something; to ponder.", "example": "He spent the evening ruminating on everything that could go wrong before the launch."},
    # index 3-5
    {"word": "laconic",       "pos": "adjective", "definition": "Using very few words; brief and concise in speech or expression.", "example": "Her laconic reply — a single nod — told him everything he needed to know."},
    {"word": "impetus",       "pos": "noun",      "definition": "A force or energy that makes something happen or happen faster.", "example": "The new funding gave the research team the impetus it needed to push forward."},
    {"word": "galvanize",     "pos": "verb",      "definition": "To shock or excite someone into taking action; to stimulate into activity.", "example": "The documentary galvanized thousands of viewers into volunteering at local shelters."},
    # index 6-8
    {"word": "pellucid",      "pos": "adjective", "definition": "Translucently clear; easily understood.", "example": "The pellucid water of the mountain lake revealed every stone on its bottom."},
    {"word": "equanimity",    "pos": "noun",      "definition": "Mental calmness and composure, especially in difficult situations.", "example": "She faced the diagnosis with remarkable equanimity, focusing on what she could control."},
    {"word": "coalesce",      "pos": "verb",      "definition": "To come together and form one mass or whole; to unite.", "example": "Gradually, the scattered ideas began to coalesce into a coherent strategy."},
    # index 9-11
    {"word": "sanguine",      "pos": "adjective", "definition": "Optimistic or positive, especially in a difficult situation.", "example": "Despite the setbacks, she remained sanguine about the project's eventual success."},
    {"word": "acumen",        "pos": "noun",      "definition": "The ability to make good judgments and quick decisions; shrewdness.", "example": "His business acumen allowed him to spot profitable ventures others overlooked."},
    {"word": "exacerbate",    "pos": "verb",      "definition": "To make a problem, bad situation, or negative feeling worse.", "example": "The late delivery only exacerbated tensions that had been building for weeks."},
    # index 12-14
    {"word": "mellifluous",   "pos": "adjective", "definition": "Pleasingly smooth and musical in tone or sound.", "example": "Her mellifluous voice made even the most mundane announcements sound beautiful."},
    {"word": "gravitas",      "pos": "noun",      "definition": "Dignity, seriousness, and solemnity in manner or bearing.", "example": "The judge entered the courtroom with a gravitas that immediately silenced the room."},
    {"word": "prevaricate",   "pos": "verb",      "definition": "To speak or act evasively; to avoid stating the truth directly.", "example": "He prevaricated for so long that the committee lost patience entirely."},
    # index 15-17
    {"word": "liminal",       "pos": "adjective", "definition": "Relating to a transitional or threshold state between two conditions.", "example": "The airport lounge exists in a liminal space between departure and arrival."},
    {"word": "probity",       "pos": "noun",      "definition": "The quality of having strong moral principles; complete honesty and integrity.", "example": "His reputation for probity made him the obvious choice for the ethics committee."},
    {"word": "mitigate",      "pos": "verb",      "definition": "To make something less severe, serious, or painful; to lessen the impact of.", "example": "Regular breaks can significantly mitigate the mental fatigue of long coding sessions."},
    # index 18-20
    {"word": "perspicacious", "pos": "adjective", "definition": "Having a ready insight into things; shrewd and perceptive.", "example": "The perspicacious analyst spotted the market trend months before her peers."},
    {"word": "verve",         "pos": "noun",      "definition": "Enthusiasm, energy, and vigor, especially in creative or artistic work.", "example": "She attacked the project with a verve that inspired her entire team."},
    {"word": "evince",        "pos": "verb",      "definition": "To reveal the presence of a quality, feeling, or characteristic.", "example": "Her careful preparation evinced a level of professionalism that impressed the panel."},
    # index 21-23
    {"word": "inimitable",    "pos": "adjective", "definition": "So good or unusual as to be impossible to copy; unique.", "example": "Her inimitable style made her designs immediately recognizable worldwide."},
    {"word": "serendipity",   "pos": "noun",      "definition": "The occurrence of happy or beneficial events by chance; a pleasant surprise.", "example": "It was pure serendipity that they both ended up at the same small bookshop in Paris."},
    {"word": "circumvent",    "pos": "verb",      "definition": "To find a clever way around an obstacle or rule; to bypass.", "example": "The team had to circumvent several technical limitations to make the feature work."},
    # index 24-26
    {"word": "salient",       "pos": "adjective", "definition": "Most noticeable, important, or relevant; standing out prominently.", "example": "The most salient point in his argument was the one everyone kept ignoring."},
    {"word": "propensity",    "pos": "noun",      "definition": "A natural inclination or tendency to behave in a particular way.", "example": "His propensity for procrastination often undermined his considerable talent."},
    {"word": "burnish",       "pos": "verb",      "definition": "To polish by rubbing; to enhance or improve something, especially a reputation.", "example": "Years of reliable work had burnished his standing across the industry."},
    # index 27-29
    {"word": "intrepid",      "pos": "adjective", "definition": "Fearless and adventurous; notably courageous.", "example": "The intrepid explorer ventured into the uncharted jungle with nothing but a compass."},
    {"word": "cacophony",     "pos": "noun",      "definition": "A harsh, discordant mixture of sounds.", "example": "The cacophony of the busy kitchen was oddly comforting to the veteran chef."},
    {"word": "inculcate",     "pos": "verb",      "definition": "To instill an attitude, habit, or idea by persistent instruction or repetition.", "example": "Great coaches inculcate discipline not by demanding it, but by modeling it."},
    # index 30-32
    {"word": "verdant",       "pos": "adjective", "definition": "Green with grass or other rich vegetation; lush.", "example": "The verdant hillsides of Ireland took her breath away on first sight."},
    {"word": "confluence",    "pos": "noun",      "definition": "A coming together of people, ideas, or events; the junction of two rivers.", "example": "The startup's success was a confluence of great timing, talent, and luck."},
    {"word": "beguile",       "pos": "verb",      "definition": "To charm or enchant someone, sometimes in a deceptive way.", "example": "The salesman tried to beguile them with glossy brochures and bold promises."},
    # index 33-35
    {"word": "punctilious",   "pos": "adjective", "definition": "Showing great attention to detail or correct behavior; meticulous.", "example": "The punctilious editor caught every misplaced comma in the manuscript."},
    {"word": "candor",        "pos": "noun",      "definition": "The quality of being open, honest, and direct in expression.", "example": "She appreciated his candor even when his feedback was difficult to hear."},
    {"word": "conflate",      "pos": "verb",      "definition": "To combine two or more ideas into one, often incorrectly or carelessly.", "example": "It's easy to conflate correlation with causation in data-heavy reports."},
    # index 36-38
    {"word": "cogent",        "pos": "adjective", "definition": "Clear, logical, and convincing; powerfully persuasive.", "example": "She made a cogent case for restructuring the team's workflow."},
    {"word": "ennui",         "pos": "noun",      "definition": "A feeling of listlessness and boredom arising from lack of occupation or excitement.", "example": "After months of unrelenting routine, a deep ennui had settled over the team."},
    {"word": "buttress",      "pos": "verb",      "definition": "To increase the strength of or give support to; to reinforce.", "example": "She used three separate studies to buttress her central argument."},
    # index 39-41
    {"word": "propitious",    "pos": "adjective", "definition": "Giving or indicating a good chance of success; favorable.", "example": "The clear skies and calm seas made it a propitious day to set sail."},
    {"word": "panacea",       "pos": "noun",      "definition": "A solution or remedy supposed to cure all problems or difficulties.", "example": "Remote work is no panacea for burnout, but it does offer meaningful flexibility."},
    {"word": "elicit",        "pos": "verb",      "definition": "To draw out a response, answer, or reaction from someone.", "example": "The moderator's pointed question finally elicited a direct answer from the candidate."},
    # index 42-44
    {"word": "redoubtable",   "pos": "adjective", "definition": "Formidable and inspiring respect, especially as an opponent.", "example": "The redoubtable chess champion had not lost a match in three years."},
    {"word": "penchant",      "pos": "noun",      "definition": "A strong or habitual liking for something or tendency to do it.", "example": "His penchant for bold color choices extended from his wardrobe to his design work."},
    {"word": "calibrate",     "pos": "verb",      "definition": "To carefully assess and adjust something for accuracy or effectiveness.", "example": "Before launching, they calibrated their messaging to address the most common objections."},
    # index 45-47
    {"word": "incisive",      "pos": "adjective", "definition": "Intelligently analytical and clear-thinking; cutting straight to the point.", "example": "Her incisive questions cut through the evasive answers in seconds."},
    {"word": "rectitude",     "pos": "noun",      "definition": "Morally correct behavior or thinking; righteousness.", "example": "The senator's rectitude was beyond question, even among her opponents."},
    {"word": "iterate",       "pos": "verb",      "definition": "To repeat a process, making improvements or adjustments with each cycle.", "example": "The design team iterated on the prototype for weeks before settling on a final version."},
    # index 48-50
    {"word": "evanescent",    "pos": "adjective", "definition": "Soon passing out of sight, memory, or existence; quickly fading.", "example": "The evanescent beauty of cherry blossoms makes them all the more precious."},
    {"word": "hubris",        "pos": "noun",      "definition": "Excessive pride or self-confidence, often leading to one's downfall.", "example": "His hubris led him to underestimate the competition, and he paid the price."},
    {"word": "dissemble",     "pos": "verb",      "definition": "To conceal or disguise one's true motives, feelings, or beliefs.", "example": "She had no talent for dissembling; her frustration was plain on her face."},
    # index 51-53
    {"word": "mercurial",     "pos": "adjective", "definition": "Subject to sudden or unpredictable changes of mood; volatile.", "example": "His mercurial temperament made him brilliant in the studio but difficult to manage."},
    {"word": "alacrity",      "pos": "noun",      "definition": "Brisk and cheerful readiness to do something.", "example": "She accepted the challenging assignment with alacrity, eager to prove herself."},
    {"word": "inveigh",       "pos": "verb",      "definition": "To speak or write about something with great hostility or vehement criticism.", "example": "The editorial inveighed against the policy as a betrayal of the public trust."},
    # index 54-56
    {"word": "tenacious",     "pos": "adjective", "definition": "Holding firmly to something; very determined and persistent.", "example": "The tenacious negotiator refused to leave the table until a deal was reached."},
    {"word": "perspicacity",  "pos": "noun",      "definition": "A ready insight into things; the quality of having a sharp, discerning mind.", "example": "The detective's perspicacity allowed her to see connections others had missed."},
    {"word": "enumerate",     "pos": "verb",      "definition": "To mention or list a number of things one by one.", "example": "The report enumerated every cost overrun from the past fiscal year."},
    # index 57-59
    {"word": "recondite",     "pos": "adjective", "definition": "Not known by many people; abstruse or dealing with obscure subject matter.", "example": "His lecture touched on the recondite history of early medieval cartography."},
    {"word": "tenacity",      "pos": "noun",      "definition": "The quality of being very determined and persistent; not giving up.", "example": "It was her tenacity, more than her raw talent, that carried her to the championship."},
    {"word": "disambiguate",  "pos": "verb",      "definition": "To remove uncertainty or confusion about the meaning of something.", "example": "The team spent an hour trying to disambiguate the client's vague requirements."},
    # index 60-62
    {"word": "affable",       "pos": "adjective", "definition": "Friendly and easy to talk to; warmly approachable.", "example": "The new director's affable manner quickly won over a team that had been skeptical."},
    {"word": "aberration",    "pos": "noun",      "definition": "A departure from what is normal or expected; an anomaly.", "example": "The string of losses was an aberration for a team that had dominated all season."},
    {"word": "abdicate",      "pos": "verb",      "definition": "To fail to fulfill a responsibility; to give up power or a position.", "example": "By ignoring the warning signs, management effectively abdicated its duty of care."},
    # index 63-65
    {"word": "ardent",        "pos": "adjective", "definition": "Enthusiastic or passionate; strongly felt or expressed.", "example": "She was an ardent supporter of the open-source movement long before it was mainstream."},
    {"word": "acrimony",      "pos": "noun",      "definition": "Bitterness or ill feeling; sharp hostility in speech or manner.", "example": "The negotiations collapsed under the weight of personal acrimony between the two sides."},
    {"word": "abjure",        "pos": "verb",      "definition": "To solemnly renounce a belief, claim, or course of action.", "example": "Under public pressure, the candidate was forced to abjure his earlier position."},
    # index 66-68
    {"word": "assiduous",     "pos": "adjective", "definition": "Showing great care, attentiveness, and effort; diligent.", "example": "Her assiduous research turned a one-page brief into a thoroughly sourced report."},
    {"word": "adage",         "pos": "noun",      "definition": "A short statement expressing a general truth; a proverb or maxim.", "example": "The old adage 'measure twice, cut once' applies just as well to software as to carpentry."},
    {"word": "accede",        "pos": "verb",      "definition": "To agree to a demand or request; to assume a position or office.", "example": "After hours of debate, the board finally acceded to the shareholders' demands."},
    # index 69-71
    {"word": "astute",        "pos": "adjective", "definition": "Having an ability to accurately assess situations; shrewd and clever.", "example": "The astute investor recognized the company's potential long before the market did."},
    {"word": "aegis",         "pos": "noun",      "definition": "The protection, support, or sponsorship of a particular person or organization.", "example": "The research was conducted under the aegis of the university's ethics committee."},
    {"word": "accentuate",    "pos": "verb",      "definition": "To make a feature more noticeable or prominent; to emphasize.", "example": "The minimalist design accentuated the product's sleek lines rather than obscuring them."},
    # index 72-74
    {"word": "audacious",     "pos": "adjective", "definition": "Showing a willingness to take bold, daring risks.", "example": "The audacious proposal — to triple the budget and cut the timeline — somehow got approved."},
    {"word": "affinity",      "pos": "noun",      "definition": "A natural liking or sympathy for someone or something; a connection.", "example": "She discovered a deep affinity for statistics after a single undergraduate course."},
    {"word": "adjudicate",    "pos": "verb",      "definition": "To make a formal judgment on a disputed matter.", "example": "A neutral panel was brought in to adjudicate the contract dispute."},
    # index 75-77
    {"word": "blithe",        "pos": "adjective", "definition": "Showing a casual and cheerful indifference; carefree or unconcerned.", "example": "He made the offhand remark with a blithe disregard for how it might land."},
    {"word": "anecdote",      "pos": "noun",      "definition": "A short, amusing or interesting story about a real incident or person.", "example": "The CEO opened every all-hands with an anecdote about a lesson learned early in her career."},
    {"word": "ameliorate",    "pos": "verb",      "definition": "To make something bad or unsatisfactory better; to improve a situation.", "example": "The new policy was designed to ameliorate the long wait times that had frustrated customers."},
    # index 78-80
    {"word": "candid",        "pos": "adjective", "definition": "Truthful and straightforward; not afraid to speak one's mind.", "example": "His candid assessment of the product's flaws was exactly what the team needed to hear."},
    {"word": "anomaly",       "pos": "noun",      "definition": "Something that deviates from what is standard, normal, or expected.", "example": "The spike in traffic at 3 a.m. was flagged as an anomaly by the monitoring system."},
    {"word": "amplify",       "pos": "verb",      "definition": "To make larger, louder, or more significant; to expand upon.", "example": "Social media tends to amplify outrage out of proportion to its actual prevalence."},
    # index 81-83
    {"word": "circumspect",   "pos": "adjective", "definition": "Wary and careful; unwilling to take risks without due consideration.", "example": "A circumspect approach to the merger saved the company from a costly mistake."},
    {"word": "aphorism",      "pos": "noun",      "definition": "A pithy observation that contains a general truth; a concise maxim.", "example": "The engineering team had adopted 'done is better than perfect' as its unofficial aphorism."},
    {"word": "annul",         "pos": "verb",      "definition": "To declare invalid; to cancel an official decision or legal arrangement.", "example": "The court moved to annul the contract on the grounds of material misrepresentation."},
    # index 84-86
    {"word": "dauntless",     "pos": "adjective", "definition": "Showing fearlessness and determination; undaunted by difficulty.", "example": "The dauntless journalist filed her report from the field despite the surrounding chaos."},
    {"word": "aplomb",        "pos": "noun",      "definition": "Self-confidence and poise, especially when dealing with difficult situations.", "example": "She handled the hostile question from the audience with remarkable aplomb."},
    {"word": "appease",       "pos": "verb",      "definition": "To pacify or relieve by making concessions; to satisfy a demand.", "example": "The compromise was designed to appease both sides without fully satisfying either."},
    # index 87-89
    {"word": "deferential",   "pos": "adjective", "definition": "Showing respect and courteous submission to another's opinion or wishes.", "example": "The young associate was deferential in meetings but direct in his written memos."},
    {"word": "approbation",   "pos": "noun",      "definition": "Approval or praise, especially from an official source.", "example": "The pilot launched to broad approbation from the very stakeholders who had opposed it."},
    {"word": "ascertain",     "pos": "verb",      "definition": "To find out for certain; to establish or determine something definitively.", "example": "Before proceeding, the team needed to ascertain whether the data was actually reliable."},
    # index 90-92
    {"word": "diffident",     "pos": "adjective", "definition": "Modest or shy due to a lack of self-confidence; hesitant to assert oneself.", "example": "Despite her expertise, she was diffident in large meetings and rarely spoke unprompted."},
    {"word": "archetype",     "pos": "noun",      "definition": "A very typical example; a universally recognized original model.", "example": "The reluctant hero pushed into action by a wise mentor is an archetype found across cultures."},
    {"word": "assimilate",    "pos": "verb",      "definition": "To take in and fully understand information; to integrate into a larger group.", "example": "New analysts were given a month to assimilate the company's methodology before starting."},
    # index 93-95
    {"word": "discerning",    "pos": "adjective", "definition": "Having or showing good taste, judgment, or understanding; perceptive.", "example": "The discerning reader will notice that the author's argument quietly shifts in chapter four."},
    {"word": "ardor",         "pos": "noun",      "definition": "Enthusiasm or passion; a great warmth or intensity of feeling.", "example": "The young team's ardor for the project more than compensated for their lack of experience."},
    {"word": "atone",         "pos": "verb",      "definition": "To make amends for a wrong or injury; to reconcile a past failing.", "example": "He spent the next year trying to atone for the damage caused by the botched rollout."},
    # index 96-98
    {"word": "ebullient",     "pos": "adjective", "definition": "Cheerful and full of energy; enthusiastically exuberant.", "example": "Her ebullient personality made her the natural choice to host the company's new podcast."},
    {"word": "artifice",      "pos": "noun",      "definition": "Clever devices or expedients used to trick someone; cunning or trickery.", "example": "Beneath the polished presentation was a great deal of artifice and very little substance."},
    {"word": "augment",       "pos": "verb",      "definition": "To make something greater by adding to it; to supplement or enhance.", "example": "The team decided to augment the human review process with an automated pre-screening step."},
    # index 99-101
    {"word": "effusive",      "pos": "adjective", "definition": "Expressing feelings of gratitude, pleasure, or approval in an unrestrained way.", "example": "The effusive thank-you note went on for three pages and arrived on embossed stationery."},
    {"word": "axiom",         "pos": "noun",      "definition": "A statement regarded as self-evidently true; an established principle or rule.", "example": "In software, the axiom 'optimize later' is often ignored at significant cost."},
    {"word": "bolster",       "pos": "verb",      "definition": "To support or strengthen; to boost confidence, morale, or a position.", "example": "The new hire was brought in specifically to bolster the team's data science capabilities."},
    # index 102-104
    {"word": "fastidious",    "pos": "adjective", "definition": "Very attentive to accuracy, detail, and propriety; meticulous.", "example": "The fastidious designer rejected fourteen font combinations before settling on a fifteenth."},
    {"word": "bastion",       "pos": "noun",      "definition": "A projecting part of a fortification; something that strongly defends a principle.", "example": "The independent press remained a bastion of accountability in an increasingly polarized era."},
    {"word": "broach",        "pos": "verb",      "definition": "To raise a sensitive or difficult topic for discussion for the first time.", "example": "She had been waiting for the right moment to broach the subject of a promotion."},
    # index 105-107
    {"word": "fervent",       "pos": "adjective", "definition": "Having or displaying a passionate intensity; earnest and heartfelt.", "example": "The CEO delivered a fervent speech about the company's mission that left few unmoved."},
    {"word": "brevity",       "pos": "noun",      "definition": "Concise and exact use of words; shortness of time or duration.", "example": "The report's brevity was its greatest virtue: three pages where ten had been expected."},
    {"word": "catalyze",      "pos": "verb",      "definition": "To cause or accelerate a process or series of events.", "example": "The acquisition catalyzed a complete rethinking of the company's product strategy."},
    # index 108-110
    {"word": "forthright",    "pos": "adjective", "definition": "Direct and outspoken; going straight to the point without evasion.", "example": "A forthright critique at the prototype stage saved months of work down the line."},
    {"word": "cachet",        "pos": "noun",      "definition": "The state of being respected or admired; a mark of prestige or quality.", "example": "Working at the firm carried a certain cachet that opened doors throughout the industry."},
    {"word": "censure",       "pos": "verb",      "definition": "To express severe official disapproval of someone or something.", "example": "The board voted to formally censure the executive for the unauthorized disclosure."},
    # index 111-113
    {"word": "garrulous",     "pos": "adjective", "definition": "Excessively talkative, especially on trivial or irrelevant subjects.", "example": "The garrulous stakeholder turned a five-minute update into a forty-minute monologue."},
    {"word": "catalyst",      "pos": "noun",      "definition": "Something that precipitates an event or accelerates a process; an agent of change.", "example": "The data breach proved to be the catalyst for a complete overhaul of the firm's security posture."},
    {"word": "codify",        "pos": "verb",      "definition": "To arrange laws, rules, or principles into a systematic code or structure.", "example": "The team finally codified its deployment process into a runbook anyone could follow."},
    # index 114-116
    {"word": "genial",        "pos": "adjective", "definition": "Friendly and cheerful; pleasantly warm and good-natured.", "example": "The new office manager's genial manner made even difficult conversations feel manageable."},
    {"word": "caveat",        "pos": "noun",      "definition": "A warning or proviso about the conditions or limits of something.", "example": "He recommended the strategy, with the caveat that it would require significant upfront investment."},
    {"word": "compel",        "pos": "verb",      "definition": "To force or oblige someone to do something; to drive irresistibly.", "example": "The weight of the evidence compelled even the most skeptical board members to reconsider."},
    # index 117-119
    {"word": "haughty",       "pos": "adjective", "definition": "Arrogantly superior and disdainful; having a high opinion of oneself.", "example": "The haughty consultant spent more time criticizing past decisions than proposing new ones."},
    {"word": "chasm",         "pos": "noun",      "definition": "A deep fissure; a profound difference between people, views, or groups.", "example": "The chasm between the engineering team and sales widened with every missed deadline."},
    {"word": "concede",       "pos": "verb",      "definition": "To admit that something is true; to yield a point or cede territory.", "example": "The CEO conceded that the initial timeline had been unrealistic from the start."},
    # index 120-122
    {"word": "imperious",     "pos": "adjective", "definition": "Assuming power or authority without justification; domineering and arrogant.", "example": "His imperious management style drove away several of his best performers within six months."},
    {"word": "chicanery",     "pos": "noun",      "definition": "The use of trickery, deception, or sharp practice to achieve a goal.", "example": "The audit revealed years of financial chicanery that had been hidden in plain sight."},
    {"word": "confound",      "pos": "verb",      "definition": "To cause surprise or confusion in someone; to prove an expectation wrong.", "example": "The tiny startup confounded analysts by outperforming every established competitor."},
    # index 123-125
    {"word": "implacable",    "pos": "adjective", "definition": "Unable to be appeased, satisfied, or placated; relentlessly determined.", "example": "She faced implacable opposition from within her own party on the reform legislation."},
    {"word": "corollary",     "pos": "noun",      "definition": "A practical consequence that follows naturally from something else.", "example": "A corollary of moving fast is that you will sometimes break things you didn't mean to."},
    {"word": "consolidate",   "pos": "verb",      "definition": "To combine several things into a single more effective whole; to make secure.", "example": "The company consolidated its four regional offices into a single headquarters."},
    # index 126-128
    {"word": "impudent",      "pos": "adjective", "definition": "Not showing due respect; boldly rude or impertinent.", "example": "The impudent intern cc'd the CEO on his reply to the senior director's critique."},
    {"word": "crucible",      "pos": "noun",      "definition": "A place or situation of severe test or trial; a melting pot.", "example": "The first year of the startup was a crucible that forged the team's culture."},
    {"word": "contemplate",   "pos": "verb",      "definition": "To think carefully and at length about something; to look thoughtfully at.", "example": "She sat for a long time contemplating the offer before calling back with her answer."},
    # index 129-131
    {"word": "inveterate",    "pos": "adjective", "definition": "Having a particular habit or interest firmly established; habitual or deeply ingrained.", "example": "As an inveterate early riser, he was always the first one on the conference call."},
    {"word": "decorum",       "pos": "noun",      "definition": "Behavior or language in keeping with good taste, propriety, and dignity.", "example": "The moderator struggled to maintain decorum as the debate grew increasingly heated."},
    {"word": "contend",       "pos": "verb",      "definition": "To struggle to surmount a difficulty; to assert or maintain a position.", "example": "The team had to contend with three major platform changes before the product could launch."},
    # index 132-134
    {"word": "judicious",     "pos": "adjective", "definition": "Having or showing good judgment; sensible and prudent.", "example": "A judicious use of white space made the dense report far easier to read."},
    {"word": "deluge",        "pos": "noun",      "definition": "A severe flood; an overwhelming quantity or amount of something.", "example": "The product launch triggered a deluge of support tickets that took two weeks to clear."},
    {"word": "corroborate",   "pos": "verb",      "definition": "To confirm or give support to a statement or theory with evidence.", "example": "The second data source corroborated the trend the first analysis had identified."},
    # index 135-137
    {"word": "lachrymose",    "pos": "adjective", "definition": "Tearful or given to weeping; mournful and sad.", "example": "The lachrymose farewell speech went on well past the scheduled time for the party."},
    {"word": "desideratum",   "pos": "noun",      "definition": "Something that is needed or wanted; an essential requirement.", "example": "Clarity of purpose is the primary desideratum for any effective product brief."},
    {"word": "crystallize",   "pos": "verb",      "definition": "To make a plan or idea clear and definite; to assume a fixed and clear form.", "example": "The heated debate helped crystallize exactly what each party actually needed from the deal."},
    # index 138-140
    {"word": "loquacious",    "pos": "adjective", "definition": "Tending to talk a great deal; very talkative or rambling.", "example": "The loquacious presenter ran thirty minutes over time and still hadn't reached the main point."},
    {"word": "diatribe",      "pos": "noun",      "definition": "A forceful and bitter verbal attack or tirade against someone or something.", "example": "What started as constructive feedback quickly deteriorated into a diatribe about past failures."},
    {"word": "cultivate",     "pos": "verb",      "definition": "To develop a quality or skill; to nurture a relationship or environment.", "example": "She had spent years cultivating a network of contacts across every tier of the industry."},
    # index 141-143
    {"word": "magnanimous",   "pos": "adjective", "definition": "Generous or forgiving, especially toward rivals or those less powerful.", "example": "The magnanimous veteran helped his direct competitors prepare for the same certification exam."},
    {"word": "dichotomy",     "pos": "noun",      "definition": "A division or contrast between two opposing things.", "example": "The report highlighted the dichotomy between what users said they wanted and how they behaved."},
    {"word": "delineate",     "pos": "verb",      "definition": "To describe or indicate something precisely; to portray clearly.", "example": "The project charter delineated each team's responsibilities so clearly that disputes became rare."},
    # index 144-146
    {"word": "obdurate",      "pos": "adjective", "definition": "Stubbornly refusing to change one's opinion or course of action.", "example": "Despite mounting evidence, the obdurate executive refused to revisit the original decision."},
    {"word": "dissonance",    "pos": "noun",      "definition": "A lack of harmony; tension or conflict between two elements.", "example": "There was uncomfortable dissonance between the company's stated values and its actual culture."},
    {"word": "demarcate",     "pos": "verb",      "definition": "To set the boundaries or limits of something; to mark a clear distinction.", "example": "The new policy clearly demarcated which decisions needed sign-off and which could be made locally."},
    # index 147-149
    {"word": "officious",     "pos": "adjective", "definition": "Asserting authority in an annoyingly overbearing or domineering way; meddlesome.", "example": "The officious compliance officer rejected the proposal on the basis of a regulation that didn't apply."},
    {"word": "dossier",       "pos": "noun",      "definition": "A collection of documents about a particular person, subject, or event.", "example": "Before the negotiation, the team assembled a dossier on each counterpart's key priorities."},
    {"word": "deprecate",     "pos": "verb",      "definition": "To express disapproval of; to strongly criticize or belittle.", "example": "The style guide deprecated the passive voice in almost all circumstances."},
    # index 150-152
    {"word": "perfidious",    "pos": "adjective", "definition": "Deceitful and untrustworthy; guilty of betrayal.", "example": "The perfidious partner had been sharing trade secrets with a rival for over a year."},
    {"word": "efficacy",      "pos": "noun",      "definition": "The ability to produce a desired or intended result; effectiveness.", "example": "The trial tested the vaccine's efficacy under real-world conditions rather than lab settings."},
    {"word": "diffuse",       "pos": "verb",      "definition": "To spread over a wide area; to reduce tension or concentration gradually.", "example": "The team leader stepped in to diffuse the argument before it could derail the meeting."},
    # index 153-155
    {"word": "pertinacious",  "pos": "adjective", "definition": "Holding firmly to an opinion or a course of action; stubbornly persistent.", "example": "The pertinacious investigator refused to close the case until every lead had been exhausted."},
    {"word": "elegance",      "pos": "noun",      "definition": "The quality of being pleasingly refined, tasteful, and ingeniously simple.", "example": "The solution's elegance was in what it left out as much as what it included."},
    {"word": "discern",       "pos": "verb",      "definition": "To recognize or find out; to perceive something that is not immediately obvious.", "example": "It took several readings to discern the subtle shift in tone between the first and second drafts."},
    # index 156-158
    {"word": "phlegmatic",    "pos": "adjective", "definition": "Having an unemotional, calm, and stoic temperament; not easily excited.", "example": "His phlegmatic reaction to the market crash allowed him to make rational decisions while others panicked."},
    {"word": "eloquence",     "pos": "noun",      "definition": "Fluent, persuasive, and expressive speech or writing.", "example": "The brevity and eloquence of the proposal made it stand out from the twenty others submitted."},
    {"word": "dispel",        "pos": "verb",      "definition": "To make a doubt, fear, or misconception disappear; to drive away.", "example": "A single well-run demo was enough to dispel most of the skepticism in the room."},
    # index 159-161
    {"word": "querulous",     "pos": "adjective", "definition": "Complaining in a petulant or whining manner; habitually complaining.", "example": "The querulous tone of his feedback undermined what were actually some valid points."},
    {"word": "emissary",      "pos": "noun",      "definition": "A person sent as a diplomatic agent on a special mission.", "example": "The company sent a senior emissary to smooth things over before the public statement."},
    {"word": "distill",       "pos": "verb",      "definition": "To extract the most important aspects; to purify through concentration.", "example": "The editor's job was to distill three hundred pages of research into a compelling ten-page summary."},
    # index 162-164
    {"word": "reticent",      "pos": "adjective", "definition": "Not revealing one's thoughts or feelings readily; reserved and restrained.", "example": "He was uncharacteristically reticent in the debrief, offering only short answers to direct questions."},
    {"word": "epiphany",      "pos": "noun",      "definition": "A moment of sudden and great revelation or insight.", "example": "The epiphany came, as they often do, not at his desk but in the shower at 6 a.m."},
    {"word": "diverge",       "pos": "verb",      "definition": "To develop in a different direction from another; to differ.", "example": "The two products had started from the same codebase but diverged significantly over three years."},
    # index 165-167
    {"word": "sagacious",     "pos": "adjective", "definition": "Having or showing good judgment; wise and discerning.", "example": "The sagacious mentor resisted the temptation to give advice and instead asked better questions."},
    {"word": "ethos",         "pos": "noun",      "definition": "The characteristic spirit of a culture, era, or community; its guiding beliefs.", "example": "The team's ethos — 'ship small and learn fast' — showed in its product velocity."},
    {"word": "edify",         "pos": "verb",      "definition": "To instruct or improve someone morally or intellectually.", "example": "The workshop was designed less to entertain than to genuinely edify participants about the research."},
    # index 168-170
    {"word": "sycophantic",   "pos": "adjective", "definition": "Behaving in an obsequious, servile way to gain favor; fawning.", "example": "The sycophantic applause for every idea from the CEO made honest feedback nearly impossible."},
    {"word": "exuberance",    "pos": "noun",      "definition": "The quality of being full of energy, excitement, and cheerfulness.", "example": "Her exuberance for the project was infectious and kept the team moving through a difficult stretch."},
    {"word": "embellish",     "pos": "verb",      "definition": "To make more attractive by adding detail; to exaggerate for effect.", "example": "The press release had been so embellished that the actual product barely resembled the description."},
    # index 171-173
    {"word": "taciturn",      "pos": "adjective", "definition": "Reserved; saying little; not inclined to talk or share opinions.", "example": "The taciturn engineer expressed more in a single line of elegant code than most did in a paragraph."},
    {"word": "fallacy",       "pos": "noun",      "definition": "A mistaken belief; a failure in reasoning that undermines an argument.", "example": "The report exposed the fallacy at the heart of the competitor's pricing model."},
    {"word": "embolden",      "pos": "verb",      "definition": "To give someone the courage or confidence to do something.", "example": "The early success of the pilot emboldened the team to propose a much more ambitious rollout."},
    # index 174-176
    {"word": "truculent",     "pos": "adjective", "definition": "Eager or quick to argue or fight; aggressively defiant.", "example": "The truculent reviewer turned every comment into a referendum on the team's competence."},
    {"word": "finesse",       "pos": "noun",      "definition": "Intricate and refined skill in handling a delicate or difficult situation.", "example": "Negotiating a pay rise requires a certain finesse that not everyone develops quickly."},
    {"word": "emulate",       "pos": "verb",      "definition": "To match or surpass someone by imitation; to follow as a model.", "example": "The startup openly set out to emulate the onboarding experience of its market-leading rival."},
    # index 177-179
    {"word": "unflappable",   "pos": "adjective", "definition": "Having or showing calmness in a crisis; not easily agitated or alarmed.", "example": "The unflappable project manager kept the team focused even as the scope doubled overnight."},
    {"word": "foible",        "pos": "noun",      "definition": "A minor weakness or eccentricity in someone's character; a small failing.", "example": "His habit of naming every test variable 'banana' was a beloved foible rather than a real problem."},
    {"word": "encapsulate",   "pos": "verb",      "definition": "To express the essential features of something succinctly; to enclose.", "example": "The one-liner at the top of the README perfectly encapsulated what the library actually did."},
    # index 180-182
    {"word": "venerable",     "pos": "adjective", "definition": "Accorded a great deal of respect, especially because of age, wisdom, or character.", "example": "The venerable professor's course had launched more careers than any other in the department."},
    {"word": "fortitude",     "pos": "noun",      "definition": "Courage and resilience in the face of pain or adversity; mental strength.", "example": "It took real fortitude to push the unpopular decision through in the face of such strong opposition."},
    {"word": "engender",      "pos": "verb",      "definition": "To cause or give rise to a situation, feeling, or condition.", "example": "The new open-office layout engendered collaboration in some teams and resentment in others."},
    # index 183-185
    {"word": "verbose",       "pos": "adjective", "definition": "Using or expressed in more words than are needed; wordy.", "example": "The verbose specification document made it difficult to identify what was actually being asked."},
    {"word": "fruition",      "pos": "noun",      "definition": "The realization or fulfillment of a plan or project; coming to maturity.", "example": "After three years of development, the vision finally came to fruition at the annual conference."},
    {"word": "entrench",      "pos": "verb",      "definition": "To establish something so firmly that change is difficult; to embed deeply.", "example": "The legacy codebase had entrenched certain inefficiencies that no one wanted to tackle."},
    # index 186-188
    {"word": "vigilant",      "pos": "adjective", "definition": "Keeping careful watch for possible danger or difficulties; alert.", "example": "Staying vigilant about security vulnerabilities is not a one-time task but a daily discipline."},
    {"word": "gambit",        "pos": "noun",      "definition": "An action intended to gain an advantage, especially at the outset of a situation.", "example": "Opening the negotiation with an extreme anchor price is a classic gambit, and both sides knew it."},
    {"word": "epitomize",     "pos": "verb",      "definition": "To be a perfect example of a quality or type; to summarize or exemplify.", "example": "The product's simple, elegant packaging epitomized the brand's philosophy."},
    # index 189-191
    {"word": "wistful",       "pos": "adjective", "definition": "Having or showing a feeling of vague, tender longing; yearningly nostalgic.", "example": "She cast a wistful glance at the old prototype, remembering how excited the team had been."},
    {"word": "genesis",       "pos": "noun",      "definition": "The origin or beginning of something; the point at which it came into being.", "example": "The genesis of the company lay in a frustrating experience the founders had as customers."},
    {"word": "espouse",       "pos": "verb",      "definition": "To adopt or support a cause or belief; to advocate strongly for.", "example": "He had espoused agile methods for years before the rest of the organization caught up."},
    # index 192-194
    {"word": "zealous",       "pos": "adjective", "definition": "Having or showing great energy or enthusiasm in pursuit of a cause or goal.", "example": "The zealous new hire had redesigned the onboarding flow on her second day without being asked."},
    {"word": "harbinger",     "pos": "noun",      "definition": "A person or thing that announces or signals the approach of another.", "example": "The sharp drop in user retention was a harbinger of a deeper problem with the core product."},
    {"word": "exhort",        "pos": "verb",      "definition": "To strongly encourage or urge someone to do something.", "example": "The coach exhorted the team to bring the same energy in the second half that they had in the first."},
    # index 195-197
    {"word": "acerbic",       "pos": "adjective", "definition": "Sharp and forthright; having a bitter, cutting quality in speech or manner.", "example": "His acerbic wit made the post-mortem entertaining, though some felt it was too close to the bone."},
    {"word": "hegemony",      "pos": "noun",      "definition": "Leadership or dominance of one group over others in a particular domain.", "example": "The new entrant's rapid growth threatened the incumbent's decade-long hegemony in the market."},
    {"word": "expedite",      "pos": "verb",      "definition": "To make an action or process happen sooner; to speed up or accelerate.", "example": "The client's deadline was immovable, so every possible step was taken to expedite the review."},
    # index 198-200
    {"word": "apposite",      "pos": "adjective", "definition": "Apt in the circumstances or in relation to something; highly pertinent.", "example": "His remark about compound interest was oddly apposite given the discussion that followed."},
    {"word": "impasse",       "pos": "noun",      "definition": "A situation in which no progress is possible; a deadlock.", "example": "Negotiations reached an impasse when neither side would budge on the key financial term."},
    {"word": "explicate",     "pos": "verb",      "definition": "To analyze and develop an idea in detail; to explain clearly and fully.", "example": "The professor took thirty minutes to fully explicate the implications of a single equation."},
    # index 201-203
    {"word": "auspicious",    "pos": "adjective", "definition": "Giving or indicating a good chance of success; favorable.", "example": "Closing the largest deal in company history on day one was an auspicious start for the new VP."},
    {"word": "imperative",    "pos": "noun",      "definition": "An essential or urgent thing; an authoritative command or rule.", "example": "In a competitive market, speed of iteration is a strategic imperative, not a luxury."},
    {"word": "extrapolate",   "pos": "verb",      "definition": "To extend a conclusion or trend to an unknown situation beyond the data.", "example": "You can't safely extrapolate from three months of data what the full-year performance will be."},
    # index 204-206
    {"word": "capacious",     "pos": "adjective", "definition": "Having a lot of space inside; roomy; able to hold a great deal.", "example": "The capacious conference room was converted into a war room for the final sprint."},
    {"word": "largesse",      "pos": "noun",      "definition": "Generosity in bestowing money, gifts, or favors; liberality.", "example": "The founder's largesse extended to every department at year-end, not just the ones that hit targets."},
    {"word": "facilitate",    "pos": "verb",      "definition": "To make an action, process, or interaction easier or smoother.", "example": "The new tool was designed to facilitate collaboration between teams in different time zones."},
    # index 207-209
    {"word": "caustic",       "pos": "adjective", "definition": "Sarcastic in a scathing way; able to destroy or damage through sharp speech.", "example": "The caustic review stung, but its core criticism of the product architecture was essentially correct."},
    {"word": "lexicon",       "pos": "noun",      "definition": "The vocabulary of a person, language, or branch of knowledge.", "example": "The onboarding guide introduced recruits to the company's extensive internal lexicon."},
    {"word": "fathom",        "pos": "verb",      "definition": "To understand something after much thought; to comprehend fully.", "example": "She couldn't fathom why the team had shipped the feature without a single user test."},
    # index 210-212
    {"word": "clandestine",   "pos": "adjective", "definition": "Kept secret, especially because illicit or potentially damaging.", "example": "The clandestine side project eventually became the company's most profitable product line."},
    {"word": "lore",          "pos": "noun",      "definition": "A body of traditions, knowledge, or stories held by a particular group.", "example": "Every long-tenured engineer at the company carried irreplaceable institutional lore."},
    {"word": "forestall",     "pos": "verb",      "definition": "To prevent something from happening by taking action in advance; to preempt.", "example": "The detailed FAQ was written specifically to forestall the questions that always came up in demos."},
    # index 213-215
    {"word": "contentious",   "pos": "adjective", "definition": "Causing or likely to cause argument or controversy; disputed.", "example": "The contentious decision to sunset the legacy API divided the engineering team for months."},
    {"word": "maelstrom",     "pos": "noun",      "definition": "A powerful whirlpool; a situation of confused, violent, or turbulent activity.", "example": "The product launch dropped the support team into a maelstrom of competing urgent priorities."},
    {"word": "formulate",     "pos": "verb",      "definition": "To create or prepare a strategy, plan, or idea in a systematic way.", "example": "The analyst spent two weeks formulating a response to the competitive threat before presenting it."},
    # index 216-218
    {"word": "decorous",      "pos": "adjective", "definition": "In keeping with good taste, propriety, and dignity; proper and seemly.", "example": "The handover was decorous and professional, even though the circumstances behind it were not."},
    {"word": "malaise",       "pos": "noun",      "definition": "A general feeling of discomfort, unease, or lack of wellbeing; dissatisfaction.", "example": "A subtle malaise had settled over the team after three consecutive quarters of missed targets."},
    {"word": "fortify",       "pos": "verb",      "definition": "To make stronger or more resistant; to strengthen mentally or physically.", "example": "The pre-briefing was designed to fortify the team's confidence ahead of a demanding client review."},
    # index 219-221
    {"word": "dilatory",      "pos": "adjective", "definition": "Slow to act; intended to cause delay; not prompt.", "example": "The committee's dilatory response allowed the situation to worsen considerably before any action was taken."},
    {"word": "manifesto",     "pos": "noun",      "definition": "A public declaration of intentions, policies, or views issued by a person or group.", "example": "The design team published a short manifesto setting out the principles behind every product decision."},
    {"word": "foment",        "pos": "verb",      "definition": "To instigate or stir up trouble, rebellion, or discord.", "example": "The anonymous posts were deliberately designed to foment distrust between the two teams."},
    # index 222-224
    {"word": "doleful",       "pos": "adjective", "definition": "Expressing sorrow or misery; mournful and sad.", "example": "The doleful tone of the quarterly memo accurately reflected how difficult the year had been."},
    {"word": "minutiae",      "pos": "noun",      "definition": "The small, precise, or trivial details of something; fine points.", "example": "He was so absorbed in the minutiae of the contract that he missed the problematic headline clause."},
    {"word": "garner",        "pos": "verb",      "definition": "To gather or collect; to acquire or earn something, especially gradually.", "example": "The open-source project had garnered over ten thousand stars before the company even noticed."},
    # index 225-227
    {"word": "eclectic",      "pos": "adjective", "definition": "Deriving ideas, style, or taste from a broad and diverse range of sources.", "example": "Her eclectic reading list — spanning philosophy, biology, and detective fiction — made her a surprisingly lateral thinker."},
    {"word": "nexus",         "pos": "noun",      "definition": "A connection or series of connections; the central and most important point.", "example": "The platform had positioned itself as the nexus of an entire industry's data flow."},
    {"word": "glean",         "pos": "verb",      "definition": "To obtain information or understanding bit by bit from various sources.", "example": "From the sparse changelog, she could glean that the API had been quietly deprecated."},
    # index 228-230
    {"word": "egregious",     "pos": "adjective", "definition": "Outstandingly bad; shocking in its severity or magnitude.", "example": "The egregious data error had been sitting undetected in the model for over six months."},
    {"word": "nuance",        "pos": "noun",      "definition": "A subtle difference in meaning, expression, or tone; a fine distinction.", "example": "The best communicators in the room were the ones who could grasp the nuance in the data."},
    {"word": "grapple",       "pos": "verb",      "definition": "To struggle to overcome a problem or difficulty; to wrestle with.", "example": "The engineering team had been grappling with the same architectural problem for two quarters."},
    # index 231-233
    {"word": "elusive",       "pos": "adjective", "definition": "Difficult to find, catch, or achieve; tending to evade grasp or understanding.", "example": "Product-market fit remained elusive despite dozens of iterations and three pivots."},
    {"word": "onus",          "pos": "noun",      "definition": "Something that is one's duty or responsibility; a burden.", "example": "The onus to prove the system worked reliably fell squarely on the team that had built it."},
    {"word": "impede",        "pos": "verb",      "definition": "To delay or block the progress or action of; to obstruct.", "example": "Unclear ownership of the decision impeded progress for weeks longer than it should have."},
    # index 234-236
    {"word": "enigmatic",     "pos": "adjective", "definition": "Difficult to interpret or understand; mysterious and puzzling.", "example": "The CEO's enigmatic responses during the earnings call left analysts with more questions than answers."},
    {"word": "paradigm",      "pos": "noun",      "definition": "A typical example or pattern; a framework of ideas, assumptions, or practices.", "example": "The shift to mobile fundamentally changed the paradigm within which product teams operated."},
    {"word": "infer",         "pos": "verb",      "definition": "To deduce or conclude something from evidence and reasoning rather than explicit statement.", "example": "From the absence of any reply, she inferred that the proposal had not landed well."},
    # index 237-239
    {"word": "equivocal",     "pos": "adjective", "definition": "Open to more than one interpretation; ambiguous or uncertain.", "example": "His equivocal response to the question left everyone in the room unsure how to proceed."},
    {"word": "paradox",       "pos": "noun",      "definition": "A seemingly contradictory statement that may nonetheless be true; a self-contradiction.", "example": "The productivity paradox — that more tools often leads to less output — was on full display."},
    {"word": "instigate",     "pos": "verb",      "definition": "To bring about or initiate an action or event, especially a problematic one; to provoke.", "example": "Nobody could agree on who had instigated the restructuring, but everyone agreed it was overdue."},
    # index 240-242
    {"word": "esoteric",      "pos": "adjective", "definition": "Intended for or understood by only a small, specialized group; highly specialized.", "example": "Her knowledge of the esoteric corner of tax law turned out to be invaluable in the negotiation."},
    {"word": "prerogative",   "pos": "noun",      "definition": "A right or privilege exclusive to a particular person or group.", "example": "Setting the deadline is the client's prerogative; meeting it is ours."},
    {"word": "invoke",        "pos": "verb",      "definition": "To cite or appeal to something as an authority or justification; to call upon.", "example": "The legal team invoked an obscure clause in the original agreement to challenge the amendment."},
    # index 243-245
    {"word": "immutable",     "pos": "adjective", "definition": "Unchanging over time or incapable of being changed; permanent.", "example": "The one immutable rule was that no deployment could happen on a Friday afternoon."},
    {"word": "provenance",    "pos": "noun",      "definition": "The place of origin or source of something; a record of ownership or history.", "example": "Knowing the provenance of the dataset was essential before drawing any conclusions from it."},
    {"word": "marshal",       "pos": "verb",      "definition": "To arrange or organize people, arguments, or resources effectively and efficiently.", "example": "She marshaled her evidence carefully before presenting the case to the executive team."},
    # index 246-248
    {"word": "incongruous",   "pos": "adjective", "definition": "Not in harmony with the surrounding or other elements; out of place.", "example": "The formal boardroom language felt incongruous in a company that prided itself on radical candor."},
    {"word": "rapprochement", "pos": "noun",      "definition": "The reestablishment of harmonious relations after a period of conflict or estrangement.", "example": "The joint project served as a rapprochement after two years of tension between the two departments."},
    {"word": "navigate",      "pos": "verb",      "definition": "To plan or direct a route through a complex environment; to find a way through.", "example": "Learning to navigate the internal approval process was a skill that took years to develop."},
    # index 249-251
    {"word": "ineffable",     "pos": "adjective", "definition": "Too great or extreme to be expressed in words; defying description.", "example": "There is an ineffable satisfaction in shipping a product that works exactly as you imagined."},
    {"word": "rancor",        "pos": "noun",      "definition": "Bitterness or resentfulness that has built up over time; long-standing ill will.", "example": "The rancor from the original dispute never fully subsided, even after the formal resolution."},
    {"word": "obviate",       "pos": "verb",      "definition": "To remove a need or difficulty; to prevent a problem from arising.", "example": "A two-sentence note at the top of the document would have obviated the entire misunderstanding."},
    # index 252-254
    {"word": "inexorable",    "pos": "adjective", "definition": "Impossible to stop or prevent; continuing without any possibility of being changed.", "example": "The inexorable rise in storage costs finally forced the team to rethink its archiving strategy."},
    {"word": "recourse",      "pos": "noun",      "definition": "A source of help in a difficult situation; the right to take legal action.", "example": "Without a clear escalation path, engineers had no recourse when infrastructure requests were ignored."},
    {"word": "ostracize",     "pos": "verb",      "definition": "To exclude from a society, group, or activity; to shun or banish.", "example": "The team informally ostracized anyone who consistently blamed others in the post-mortem process."},
    # index 255-257
    {"word": "insipid",       "pos": "adjective", "definition": "Lacking flavor, vigor, or interest; dull and unexciting.", "example": "The insipid tagline failed to communicate anything memorable about what the product actually did."},
    {"word": "reprieve",      "pos": "noun",      "definition": "A cancellation or postponement of a punishment or difficulty; temporary relief.", "example": "The extended deadline was a welcome reprieve, but everyone knew the work still had to be done."},
    {"word": "interpolate",   "pos": "verb",      "definition": "To insert something between existing elements; to estimate values between known data points.", "example": "The model was designed to interpolate missing values rather than discard incomplete records."},
    # index 258-260
    {"word": "lucid",         "pos": "adjective", "definition": "Expressed clearly and easily understood; mentally clear and rational.", "example": "The most lucid explanation of the architecture came not from the docs but from a five-minute whiteboard sketch."},
    {"word": "resonance",     "pos": "noun",      "definition": "The quality of evoking a response; the ability to evoke significance or meaning.", "example": "The campaign's resonance with younger audiences surprised even the team that had created it."},
    {"word": "kindle",        "pos": "verb",      "definition": "To light a fire; to arouse or inspire a feeling or quality.", "example": "The mentor's enthusiasm for the problem kindled a curiosity in the intern that lasted for years."},
]

# ── Shared style values ────────────────────────────────────────────────────────

_FONT = "'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"
_TEXT = f"font-family:{_FONT};color:#1a202c"

# ── HTML helpers ───────────────────────────────────────────────────────────────

def _cap_sentences(text: str, n: int) -> str:
    parts = re.split(r'(?<=[.!?])\s+', text.strip(), maxsplit=n)
    return ' '.join(parts[:n])


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
        f'<div style="font-size:28px;font-weight:800;color:#f07030;letter-spacing:-.3px;'
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
    <p style="margin:0 0 8px;font-size:13px;line-height:1.5;color:#3d4852;font-family:{_FONT}">{exec_summary}</p>
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
