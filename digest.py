"""
Builds the account book digest.

Two things go out:
  1. An HTML table in the email body, one row per account
  2. A CSV attachment you can paste straight into your TAM spreadsheet
"""

import io
import csv
import html
import smtplib
import datetime as dt
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

import config

CSV_COLUMNS = [
    ("company", "Company"),
    ("industry", "Industry"),
    ("tier", "Tier"),
    ("employees", "Est. employees"),
    ("employees_source", "Size basis"),
    ("funding_stage", "Stage"),
    ("funding_amount", "Amount"),
    ("investors", "Investors"),
    ("funding_date", "Funding date"),
    ("priority", "Priority"),
    ("signal_text", "Signals"),
    ("cloud", "Cloud"),
    ("stack", "Stack seen"),
    ("engineering_roles", "Eng roles open"),
    ("open_roles", "Open roles"),
    ("reliability_roles", "Reliability roles"),
    ("verified", "Job board read"),
    ("source_url", "Source"),
]

CSS = """
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       color: #1a1a1a; background: #f5f5f4; margin: 0; padding: 20px; }
.wrap { max-width: 900px; margin: 0 auto; }
h1 { font-size: 20px; margin: 0 0 3px; }
.sub { color: #6b6b6b; font-size: 13px; margin-bottom: 20px; }
.section { font-size: 11px; font-weight: 700; text-transform: uppercase;
           letter-spacing: 0.07em; color: #6b6b6b; margin: 24px 0 8px; }
table { width: 100%; border-collapse: collapse; background: #fff;
        border: 1px solid #e4e4e2; border-radius: 6px; overflow: hidden; }
th { text-align: left; font-size: 11px; text-transform: uppercase;
     letter-spacing: 0.05em; color: #6b6b6b; background: #fafaf9;
     padding: 9px 12px; border-bottom: 1px solid #e4e4e2; }
td { padding: 11px 12px; font-size: 13px; vertical-align: top;
     border-bottom: 1px solid #f0efec; line-height: 1.45; }
tr:last-child td { border-bottom: none; }
.co { font-weight: 600; font-size: 14px; }
.co a { color: #1a1a1a; text-decoration: none; }
.meta { color: #8a8a8a; font-size: 11px; }
.pill { display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 7px;
        border-radius: 3px; color: #fff; letter-spacing: 0.03em; }
.High { background: #b91c1c; } .Medium { background: #c2670a; } .Low { background: #4d7c0f; }
.sig { color: #3f3f3f; }
.sig { line-height: 1.6; }
.note { color: #8a8a8a; font-size: 12px; margin-top: 8px; }
.foot { color: #8a8a8a; font-size: 11px; text-align: center; margin-top: 26px; }
.empty { background: #fff; border: 1px solid #e4e4e2; border-radius: 6px;
         padding: 18px; font-size: 14px; }
"""


def _signal_text(acc):
    return "; ".join(acc.get("signals", []))


def build_csv(accounts):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([label for _, label in CSV_COLUMNS])
    for acc in accounts:
        row = dict(acc)
        row["signal_text"] = _signal_text(acc)
        row["verified"] = "Yes" if acc.get("verified") else "No"
        writer.writerow([row.get(key, "") for key, _ in CSV_COLUMNS])
    return buffer.getvalue()


