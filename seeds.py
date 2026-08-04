"""
Seed companies to check every run, each tagged with its industry.

Tagging matters. Industry drives the tier multiplier, and inferring it from job
text fails whenever a company has few or no open roles. Setu and FinBox are
obviously Fintech, but with an empty job board the bot had no way to know, so
they landed in the lowest tier. Declaring it here fixes that permanently.

Industry labels must match the keys in config.INDUSTRY_TIERS:
  Tier 1  BFSI, Fintech, Insurtech, Manufacturing
  Tier 2  Software, Internet, SaaS, Devtools, AI, Ecommerce, Gaming
  Tier 3  IT Services, Professional Services, Edtech

Everything here is deliberately under 1000 employees. Add your own at the end.
"""

SEED_COMPANIES = {
    # --- Tier 1: Fintech, BFSI, Insurtech -------------------------------
    "Setu": "Fintech", "Decentro": "Fintech", "Cashfree": "Fintech",
    "Recko": "Fintech", "FinBox": "Fintech", "Zolve": "Fintech",
    "Jupiter Money": "Fintech", "Fi Money": "Fintech", "Stable Money": "Fintech",
    "Wint Wealth": "Fintech", "Dezerv": "Fintech", "Smallcase": "Fintech",
    "Vested Finance": "Fintech", "Fisdom": "Fintech", "Kaleidofin": "Fintech",
    "Rupifi": "Fintech", "Velocity": "Fintech", "GetVantage": "Fintech",
    "Klub": "Fintech", "Efficient Capital Labs": "Fintech", "Mesh": "Fintech",
    "Volopay": "Fintech", "Zamp": "Fintech", "Kodo": "Fintech",
    "Enkash": "Fintech", "Zaggle": "Fintech", "Fyle": "Fintech",
    "Bureau": "BFSI", "IDfy": "BFSI", "Signzy": "BFSI",
    "HyperVerge": "BFSI", "Karza": "BFSI",
    "Riskcovry": "Insurtech", "Turtlemint": "Insurtech", "Onsurity": "Insurtech",
    "Zopper": "Insurtech", "Vitraya": "Insurtech", "Artivatic": "Insurtech",
    "Bimaplan": "Insurtech", "Plum": "Insurtech", "Pazcare": "Insurtech",
    "Nova Benefits": "Insurtech", "Loop Health": "Insurtech",

    # --- Tier 1: Manufacturing and industrial ---------------------------
    "Detect Technologies": "Manufacturing", "Intangles": "Manufacturing",
    "Ripik AI": "Manufacturing", "Nanoprecise": "Manufacturing",
    "Entrib": "Manufacturing", "Bert Labs": "Manufacturing",
    "Ati Motors": "Manufacturing", "Grey Orange": "Manufacturing",
    "Wobot AI": "Manufacturing", "AlphaICs": "Manufacturing",

    # --- Tier 2: Devtools, SaaS, AI -------------------------------------
    "Hasura": "Devtools", "Atlan": "Devtools", "Facets": "Devtools",
    "Devtron": "Devtools", "Hevo Data": "Devtools", "Airbyte India": "Devtools",
    "Zluri": "SaaS", "Zenskar": "SaaS", "Rocketlane": "SaaS",
    "Kissflow": "SaaS", "Springworks": "SaaS", "Wooqer": "SaaS",
    "Locobuzz": "SaaS", "Vymo": "SaaS", "Kapture CX": "SaaS",
    "Spotdraft": "SaaS", "Leegality": "SaaS", "Toplyne": "SaaS",
    "Threado": "SaaS", "Mesh Payments": "SaaS", "Jify": "SaaS",
    "Typeface": "AI", "Sarvam AI": "AI", "Krutrim": "AI", "CoRover": "AI",
    "Neysa": "AI", "Nurix AI": "AI", "Attentive AI": "AI",
    "SquadStack": "AI", "AiDash": "AI", "Hyperbots": "AI",

    # --- Tier 2: Ecommerce and internet ---------------------------------
    "Vaaree": "Ecommerce", "Wakefit": "Ecommerce",
    "Bombay Shaving Company": "Ecommerce", "Sleepyhead": "Ecommerce",
    "The Whole Truth": "Ecommerce", "Blue Tokai": "Ecommerce",
    "Snitch": "Ecommerce", "Bewakoof": "Ecommerce", "Newme": "Ecommerce",

    # --- Tier 3: IT Services, Professional Services, EdTech -------------
    "Everest Engineering": "IT Services", "Tarento": "IT Services",
    "Josh Software": "IT Services", "Talentica": "IT Services",
    "Sahaj Software": "IT Services", "Incubyte": "IT Services",
    "Nashtech India": "IT Services", "Equal Experts India": "IT Services",
    "Airmeet": "Edtech", "Teachmint": "Edtech", "Filo": "Edtech",
    "Classplus": "Edtech", "Edmingle": "Edtech", "Suraasa": "Edtech",
    "SP Robotic Works": "Edtech",

    # --- Add your own below, as "Company Name": "Industry" ---------------
}

# Backwards-compatible list view
SEED_NAMES = list(SEED_COMPANIES.keys())
