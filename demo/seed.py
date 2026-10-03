#!/usr/bin/env python3
"""Generate the demonstration vault for the uvularia records product.

What this does, and why. The demonstration client (docs/adr/0001) is a fictional
land trust whose whole identity — name, short name, domain, contact, accent,
logo — lives in exactly one file, ``demo/org.yaml``. This script reads that file,
renders the record templates in ``demo/templates/`` with those identity fields,
and writes a complete, browsable records vault under ``demo/generated/`` in the
same layout a real client's vault uses. Every record it writes validates with
``core/validate.py``; the receipts it writes carry server-side publish times
chosen so that ``core/evaluate.py`` produces an honest board with at least one
red and one amber against the Massachusetts obligations pack.

How long. A second or two. It is deterministic: the same ``org.yaml`` and the
same ``--seed`` always produce byte-identical output, which is how CI can
regenerate and diff to prove the committed vault has not drifted.

How you know it worked. It prints the vault path and the board summary, and exits
0. CI then runs ``core/validate.py`` and ``core/evaluate.py`` over the output and
checks the board for a red and an amber.

    python3 demo/seed.py                 # (re)generate demo/generated/
    python3 demo/seed.py --print-vault-path   # print the vault root, generate nothing
    python3 demo/seed.py --print-asof         # print the pinned evaluation instant
    python3 demo/seed.py --seed 1781          # vary the deterministic flavour

A real client never starts from this seed. It is a demonstration and a lab
fixture; see demo/README.md. Python 3.12, standard library only.
"""

import argparse
import calendar
import hashlib
import json
import random
import re
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parent
CORE_DIR = REPO_ROOT / "core"
TEMPLATES_DIR = DEMO_DIR / "templates"
GENERATED_DIR = DEMO_DIR / "generated"
PACK_DIR = REPO_ROOT / "obligations" / "packs" / "ma"

# Reuse the core evaluator, unchanged, to write the demo's standing.json and the
# honest per-publish standing snapshot in each receipt. core/evaluate.py puts its
# own schema dir on sys.path at import, so importing it as a top-level module is
# enough.
sys.path.insert(0, str(CORE_DIR))
import evaluate  # noqa: E402  (path insert must precede the import)
# evaluate put core/schema on sys.path at import, so the schema validator is
# importable for the standing.json self-check.
from check_examples import validate as schema_validate  # noqa: E402

# The demonstration is a fixed snapshot. The board is evaluated as of this
# instant so it is reproducible regardless of the calendar day CI runs on. A
# real client evaluates at real "now"; see demo/README.md.
ASOF = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)
WARN_DAYS = 7
DEFAULT_SEED = 1781

# The four Massachusetts rules this fictional nonprofit holds itself to. The
# files are copied verbatim from the pack into the vault's obligations/ so the
# demo can never drift from the core pack.
ADOPTED_OBLIGATIONS = [
    "ma-oml-meeting-notice",
    "ma-oml-minutes-timely",
    "ma-ag-charity-annual-filing",
    "ma-corp-annual-report",
]

# Board meetings run monthly for two years, Oct 2024 through Sep 2026.
FIRST_MEETING = (2024, 10)
MEETING_COUNT = 24

# Texture that the ADR says belongs in the parameters, not in hand-written files.
# These two meeting notices are posted deliberately late so the board can show an
# honest breach rather than a fake green:
#   * index 9  (July 2025): a late notice in the history — it shows red in that
#     week's receipt snapshot but is not the current state.
#   * index 23 (Sep 2026, the most recent meeting): posted the day before the
#     meeting, so the *current* meeting-notice row on the board is red.
LATE_NOTICE_INDICES = {9, 23}

# The May meeting is the annual meeting (elections, annual report to members).
ANNUAL_MEETING_MONTH = 5


# --------------------------------------------------------------------------- #
# org.yaml — a tiny reader for flat scalars plus one block scalar (the logo).  #
# --------------------------------------------------------------------------- #

def load_org(path):
    """Read demo/org.yaml: ``key: value`` scalars and ``key: |`` block scalars.

    Deliberately minimal — the identity file is flat by construction, so there is
    no need for a general YAML parser here."""
    org = {}
    lines = path.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        key, sep, rest = raw.partition(":")
        if not sep:
            i += 1
            continue
        key = key.strip()
        rest = rest.strip()
        if rest == "|":
            # A literal block scalar: gather the more-indented lines that follow.
            block = []
            base_indent = len(raw) - len(raw.lstrip(" "))
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "":
                    block.append("")
                    i += 1
                    continue
                indent = len(nxt) - len(nxt.lstrip(" "))
                if indent <= base_indent:
                    break
                block.append(nxt[base_indent + 2:])
                i += 1
            org[key] = "\n".join(block).rstrip("\n") + "\n"
        else:
            if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in "\"'":
                rest = rest[1:-1]
            org[key] = rest
            i += 1
    for field in ("name", "short_name", "domain", "contact", "accent", "logo"):
        if field not in org:
            raise SystemExit(f"demo/org.yaml is missing required field '{field}'")
    return org


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