def _table(accounts):
    parts = ["<table><tr>"
             "<th>Company</th><th>Size</th><th>Funding</th>"
             "<th>Why now</th><th>Priority</th></tr>"]
    for acc in accounts:
        link = acc.get("source_url", "")
        name = html.escape(acc["company"])
        name_cell = f"<a href='{html.escape(link)}'>{name}</a>" if link else name

        sector = html.escape(f"{acc.get('industry','')} · T{acc.get('tier',4)}")
        size = html.escape(str(acc.get("employees", "")))
        basis = "confirmed" if acc.get("employees_source") == "wikidata" else "estimated"

        funding = html.escape(acc.get("funding_label", "") or "-")
        investors = html.escape(acc.get("investors", ""))
        fdate = html.escape(acc.get("funding_date", ""))
        funding_meta = " &middot; ".join(b for b in [investors, fdate] if b)

        signal_list = acc.get("signals", [])[:4]
        signals = "<br>&bull; ".join(html.escape(s) for s in signal_list)
        signals = ("&bull; " + signals) if signals else "-"

        pri = acc.get("priority", "Low")

        parts.append(
            f"<tr>"
            f"<td><div class='co'>{name_cell}</div>"
            f"<div class='meta'>{sector}</div></td>"
            f"<td>{size}<div class='meta'>{basis}</div></td>"
            f"<td>{funding}<div class='meta'>{funding_meta}</div></td>"
            f"<td class='sig'>{signals}</td>"
            f"<td><span class='pill {pri}'>{pri}</span></td>"
            f"</tr>"
        )
    parts.append("</table>")
    return "".join(parts)


def build_html(accounts, run_date=None):
    run_date = run_date or dt.date.today().strftime("%d %b %Y")
    verified = [a for a in accounts if a.get("verified")]
    unverified = [a for a in accounts if not a.get("verified")]

    parts = [
        f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='wrap'>",
        "<h1>Account book additions</h1>",
        f"<div class='sub'>{run_date} &middot; {len(accounts)} account(s) "
        f"&middot; all under {config.HEADCOUNT_CEILING} employees</div>",
    ]

    if not accounts:
        parts.append("<div class='empty'>No new accounts matched today.</div>")

    if verified:
        parts.append("<div class='section'>Signals confirmed</div>")
        parts.append(_table(verified))
        parts.append("<div class='note'>Job board was read for these, so the stack "
                     "and hiring signals are evidenced.</div>")

    if unverified:
        parts.append("<div class='section'>Funding signal only</div>")
        parts.append(_table(unverified))
        parts.append("<div class='note'>No readable job board, so headcount and stack "
                     "are estimates from funding stage. Worth a manual check before "
                     "committing to your book.</div>")

    if accounts:
        parts.append("<div class='note' style='margin-top:16px'>"
                     "The attached CSV has every column, ready to paste into your TAM sheet."
                     "</div>")

    parts.append("<div class='foot'>Generated by your account signal bot</div>")
    parts.append("</div></body></html>")
    return "".join(parts)


def build_text(accounts):
    lines = [f"Account book additions, {dt.date.today():%d %b %Y}", ""]
    for acc in accounts:
        lines.append(f"{acc['company']}  [{acc['priority']}]")
        lines.append(f"  {acc.get('sector','')} | {acc.get('employees','')} employees "
                     f"| {acc.get('funding_label','')}")
        for signal in acc.get("signals", []):
            lines.append(f"  - {signal}")
        lines.append("")
    return "\n".join(lines) or "No new accounts matched today."


def send(accounts, to=None, dry_run=False, out_path="digest_preview.html"):
    html_body = build_html(accounts)
    csv_body = build_csv(accounts)

    if dry_run or not config.SMTP_USER:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        with open("accounts_preview.csv", "w", encoding="utf-8") as f:
            f.write(csv_body)
        print(f"Dry run. Preview written to {out_path} and accounts_preview.csv")
        return False

    msg = MIMEMultipart("mixed")
    msg["Subject"] = config.EMAIL_SUBJECT.format(date=dt.date.today().strftime("%d %b"))
    msg["From"] = config.SMTP_USER
    msg["To"] = to or config.EMAIL_TO

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(build_text(accounts), "plain"))
    body.attach(MIMEText(html_body, "html"))
    msg.attach(body)

    if accounts:
        attachment = MIMEBase("text", "csv")
        attachment.set_payload(csv_body.encode("utf-8"))
        encoders.encode_base64(attachment)
        filename = f"accounts_{dt.date.today():%Y%m%d}.csv"
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)

    print(f"Digest sent to {to or config.EMAIL_TO} with {len(accounts)} account(s)")
    return True
