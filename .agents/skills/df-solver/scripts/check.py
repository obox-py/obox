#!/usr/bin/env python3
"""Deterministic structural check for dev-flow artifacts.

Usage:
  python check.py --proj <df_proj_dir> --us <df_us_id> [--baseline-only]

Prints one JSON object:
  {"ok": bool, "issues": [{"level","code","file","line","message"}], "stats": {...}}
Exit code 1 when any 严重 issue exists.
"""
import argparse
import json
import os
import re
import sys

SPEC_SECTIONS = ["## Purpose", "## Requirements"]
DESIGN_SECTIONS = ["## Context", "## Goals / Non-Goals", "## Decisions", "## Risks / Trade-offs"]
DELTA_ARCH_SECTIONS = ["## 变更背景", "## 待修改模块", "## 直接关联模块",
                      "## 时序图", "## UML 图", "## 对整体架构的影响"]
DELTA_SPEC_SECTIONS = ["## ADDED Requirements", "## MODIFIED Requirements",
                       "## REMOVED Requirements", "## RENAMED Requirements"]
DELTA_DESIGN_SECTIONS = [
    "## Context", "## Scope", "## Changes", "## Baseline Diff", "## Risks / Rollback",
]
LEVELS = ("严重", "一般", "建议")
HANDLES = ("已修复", "待验证", "待用户决策", "需上游修正", "不修复")

issues = []


def add(level, code, path, line, message):
    issues.append({"level": level, "code": code, "file": os.path.basename(path), "line": line, "message": message})


def read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def discover_specs(spec_dir):
    """[(path, capability)] — single-file layout, or one file per capability."""
    out = []
    single = os.path.join(spec_dir, "spec.md")
    if os.path.exists(single):
        out.append((single, None))
    try:
        names = sorted(os.listdir(spec_dir))
    except OSError:
        return out
    for name in names:
        sub = os.path.join(spec_dir, name, "spec.md")
        if os.path.isdir(os.path.join(spec_dir, name)) and os.path.exists(sub):
            out.append((sub, name))
    return out


def check_adr_links(path, text, proj):
    for m in re.finditer(r"docs/adr/[A-Za-z0-9_.\-]+\.md", text):
        if not os.path.exists(os.path.join(proj, m.group(0))):
            add("一般", "W_ADR_LINK", path, 1, f"引用了不存在的 ADR：{m.group(0)}")


def status_of(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.strip().startswith("status:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def headings(text):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## ") or line.startswith("### ") or line.startswith("#### "):
            out.append((i, line.strip()))
    return out


def requirements(text):
    """[(line, name, body)] for each '### Requirement:'."""
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"^###\s+Requirement:\s*(.*)$", line.strip())
        if not m:
            continue
        body = []
        for nxt in lines[i + 1:]:
            if nxt.startswith("### ") or nxt.startswith("## "):
                break
            body.append(nxt)
        out.append((i + 1, m.group(1).strip(), "\n".join(body)))
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).strip().strip("\u3000").lower()


def check_frontmatter(path, text, severity="严重"):
    """Baseline files are judged by existence, not status: pass severity='一般' for them."""
    prefix = "W" if severity == "一般" else "E"
    st = status_of(text)
    if st is None:
        add(severity, f"{prefix}_FM_MISSING", path, 1, "frontmatter 缺 status 字段")
        return False
    if st != "done":
        add(severity, f"{prefix}_FM_NOT_DONE", path, 1, f"status 是 {st}，未定稿")
        return False
    return True


def check_placeholders(path, text):
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"<[^<>\n]{1,60}>", line) or "TODO" in line:
            add("一般", "W_PLACEHOLDER", path, i, "残留占位符或 TODO")
        if re.search(r"\{\{[^}]{1,60}\}\}", line):
            add("严重", "E_TEMPLATE_BRACE", path, i, "模板占位符 {{...}} 未替换")


def check_spec(path, text):
    body_lines = [l for l in text.splitlines() if not l.strip().startswith("<!--")]
    body = "\n".join(body_lines)
    for sec in SPEC_SECTIONS:
        if sec not in text:
            add("严重", "E_SPEC_SECTION", path, 1, f"缺小节 {sec}")
    purpose = ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "## Purpose":
            for nxt in lines[i + 1:]:
                if nxt.startswith("## "):
                    break
                purpose += nxt.strip()
            break
    if len(purpose) < 50:
        add("一般", "W_PURPOSE_SHORT", path, 1, f"Purpose 只有 {len(purpose)} 字符，openspec 建议 >= 50")
    reqs = requirements(text)
    if not reqs:
        add("严重", "E_SPEC_NO_REQ", path, 1, "没有任何 ### Requirement:")
    for line, name, body in reqs:
        if "#### Scenario:" not in body:
            add("严重", "E_SPEC_NO_SCENARIO", path, line, f"需求 {name!r} 没有 #### Scenario:")
        else:
            for seg in body.split("#### Scenario:")[1:]:
                if "**WHEN**" not in seg or "**THEN**" not in seg:
                    add("严重", "E_SCENARIO_BODY", path, line, f"需求 {name!r} 的场景缺 WHEN 或 THEN")
    return {norm(n) for _, n, _ in reqs}


