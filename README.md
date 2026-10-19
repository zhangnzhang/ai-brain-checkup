# ai-brain-checkup

English | [简体中文](README.zh-CN.md)

A health check for the Markdown "brain" your AI agents read every day. One Python script finds the mechanical problems; one agent skill turns them into a prioritized fix list.

Works on any folder of Markdown notes that an agent reads as memory — Obsidian or not. The defaults fit the common `AGENTS.md` / `memory.md` / `MAP.md` layout, and everything is configurable.

## Why

An AI memory vault rots quietly:

- the index file that is loaded every session keeps growing, and so does your token bill;
- the same rule ends up in three files, then the copies drift apart;
- notes get moved and the links pointing to them break;
- projects nobody has touched in months still sit in the "active" list.

None of this throws an error. You only notice when the agent starts acting on stale or contradictory instructions.

## What it checks

| # | Check | Example finding |
|---|---|---|
| 1 | **Size limits** on the files loaded every session | `memory.md` is 91 lines / 6.2 KB, limit 80 / 5 KB |
| 2 | **Dead links** | `memory.md` → `memory/tools.md` (doesn't exist) |
| 3 | **Outdated paths** | `MAP.md` points to `knowledge/x.md`, the file is now in `knowledge/design/x.md` |
| 4 | **Orphan notes** that no other file mentions | `knowledge/writing/old-draft-ideas.md` |
| 5 | **Missing front matter** on knowledge notes | `knowledge/writing/headline-formulas.md` |
| 6 | **Stale projects** with no date newer than 30 days | `landing-page.md`, last date 109 days ago |
| 7 | **Duplicated rules** across rule files | `AGENTS.md:5` = `memory.md:5` |

The skill then adds the judgement a script can't make: rules sitting in the facts file (and vice versa), the same rule in different words, projects waiting on you forever, and an exact replacement text for every change that needs your approval.

See the full [sample output](examples/sample-output.md), produced from the deliberately messy [example vault](examples/messy-vault/).

## Quick start

### Just the script

Python 3.8+, no dependencies, read-only.

```bash
python3 skills/brain-checkup/scripts/vault_scan.py /path/to/your/vault
python3 skills/brain-checkup/scripts/vault_scan.py /path/to/your/vault --json     # for other tools
python3 skills/brain-checkup/scripts/vault_scan.py /path/to/your/vault --strict   # exit 1 if anything is found (CI)
```

### As an agent skill

Copy `skills/brain-checkup/` into your agent's skills folder (for Claude: `~/.claude/skills/` or your project's `.claude/skills/`), then ask:

> Run a brain checkup on my vault. Read-only for now.

The skill runs the scan, reviews the results, and returns an executive summary, prioritized findings (`P0` / `P1` / `P2`, each with file and line), and two lists: what it fixed itself (low risk only) and what needs your approval.

Agents without skill support can read `SKILL.md` as a plain instruction file.

## Configuration

Defaults assume a common layout (`AGENTS.md`, `CLAUDE.md`, `memory.md`, `MAP.md`, `memory/`, `knowledge/`). For a different structure, put a `.brain-checkup.json` in the vault root (or pass `--config`). Start from [`config.example.json`](skills/brain-checkup/config.example.json):

| Key | What it controls |
|---|---|
| `limits` | Max lines / bytes per file |
| `skip_dirs` | Folders ignored for links and orphans (backups, processed inbox) |
| `front_matter_dirs` | Folders whose notes must start with YAML front matter |
| `project_dirs`, `stale_days` | Where project files live and when they count as stale |
| `rule_files`, `duplicate_min_chars` | Which files are compared for duplicated rules |
| `external_markers`, `external_extensions`, `generic_names` | What is *not* treated as an internal link |

## Safety

- The script only reads. It never writes to your vault.
- The skill backs up a file before any edit, never deletes, and only proposes changes to high-risk files (rules, facts, red lines, the constitution).

## License

[MIT](LICENSE)
