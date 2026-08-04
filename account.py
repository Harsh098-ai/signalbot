"""
Account record builder.

The output of this module is an ACCOUNT, not a job posting. Every field is
something you would want in an account book: who they are, how big, what they
just raised, and why they are worth a call for an observability platform.

Job board data is used as evidence and summarised into one line. It never
appears as a list of vacancies.
"""

import config
import headcount

W = config.SCORE_WEIGHTS
CAPS = config.SCORE_CAPS


def _matches(text, keywords):
    lowered = text.lower()
    return sorted({k for k in keywords if k in lowered})


SECTOR_FROM_TEXT = {
    "Fintech": ["payments", "lending", "upi", "neobank", "wealth", "mutual fund",
                "credit", "kyc", "underwriting", "insurance"],
    "Ecommerce": ["ecommerce", "e-commerce", "marketplace", "catalog", "checkout",
                  "d2c", "storefront"],
    "SaaS": ["saas", "b2b software", "subscription", "multi-tenant", "crm", "erp"],
    "Healthtech": ["patient", "clinical", "healthcare", "diagnostics", "ehr"],
    "Logistics": ["logistics", "supply chain", "fleet", "warehouse", "last mile",
                  "delivery", "shipment"],
    "AI": ["llm", "machine learning", "nlp", "computer vision", "genai",
           "model training", "inference"],
    "Devtools": ["developer tools", "api platform", "sdk", "open source",
                 "developer experience", "ci/cd"],
    "Edtech": ["learner", "course", "curriculum", "edtech", "student"],
}


def _infer_sector(text):
    lowered = text.lower()
    best, best_hits = "", 0
    for label, words in SECTOR_FROM_TEXT.items():
        hits = sum(1 for w in words if w in lowered)
        if hits > best_hits:
            best, best_hits = label, hits
    return best if best_hits >= 2 else ""


def is_excluded(name):
    """Competitors and observability vendors never belong in the book."""
    lowered = (name or "").lower()
    return any(bad in lowered for bad in config.EXCLUDE_COMPANIES)


def build_account(company, jobs, new_jobs, previous_role_count=None):
    """
    company: dict from discovery or the seed list
    jobs:    currently open roles, may be empty
    Returns a flat account record ready for a table or a spreadsheet row.
    """
    score = 0
    signals = []          # short phrases for the "why" column
    has_board = bool(jobs)
    all_text = " ".join(f"{j['title']} {j['description']}" for j in jobs)
    stage = (company.get("funding_stage") or "unknown").lower()

    # --- 1. Funding, your top priority ------------------------------------
    stage_key = {
        "seed": "funding_seed", "pre-seed": "funding_seed",
        "series a": "funding_series_a", "series b": "funding_series_b",
        "series c": "funding_series_c",
    }.get(stage)

    funding_label = ""
    if stage_key:
        score += W[stage_key]
        amount = company.get("funding_amount", "")
        funding_label = f"{stage.title()} {amount}".strip()
        signals.append(f"Raised {funding_label}")
    elif company.get("funding_url"):
        score += W["funding_other"]
        funding_label = company.get("funding_amount", "Recent round")
        signals.append("Recent funding")

    # --- 2. Tech stack fit -------------------------------------------------
    obs_stack = _matches(all_text, config.OBSERVABILITY_STACK)
    competitors = _matches(all_text, config.COMPETITOR_KEYWORDS)
    scale = _matches(all_text, config.SCALE_KEYWORDS)
    cloud = _matches(all_text, config.CLOUD_KEYWORDS)

    if obs_stack:
        score += W["observability_stack"]
        signals.append(f"Self-hosted monitoring ({', '.join(obs_stack[:3])})")
    own_product = [k for k in config.OWN_PRODUCT_KEYWORDS if k in all_text.lower()]
    rivals = [c for c in competitors if c not in ("datadog",)]
    if own_product:
        signals.append("Already running Datadog, check CRM before working this")
    if rivals:
        score += W["competitor_mention"]
        signals.append(f"Using {', '.join(rivals[:2])}, displacement play")
    if scale:
        score += min(len(scale) * W["scale_keyword"], CAPS["scale_keyword"])
        signals.append(f"Distributed systems ({', '.join(scale[:3])})")
    if cloud:
        score += W["cloud"]

    stack_summary = ", ".join((obs_stack + cloud + scale)[:6])

    # --- 3. Expansion ------------------------------------------------------
    growth_note = ""
    if previous_role_count and previous_role_count > 0:
        growth = (len(jobs) - previous_role_count) / previous_role_count
        if growth >= 0.5:
            score += W["hiring_surge"]
            growth_note = f"{previous_role_count} to {len(jobs)} open roles"
            signals.append(f"Hiring surge, {growth_note}")

    leadership = [j for j in new_jobs
                  if any(k in j["title"].lower() for k in config.LEADERSHIP_ROLE_KEYWORDS)]
    if leadership:
        score += W["leadership_hire"]
        signals.append(f"Building eng leadership ({leadership[0]['title']})")

    # --- 4. Reliability hiring, summarised not listed ----------------------
    reliability = [j for j in jobs
                   if any(k in j["title"].lower() for k in config.RELIABILITY_ROLE_KEYWORDS)]
    new_reliability = [j for j in new_jobs
                       if any(k in j["title"].lower() for k in config.RELIABILITY_ROLE_KEYWORDS)]

    if new_reliability:
        score += min(len(new_reliability) * W["new_reliability_role"],
                     CAPS["new_reliability_role"])
        signals.append(f"Hiring {len(new_reliability)} reliability role(s)")
    elif reliability:
        score += 8
        signals.append(f"{len(reliability)} reliability role(s) open")

    # --- 5. Headcount, the 0 to 1000 gate ----------------------------------
    size = headcount.assess(
        company.get("name", ""), stage, len(jobs),
        use_wikidata=config.USE_WIKIDATA,
    )

    # --- 6. Priority band --------------------------------------------------
    has_funding = bool(stage_key or company.get("funding_url"))
    if score >= 100 and (has_funding or not config.REQUIRE_FUNDING_FOR_HIGH):
        priority = "High"
    elif score >= 100:
        priority = "Medium"   # strong fit but no funding event, so not urgent
    elif score >= 60:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        # identity
        "company": company.get("name", ""),
        "sector": (company.get("sector") or _infer_sector(all_text) or "Unclassified"),
        # size
        "employees": size["estimate"],
        "employees_source": size["source"],
        "in_band": size["in_band"],
        "size_reason": size["reason"],
        # funding
        "funding_stage": stage.title() if stage != "unknown" else "",
        "funding_amount": company.get("funding_amount", ""),
        "funding_label": funding_label,
        "investors": company.get("investors", ""),
        "funding_date": company.get("published", ""),
        # evidence
        "signals": signals,
        "stack": stack_summary,
        "open_roles": len(jobs),
        "reliability_roles": len(reliability),
        "growth_note": growth_note,
        "verified": has_board,
        "existing_customer": bool(own_product),
        # ranking
        "score": score,
        "priority": priority,
        "source_url": company.get("funding_url", ""),
        "headline": company.get("headline", ""),
    }
