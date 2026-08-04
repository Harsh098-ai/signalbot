"""
Optional: turn raw evidence into a readable account brief.

Everything else in this bot produces keyword lists. This module hands the
evidence to Claude and asks for two sentences a salesperson would actually
read, plus a suggested opening line.

This is the ONLY part of the bot that costs money. It is off by default.
To switch it on, add ANTHROPIC_API_KEY as a repository secret. At roughly
15 accounts a day the cost is a few rupees a month.

If the key is absent, every function here returns None and the digest falls
back to the keyword signals. Nothing breaks.
"""

import os
import json

import requests

import config

API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

ENABLED = bool(API_KEY)

SYSTEM_PROMPT = """You write short account briefs for a salesperson at an \
observability platform (like Datadog) covering India.

You will be given evidence about one company. Return ONLY valid JSON, no \
markdown fences, no preamble, in this exact shape:

{"why_now": "...", "opener": "...", "risk": "..."}

Rules:
- why_now: two sentences maximum. Say what changed and why it creates \
observability need right now. Be concrete, cite the evidence given. No \
marketing language.
- opener: one sentence a rep could send as the first line of an email. \
Specific to this company. No greeting, no signature, no exclamation marks.
- risk: one short phrase naming the main reason this account might not be \
worth the time, or "none obvious" if the fit is strong.
- If the evidence is thin, say so plainly rather than inventing detail.
- Never invent facts not present in the evidence."""


def _evidence_block(acc):
    lines = [
        f"Company: {acc.get('company')}",
        f"Industry: {acc.get('industry')} (priority tier {acc.get('tier')})",
        f"Estimated employees: {acc.get('employees')} ({acc.get('employees_source')})",
    ]
    if acc.get("funding_label"):
        lines.append(f"Funding: {acc['funding_label']} "
                     f"{acc.get('investors','')} {acc.get('funding_date','')}".strip())
    if acc.get("cloud"):
        lines.append(f"Cloud in use: {acc['cloud']}")
    if acc.get("stack"):
        lines.append(f"Stack seen: {acc['stack']}")
    if acc.get("github_evidence"):
        lines.append(f"GitHub evidence: {'; '.join(acc['github_evidence'])}")
    if acc.get("web_signals"):
        lines.append(f"Web signals: {'; '.join(acc['web_signals'])}")
    if acc.get("velocity_note"):
        lines.append(f"Hiring trend: {acc['velocity_note']}")
    lines.append(f"Open roles: {acc.get('open_roles')} "
                 f"(engineering {acc.get('engineering_roles')}, "
                 f"SRE/DevOps {acc.get('reliability_roles')})")
    lines.append(f"Detected signals: {'; '.join(acc.get('signals', []))}")
    if acc.get("existing_customer"):
        lines.append("NOTE: job ads mention Datadog, may already be a customer")
    return "\n".join(lines)


def write_brief(acc, timeout=30):
    """Returns {"why_now","opener","risk"} or None."""
    if not ENABLED:
        return None

    try:
        resp = requests.post(
            API_URL,
            headers={
                "content-type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": MODEL,
                "max_tokens": 400,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": _evidence_block(acc)}],
            },
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None

        text = "".join(
            block.get("text", "")
            for block in resp.json().get("content", [])
            if block.get("type") == "text"
        ).strip()

        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            return None
        return {
            "why_now": parsed.get("why_now", ""),
            "opener": parsed.get("opener", ""),
            "risk": parsed.get("risk", ""),
        }
    except Exception:
        return None


def enrich_all(accounts, limit=20):
    """Adds a 'brief' key to the top accounts. Silent no-op without a key."""
    if not ENABLED:
        return accounts
    for acc in accounts[:limit]:
        brief = write_brief(acc)
        if brief:
            acc["brief"] = brief
    return accounts
