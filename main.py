"""
Entry point. Run daily via cron or GitHub Actions.

    python main.py              # full run, sends email
    python main.py --dry-run    # writes digest_preview.html instead of sending
    python main.py --demo       # runs on bundled sample data, no network
    python main.py --diagnose   # shows which companies have a readable job board
"""

import sys
import argparse

import config
import discover
import seeds
import ats
import signals
import digest
from store import Store


def build_worklist(lookback_days, verbose):
    """
    Two sources of companies:
      1. Seed list, checked every run. Reliable, gives steady signal.
      2. Funding news, which adds fresh names and attaches funding context.
    """
    print("Discovering companies from funding news...")
    discovered = discover.discover(lookback_days=lookback_days, verbose=verbose)
    print(f"Found {len(discovered)} company/companies in the news\n")

    worklist = {}

    for name in seeds.SEED_COMPANIES:
        key = discover.slugify(name)
        worklist[key] = {
            "name": name,
            "slug": key,
            "funding_stage": "unknown",
            "funding_amount": "",
            "funding_url": "",
            "source": "seed",
        }

    # News entries overwrite seeds so the funding context is not lost
    for company in discovered:
        company["source"] = "news"
        worklist[company["slug"]] = company

    print(f"Watching {len(worklist)} companies "
          f"({len(seeds.SEED_COMPANIES)} on the seed list, "
          f"{len(discovered)} from the news)\n")
    return list(worklist.values())


def run(dry_run=False, lookback_days=7, limit=None, verbose=True, diagnose=False):
    can_send = bool(config.SMTP_USER and config.SMTP_PASS) and not dry_run and not diagnose
    if not can_send:
        print("Email not configured or preview mode. Nothing will be saved.\n")

    store = Store(persist=can_send)
    results = []

    worklist = build_worklist(lookback_days, verbose)
    if limit:
        worklist = worklist[:limit]

    print("Checking job boards...")
    with_board, without_board = [], []

    for company in worklist:
        name = company["name"]
        existing = store.get_company(name) or {}

        if existing.get("probe_failed", 0) >= 3:
            continue  # stop wasting requests on companies with no findable board

        found_ats, slug, jobs = ats.resolve(
            name,
            known_ats=existing.get("ats"),
            known_slug=existing.get("ats_slug"),
        )

        if not jobs:
            without_board.append(name)
            store.upsert_company(
                name,
                probe_failed=existing.get("probe_failed", 0) + 1,
                funding_stage=company["funding_stage"],
                funding_amount=company["funding_amount"],
                funding_url=company["funding_url"],
            )
            continue

        with_board.append((name, found_ats, slug, len(jobs)))
        print(f"  {name:<28} {found_ats}/{slug}  {len(jobs)} open roles")

        store.upsert_company(
            name,
            slug=company["slug"],
            ats=found_ats,
            ats_slug=slug,
            funding_stage=company["funding_stage"],
            funding_amount=company["funding_amount"],
            funding_url=company["funding_url"],
            probe_failed=0,
        )

        previous = store.previous_role_count(name)
        new_jobs = store.filter_new_jobs(name, jobs)
        store.record_snapshot(name, len(jobs))

        scored = signals.score_account(company, jobs, new_jobs, previous)

        if scored["score"] >= config.MIN_SCORE_TO_REPORT and not store.already_reported(name):
            results.append(scored)
            store.mark_reported(name, scored["score"], scored)

    # -- summary -----------------------------------------------------------
    print(f"\n{'-' * 55}")
    print(f"Companies checked          : {len(worklist)}")
    print(f"Readable job board found   : {len(with_board)}")
    print(f"No board found             : {len(without_board)}")
    print(f"Cleared score threshold {config.MIN_SCORE_TO_REPORT:<3}: {len(results)}")
    print(f"{'-' * 55}\n")

    if diagnose:
        print("Companies WITH a readable board:")
        for name, a, s, n in sorted(with_board):
            print(f"  {name:<30} {a}/{s}  ({n} roles)")
        print("\nCompanies with NO board found:")
        for name in sorted(without_board):
            print(f"  {name}")
        store.close()
        return []

    results.sort(key=lambda r: r["score"], reverse=True)
    for r in results:
        print(f"  {r['score']:>3}  {r['company']}")
        for reason in r["reasons"][:3]:
            print(f"         {reason}")

    digest.send(results, dry_run=dry_run)
    store.close()
    return results


def demo():
    """Runs the scoring and email layers on fake data. Proves the pipeline offline."""
    company = {
        "name": "Kestrel Logistics",
        "funding_stage": "series b",
        "funding_amount": "$34 Mn",
        "funding_url": "https://entrackr.com/example",
    }
    jobs = [
        {"id": 1, "title": "Senior Site Reliability Engineer", "location": "Bengaluru",
         "description": "You will own our Kubernetes platform on AWS, run Prometheus and "
                        "Grafana, improve SLOs and on-call incident response across microservices.",
         "url": "https://example.com/1", "posted": ""},
        {"id": 2, "title": "Platform Engineer", "location": "Remote, India",
         "description": "Terraform, multi-region high availability, service mesh with Istio.",
         "url": "https://example.com/2", "posted": ""},
        {"id": 3, "title": "Head of Infrastructure", "location": "Bengaluru",
         "description": "Lead the infra org. Distributed systems at high traffic and low latency.",
         "url": "https://example.com/3", "posted": ""},
        {"id": 4, "title": "Product Designer", "location": "Bengaluru",
         "description": "Figma, design systems.", "url": "https://example.com/4", "posted": ""},
    ]
    scored = signals.score_account(company, jobs, new_jobs=jobs, previous_role_count=2)
    print(f"{scored['company']}  score {scored['score']}")
    for reason in scored["reasons"]:
        print(f"  - {reason}")
    digest.send([scored], dry_run=True, out_path="digest_preview.html")
    return [scored]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="write HTML preview, do not send")
    parser.add_argument("--demo", action="store_true", help="run offline on sample data")
    parser.add_argument("--diagnose", action="store_true", help="report job board coverage only")
    parser.add_argument("--days", type=int, default=7, help="funding news lookback window")
    parser.add_argument("--limit", type=int, default=None, help="cap companies checked per run")
    args = parser.parse_args()

    if args.demo:
        demo()
        sys.exit(0)

    run(dry_run=args.dry_run, lookback_days=args.days, limit=args.limit, diagnose=args.diagnose)