def check_design(path, text):
    for sec in DESIGN_SECTIONS:
        if sec not in text:
            add("严重", "E_DESIGN_SECTION", path, 1, f"缺小节 {sec}")
    check_mermaid(path, text)


def check_mermaid(path, text):
    fences = text.count("```")
    if fences % 2 != 0:
        add("严重", "E_MERMAID_FENCE", path, 1, "代码围栏数量为奇数，存在未闭合围栏")
    if "mermaid" in text and text.count("```mermaid") == 0:
        add("一般", "W_MERMAID_TAG", path, 1, "出现 mermaid 字样但没有 ```mermaid 围栏")


def check_delta_spec(path, text, baseline_reqs):
    present = [s for s in DELTA_SPEC_SECTIONS if s in text]
    if not present:
        if "## Skipped" in text:
            return []  # 显式声明本次不动需求，是合法产出
        add("严重", "E_DELTA_NO_SECTION", path, 1, "四个差异小节一个都没有，也没写 ## Skipped")
    reqs = requirements(text)
    for line, name, body in reqs:
        if "#### Scenario:" not in body:
            add("严重", "E_DELTA_NO_SCENARIO", path, line, f"差异需求 {name!r} 没有场景")
    if baseline_reqs is not None:
        section = None
        for i, raw in enumerate(text.splitlines(), 1):
            if raw.startswith("## "):
                section = raw.strip()
            m = re.match(r"^###\s+Requirement:\s*(.*)$", raw.strip())
            if m and section and ("MODIFIED" in section or "REMOVED" in section):
                if norm(m.group(1)) not in baseline_reqs:
                    add("严重", "E_DELTA_REF", path, i,
                        f"{section} 里的 {m.group(1)!r} 在基线 spec.md 中找不到")
    return [n for _, n, _ in reqs]


def check_delta_design(path, text):
    for sec in DELTA_DESIGN_SECTIONS:
        if sec not in text:
            add("严重", "E_DDESIGN_SECTION", path, 1, f"缺小节 {sec}")
    check_mermaid(path, text)


def check_task(path, text, delta_reqs):
    rows = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s.startswith("|") or set(s) <= set("|- "):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and norm(cells[0]) in ("id",):
            continue
        if len(cells) != 8:
            add("严重", "E_TASK_COLUMNS", path, i, f"表格有 {len(cells)} 列，应为 8 列")
            continue
        rows.append({"line": i, "id": cells[0], "mode": cells[2], "req": cells[4], "dep": cells[5], "status": cells[7]})
    if not rows:
        add("严重", "E_TASK_EMPTY", path, 1, "任务表为空")
        return
    for sec, code in (("## 任务详情", "W_TASK_DETAILS"), ("## 自检", "W_TASK_SELFREVIEW"),
                      ("## 测试策略", "W_TASK_TESTSTRATEGY")):
        if sec not in text:
            add("一般", code, path, 1, f"缺 {sec} 小节")
    ids = {r["id"] for r in rows}
    for r in rows:
        if r["mode"] not in ("主 Agent", "subagent", "后台"):
            add("严重", "E_TASK_MODE", path, r["line"], f"{r['id']} 的 方式 {r['mode']!r} 不在三值之内")
        if r["status"] not in ("待办", "进行中", "完成", "阻塞"):
            add("严重", "E_TASK_STATUS", path, r["line"], f"{r['id']} 的 状态 {r['status']!r} 非法")
        for dep in re.findall(r"T\d+", r["dep"]):
            if dep not in ids:
                add("严重", "E_TASK_DEP", path, r["line"], f"{r['id']} 依赖不存在的 {dep}")
    # 覆盖检查
    covered = " ".join(r["req"] for r in rows)
    for req in delta_reqs or []:
        if req not in norm(covered):
            add("严重", "E_TASK_COVER", path, 1, f"需求 {req!r} 没有被任何任务覆盖")
    # 环检测
    graph = {r["id"]: re.findall(r"T\d+", r["dep"]) for r in rows}
    state = {}

    def walk(node, stack):
        if state.get(node) == 1:
            add("严重", "E_TASK_CYCLE", path, 1, f"依赖有环：{' -> '.join(stack + [node])}")
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for nxt in graph.get(node, []):
            walk(nxt, stack + [node])
        state[node] = 2

    for node in graph:
        walk(node, [])


