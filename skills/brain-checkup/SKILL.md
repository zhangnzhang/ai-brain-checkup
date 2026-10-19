---
name: brain-checkup
description: Health check for a Markdown "AI brain" vault (memory + rules + knowledge that agents read). Finds oversized root files, misplaced memory, duplicated rules, broken or outdated links, orphan notes, stale projects and index drift, then outputs findings plus a fix list. Use when the user says "check my vault", "brain checkup", "hygiene pass", "audit my memory", "my memory is a mess", "token usage is too high", or on a monthly schedule.
---

# Brain checkup

Run a structural health check on a Markdown vault that AI agents use as long-term memory (typically an entry file such as `AGENTS.md` or `CLAUDE.md`, a memory index like `memory.md`, a map like `MAP.md`, plus `memory/` and `knowledge/` folders).

**Goal:** keep the fixed per-session token cost low and stop memory from rotting.

## Ground rules (read before touching anything)

1. **Read the vault's own constitution first** (`AGENTS.md`, `memory.md`, or whatever the vault uses as its entry point). If this skill and the vault's rules disagree, the vault's rules win.
2. **Two tiers of changes:**
   - **Low risk → fix directly, then list what you changed:** index lines in `MAP.md` / `_index.md` / `memory.md`, broken or outdated link paths, single-line project status in `memory/projects.md`.
   - **High risk → propose only, never write yourself:** red lines, `memory/rules.md`, `memory/facts.md`, `AGENTS.md`. Every proposal includes the **exact replacement text**, so the owner can approve it in one sentence.
3. **Back up before editing:** copy each file you are about to change to `logs/<file>-before-checkup-<YYYY-MM-DD>.md`.
4. **Never delete.** Outdated notes move to `knowledge/_archive/` (create it if missing). Finished projects follow the vault's archive rule.
5. If the user only asked to *check* or *audit*, stay read-only: report and propose, change nothing.

## Process

### Step 0 · Run the mechanical scan

```bash
python3 scripts/vault_scan.py /path/to/vault
```

It reports: file sizes vs. limits, dead links, outdated paths, orphan notes, notes missing front matter, stale project files, and identical lines repeated across rule files. Limits and folders are configurable (`--config`, or `.brain-checkup.json` in the vault root; see `config.example.json`). **Read its output first, then apply judgement in the steps below.** The scan is a lead, not a verdict.

### Step 1 · Size

| File | Default limit | If over |
|---|---|---|
| `memory.md` | 80 lines / 5 KB | Compress and push details into `memory/` topic files. **Never raise the limit.** |
| `memory/projects.md` | 30 lines | Archive finished projects; move details into `memory/projects/<project>.md`. |
| `memory/*.md` topic files | ~60 lines each | Split into sub-files or archive old entries. |
| `AGENTS.md` / `CLAUDE.md` | as short as possible, hard cap ~100 / 40 lines | Move task-specific sections into an SOP note and leave a one-line pointer. |

Every over-limit item must name **the exact file the content should move to**. "Too long" alone is not a finding.

### Step 2 · Misplacement (rules vs. facts)

- In `memory.md` / `memory/facts.md`, look for **normative** lines ("always / never / must / first … then …") whose purpose is to govern behaviour → they belong in `memory/rules.md` or the constitution.
- In `memory/rules.md` / `AGENTS.md`, look for **factual** lines that describe a state that can change tomorrow (IDs, prices, who is doing what right now) → they belong in `memory/facts.md` or a project file.
- In `memory/projects.md`, look for **anything longer than one line** (IDs, parameters, open-item lists) → it belongs in `memory/projects/<project>.md`.

### Step 3 · Duplication

Each rule lives in **exactly one file**. Compare red lines ↔ `rules.md` ↔ `AGENTS.md` ↔ any skill files that restate rules. The scan catches identical lines; you also look for the same rule in different words. For each duplicate, decide which file is the single source of truth and turn the others into a one-line pointer. Skills should point to the source of truth, not copy rules from each other.

### Step 4 · Staleness and broken links

- Project files with **no update in 30+ days** → list them and ask whether the project is finished or parked.
- Items that have been **waiting on the owner** for a long time → collect them in their own list. These rot fastest.
- Projects marked finished but not fully archived (summary archived + index row removed + project file moved) → P0.
- Dead links, outdated paths and orphans from the scan → low risk, fix directly (or propose, if read-only).

### Step 5 · Report

Always in this shape, **executive summary first**:

```
## Executive summary
(≤ 3 lines: what was checked, the N most serious problems, how many low-risk fixes I already made)

## Findings
Sorted P0 / P1 / P2, one line each:
- **[P0] <problem in one sentence>** — `file:line` · why it matters (one sentence) · suggested action (one sentence)

## Fixed (low risk)
- <file> — <what changed> (backup in logs/…)

## Needs approval (high risk, with exact replacement text)
- <file> — now: `…` → proposed: `…` · reason
```

**No vague advice.** If a finding cannot point to a file and line, leave it out.

### Step 6 · Verify before sending

Audits produce false positives too. **Re-open the source file for every P0** and confirm it. Anything you could not confirm is downgraded to P1 and marked "needs re-check".

## Scheduling it

Run monthly. A good scheduled prompt: *"Run the brain-checkup skill on <vault path>. Read-only: report findings and proposals, change nothing."* Register the schedule in the vault's `memory/schedules.md` so it is not created twice.
