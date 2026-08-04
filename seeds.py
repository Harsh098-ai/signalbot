"""
Seed list: Indian tech companies to check every run.

Curated for your ICP, so this list deliberately excludes anything known to be
over 1000 employees. Those are hard-blocked in config.KNOWN_TOO_LARGE anyway,
but keeping them out here saves probing time.

Weighted toward your priority industries: BFSI and Fintech, Manufacturing,
then Software and SaaS, then IT Services and EdTech.

Add your own targets at the bottom. One name per line, as the company writes it.
"""

SEED_COMPANIES = [
    # --- Tier 1: Fintech, BFSI, Insurtech -------------------------------
    "Setu", "Decentro", "Cashfree", "Recko", "Finbox", "Zolve", "Jupiter Money",
    "Fi Money", "Stable Money", "Wint Wealth", "Dezerv", "Smallcase",
    "Vested Finance", "InCred Money", "Fisdom", "Kaleidofin", "Rupifi",
    "Velocity", "GetVantage", "Klub", "Efficient Capital Labs",
    "Bureau", "IDfy", "Signzy", "HyperVerge", "Karza", "FinBox",
    "Riskcovry", "Turtlemint", "Onsurity", "Loop Health", "Even Healthcare",
    "Zopper", "Vitraya", "Artivatic", "Sanas", "Bimaplan",

    # --- Tier 1: Manufacturing and industrial ---------------------------
    "Detect Technologies", "Intangles", "Fero AI", "Wobot AI", "Flexiple",
    "Ripik AI", "Nanoprecise", "Entrib", "Cognext", "AlphaICs",
    "Ati Motors", "Grey Orange", "Rapid Fleet", "Bert Labs",

    # --- Tier 2: Software, SaaS, Devtools, AI ---------------------------
    "Hasura", "Atlan", "Zluri", "Facets", "Devtron", "Zenskar", "Rocketlane",
    "Nector", "Typeface", "Sarvam AI", "Krutrim", "CoRover", "Neysa",
    "Kissflow", "Springworks", "Wooqer", "Locobuzz", "Vymo", "Kapture CX",
    "SquadStack", "Nurix AI", "Attentive AI", "Spotdraft", "Leegality",
    "Zluri", "Plum", "Jify", "Pazcare", "Nova Benefits",
    "Hyperbots", "Nutanix India",
    "Toplyne", "Hevo Data", "Airbyte India", "Rivi", "Assiduus",
    "AiDash", "Mesh", "Peak XV Portfolio", "Threado", "Fyle", "Volopay",
    "Zamp", "Kodo", "Enkash", "Zaggle",

    # --- Tier 2: Ecommerce and internet ---------------------------------
    "Vaaree", "Wakefit", "Bombay Shaving Company", "Sleepyhead",
    "The Whole Truth", "Blue Tokai", "Snitch", "Bewakoof", "Newme",

    # --- Tier 3: IT Services, Professional Services, EdTech -------------
    "Everest Engineering", "Tarento", "Josh Software", "Talentica",
    "Sahaj Software", "Incubyte", "Nashtech India", "Equal Experts India",
    "Airmeet", "Teachmint", "Filo", "Classplus", "SP Robotic Works",
    "Edmingle", "Suraasa", "PhysicsWallah Labs",

    # --- Add your own below ---------------------------------------------
]