def check_scope(path, text, changed):
    for sec in ("## 可改", "## 明确不动", "## 越界处置"):
        if sec not in text:
            add("严重", "E_SCOPE_SECTION", path, 1, f"缺小节 {sec}")
    inside = False
    whitelist = []
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip().startswith("## 可改")
            continue
        if inside:
            for m in re.finditer(r"`([^`]+)`", line):
                whitelist.append(m.group(1))
    if not whitelist:
        add("严重", "E_SCOPE_EMPTY", path, 1, "可改白名单为空")
    if changed and whitelist:
        import fnmatch
        for name in changed:
            if not any(fnmatch.fnmatch(name.replace(os.sep, "/"), g) or name.replace(os.sep, "/").startswith(g.rstrip("*").rstrip("/") + "/") for g in whitelist):
                add("严重", "E_SCOPE_VIOLATION", path, 1, f"改动文件不在白名单内：{name}")


PROPOSAL_SECTIONS = ["## 背景", "## 目标", "## 范围", "## 需求草案", "## 关键取舍", "## 与基线的冲突"]


def check_proposal(path, text):
    for sec in PROPOSAL_SECTIONS:
        if sec not in text:
            add("严重", "E_PROPOSAL_SECTION", path, 1, f"缺小节 {sec}")
    if "## 需求草案" in text:
        start = text.index("## 需求草案")
        end = text.find("\n## ", start + 1)
        body = text[start:end if end != -1 else len(text)]
        if len([l for l in body.splitlines() if l.strip().startswith(("1.", "2.", "- "))]) == 0:
            add("一般", "W_PROPOSAL_EMPTY", path, 1, "需求草案没有任何条目")


def check_review(path, text):
    for sec in ("## 评审包", "## 意见清单", "## 结论"):
        if sec not in text:
            add("一般", "W_REVIEW_SECTION", path, 1, f"缺 {sec} 小节")
    inside = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            inside = line.strip() == "## 意见清单"
            continue
        if not inside:
            continue
        s = line.strip()
        if not s.startswith("|") or set(s) <= set("|- "):
            continue
        cells = [x.strip() for x in s.strip("|").split("|")]
        if len(cells) < 6 or cells[1] in ("档位", ""):
            continue
        if cells[1] not in LEVELS:
            add("一般", "W_REVIEW_LEVEL", path, i, f"档位 {cells[1]!r} 不在 严重/一般/建议 之内")
        conclusion = cells[5]
        if cells[1] == "严重" and conclusion not in ("接受", "部分接受", "反驳"):
            add("严重", "E_REVIEW_OPEN", path, i, "严重项没有明确结论（接受/部分接受/反驳）")
        if conclusion and conclusion not in ("接受", "部分接受", "反驳") and not conclusion.startswith("反驳"):
            add("一般", "W_REVIEW_CONCLUSION", path, i, f"结论 {conclusion!r} 不合规")


def check_arch(change_arch_path, readme_path, merged_path, us):
    arch_text = read(change_arch_path)
    merged_text = read(merged_path) or ""
    readme_text = read(readme_path)
    if arch_text is None:
        if "df-arch:%s" % us in merged_text:
            return  # 已并入 docs/arch.md，属于收尾后的正常状态
        add("严重", "E_NOFILE", change_arch_path, 0, "delta-arch.md 不存在，也没并入 docs/arch.md")
        return
    check_placeholders(change_arch_path, arch_text)
    for sec in DELTA_ARCH_SECTIONS:
        if sec not in arch_text:
            add("严重", "E_ARCH_SECTION", change_arch_path, 1, f"缺章节 {sec}")
    if "sequenceDiagram" not in arch_text:
        add("严重", "E_ARCH_SEQUENCE", change_arch_path, 1, "缺时序图（sequenceDiagram 必需）")
    if "classDiagram" not in arch_text and "flowchart" not in arch_text:
        add("严重", "E_ARCH_UML", change_arch_path, 1, "缺 UML 图（classDiagram 或组件 flowchart 必需）")
    check_mermaid(change_arch_path, arch_text)
    if merged_text == "" and readme_text is not None:
        pass
    if readme_text is None:
        add("一般", "W_README_MISSING", readme_path, 0, "README.md 不存在（建议由基线阶段补）")
    else:
        check_placeholders(readme_path, readme_text)
        if not readme_text.lstrip().startswith("# "):
            add("严重", "E_README_TITLE", readme_path, 1, "README.md 缺少一级标题")


