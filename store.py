"""
SQLite persistence. Keeps the bot from emailing you the same account twice
and lets us detect hiring surges by comparing against previous runs.
"""

import sqlite3
import json
import datetime as dt

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    name            TEXT PRIMARY KEY,
    slug            TEXT,
    ats             TEXT,
    ats_slug        TEXT,
    website         TEXT,
    first_seen      TEXT,
    last_checked    TEXT,
    funding_stage   TEXT,
    funding_amount  TEXT,
    funding_url     TEXT,
    probe_failed    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS job_snapshots (
    company     TEXT,
    run_date    TEXT,
    open_roles  INTEGER,
    PRIMARY KEY (company, run_date)
);

CREATE TABLE IF NOT EXISTS seen_jobs (
    company     TEXT,
    job_id      TEXT,
    title       TEXT,
    first_seen  TEXT,
    PRIMARY KEY (company, job_id)
);

CREATE TABLE IF NOT EXISTS reported (
    company     TEXT,
    run_date    TEXT,
    score       INTEGER,
    payload     TEXT,
    PRIMARY KEY (company, run_date)
);
"""


class Store:
    def __init__(self, path=None, persist=True):
        # persist=False means run normally but write nothing. Used when email
        # is not configured yet, so a test run does not consume the signals.
        self.persist = persist
        self.conn = sqlite3.connect(path or config.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # -- companies ----------------------------------------------------------
    def upsert_company(self, name, **fields):
        if not self.persist:
            return
        today = dt.date.today().isoformat()
        cur = self.conn.execute("SELECT name FROM companies WHERE name = ?", (name,))
        if cur.fetchone() is None:
            self.conn.execute(
                "INSERT INTO companies (name, first_seen, last_checked) VALUES (?, ?, ?)",
                (name, today, today),
            )
        if fields:
            cols = ", ".join(f"{k} = ?" for k in fields)
            self.conn.execute(
                f"UPDATE companies SET {cols}, last_checked = ? WHERE name = ?",
                (*fields.values(), today, name),
            )
        self.conn.commit()

    def get_company(self, name):
        cur = self.conn.execute("SELECT * FROM companies WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def all_companies(self):
        cur = self.conn.execute("SELECT * FROM companies ORDER BY first_seen DESC")
        return [dict(r) for r in cur.fetchall()]

    # -- job tracking -------------------------------------------------------
    def record_snapshot(self, company, open_roles):
        if not self.persist:
            return
        self.conn.execute(
            "INSERT OR REPLACE INTO job_snapshots (company, run_date, open_roles) VALUES (?, ?, ?)",
            (company, dt.date.today().isoformat(), open_roles),
        )
        self.conn.commit()

    def previous_role_count(self, company, days_back=30):
        cutoff = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()
        today = dt.date.today().isoformat()
        cur = self.conn.execute(
            """SELECT open_roles FROM job_snapshots
               WHERE company = ? AND run_date >= ? AND run_date < ?
               ORDER BY run_date ASC LIMIT 1""",
            (company, cutoff, today),
        )
        row = cur.fetchone()
        return row["open_roles"] if row else None

    def filter_new_jobs(self, company, jobs):
        """Return only jobs never seen before, and mark them as seen."""
        today = dt.date.today().isoformat()
        fresh = []
        for job in jobs:
            jid = str(job.get("id", job.get("title", "")))
            cur = self.conn.execute(
                "SELECT 1 FROM seen_jobs WHERE company = ? AND job_id = ?", (company, jid)
            )
            if cur.fetchone() is None:
                fresh.append(job)
                if self.persist:
                    self.conn.execute(
                        "INSERT INTO seen_jobs (company, job_id, title, first_seen) VALUES (?, ?, ?, ?)",
                        (company, jid, job.get("title", ""), today),
                    )
        if self.persist:
            self.conn.commit()
        return fresh

    # -- reporting ----------------------------------------------------------
    def already_reported(self, company, cooldown_days=21):
        """Do not re-surface the same account inside the cooldown window."""
        cutoff = (dt.date.today() - dt.timedelta(days=cooldown_days)).isoformat()
        cur = self.conn.execute(
            "SELECT 1 FROM reported WHERE company = ? AND run_date >= ?", (company, cutoff)
        )
        return cur.fetchone() is not None

    def mark_reported(self, company, score, payload):
        if not self.persist:
            return
        self.conn.execute(
            "INSERT OR REPLACE INTO reported (company, run_date, score, payload) VALUES (?, ?, ?, ?)",
            (company, dt.date.today().isoformat(), score, json.dumps(payload, default=str)),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
