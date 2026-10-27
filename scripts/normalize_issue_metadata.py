"""One-time, idempotent removal of label-duplicated metadata from OEM issues.

The source-of-truth for priority, type, stage, severity, iteration, and points
is the issue's GitHub labels/milestone or native Project fields—not its title/body.
This script intentionally keeps substantive task scope, scientific limitations,
reference identifiers, dependencies, and user-story acceptance evidence.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "OEM-issue-content-normalizer",
}
SPRINT_TITLES = {
    "S0": "Reproducible installation, physical contracts and IP readiness",
    "S1": "First-law tolerances, benchmark references and report contracts",
    "S2": "Analytical reference cases, negative controls and user discovery",
    "S3": "Manufactured benchmarks, false-alarm scoring and governance",
}

def api(method, endpoint, payload=None):
    url = f"https://api.github.com/repos/{REPO}/{endpoint}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub {method} {endpoint}: {exc.code} {exc.read().decode(errors='replace')[:250]}") from exc

def normalize_title(issue):
    title = issue["title"]
    name_set = {x["name"] for x in issue.get("labels", [])}
    sprint_label = next((x for x in name_set if re.fullmatch(r"sprint:S[0-3]", x)), None)
    if title.startswith("SPRINT ") and sprint_label:
        return SPRINT_TITLES[sprint_label.split(":", 1)[1]]
    return re.sub(r"^(?:P[012]\s+\|\s+|EPIC E\d+\s+\|\s+|SPRINT S\d+\s+\|\s+|ROADMAP\s+\|\s+)", "", title).strip()

def normalize_body(issue):
    body = issue.get("body") or ""
    sources = []

    # Remove entire metadata-only sections; preserve references to the
    # internal research report as short research-basis text.
    def remove_meta_section(match):
        section = match.group(0)
        m = re.search(r"(?m)^-\s+\*\*Source(?: mapping)?:\*\*\s*(.+)$", section)
        if m:
            sources.append(m.group(1).strip())
        return "\n"

    body = re.sub(
        r"(?ms)^## (?:Project tracking|Tracking|Scrum|Scrum ceremonies)\s*\n.*?(?=^## |\Z)",
        remove_meta_section, body,
    )

    # A few earlier issues contain inline priority/iteration bookkeeping.
    def planning_line(match):
        value = match.group(1).strip()
        if "Founder's Research Bible" in value:
            value = value.split(";", 1)[-1].strip()
            value = re.sub(r"\s+No external validation is claimed\.\s*$", "", value)
            sources.append(value)
        return ""
    body = re.sub(r"(?m)^\*\*Planning:\*\*\s*(.+?)\s*$", planning_line, body)

    def source_priority_line(match):
        value = match.group(1)
        value = re.split(r"\s+\*\*Priority:\*\*", value, maxsplit=1)[0].strip()
        if value:
            sources.append(value)
        return ""
    body = re.sub(
        r"(?m)^\*\*Source:\*\*\s*(.+?\*\*Priority:\*\*.+)$",
        source_priority_line, body,
    )

    # Sprint planning is part of the issue's labels, Project fields and report.
    body = re.sub(
        r"(?m)^## Sprint S\d+\s+—\s+user story and demo criterion\s*$",
        "## User story and acceptance evidence", body,
    )
    body = re.sub(
        r"(?m)^## Candidate sprint backlog \([^)]*\)\s*$",
        "## Planned stories", body,
    )
    body = re.sub(r"(?m)[ \t]+—[ \t]+\*\*\d+[ \t]+points\*\*(?=[ \t]*$)", "", body)
    body = re.sub(r"(?m)^\*\*Project ownership:\*\*.*$\n?", "", body)

    # Rename grouping headings in master trackers without changing links.
    headings = {
        "## P0 — contract, truthfulness, installability and synthetic benchmark quality": "## Scientific foundation and reproducible checks",
        "## P1 — externally meaningful scientific evidence, late 2026–mid 2027": "## Independent external evidence",
        "## P2 — conditional work, no promise of delivery": "## Conditional future research",
        "## P0 — build a safe and credible organizational foundation": "## Organizational foundations",
        "## P1 — real user evidence, collaboration and sustainable operations": "## User research and sustainable operations",
        "## P2 — evidence-dependent scale and institutionalization": "## Conditional organizational growth",
    }
    for old, new in headings.items():
        body = body.replace(old, new)

    # Clear boilerplate repeated in all issues without removing the actual
    # data-rights and validation restrictions inside the task and acceptance text.
    body = re.sub(
        r"(?m)^_This issue is a public work item derived from an internal strategy document;.*_\s*$",
        "", body,
    )
    existing = "Founder's Research Bible" in body
    if sources and not existing:
        unique = list(dict.fromkeys(sources))
        body = body.rstrip() + "\n\n**Research basis:** " + "; ".join(unique) + "\n"

    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"

changes = []
skips = 0
for page in range(1, 5):
    issues = api("GET", f"issues?state=all&per_page=100&page={page}")
    if not issues:
        break
    for issue in issues:
        if "pull_request" in issue:
            continue
        title = normalize_title(issue)
        body = normalize_body(issue)
        if title != issue["title"] or body.rstrip() != (issue.get("body") or "").rstrip():
            changes.append((issue["number"], title, body, issue["title"]))
        else:
            skips += 1
    if len(issues) < 100:
        break

print(f"{REPO}: {len(changes)} issues to normalize; {skips} unchanged.")
for number, title, body, original_title in changes:
    api("PATCH", f"issues/{number}", {"title": title, "body": body})
    print(f"#{number} {original_title} => {title}")

print(f"Completed {len(changes)} issue title/body updates in {REPO}.")
