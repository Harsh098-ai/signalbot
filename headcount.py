"""
Headcount estimation.

The 0 to 1000 requirement is the hardest thing to do on free data, because no
free source publishes reliable current headcount for private Indian companies.

So we work from three angles, cheapest first:

  1. Funding stage        cheap, always available, rough
  2. Open role count      cheap, always available, rough
  3. Wikidata             free API, accurate when present, but only covers
                          larger and better known companies

Angle 3 is the important one, and it is useful precisely because of its bias.
Wikidata mostly knows about big companies, and big companies are exactly what
we want to exclude. A hit above the ceiling is a reliable reject. A miss tells
us very little, so we fall back to the proxies.

Everything here fails soft. If the network call breaks, we return None and the
caller carries on with the proxy estimate.
"""

import re
import time

import requests

import config

WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
EMPLOYEE_PROPERTY = "P1128"   # "employees" in Wikidata

HEADERS = {"User-Agent": config.USER_AGENT}

# Words in a Wikidata description that suggest we found an actual company and
# not a person, place or song with the same name.
COMPANY_HINTS = [
    "company", "business", "corporation", "startup", "firm", "enterprise",
    "brand", "platform", "bank", "manufacturer", "retailer", "subsidiary",
    "conglomerate", "services", "technology", "software",
]

_cache = {}


def _wikidata_employees(name):
    """
    Returns an integer employee count, or None if unknown.
    Never raises. Any failure returns None.
    """
    if name in _cache:
        return _cache[name]

    result = None
    try:
        search = requests.get(
            WIKIDATA_SEARCH,
            params={
                "action": "wbsearchentities",
                "search": name,
                "language": "en",
                "format": "json",
                "limit": 3,
                "type": "item",
            },
            headers=HEADERS,
            timeout=config.REQUEST_TIMEOUT,
        ).json()

        for hit in search.get("search", []):
            description = (hit.get("description") or "").lower()
            if not any(word in description for word in COMPANY_HINTS):
                continue  # probably not the company we mean

            claims = requests.get(
                WIKIDATA_SEARCH,
                params={
                    "action": "wbgetclaims",
                    "entity": hit["id"],
                    "property": EMPLOYEE_PROPERTY,
                    "format": "json",
                },
                headers=HEADERS,
                timeout=config.REQUEST_TIMEOUT,
            ).json()

            statements = claims.get("claims", {}).get(EMPLOYEE_PROPERTY, [])
            counts = []
            for statement in statements:
                value = (statement.get("mainsnak", {})
                                  .get("datavalue", {})
                                  .get("value", {}))
                amount = value.get("amount") if isinstance(value, dict) else None
                if amount:
                    try:
                        counts.append(int(float(str(amount).lstrip("+"))))
                    except ValueError:
                        continue
            if counts:
                result = max(counts)   # most recent figures are usually largest
                break
            time.sleep(0.2)
    except Exception:
        result = None

    _cache[name] = result
    return result


def _proxy_band(stage, open_roles):
    """Rough band from funding stage and hiring volume. Returns (low, high)."""
    bands = {
        "pre-seed": (5, 30),
        "seed": (15, 60),
        "series a": (50, 160),
        "series b": (150, 400),
        "series c": (350, 800),
        "series d": (700, 2000),
    }

    if stage in bands:
        low, high = bands[stage]
    elif open_roles:
        # No funding stage known, so lean on hiring volume alone.
        # Roughly, open roles sit around 3 to 12 percent of headcount.
        low, high = max(20, open_roles * 8), open_roles * 30
    else:
        low, high = 20, 800

    if open_roles > 80:
        low, high = int(low * 1.5), int(high * 1.5)
    elif open_roles and open_roles < 5:
        high = int(high * 0.7)

    # Never imply more precision than we have. Keep the band honestly wide.
    if high < low * 3:
        high = low * 3

    return low, high


def assess(name, stage, open_roles, use_wikidata=True):
    """
    Returns a dict:
      {
        "estimate": "40 to 180",
        "source": "wikidata" | "proxy",
        "exact": 350 or None,
        "in_band": True/False,
        "confidence": "high" | "low",
        "reason": "..."
      }
    """
    stage = (stage or "unknown").lower()
    ceiling = config.HEADCOUNT_CEILING

    exact = _wikidata_employees(name) if use_wikidata else None

    if exact is not None:
        return {
            "estimate": f"{exact:,}",
            "source": "wikidata",
            "exact": exact,
            "in_band": exact <= ceiling,
            "confidence": "high",
            "reason": (f"Wikidata reports {exact:,} employees, above your {ceiling} ceiling"
                       if exact > ceiling else
                       f"Wikidata reports {exact:,} employees"),
        }

    low, high = _proxy_band(stage, open_roles)

    # Very high hiring volume is a strong standalone signal of a large org.
    if open_roles > config.MAX_OPEN_ROLES:
        return {
            "estimate": f"{low} to {high}",
            "source": "proxy",
            "exact": None,
            "in_band": False,
            "confidence": "low",
            "reason": (f"{open_roles} open roles at once, well above your "
                       f"{config.MAX_OPEN_ROLES} threshold, so likely over "
                       f"{ceiling} headcount"),
        }

    # Only reject on the proxy when the whole band sits above the ceiling.
    # Being unsure should not silently drop a good account.
    in_band = low <= ceiling

    return {
        "estimate": f"{low} to {high}",
        "source": "proxy",
        "exact": None,
        "in_band": in_band,
        "confidence": "low",
        "reason": (f"Estimated {low} to {high} from {stage} stage and "
                   f"{open_roles} open roles"),
    }