def check_validation(path, text):
    inside = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            inside = line.strip() == "## 问题清单"
            continue
        if not inside:
            continue
        s = line.strip()
        if not s.startswith("|") or set(s) <= set("|- "):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 3 and cells[1] not in ("档位", ""):
            if cells[1] not in LEVELS:
                add("一般", "W_VALIDATION_LEVEL", path, i, f"档位 {cells[1]!r} 不在 严重/一般/建议 之内")
            if len(cells) >= 6 and cells[5] and cells[5] not in HANDLES:
                add("一般", "W_VALIDATION_HANDLE", path, i, f"处理 {cells[5]!r} 不在 {'/'.join(HANDLES)} 之内")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", default=os.getcwd())
    ap.add_argument("--us", required=True)
    ap.add_argument("--baseline-only", action="store_true")
    ap.add_argument("--changed-files", default="", help="逗号分隔的改动文件，用于对 scope 白名单做越界检查")
    args = ap.parse_args()

    proj = os.path.abspath(args.proj)
    spec_dir = os.path.join(proj, "codespec", "specs")
    change_dir = os.path.join(proj, "codespec", "changes", args.us)
    spec_path = os.path.join(spec_dir, "spec.md")
    design_path = os.path.join(spec_dir, "design.md")

    baseline_reqs = set()
    specs = discover_specs(spec_dir)
    if not specs:
        add("严重", "E_NOFILE", spec_path, 0, "基线 spec 不存在（既没有 specs/spec.md，也没有 specs/<capability>/spec.md）")
    for spec_file, capability in specs:
        spec_text = read(spec_file)
        if spec_text is None:
            add("严重", "E_NOFILE", spec_file, 0, "spec 文件读取失败")
            continue
        check_frontmatter(spec_file, spec_text, "一般")
        check_placeholders(spec_file, spec_text)
        names = check_spec(spec_file, spec_text)
        baseline_reqs |= names
        if capability:
            baseline_reqs |= {capability + "/" + n for n in names}

    design_text = read(design_path)
    if design_text is None:
        add("严重", "E_NOFILE", design_path, 0, "基线 design.md 不存在")
    else:
        check_frontmatter(design_path, design_text, "一般")
        check_placeholders(design_path, design_text)
        check_design(design_path, design_text)
        check_adr_links(design_path, design_text, proj)

    ds_reqs = []
    if not args.baseline_only:
        ds_path = os.path.join(change_dir, "delta-spec.md")
        dd_path = os.path.join(change_dir, "delta-design.md")
        task_path = os.path.join(change_dir, "task.md")
        val_path = os.path.join(change_dir, "validation.md")
        for path, label in ((ds_path, "delta-spec.md"), (dd_path, "delta-design.md"),
                            (task_path, "task.md"), (val_path, "validation.md")):
            if not os.path.exists(path):
                add("严重", "E_NOFILE", path, 0, f"{label} 不存在")
        ds_text = read(ds_path)
        if ds_text:
            check_frontmatter(ds_path, ds_text)
            check_placeholders(ds_path, ds_text)
            ds_reqs = check_delta_spec(ds_path, ds_text, baseline_reqs)
        dd_text = read(dd_path)
        if dd_text:
            check_frontmatter(dd_path, dd_text)
            check_placeholders(dd_path, dd_text)
            check_delta_design(dd_path, dd_text)
        task_text = read(task_path)
        if task_text:
            check_placeholders(task_path, task_text)
            check_task(task_path, task_text, ds_reqs)
        val_text = read(val_path)
        if val_text:
            check_validation(val_path, val_text)
        proposal_path = os.path.join(change_dir, "proposal.md")
        proposal_text = read(proposal_path)
        if proposal_text is None:
            add("严重", "E_PROPOSAL_MISSING", proposal_path, 0, "proposal.md 不存在（本次变更没有提案记录）")
        else:
            check_placeholders(proposal_path, proposal_text)
            check_proposal(proposal_path, proposal_text)
        scope_path = os.path.join(change_dir, "scope.md")
        scope_text = read(scope_path)
        if scope_text is None:
            add("严重", "E_NOFILE", scope_path, 0, "scope.md 不存在（执行边界缺失）")
        else:
            check_placeholders(scope_path, scope_text)
            check_scope(scope_path, scope_text,
                        [x for x in (args.changed_files or "").split(",") if x.strip()])
        review_path = os.path.join(change_dir, "review.md")
        review_text = read(review_path)
        if review_text is None:
            add("一般", "W_REVIEW_MISSING", review_path, 0, "review.md 不存在（本次变更尚未评审）")
        else:
            check_placeholders(review_path, review_text)
            check_review(review_path, review_text)
        check_arch(os.path.join(change_dir, "delta-arch.md"),
                   os.path.join(proj, "README.md"),
                   os.path.join(proj, "docs", "arch.md"),
                   args.us)

    fatal = [i for i in issues if i["level"] == "严重"]
    result = {
        "ok": not fatal,
        "stats": {"issues": len(issues), "fatal": len(fatal), "warn": len(issues) - len(fatal)},
        "issues": issues,
    }
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