# --------------------------------------------------------------------------- #
# Template rendering: {{ token }} substitution, with no token left behind.     #
# --------------------------------------------------------------------------- #

_TOKEN = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")


def render(template, tokens):
    def sub(match):
        key = match.group(1)
        if key not in tokens:
            raise KeyError(f"template references unknown token {{{{ {key} }}}}")
        return str(tokens[key])
    out = _TOKEN.sub(sub, template)
    leftover = _TOKEN.search(out)
    if leftover:
        raise KeyError(f"token {{{{ {leftover.group(1)} }}}} was not substituted")
    return out


# --------------------------------------------------------------------------- #
# Small helpers.                                                               #
# --------------------------------------------------------------------------- #

def add_months(year, month, delta):
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def third_wednesday(year, month):
    first_weekday, _ = calendar.monthrange(year, month)  # Mon=0 .. Sun=6
    first_wed = 1 + (calendar.WEDNESDAY - first_weekday) % 7
    return date(year, month, first_wed + 14)


LONG_DATE = "%A, %B %-d, %Y"


def long_date(d):
    return d.strftime(LONG_DATE)


def iso_z(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def flow(items):
    return "[" + ", ".join(items) + "]"


def corrections_block(items):
    if not items:
        return ""
    out = ["corrections:"]
    for when, note in items:
        out.append(f"  - date: {when}")
        out.append(f'    note: "{note}"')
    return "\n".join(out) + "\n"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- #
# The record model. One dict per record: the schema frontmatter under "fm",    #
# the server-side publish time, the body prose, the source text, and the extra #
# tokens the type's template needs.                                            #
# --------------------------------------------------------------------------- #

class Vault:
    def __init__(self, org, rng):
        self.org = org
        self.rng = rng
        self.records = []        # list of record dicts
        self.base_tokens = {
            "org_name": org["name"],
            "org_short_name": org["short_name"],
            "domain": org["domain"],
            "contact": org["contact"],
            "status_url": f"https://{org['domain']}/status",
            "meeting_url": f"https://{org['domain']}/meetings",
        }

    def add(self, template, fm, published_at, body, extra=None, source_text=None):
        self.records.append({
            "template": template,
            "fm": fm,
            "published_at": published_at,
            "body": body,
            "extra": extra or {},
            "source_text": source_text if source_text is not None
            else f"{fm['title']}\n\n{body}\n",
        })


# --------------------------------------------------------------------------- #
# Body prose. Realistic for a small land trust with four staff, a board of      #
# seven, a visitor center, and river sensors. No personal names — roles only.   #
# --------------------------------------------------------------------------- #

STAFF = [
    "the Executive Director",
    "the Stewardship Coordinator",
    "the Outreach Coordinator",
    "the Office Manager",
]

BUSINESS_TOPICS = [
    ("stewardship of the Cedar Marsh easement",
     "Stewardship report: Cedar Marsh easement monitoring"),
    ("the high-water trail-closure protocol and recent river-sensor readings",
     "River-sensor data and the high-water trail-closure protocol"),
    ("visitor-center staffing and seasonal hours",
     "Visitor-center staffing and seasonal hours"),
    ("trail maintenance on the Ridge Loop",
     "Trail maintenance: Ridge Loop"),
    ("acceptance of the Hadley parcel donation",
     "Proposed acceptance of the Hadley parcel donation"),
    ("the water-quality monitoring partnership with the regional college",
     "Water-quality monitoring partnership"),
    ("the annual appeal and the draft operating budget",
     "Annual appeal and draft operating budget"),
    ("a grant application to the state Division of Ecological Restoration",
     "Grant application: Division of Ecological Restoration"),
]


def minutes_body(rng, topics):
    lines = []
    lines.append("## Approval of prior minutes\n")
    lines.append("The minutes of the previous regular meeting were reviewed and "
                 "approved as circulated.\n")
    lines.append("## Staff and committee reports\n")
    reporter = rng.choice(STAFF)
    lines.append(f"{reporter.capitalize()} summarized operations since the last "
                 "meeting, including visitor-center attendance and the status of "
                 "the river-sensor network. The Stewardship Committee reported on "
                 "easement monitoring visits completed during the period.\n")
    lines.append("## Business\n")
    for blurb, _title in topics:
        lines.append(f"- The Board discussed {blurb}.")
    lines.append("")
    lines.append("## Votes\n")
    for blurb, _title in topics:
        yes = rng.randint(5, 7)
        no = rng.randint(0, 7 - yes)
        lines.append(f"- Motion on {blurb}: carried {yes}–{no}.")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def agenda_body(topics):
    items = ["1. Call to order and roll call",
             "2. Approval of the prior meeting's minutes",
             "3. Staff and committee reports"]
    n = 4
    for _blurb, title in topics:
        items.append(f"{n}. {title}")
        n += 1
    items.append(f"{n}. Public comment")
    items.append(f"{n + 1}. Adjournment")
    return "\n".join(items) + "\n"


# --------------------------------------------------------------------------- #
# Generation.                                                                  #
# --------------------------------------------------------------------------- #

def build_meetings(vault):
    rng = vault.rng
    org_short = vault.org["short_name"]
    meetings = []
    y, m = FIRST_MEETING
    for i in range(MEETING_COUNT):
        meetings.append((i, third_wednesday(y, m)))
        y, m = add_months(y, m, 1)

    for i, mtg in meetings:
        is_annual = mtg.month == ANNUAL_MEETING_MONTH
        base_subjects = ["meetings"] + (["annual-meeting"] if is_annual else [])
        topics = [BUSINESS_TOPICS[(i + k) % len(BUSINESS_TOPICS)] for k in range(2 + (i % 2))]

        # ----- notice (lead: posted >= 48h before the meeting) ----- #
        late = i in LATE_NOTICE_INDICES
        if late:
            posted = datetime(mtg.year, mtg.month, mtg.day, tzinfo=timezone.utc) - timedelta(days=1)
            posted = posted.replace(hour=14)
        else:
            posted = datetime(mtg.year, mtg.month, mtg.day, tzinfo=timezone.utc) - timedelta(days=7)
            posted = posted.replace(hour=9)
        notice_id = f"{mtg.isoformat()}-meeting-notice"
        vault.add(
            "notice",
            {
                "id": notice_id, "title": f"{mtg.strftime('%B %Y')} board meeting notice",
                "type": "notice", "status": "approved", "visibility": "public",
                "effective": mtg.isoformat(), "approved": posted.date().isoformat(),
                "certainty": "verified",
                "subjects": base_subjects, "tags": ["board", str(mtg.year)],
            },
            posted,
            body="",
            extra={
                "meeting_long": long_date(mtg),
                "meeting_time": "7:00 p.m.",
                "place": "the Watershed Visitor Center, Route 9",
            },
        )

        # ----- agenda ----- #
        agenda_id = f"{mtg.isoformat()}-meeting-agenda"
        vault.add(
            "agenda",
            {
                "id": agenda_id, "title": f"{mtg.strftime('%B %Y')} board meeting agenda",
                "type": "agenda", "status": "approved", "visibility": "public",
                "effective": mtg.isoformat(), "approved": posted.date().isoformat(),
                "certainty": "verified",
                "subjects": base_subjects + ["agenda"], "tags": ["board", str(mtg.year)],
            },
            posted,
            body=agenda_body(topics),
            extra={"meeting_long": long_date(mtg)},
        )

        # ----- minutes (lag: approved at the NEXT meeting, then posted) ----- #
        if i + 1 < len(meetings):
            next_mtg = meetings[i + 1][1]
            approved_dt = datetime(next_mtg.year, next_mtg.month, next_mtg.day,
                                   tzinfo=timezone.utc)
            posted_min = approved_dt.replace(hour=10) + timedelta(days=1)
            present = rng.randint(5, 7)
            staff_present = "; ".join(rng.sample(STAFF, 2)).replace("the ", "", 1)
            minutes_id = f"{mtg.isoformat()}-board-minutes"
            vault.add(
                "minutes",
                {
                    "id": minutes_id,
                    "title": f"Board meeting minutes, {mtg.isoformat()}",
                    "type": "minutes", "status": "approved", "visibility": "public",
                    "effective": mtg.isoformat(),
                    "approved": approved_dt.date().isoformat(),
                    "certainty": "verified",
                    "subjects": base_subjects + ["minutes"], "tags": ["board", str(mtg.year)],
                },
                posted_min,
                body=minutes_body(rng, topics),
                extra={
                    "meeting_long": long_date(mtg),
                    "present": str(present),
                    "staff_present": staff_present,
                    "adjourned": f"{rng.randint(8, 9)}:{rng.choice(['15', '30', '45'])} p.m.",
                },
            )


def build_governance(vault):
    org = vault.org
    # ----- bylaws: v1 superseded by v2 (one supersession) ----- #
    vault.add(
        "bylaw",
        {
            "id": "2015-04-15-bylaws", "title": "Bylaws (2015)", "type": "bylaw",
            "status": "superseded", "visibility": "public", "effective": "2015-04-15",
            "approved": "2015-04-15", "certainty": "verified",
            "subjects": ["bylaws", "governance"], "tags": ["governance"],
        },
        datetime(2015, 4, 15, 9, tzinfo=timezone.utc),
        body=("These are the original bylaws adopted at incorporation. They were "
              "superseded in 2024; this version is retained and marked "
              "`superseded`, never deleted.\n\n"
              "## Article I — Purpose\n\nTo protect the land and water of the "
              "watershed through conservation, stewardship, and education.\n\n"
              "## Article II — Membership and Trustees\n\nThe affairs of the "
              "corporation are managed by a Board of up to seven Trustees.\n"),
        extra={"supersedes_line": ""},
    )
    vault.add(
        "bylaw",
        {
            "id": "2024-03-20-bylaws", "title": "Bylaws (2024)", "type": "bylaw",
            "status": "approved", "visibility": "public", "effective": "2024-03-20",
            "approved": "2024-03-20", "certainty": "verified",
            "supersedes": "2015-04-15-bylaws",
            "subjects": ["bylaws", "governance"], "tags": ["governance"],
        },
        datetime(2024, 3, 20, 9, tzinfo=timezone.utc),
        body=("The Board amended and restated the bylaws in 2024 to add a "
              "conflict-of-interest article and to fix the number of Trustees at "
              "seven.\n\n## Article I — Purpose\n\nTo protect the land and water "
              "of the watershed through conservation, stewardship, and "
              "education.\n\n## Article II — Board of Trustees\n\nThe Board "
              "consists of seven Trustees elected at the annual meeting.\n\n"
              "## Article III — Conflicts of Interest\n\nTrustees and staff "
              "follow the conflict-of-interest policy, reviewed annually.\n"),
        extra={"supersedes_line": "supersedes: 2015-04-15-bylaws\n"},
    )

    # ----- conflict-of-interest policy: v1 revised once ----- #
    vault.add(
        "policy",
        {
            "id": "2016-02-10-conflict-of-interest-policy",
            "title": "Conflict-of-Interest Policy (2016)", "type": "policy",
            "status": "superseded", "visibility": "public", "effective": "2016-02-10",
            "approved": "2016-02-10", "certainty": "verified",
            "subjects": ["conflict-of-interest", "governance"], "tags": ["governance"],
        },
        datetime(2016, 2, 10, 9, tzinfo=timezone.utc),
        body=("The original conflict-of-interest policy. Superseded in 2024; "
              "retained and marked `superseded`.\n\n## Disclosure\n\nEach Trustee "
              "discloses any financial interest that could conflict with the "
              "organization's purpose.\n"),
        extra={"supersedes_line": ""},
    )
    vault.add(
        "policy",
        {
            "id": "2024-01-17-conflict-of-interest-policy",
            "title": "Conflict-of-Interest Policy (2024)", "type": "policy",
            "status": "approved", "visibility": "public", "effective": "2024-01-17",
            "approved": "2024-01-17", "certainty": "verified",
            "supersedes": "2016-02-10-conflict-of-interest-policy",
            "subjects": ["conflict-of-interest", "governance"], "tags": ["governance"],
        },
        datetime(2024, 1, 17, 9, tzinfo=timezone.utc),
        body=("The Board revised the policy in 2024 to require an annual written "
              "disclosure from every Trustee and from staff with purchasing "
              "authority.\n\n## Disclosure\n\nEach Trustee and covered staff "
              "member files a written disclosure annually and whenever a new "
              "interest arises.\n\n## Recusal\n\nA person with a conflict leaves "
              "the discussion and does not vote on the matter.\n"),
        extra={"supersedes_line": "supersedes: 2016-02-10-conflict-of-interest-policy\n"},
    )


def build_filings_and_reports(vault):
    # ----- annual reports to the Secretary of the Commonwealth (cadence 12mo) ----- #
    for year, fy_end in ((2024, "June 30, 2024"), (2025, "June 30, 2025")):
        eff = date(year, 11, 1)
        vault.add(
            "report",
            {
                "id": f"{eff.isoformat()}-annual-report",
                "title": f"Annual report {year}", "type": "report", "status": "approved",
                "visibility": "public", "effective": eff.isoformat(),
                "approved": eff.isoformat(), "certainty": "verified",
                "subjects": ["annual-report", "secretary-of-state"],
                "tags": ["filing", str(year)],
            },
            datetime(eff.year, eff.month, eff.day, 9, tzinfo=timezone.utc),
            body=("Summary of the year: acres under protection, easements "
                  "monitored, visitor-center attendance, and the independent "
                  "financial review.\n\n- Protected acreage and new easements\n"
                  "- Stewardship monitoring visits completed\n- Visitor-center "
                  "and education program attendance\n- Summary financials\n"),
            extra={"fy_end": fy_end},
        )

    # ----- Form PC charity filings with the Attorney General (cadence 12mo) ----- #
    for eff in (date(2024, 10, 9), date(2025, 10, 8)):
        vault.add(
            "filing",
            {
                "id": f"{eff.isoformat()}-form-pc",
                "title": f"Annual Form PC filing ({eff.year})", "type": "filing",
                "status": "approved", "visibility": "public", "effective": eff.isoformat(),
                "approved": eff.isoformat(), "certainty": "verified",
                "subjects": ["annual-filing", "charities", "attorney-general"],
                "tags": ["filing", str(eff.year)],
            },
            datetime(eff.year, eff.month, eff.day, 9, tzinfo=timezone.utc),
            body=(f"Form PC filed with the Non-Profit Organizations/Public "
                  f"Charities Division of the Attorney General's Office for the "
                  f"fiscal year, with the IRS Form 990 and schedules attached. "
                  f"This record notes what was filed and when; the board shows "
                  f"when the next annual filing is due.\n"),
        )

    # ----- a stewardship permit filing (no obligation; it is just a record) ----- #
    eff = date(2025, 4, 22)
    vault.add(
        "filing",
        {
            "id": f"{eff.isoformat()}-stewardship-permit",
            "title": "Order of Conditions — Lower Brook footbridge repair",
            "type": "filing", "status": "approved", "visibility": "public",
            "effective": eff.isoformat(), "approved": eff.isoformat(),
            "certainty": "verified", "subjects": ["stewardship", "permit"],
            "tags": ["stewardship", "2025"],
        },
        datetime(eff.year, eff.month, eff.day, 9, tzinfo=timezone.utc) + timedelta(days=1),
        body=("The local Conservation Commission issued an Order of Conditions "
              "permitting repair of the Lower Brook footbridge under the Wetlands "
              "Protection Act. Work was completed within the conditions.\n"),
    )


ANNOUNCEMENTS = [
    ("2024-11-15T08:00:00Z", "Visitor center shifts to winter hours",
     ["visitor-center", "hours"], "verified",
     "The Watershed Visitor Center is open Saturdays and Sundays, 10 a.m. to "
     "3 p.m., through March. Trails remain open dawn to dusk."),
    ("2025-03-20T07:30:00Z", "Spring trail reopening",
     ["trail-status", "trails"], "verified",
     "All trails are open for the season. The Lower Brook Trail may close on "
     "short notice during high water; the current status is always posted."),
    ("2025-06-05T06:45:00Z", "High water: Lower Brook Trail closed",
     ["trail-status", "river-sensors", "safety"], "reported",
     "River-sensor readings at the Route 9 gauge crossed the high-water "
     "threshold overnight. The Lower Brook Trail is closed until the water "
     "recedes and staff inspect the crossing."),
    ("2025-07-18T16:00:00Z", "Lower Brook Trail reopened",
     ["trail-status", "river-sensors"], "verified",
     "The Lower Brook Trail is open again. Water levels have returned to normal "
     "and staff have inspected the crossing."),
    ("2025-10-10T08:00:00Z", "Fall foliage walk and visitor-center hours",
     ["events", "visitor-center"], "verified",
     "Join a guided foliage walk on the Ridge Loop this month. The visitor "
     "center is open weekends; see the status page for times."),
    ("2026-03-18T07:30:00Z", "Spring trail reopening",
     ["trail-status", "trails"], "verified",
     "Trails are open for the season. Expect mud on the Lower Brook Trail in "
     "early spring and check the status page before high water."),
    ("2026-06-22T06:30:00Z", "High water: Ridge Loop ford closed",
     ["trail-status", "river-sensors", "safety"], "reported",
     "The river-sensor network shows the brook above the safe ford level. The "
     "Ridge Loop ford is closed; use the footbridge route until further notice."),
    ("2026-09-12T08:00:00Z", "Fall trail conditions and sensor update",
     ["trail-status", "river-sensors"], "reported",
     "All trails are open. The Route 9 and Cedar Marsh river sensors were "
     "serviced this month and are reporting normally."),
]


def build_announcements(vault):
    for publish_at, title, subjects, certainty, body in ANNOUNCEMENTS:
        dt = evaluate.parse_datetime(publish_at)
        eff = dt.date().isoformat()
        slug = slugify(title)
        vault.add(
            "announcement",
            {
                "id": f"{eff}-{slug}", "title": title, "type": "announcement",
                "status": "approved", "visibility": "public", "effective": eff,
                "approved": eff, "publish_at": publish_at, "certainty": certainty,
                "subjects": subjects, "tags": ["announcement", eff[:4]],
            },
            dt,
            body=body,
            extra={"publish_at": publish_at, "certainty": certainty},
        )


FAQS = [
    ("2024-12-01", "Is the visitor center open today?",
     ["visitor-center", "hours"],
     "The Watershed Visitor Center is open weekends year-round and daily in "
     "July and August. Winter and holiday hours change; the current hours are "
     "always on the status page."),
    ("2024-12-01", "Are dogs allowed on the trails?",
     ["trails", "rules"],
     "Yes, on a leash. Please carry out what your dog carries in, and keep dogs "
     "out of the marsh and off the river-sensor equipment."),
    ("2025-02-15", "Is the Lower Brook Trail open?",
     ["trail-status", "trails"],
     "Usually. It closes during high water, which the river sensors detect. "
     "Check the status page for the live trail status before you visit."),
    ("2025-02-15", "What do the river sensors measure?",
     ["river-sensors", "water-quality"],
     "Water level and temperature at two gauges, read every fifteen minutes. "
     "Level drives the high-water trail-closure protocol; temperature feeds the "
     "water-quality monitoring partnership."),
    ("2025-05-01", "How do I report a downed tree or a trail hazard?",
     ["trails", "stewardship"],
     "Use the report form on the website. Note the trail and roughly where you "
     "saw it. Staff and stewardship volunteers check reports through the week."),
    ("2025-05-01", "Can I hold an event at the preserve?",
     ["events", "rules"],
     "Small gatherings are welcome on the trails. Organized events and anything "
     "with amplified sound or vehicles need advance permission; ask through the "
     "website."),
    ("2025-08-01", "How do I donate land or a conservation easement?",
     ["easements", "donations"],
     "Start a conversation through the website. The Stewardship Coordinator "
     "will walk you through what the alliance can accept and what stewardship "
     "commitment an easement carries."),
    ("2025-08-01", "What does a conservation easement allow?",
     ["easements", "stewardship"],
     "It depends on the easement's terms, which run with the land. In general "
     "easements limit development while allowing continued stewardship and, "
     "where the terms say so, public access. The specific easement record "
     "governs."),
    ("2026-01-15", "When does the Board meet, and can I attend?",
     ["meetings", "board"],
     "The Board of Trustees meets monthly, usually the third Wednesday. "
     "Meetings are open to the public; the notice and agenda for each are "
     "posted here in advance."),
    ("2026-01-15", "Where are the board minutes and the annual report?",
     ["minutes", "annual-report", "board"],
     "All approved minutes and each year's annual report are in this vault, "
     "under records. Minutes are posted after the Board approves them at the "
     "following meeting."),
    ("2026-04-01", "How is my donation used?",
     ["donations", "finance"],
     "Donations support land stewardship, the visitor center and education "
     "programs, and the river-sensor network. The annual report summarizes the "
     "year's finances."),
    ("2026-09-01", "How do I volunteer?",
     ["volunteering", "stewardship"],
     "The alliance runs stewardship workdays and visitor-center shifts through "
     "the season. Sign up through the website; no experience is needed."),
]


def build_faqs(vault):
    for eff, title, subjects, body in FAQS:
        slug = slugify(title)
        vault.add(
            "faq",
            {
                "id": f"{eff}-{slug}", "title": title, "type": "faq",
                "status": "approved", "visibility": "public", "effective": eff,
                "approved": eff, "certainty": "verified",
                "subjects": subjects, "tags": ["faq"],
            },
            datetime.fromisoformat(eff).replace(tzinfo=timezone.utc) + timedelta(hours=9),
            body=body,
            extra={"certainty": "verified"},
        )


# --------------------------------------------------------------------------- #
# Writing the vault to disk.                                                   #
# --------------------------------------------------------------------------- #

def render_record(vault, rec):
    fm = rec["fm"]
    tokens = dict(vault.base_tokens)
    tokens.update({
        "id": fm["id"], "title": fm["title"], "status": fm["status"],
        "effective": fm["effective"], "approved": fm.get("approved", ""),
        "source_file": fm["source"]["file"], "source_sha": fm["source"]["sha256"],
        "subjects": flow(fm["subjects"]), "tags": flow(fm["tags"]),
        "corrections_block": corrections_block(fm.get("corrections")),
        "certainty": fm.get("certainty", "verified"),
        "body": rec["body"],
        "supersedes_line": "",
    })
    tokens.update(rec["extra"])
    template = (TEMPLATES_DIR / f"{rec['template']}.md").read_text(encoding="utf-8")
    return render(template, tokens)


def write_vault(vault, vault_root):
    if GENERATED_DIR.exists():
        shutil.rmtree(GENERATED_DIR)
    (vault_root / "records").mkdir(parents=True)
    (vault_root / "obligations").mkdir()
    (vault_root / "receipts").mkdir()
    (vault_root / "library" / "files").mkdir(parents=True)
    (vault_root / "assets").mkdir()
    (vault_root / "templates").mkdir()
    (vault_root / "intake").mkdir()
    (vault_root / ".obsidian").mkdir()

    manifest = {}
    # First pass: write source files and fill each record's source sha256.
    for rec in vault.records:
        fm = rec["fm"]
        rel = f"library/files/{fm['type']}/{fm['id']}.txt"
        fpath = vault_root / rel
        fpath.parent.mkdir(parents=True, exist_ok=True)
        data = rec["source_text"].encode("utf-8")
        fpath.write_bytes(data)
        sha = sha256_bytes(data)
        fm["source"] = {"kind": "text", "file": rel, "sha256": sha}
        manifest[rel] = sha

    # Second pass: render and write each record.
    for rec in vault.records:
        fm = rec["fm"]
        out = vault_root / "records" / fm["type"] / f"{fm['id']}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_record(vault, rec), encoding="utf-8")

    # library/manifest.json
    (vault_root / "library" / "manifest.json").write_text(
        json.dumps({"generated_by": "demo/seed.py", "files": manifest},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # obligations/ — copied verbatim from the Massachusetts pack.
    obligations = []
    for oid in ADOPTED_OBLIGATIONS:
        data = json.loads((PACK_DIR / f"{oid}.json").read_text(encoding="utf-8"))
        obligations.append(data)
        (vault_root / "obligations" / f"{oid}.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # receipts/ — one per record, in publish order, each carrying an honest
    # snapshot of the board as it stood at that publish.
    write_receipts(vault, vault_root, obligations)

    # assets/logo.svg — the identity logo, with tokens substituted.
    logo = render(vault.org["logo"], {
        "short_name": vault.org["short_name"], "accent": vault.org["accent"]})
    (vault_root / "assets" / "logo.svg").write_text(logo, encoding="utf-8")

    # templates/record.md — the blank template a human duplicates in Obsidian.
    (vault_root / "templates" / "record.md").write_text(
        (TEMPLATES_DIR / "record-template.md").read_text(encoding="utf-8"),
        encoding="utf-8")

    # index.md
    (vault_root / "index.md").write_text(render_index(vault), encoding="utf-8")

    # validate.toml — see the comment in the file for why no_delete is off here.
    (vault_root / "validate.toml").write_text(VALIDATE_TOML, encoding="utf-8")

    # .obsidian — tracked, relative links, markdown links; the repo never depends
    # on Obsidian.
    (vault_root / ".obsidian" / "app.json").write_text(
        json.dumps({"useMarkdownLinks": True, "newLinkFormat": "relative",
                    "alwaysUpdateLinks": True}, indent=2) + "\n", encoding="utf-8")

    # intake — present but never built or published.
    (vault_root / "intake" / "README.md").write_text(INTAKE_README, encoding="utf-8")

    # standing.json — produced by the core evaluator reading what we just wrote.
    return write_standing(vault_root)


def write_receipts(vault, vault_root, obligations):
    ordered = sorted(enumerate(vault.records), key=lambda t: (t[1]["published_at"], t[0]))
    slug = vault_root.name.rsplit("-records", 1)[0]
    receipts_so_far = []
    for n, (_orig, rec) in enumerate(ordered, start=1001):
        fm = rec["fm"]
        dt = rec["published_at"]
        published_at = iso_z(dt)
        digest = sha256_bytes(f"{fm['id']}|{published_at}".encode("utf-8"))
        receipt = {
            "digest": digest,
            "published_at": published_at,
            "run_url": f"https://github.com/{slug}/{slug}-records/actions/runs/{n}",
            "commit": digest[:10],
            "records": {"added": [fm["id"]], "changed": [], "retracted": []},
        }
        receipts_so_far.append(receipt)
        # Honest snapshot: evaluate only what had been published by this instant.
        pubs = evaluate.publish_index(receipts_so_far)
        records_so_far = [r["fm"] for r in vault.records if r["fm"]["id"] in pubs]
        counts = {"green": 0, "amber": 0, "red": 0, "no_data": 0}
        for ob in obligations:
            row = evaluate.evaluate_obligation(ob, records_so_far, pubs, dt, WARN_DAYS)
            counts[row["state"].replace("-", "_")] += 1
        receipt["standing"] = counts
        name = dt.strftime("%Y%m%d-%H%M%S") + f"-{fm['id']}.json"
        (vault_root / "receipts" / name).write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_index(vault):
    type_titles = {
        "minutes": "Board minutes", "notice": "Meeting notices",
        "agenda": "Meeting agendas", "bylaw": "Bylaws",
        "policy": "Policies", "report": "Annual reports",
        "filing": "Filings", "announcement": "Announcements", "faq": "FAQs",
    }
    by_type = {}
    for rec in vault.records:
        by_type.setdefault(rec["fm"]["type"], []).append(rec["fm"])
    sections = []
    for t in ["minutes", "notice", "agenda", "bylaw", "policy", "report",
              "filing", "announcement", "faq"]:
        items = by_type.get(t)
        if not items:
            continue
        sections.append(f"### {type_titles[t]}\n")
        for fm in sorted(items, key=lambda f: f["id"]):
            link = f"records/{t}/{fm['id']}.md"
            sections.append(f"- [{fm['title']}]({link})")
        sections.append("")
    tokens = dict(vault.base_tokens)
    tokens["record_sections"] = "\n".join(sections).rstrip() + "\n"
    return render((TEMPLATES_DIR / "index.md").read_text(encoding="utf-8"), tokens)


def write_standing(vault_root):
    rows = evaluate.evaluate(vault_root, now=ASOF, warn_days=WARN_DAYS)
    schema_path = CORE_DIR / "schema" / "standing.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = schema_validate(schema, rows, schema)
    if errors:
        raise SystemExit("generated standing.json failed its own schema: " + errors[0])
    (vault_root / "standing.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rows


VALIDATE_TOML = """\
# This vault is generated by demo/seed.py and verified in CI by regenerating and
# diffing it, which is a stronger integrity guarantee than per-file deletion
# tracking. The no_delete check is therefore switched OFF here: renaming the demo
# (docs/adr/0001) changes every record's path at once, which the deletion guard
# would otherwise read as mass deletion. In a REAL client vault, no_delete stays
# on by default — do not copy this setting into one.
[checks]
no_delete = false
"""

INTAKE_README = """\
# intake/

The staging door. Drafts and attachments land here on their way to becoming
records; nothing in this folder is ever built or published. Records and the
index never link into it. This directory is intentionally kept in the demo so
the layout matches a real vault.
"""


# --------------------------------------------------------------------------- #
# Entry point.                                                                 #
# --------------------------------------------------------------------------- #

def generate(seed=DEFAULT_SEED):
    org = load_org(DEMO_DIR / "org.yaml")
    vault_root = GENERATED_DIR / f"{slugify(org['short_name'])}-records"
    rng = random.Random(seed)
    vault = Vault(org, rng)
    build_governance(vault)
    build_meetings(vault)
    build_filings_and_reports(vault)
    build_announcements(vault)
    build_faqs(vault)
    rows = write_vault(vault, vault_root)
    return vault_root, rows


def vault_path():
    org = load_org(DEMO_DIR / "org.yaml")
    return GENERATED_DIR / f"{slugify(org['short_name'])}-records"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the demonstration vault.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"deterministic flavour seed (default: {DEFAULT_SEED})")
    parser.add_argument("--print-vault-path", action="store_true",
                        help="print the generated vault root and exit (generate nothing)")
    parser.add_argument("--print-asof", action="store_true",
                        help="print the pinned evaluation instant and exit")
    args = parser.parse_args(argv)

    if args.print_asof:
        print(iso_z(ASOF))
        return 0
    if args.print_vault_path:
        print(vault_path().as_posix())
        return 0

    vault_root, rows = generate(args.seed)
    counts = {"green": 0, "amber": 0, "red": 0, "no-data": 0}
    for row in rows:
        counts[row["state"]] += 1
    rel = vault_root.relative_to(REPO_ROOT).as_posix()
    n_records = len(list((vault_root / "records").rglob("*.md")))
    print(f"Generated {n_records} records and {len(rows)} obligation rows.")
    print(f"Vault: {rel}")
    print(f"Board as of {iso_z(ASOF)}: "
          f"{counts['green']} green, {counts['amber']} amber, "
          f"{counts['red']} red, {counts['no-data']} no-data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
