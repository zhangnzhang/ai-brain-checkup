#!/usr/bin/env python3
"""vault_scan.py — mechanical health check for a Markdown "AI brain" vault.

Usage:
    python3 vault_scan.py /path/to/vault
    python3 vault_scan.py /path/to/vault --config my-config.json
    python3 vault_scan.py /path/to/vault --json          # machine-readable output
    python3 vault_scan.py /path/to/vault --strict        # exit code 1 if anything is found

Only does the mechanical part (sizes, broken links, orphans, front matter,
stale projects, duplicated lines). Judgement calls are left to the agent
following SKILL.md. Python 3.8+, standard library only. Read-only: never
writes to the vault.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Defaults. They match the ai-brain-vault layout; override any of them with a
# JSON config file (see config.example.json) or `.brain-checkup.json` in the
# vault root.
# ---------------------------------------------------------------------------
DEFAULTS = {
    # relative path -> [max_lines, max_bytes or null]
    "limits": {
        "AGENTS.md": [100, None],
        "CLAUDE.md": [40, None],
        "memory.md": [80, 5120],
        "MAP.md": [120, None],
        "memory/projects.md": [30, None],
    },
    # any other .md bigger than this is listed as "large — make sure it is loaded on demand"
    "large_file_lines": 400,
    # folders (relative, trailing slash) that are not scanned for links/orphans
    "skip_dirs": ["logs/", "inbox/_processed/", ".git/", ".obsidian/", ".trash/"],
    # references containing any of these markers point outside the vault
    "external_markers": ["http://", "https://", "~/", "../"],
    # references ending with these extensions are not checked
    "external_extensions": [".json", ".html", ".xlsx", ".csv", ".png", ".jpg", ".svg", ".pdf"],
    # file names that legitimately appear in many places; bare mentions are not links
    "generic_names": ["_index.md", "SKILL.md", "CLAUDE.md", "AGENTS.md", "memory.md", "MAP.md", "README.md"],
    # notes under these folders must start with YAML front matter
    "front_matter_dirs": ["knowledge/"],
    # project detail files: flag if their newest YYYY-MM-DD date is older than N days
    "project_dirs": ["memory/projects/"],
    "stale_days": 30,
    # files compared against each other for duplicated rule lines
    "rule_files": ["AGENTS.md", "memory.md", "memory/rules.md", "memory/facts.md"],
    "duplicate_min_chars": 25,
}

LINK_RE = re.compile(r"`([^`\n]+?\.md)`|\[\[([^\]\n|#]+)|\]\(([^)\s]+?\.md)\)")
DATE_RE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")


def load_config(vault, path):
    cfg = json.loads(json.dumps(DEFAULTS))
    candidate = path or os.path.join(vault, ".brain-checkup.json")
    if candidate and os.path.isfile(candidate):
        with open(candidate, encoding="utf-8") as fh:
            user = json.load(fh)
        for key, value in user.items():
            if key not in cfg:
                print(f"warning: unknown config key '{key}' ignored", file=sys.stderr)
                continue
            cfg[key] = value
    return cfg


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def norm(rel):
    return rel.replace(os.sep, "/")


def collect(vault, cfg):
    files, by_name = [], {}
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            rel = norm(os.path.relpath(os.path.join(dirpath, name), vault))
            files.append(rel)
            by_name.setdefault(name, []).append(rel)
            by_name.setdefault(name[:-3], []).append(rel)  # Obsidian wikilinks omit .md
    scanned = [f for f in files if not f.startswith(tuple(cfg["skip_dirs"]))]
    return sorted(files), sorted(scanned), by_name


def is_external(target, cfg):
    return (target.startswith("/")
            or any(m in target for m in cfg["external_markers"])
            or target.lower().endswith(tuple(cfg["external_extensions"])))


def check_sizes(vault, files, cfg):
    rows, problems = [], []
    for rel in files:
        text = read(os.path.join(vault, rel))
        if text is None:
            continue
        lines, size = text.count("\n") + 1, len(text.encode("utf-8"))
        note = ""
        if rel in cfg["limits"]:
            max_lines, max_bytes = cfg["limits"][rel]
            if lines > max_lines:
                note += f" over line limit ({max_lines})"
            if max_bytes and size > max_bytes:
                note += f" over byte limit ({max_bytes})"
            if note:
                problems.append({"file": rel, "lines": lines, "bytes": size, "issue": note.strip()})
        elif lines > cfg["large_file_lines"]:
            note = " large — make sure it is loaded on demand"
        rows.append({"file": rel, "lines": lines, "bytes": size, "note": note.strip()})
    return rows, problems


def check_links(vault, scanned, by_name, cfg):
    dead, moved = set(), set()
    generic = set(cfg["generic_names"])
    for rel in scanned:
        text = read(os.path.join(vault, rel)) or ""
        here = os.path.dirname(os.path.join(vault, rel))
        for match in LINK_RE.finditer(text):
            target = (match.group(1) or match.group(2) or match.group(3)).strip()
            if not target or is_external(target, cfg) or any(c in target for c in "<>*{}"):
                continue
            if "/" not in target and os.path.basename(target) in generic:
                continue
            if os.path.exists(os.path.join(here, target)) or os.path.exists(os.path.join(vault, target)):
                continue
            hits = by_name.get(os.path.basename(target)) or by_name.get(target)
            if hits and "/" in target:
                moved.add((rel, target, hits[0]))
            elif not hits:
                dead.add((rel, target))
    return ([{"in": a, "link": b} for a, b in sorted(dead)],
            [{"in": a, "link": b, "actual": c} for a, b, c in sorted(moved)])


def check_orphans(vault, scanned, cfg):
    corpus = "\n".join(read(os.path.join(vault, r)) or "" for r in scanned)
    generic = set(cfg["generic_names"])
    orphans = []
    for rel in scanned:
        base = os.path.basename(rel)
        if base in generic or base.startswith("_index"):
            continue
        others = corpus.replace(read(os.path.join(vault, rel)) or "", "", 1)
        if base[:-3] not in others and rel not in others:
            orphans.append(rel)
    return orphans


def check_front_matter(vault, scanned, cfg):
    missing = []
    for rel in scanned:
        if not rel.startswith(tuple(cfg["front_matter_dirs"])):
            continue
        if os.path.basename(rel).startswith("_index") or os.path.basename(rel) == "README.md":
            continue
        if not (read(os.path.join(vault, rel)) or "").lstrip().startswith("---"):
            missing.append(rel)
    return missing


def check_stale_projects(vault, scanned, cfg, today):
    stale = []
    for rel in scanned:
        if not rel.startswith(tuple(cfg["project_dirs"])):
            continue
        dates = []
        for y, m, d in DATE_RE.findall(read(os.path.join(vault, rel)) or ""):
            try:
                dates.append(dt.date(int(y), int(m), int(d)))
            except ValueError:
                pass
        if not dates:
            stale.append({"file": rel, "last_date": None, "days": None})
            continue
        newest = max(dates)
        age = (today - newest).days
        if age > cfg["stale_days"]:
            stale.append({"file": rel, "last_date": newest.isoformat(), "days": age})
    return stale


def check_duplicates(vault, cfg):
    seen, dupes = {}, []
    strip = re.compile(r"^[\s>*\-+\d.|#]+|[\s*_`|]+$")
    for rel in cfg["rule_files"]:
        text = read(os.path.join(vault, rel))
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            key = strip.sub("", line)
            key = re.sub(r"^\(\s*20\d\d-\d\d-\d\d\s*\)\s*", "", key)  # ignore a leading "(YYYY-MM-DD)"
            key = re.sub(r"\s+", " ", key).strip().lower()
            if len(key) < cfg["duplicate_min_chars"]:
                continue
            if key in seen and seen[key][0] != rel:
                dupes.append({"text": line.strip()[:120], "first": f"{seen[key][0]}:{seen[key][1]}",
                              "again": f"{rel}:{lineno}"})
            else:
                seen.setdefault(key, (rel, lineno))
    return dupes


def run(vault, cfg, today):
    files, scanned, by_name = collect(vault, cfg)
    sizes, size_problems = check_sizes(vault, files, cfg)
    dead, moved = check_links(vault, scanned, by_name, cfg)
    return {
        "vault": vault,
        "date": today.isoformat(),
        "files": len(files),
        "sizes": sizes,
        "size_problems": size_problems,
        "dead_links": dead,
        "moved_links": moved,
        "orphans": check_orphans(vault, scanned, cfg),
        "missing_front_matter": check_front_matter(vault, scanned, cfg),
        "stale_projects": check_stale_projects(vault, scanned, cfg, today),
        "duplicates": check_duplicates(vault, cfg),
    }


def render(r):
    out = [f"# vault_scan · {os.path.basename(r['vault'])} · {r['date']}", "", "## 1. Size"]
    for row in r["sizes"]:
        flag = f"  ⚠️ {row['note']}" if row["note"] else ""
        for p in r["size_problems"]:
            if p["file"] == row["file"]:
                flag = f"  ⚠️ {p['issue']}"
        out.append(f"  {row['file']:<52} {row['lines']:>5} lines {row['bytes']:>7} bytes{flag}")

    def section(title, items, fmt):
        out.extend(["", title])
        out.extend([fmt(i) for i in items] or ["  (none)"])

    section("## 2. Dead links (target not found anywhere)", r["dead_links"],
            lambda i: f"  {i['in']} → `{i['link']}`")
    section("## 3. Outdated paths (file exists, but somewhere else)", r["moved_links"],
            lambda i: f"  {i['in']} → `{i['link']}`  actually at `{i['actual']}`")
    section("## 4. Orphans (not mentioned by any other file)", r["orphans"], lambda i: f"  {i}")
    section("## 5. Notes missing YAML front matter", r["missing_front_matter"], lambda i: f"  {i}")
    section("## 6. Stale projects (no date newer than the limit)", r["stale_projects"],
            lambda i: f"  {i['file']}  last date {i['last_date']} ({i['days']} days)" if i["last_date"]
            else f"  {i['file']}  no date found")
    section("## 7. Same line in more than one rule file", r["duplicates"],
            lambda i: f"  {i['first']} = {i['again']}  “{i['text']}”")

    out += ["", "---", "Total: {files} md files · size issues {a} · dead links {b} · outdated paths {c} · "
            "orphans {d} · missing front matter {e} · stale projects {f} · duplicates {g}".format(
                files=r["files"], a=len(r["size_problems"]), b=len(r["dead_links"]), c=len(r["moved_links"]),
                d=len(r["orphans"]), e=len(r["missing_front_matter"]), f=len(r["stale_projects"]),
                g=len(r["duplicates"]))]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Mechanical health check for a Markdown AI-brain vault.")
    ap.add_argument("vault", help="path to the vault folder")
    ap.add_argument("--config", help="JSON config file (default: <vault>/.brain-checkup.json if present)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of the text report")
    ap.add_argument("--strict", action="store_true", help="exit with code 1 if any issue is found")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for testing")
    args = ap.parse_args()

    vault = os.path.abspath(args.vault)
    if not os.path.isdir(vault):
        ap.error(f"not a folder: {vault}")
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    report = run(vault, load_config(vault, args.config), today)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))

    issues = sum(len(report[k]) for k in ("size_problems", "dead_links", "moved_links", "orphans",
                                          "missing_front_matter", "stale_projects", "duplicates"))
    sys.exit(1 if args.strict and issues else 0)


if __name__ == "__main__":
    main()
