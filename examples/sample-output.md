# Sample output

Result of running the scan on [`messy-vault/`](messy-vault/), a small vault with one of each problem planted in it:

```bash
python3 skills/brain-checkup/scripts/vault_scan.py examples/messy-vault --today 2026-10-19
```

```text
# vault_scan · messy-vault · 2026-10-19

## 1. Size
  AGENTS.md                                                7 lines     183 bytes
  MAP.md                                                   9 lines     211 bytes
  knowledge/_index.md                                      7 lines     136 bytes
  knowledge/design/color-palette-notes.md                  9 lines     131 bytes
  knowledge/writing/headline-formulas.md                   4 lines      43 bytes
  knowledge/writing/old-draft-ideas.md                     7 lines      89 bytes
  logs/README.md                                           2 lines      40 bytes
  memory.md                                               91 lines    6276 bytes  ⚠️ over line limit (80) over byte limit (5120)
  memory/projects.md                                       7 lines     221 bytes
  memory/projects/landing-page.md                          4 lines      90 bytes
  memory/projects/newsletter.md                            4 lines      60 bytes
  memory/rules.md                                          5 lines     126 bytes

## 2. Dead links (target not found anywhere)
  memory.md → `memory/tools.md`

## 3. Outdated paths (file exists, but somewhere else)
  MAP.md → `knowledge/color-palette-notes.md`  actually at `knowledge/design/color-palette-notes.md`

## 4. Orphans (not mentioned by any other file)
  knowledge/writing/old-draft-ideas.md

## 5. Notes missing YAML front matter
  knowledge/writing/headline-formulas.md

## 6. Stale projects (no date newer than the limit)
  memory/projects/landing-page.md  last date 2026-07-02 (109 days)

## 7. Same line in more than one rule file
  AGENTS.md:5 = memory.md:5  “1. Never overwrite a file without reading its current version first.”
  memory.md:6 = memory/rules.md:3  “- (2026-05-01) Always confirm before publishing anything.”

---
Total: 12 md files · size issues 1 · dead links 1 · outdated paths 1 · orphans 1 · missing front matter 1 · stale projects 1 · duplicates 2
```
