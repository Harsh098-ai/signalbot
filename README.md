# Account Signal Bot

Finds Indian companies showing observability buying signals and emails you a daily digest.
Zero paid data sources.

## How it works

1. **Discovery.** Parses free funding RSS (Entrackr, Inc42, YourStory, VCCircle, Google News) and pulls company names out of headlines. Late stage companies get filtered out so you stay inside the 0 to 1000 headcount band.
2. **Signal collection.** For each company, guesses its job board slug and probes five public ATS APIs (Greenhouse, Lever, Ashby, Recruitee, Workable). These are public JSON endpoints, no key and no scraping.
3. **Scoring.** Reads job titles and full descriptions to detect SRE hiring, engineering leadership hires, tech stack, scale complexity and competitor tools.
4. **Digest.** Ranks accounts, drops anything below the threshold, skips anything already sent in the last 21 days, emails you an HTML summary.

## Setup

```bash
pip install feedparser requests
```

Set five environment variables:

```bash
export SMTP_USER="you@gmail.com"
export SMTP_PASS="your-16-char-app-password"   # Google Account > Security > App passwords
export EMAIL_TO="where-the-digest-goes@company.com"
```

Gmail requires an app password, not your normal login. 2FA must be on to generate one.

## Running

```bash
python main.py --demo       # offline sample run, proves the pipeline works
python main.py --dry-run    # real data, writes digest_preview.html instead of emailing
python main.py              # real run, sends the email
python main.py --days 14 --limit 25
```

Open `digest_preview.html` in a browser to see exactly what the email looks like.

## Scheduling for free

**Option A, GitHub Actions.** Push this repo private, add `SMTP_USER`, `SMTP_PASS` and `EMAIL_TO` as repository secrets, and use the included `.github/workflows/daily.yml`. Free tier covers this easily. Note that the SQLite file will not persist between runs unless you commit it back or use the Actions cache, and the workflow does the cache step for you.

**Option B, your own machine.** Add a cron entry:

```
0 8 * * 1-5 cd /path/to/signalbot && /usr/bin/python3 main.py >> run.log 2>&1
```

## First run behaviour

The first run marks every job as new, so scores will be inflated and you will get a large digest. That is expected. From day two onwards the bot only reacts to genuine changes. Consider running the first one with `--dry-run`.

## Tuning

Everything worth adjusting is in `config.py`:

- `MIN_SCORE_TO_REPORT` — raise it if the digest is noisy, lower it if it is thin
- `SCORE_WEIGHTS` — reweight what matters to you
- `RELIABILITY_ROLE_KEYWORDS` — add role titles you care about
- `FUNDING_FEEDS` — add or edit the Google News queries to reshape discovery
- `MAX_OPEN_ROLES` — the crude upper bound on company size

## Honest limitations

- **Headcount is estimated, not known.** Free sources do not expose it. The bot infers a band from funding stage and hiring volume. Verify before you commit an account to your book.
- **ATS coverage is maybe 40 to 60 percent** of Indian startups. Companies on Darwinbox, Keka, Zoho Recruit or a custom careers page will not be found. You can add those parsers later.
- **Headline parsing is not perfect.** Unusual phrasing will produce the odd bad company name. They fail harmlessly at the ATS probe step.
- **Do not add LinkedIn scraping.** It violates their terms and gets accounts banned. Everything here stays on public APIs.

## Natural upgrades if budget ever appears

- Apollo or Clay for real headcount and contact enrichment
- Crunchbase API for clean funding data instead of headline parsing
- An LLM call to summarise each account into a ready-to-send opening line
- BuiltWith for tech stack confirmation beyond job description keywords
