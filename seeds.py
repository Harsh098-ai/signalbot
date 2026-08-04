"""
Seed list of Indian tech companies to check on every run.

Why this exists: discovery from funding news finds companies that often have no
readable job board. This list is the opposite, companies that are likely to be
on Greenhouse, Lever, Ashby, Recruitee or Workable, so the bot has a dependable
base to watch for SRE hiring even on quiet news days.

The bot probes each name once, caches whichever board it finds, and skips the
name permanently after three failed attempts. So wrong guesses cost nothing but
a little time on the first run.

Add your own targets to the bottom. One name per line, exactly as the company
writes it.
"""

SEED_COMPANIES = [
    # Developer tools and infrastructure
    "Postman", "Hasura", "Atlan", "BrowserStack", "Zluri", "Facets",
    "Last9", "SigNoz", "Devtron", "Nitrogen", "Chargebee", "Zenskar",

    # Fintech
    "Zeta", "Juspay", "Setu", "Signzy", "Perfios", "M2P Fintech", "Yubi",
    "KreditBee", "Slice", "Jupiter Money", "Fi Money", "Navi", "Groww",
    "CRED", "Decentro", "Cashfree", "Recko", "Falcon", "Finbox",

    # SaaS and enterprise
    "MoEngage", "CleverTap", "Whatfix", "LeadSquared", "Mindtickle",
    "SirionLabs", "Capillary Technologies", "Zenoti", "Wooqer", "Springworks",
    "Darwinbox", "Keka", "Kissflow", "Chargebee", "Rocketlane", "Nurture Farm",

    # AI and conversational
    "Yellow.ai", "Haptik", "Uniphore", "Observe.ai", "Gupshup", "Exotel",
    "Amagi", "Kaleyra", "Sarvam AI", "Krutrim",

    # Commerce, logistics and supply chain
    "Zetwerk", "Moglix", "Bizongo", "Locus", "FarEye", "Shiprocket",
    "Ninjacart", "DeHaat", "Porter", "Zepto", "Ripplr", "ElasticRun",

    # Consumer
    "Licious", "Country Delight", "Rebel Foods", "Wakefit", "Noise",
    "boAt", "Ather Energy", "Spinny", "Lenskart", "Bombay Shaving Company",

    # Health and other
    "Innovaccer", "PharmEasy", "HealthifyMe", "Practo", "Eka Care",

    # Data and analytics
    "Sigmoid", "Tredence", "LatentView", "Quantiphi", "Crayon Data",

    # Add your own below
]
