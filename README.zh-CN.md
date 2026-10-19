# ai-brain-checkup

[English](README.md) | 简体中文

给 AI 助手每天要读的 Markdown "大脑"做体检。一个 Python 脚本负责找出机械性问题，一个 Skill 负责把问题整理成按优先级排好的修复清单。

任何被 AI 当作记忆来读的 Markdown 笔记文件夹都能用，用不用 Obsidian 都行。默认配置适配常见的 `AGENTS.md` / `memory.md` / `MAP.md` 结构，所有设置都可以改。

## 为什么需要它

AI 的记忆库会悄悄变烂：

- 每次会话都要加载的索引文件越写越长，token 越烧越多；
- 同一条规则被抄进三个文件，后来各改各的；
- 笔记挪了位置，指向它的链接就断了；
- 几个月没人碰的项目还挂在"进行中"列表里。

这些都不会报错，等你发现时，AI 已经在按过期或互相矛盾的规则干活了。

## 检查什么

| # | 检查项 | 发现示例 |
|---|---|---|
| 1 | 每次都加载的文件**是否超长** | `memory.md` 91 行 / 6.2 KB，上限 80 行 / 5 KB |
| 2 | **死链** | `memory.md` → `memory/tools.md`（文件不存在） |
| 3 | **路径过时** | `MAP.md` 写的是 `knowledge/x.md`，文件实际在 `knowledge/design/x.md` |
| 4 | **孤儿笔记**：没有任何文件提到它 | `knowledge/writing/old-draft-ideas.md` |
| 5 | 知识笔记**缺少 front matter** | `knowledge/writing/headline-formulas.md` |
| 6 | **过期项目**：30 天内没有任何日期更新 | `landing-page.md`，最后日期是 109 天前 |
| 7 | **规则重复**：同一行出现在多个规则文件里 | `AGENTS.md:5` = `memory.md:5` |

Skill 还会补上脚本做不到的判断：规则写进了事实文件（或反过来）、同一条规则换了说法重复出现、一直在等你拍板的事项；每条需要你批准的改动，都会附上准确的替换文本。

完整输出见[示例报告](examples/sample-output.md)，它来自一个故意弄乱的[示例仓库](examples/messy-vault/)。

## 快速开始

### 只用脚本

需要 Python 3.8+，不依赖任何第三方库，只读不写。

```bash
python3 skills/brain-checkup/scripts/vault_scan.py /你的/仓库/路径
python3 skills/brain-checkup/scripts/vault_scan.py /你的/仓库/路径 --json     # 输出 JSON，方便接其他工具
python3 skills/brain-checkup/scripts/vault_scan.py /你的/仓库/路径 --strict   # 发现问题时以 1 退出（适合 CI）
```

### 作为 AI Skill 使用

把 `skills/brain-checkup/` 复制到 AI 的 skills 目录（Claude 是 `~/.claude/skills/` 或项目里的 `.claude/skills/`），然后说：

> 给我的仓库做一次大脑体检，先只读。

Skill 会跑扫描、复核结果，然后给出执行摘要、按 `P0` / `P1` / `P2` 排序的发现（每条都带文件和行号），另外分两张清单：它自己修了什么（只限低风险）、哪些需要你批准。

不支持 Skill 的 AI 工具，可以把 `SKILL.md` 当普通指令文件读。

## 配置

默认值按常见结构设定（`AGENTS.md`、`CLAUDE.md`、`memory.md`、`MAP.md`、`memory/`、`knowledge/`）。结构不同的话，在仓库根目录放一个 `.brain-checkup.json`（或用 `--config` 指定），可以从 [`config.example.json`](skills/brain-checkup/config.example.json) 改起：

| 配置项 | 控制什么 |
|---|---|
| `limits` | 各文件的行数 / 字节上限 |
| `skip_dirs` | 不检查链接和孤儿的目录（备份、已处理的 inbox） |
| `front_matter_dirs` | 哪些目录的笔记必须以 YAML front matter 开头 |
| `project_dirs`、`stale_days` | 项目文件在哪、多少天没更新算过期 |
| `rule_files`、`duplicate_min_chars` | 哪些文件之间比对重复规则 |
| `external_markers`、`external_extensions`、`generic_names` | 哪些引用**不**算内部链接 |

## 安全

- 脚本只读，不会写入你的仓库。
- Skill 改任何文件前先备份，从不删除；高风险文件（规则、事实、红线、宪法）只提案不直接改。

## 许可证

[MIT](LICENSE)
