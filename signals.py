"""
Scoring engine.

Turns raw job postings plus funding news into a single account score and a
readable list of reasons. The reasons matter more than the number, because
that is what you paste into an outreach email.
"""

import config

W = config.SCORE_WEIGHTS
CAPS = config.SCORE_CAPS


def _matches(text, keywords):
    lowered = text.lower()
    return sorted({k for k in keywords if k in lowered})


def score_account(company, jobs, new_jobs, previous_role_count=None):
    """
    company: dict with funding_stage, funding_amount, name
    jobs: all currently open roles
    new_jobs: roles that appeared since the last run
    Returns dict with score, reasons, and supporting detail.
    """
    score = 0
    reasons = []
    detail = {}

    all_text = " ".join(f"{j['title']} {j['description']}" for j in jobs)

    # --- 1. Reliability hiring, the core signal --------------------------
    reliability_roles = [
        j for j in jobs
        if any(k in j["title"].lower() for k in config.RELIABILITY_ROLE_KEYWORDS)
    ]
    new_reliability = [
        j for j in new_jobs
        if any(k in j["title"].lower() for k in config.RELIABILITY_ROLE_KEYWORDS)
    ]

    if new_reliability:
        pts = min(len(new_reliability) * W["new_reliability_role"], CAPS["new_reliability_role"])
        score += pts
        titles = ", ".join(j["title"] for j in new_reliability[:3])
        reasons.append(f"Newly posted reliability roles: {titles}")
    elif reliability_roles:
        score += 15
        reasons.append(f"{len(reliability_roles)} open reliability role(s), posted earlier")

    detail["reliability_roles"] = [
        {"title": j["title"], "location": j["location"], "url": j["url"]}
        for j in reliability_roles[:5]
    ]

    # --- 2. Leadership hires ---------------------------------------------
    leadership = [
        j for j in new_jobs
        if any(k in j["title"].lower() for k in config.LEADERSHIP_ROLE_KEYWORDS)
    ]
    if leadership:
        score += W["leadership_hire"]
        reasons.append(f"Engineering leadership hire: {leadership[0]['title']}")
        detail["leadership"] = [j["title"] for j in leadership[:3]]

    # --- 3. Tech stack pulled from job descriptions ----------------------
    obs_stack = _matches(all_text, config.OBSERVABILITY_STACK)
    if obs_stack:
        score += W["observability_stack"]
        reasons.append(f"Running DIY monitoring: {', '.join(obs_stack[:5])}")
    detail["observability_stack"] = obs_stack

    scale = _matches(all_text, config.SCALE_KEYWORDS)
    if scale:
        pts = min(len(scale) * W["scale_keyword"], CAPS["scale_keyword"])
        score += pts
        reasons.append(f"Distributed systems complexity: {', '.join(scale[:6])}")
    detail["scale_keywords"] = scale

    cloud = _matches(all_text, config.CLOUD_KEYWORDS)
    if cloud:
        score += W["cloud"]
    detail["cloud"] = cloud

    competitors = _matches(all_text, config.COMPETITOR_KEYWORDS)
    if competitors:
        score += W["competitor_mention"]
        reasons.append(f"Already using a competitor, displacement play: {', '.join(competitors)}")
    detail["competitors"] = competitors

    # --- 4. Funding -------------------------------------------------------
    stage = (company.get("funding_stage") or "unknown").lower()
    stage_key = {
        "seed": "funding_seed",
        "pre-seed": "funding_seed",
        "series a": "funding_series_a",
        "series b": "funding_series_b",
        "series c": "funding_series_c",
    }.get(stage)
    if stage_key:
        score += W[stage_key]
        amount = company.get("funding_amount") or ""
        reasons.append(f"Recently raised {stage.title()} {amount}".strip())
    elif company.get("funding_url"):
        score += W["funding_other"]
        reasons.append("Recent funding news")

    # --- 5. Hiring surge --------------------------------------------------
    if previous_role_count and previous_role_count > 0:
        growth = (len(jobs) - previous_role_count) / previous_role_count
        if growth >= 0.5:
            score += W["hiring_surge"]
            reasons.append(
                f"Hiring surge: {previous_role_count} to {len(jobs)} open roles "
                f"({growth:.0%} up)"
            )
        detail["role_growth"] = round(growth, 2)

    # --- 6. Headcount proxy filter ---------------------------------------
    too_big = len(jobs) > config.MAX_OPEN_ROLES
    if too_big:
        detail["flag"] = "Likely above 1000 headcount, verify before adding"
        score = int(score * 0.5)

    detail["total_open_roles"] = len(jobs)
    detail["estimated_size"] = _estimate_size(len(jobs), stage)

    return {
        "company": company.get("name"),
        "score": score,
        "reasons": reasons,
        "detail": detail,
        "funding_url": company.get("funding_url", ""),
    }


def _estimate_size(open_roles, stage):
    """Very rough headcount band. Free data cannot do better than this."""
    if stage in ("pre-seed", "seed"):
        band = "10 to 60"
    elif stage == "series a":
        band = "40 to 150"
    elif stage == "series b":
        band = "120 to 400"
    elif stage == "series c":
        band = "300 to 900"
    else:
        band = "unknown"

    if open_roles > 100:
        band += " (high hiring volume, likely upper end)"
    return band
