"""
Entry point. Run daily via cron or GitHub Actions.

    python main.py              # full run, sends email
    python main.py --dry-run    # writes digest_preview.html instead of sending
    python main.py --demo       # runs on bundled sample data, no network
"""

import sys
import argparse

import config
import discover
import ats
import signals
import digest
from store import Store


def run(dry_run=False, lookback_days=7, limit=None, verbose=True):
    store = Store()
    results = []

    print("Discovering companies from funding news...")
    discovered = discover.discover(lookback_days=lookback_days, verbose=verbose)
    print(f"Found {len(discovered)} candidate companies\n")

    if limit:
        discovered = discovered[:limit]

    print("Checking job boards...")
    for company in discovered:
        name = company["name"]
        existing = store.get_company(name) or {}

        if existing.get("probe_failed", 0) >= 3:
            continue  # stop wasting requests on companies with no findable board

        found_ats, slug, jobs = ats.resolve(
            name,
            known_ats=existing.get("ats"),
            known_slug=existing.get("ats_slug"),
            verbose=verbose,
        )

        if not jobs:
            store.upsert_company(
                name,
                probe_failed=existing.get("probe_failed", 0) + 1,
                funding_stage=company["funding_stage"],
                funding_amount=company["funding_amount"],
                funding_url=company["funding_url"],
            )
            continue

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

    results.sort(key=lambda r: r["score"], reverse=True)
    print(f"\n{len(results)} account(s) cleared the threshold of {config.MIN_SCORE_TO_REPORT}")
    for r in results:
        print(f"  {r['score']:>3}  {r['company']}")

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
    parser.add_argument("--days", type=int, default=7, help="funding news lookback window")
    parser.add_argument("--limit", type=int, default=None, help="cap companies checked per run")
    args = parser.parse_args()

    if args.demo:
        demo()
        sys.exit(0)

    run(dry_run=args.dry_run, lookback_days=args.days, limit=args.limit)
