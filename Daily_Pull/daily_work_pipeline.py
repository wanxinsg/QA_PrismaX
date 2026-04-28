#!/usr/bin/env python3
"""
工作日 Daily Work：拉取四仓库 testing 分支 → 发邮件 → 采集 git 事实 → 可选 LLM 生成中文分析与测试建议 → 写入 QA_Feature_CaseDesign。

环境变量（LLM）:
    LLM_PROVIDER           - openai | anthropic | cursor（cursor=不调用 API，在 MD 里预留 Cursor 补全材料与提示词）
    OPENAI_API_KEY         - OpenAI
    OPENAI_MODEL           - 默认 gpt-4o-mini
    ANTHROPIC_API_KEY      - Anthropic
    ANTHROPIC_MODEL        - 默认 claude-3-5-haiku-20241022
    SKIP_LLM_IF_NO_COMMITS - 1/true 时四库均无新 commit 则不调用 API（默认 1）
    DAILY_WORK_MAX_PATCH_CHARS - 单仓纳入 prompt 的 diff 字符上限（默认 120000）
    DAILY_WORK_MAX_PATCH_FILES   - 最多拼接 patch 的文件数（默认 40）
    LLM_TIMEOUT_SEC        - API 超时秒数（默认 180）

输出:
    ${PROJECT_ROOT}/QA_PrismaX/QA_Feature_CaseDesign/Daily_Work_Reports/YYYY-MM-DD_Daily_Work.md

用法:
    python3 daily_work_pipeline.py
    python3 daily_work_pipeline.py --regenerate-cursor [path/to/YYYY-MM-DD_Daily_Work.md]
        从已有报告解析各仓 old..new，重建事实块与「Cursor 补全」段（不拉取、不发邮件）。
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from daily_pull_testing_branches import (
    REPOSITORIES,
    GitPullResult,
    get_project_root,
    pull_testing_branch,
    run_git_command,
    send_email_report,
)


def feature_case_design_root(project_root: Path) -> Path:
    return project_root / "QA_PrismaX" / "QA_Feature_CaseDesign"


def daily_work_report_path(project_root: Path) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = feature_case_design_root(project_root) / "Daily_Work_Reports"
    return out_dir / f"{date_str}_Daily_Work.md"


def _report_title_date(out_path: Path) -> str:
    stem = out_path.stem
    if "_Daily_Work" in stem:
        return stem.replace("_Daily_Work", "")
    return datetime.now().strftime("%Y-%m-%d")


def parse_git_pull_results_from_report(
    text: str, project_root: Path
) -> List[GitPullResult]:
    """从已生成的 Daily_Work.md 中解析各仓 commit 范围与摘要，用于 --regenerate-cursor。"""
    sections: Dict[str, str] = {}
    for block in re.split(r"\n(?=### )", text):
        block = block.strip()
        if not block.startswith("### "):
            continue
        first, _, rest = block.partition("\n")
        name = first.replace("###", "").strip()
        if name in REPOSITORIES:
            sections[name] = rest

    out: List[GitPullResult] = []
    for name in REPOSITORIES:
        if name not in sections:
            raise ValueError(f"报告中缺少仓库小节: {name}")
        body = sections[name]
        rm = re.search(
            r"- \*\*范围\*\*: `([0-9a-f]+)` → `([0-9a-f]+)`",
            body,
        )
        if not rm:
            raise ValueError(f"无法解析 {name} 的 commit 范围")
        old_s, new_s = rm.group(1), rm.group(2)
        sm = re.search(r"- \*\*摘要\*\*: (.+)", body)
        summary = sm.group(1).strip() if sm else ""

        r = GitPullResult(name, str(project_root / name))
        r.success = True
        r.branch = "testing"
        r.pulled = True
        r.old_commit_sha = old_s
        r.new_commit_sha = new_s
        r.changes_summary = summary
        r.latest_commit = new_s[:8] if len(new_s) >= 8 else new_s
        r.commit_list = []
        r.commit_message = ""
        r.commit_author = ""
        r.commit_date = ""

        if "**Commits:**" in body:
            after = body.split("**Commits:**", 1)[1]
            for line in after.splitlines():
                line_st = line.strip()
                if not line_st:
                    continue
                if line_st.startswith("**") and "Commits" not in line_st:
                    break
                if line_st.startswith("- 无新 commit"):
                    break
                if line_st.startswith("**变更文件数**"):
                    break
                cm = re.match(r"- `([a-f0-9]+)`\s*(.+)", line_st)
                if cm:
                    r.commit_list.append(
                        {"hash": cm.group(1), "message": cm.group(2).strip()}
                    )
        if r.commit_list:
            r.commit_message = r.commit_list[0]["message"]

        out.append(r)
    return out


def regenerate_cursor_report(report_path: Path) -> Path:
    """不拉取、不发邮件：按报告中的 old..new 重采 git 事实并写入 Cursor 补全段。"""
    text = report_path.read_text(encoding="utf-8")
    m = re.search(r"\*\*PROJECT_ROOT\*\*: `([^`]+)`", text)
    project_root = Path(m.group(1)) if m else get_project_root()

    results = parse_git_pull_results_from_report(text, project_root)
    facts_map: Dict[str, Dict[str, Any]] = {}
    for r in results:
        if r.old_commit_sha and r.new_commit_sha and r.old_commit_sha != r.new_commit_sha:
            facts_map[r.repo_name] = collect_repo_git_facts(
                Path(r.repo_path), r.old_commit_sha, r.new_commit_sha
            )
        else:
            facts_map[r.repo_name] = collect_repo_git_facts(
                Path(r.repo_path), "", ""
            )

    any_new = any(
        r.old_commit_sha and r.new_commit_sha and r.old_commit_sha != r.new_commit_sha
        for r in results
    )
    os.environ["LLM_PROVIDER"] = "cursor"
    if any_new:
        ctx = build_llm_context(results, facts_map)
        cursor_md = build_cursor_followup_section(ctx, True)
        print("已按报告中的范围重建 Cursor 补全材料（含 diff）。")
    else:
        cursor_md = build_cursor_followup_section("", False)
        print("报告中各仓均无新 commit 范围，仅写入简短说明。")

    return write_daily_work_markdown(
        project_root,
        results,
        facts_map,
        None,
        None,
        cursor_followup_md=cursor_md,
        output_path=report_path,
    )


def _env_bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _parse_numstat_paths(numstat: str) -> List[Tuple[int, str]]:
    """Return (score, path) sorted descending by change volume."""
    rows: List[Tuple[int, str]] = []
    for line in numstat.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, b, path = parts[0], parts[1], parts[2]
        try:
            score = int(a) + int(b)
        except ValueError:
            score = 0
        rows.append((score, path))
    rows.sort(key=lambda x: -x[0])
    return rows


def collect_repo_git_facts(
    repo_path: Path, old_sha: str, new_sha: str
) -> Dict[str, Any]:
    timeout = 180
    facts: Dict[str, Any] = {
        "log_oneline": "",
        "diff_stat": "",
        "names_only": [],
        "patch_excerpt": "",
        "patch_truncated": False,
    }
    if not old_sha or not new_sha or old_sha == new_sha:
        return facts

    r, out, _ = run_git_command(
        repo_path,
        ["log", f"{old_sha}..{new_sha}", "--oneline", "--no-decorate"],
        timeout=timeout,
    )
    if r:
        facts["log_oneline"] = out

    r, out, _ = run_git_command(
        repo_path, ["diff", f"{old_sha}..{new_sha}", "--stat"], timeout=timeout
    )
    if r:
        facts["diff_stat"] = out

    r, out, _ = run_git_command(
        repo_path, ["diff", f"{old_sha}..{new_sha}", "--name-only"], timeout=timeout
    )
    if r and out:
        facts["names_only"] = [ln for ln in out.splitlines() if ln.strip()]

    r, out, _ = run_git_command(
        repo_path, ["diff", f"{old_sha}..{new_sha}", "--numstat"], timeout=timeout
    )
    ordered: List[str] = []
    if r and out:
        ordered = [p for _, p in _parse_numstat_paths(out)]
    if not ordered:
        ordered = list(facts["names_only"])

    max_chars = int(os.environ.get("DAILY_WORK_MAX_PATCH_CHARS", "120000"))
    max_files = int(os.environ.get("DAILY_WORK_MAX_PATCH_FILES", "40"))
    buf: List[str] = []
    used = 0
    file_count = 0
    for path in ordered[:max_files]:
        r, chunk, _ = run_git_command(
            repo_path,
            ["diff", f"{old_sha}..{new_sha}", "--", path],
            timeout=timeout,
        )
        if not r or not chunk:
            continue
        prefix = f"\n--- a/{path} ---\n"
        block = prefix + chunk
        if used + len(block) > max_chars:
            facts["patch_truncated"] = True
            remain = max_chars - used - len(prefix)
            if remain > 500:
                buf.append(prefix + chunk[:remain] + "\n... [truncated mid-file]\n")
            break
        buf.append(block)
        used += len(block)
        file_count += 1
    if file_count >= max_files and len(ordered) > max_files:
        facts["patch_truncated"] = True
    facts["patch_excerpt"] = "".join(buf)
    if not facts["patch_excerpt"] and facts["names_only"]:
        facts["patch_excerpt"] = (
            "[未包含逐文件 patch：变更仅列出路径与统计，见上表]\n"
        )
    return facts


def _facts_markdown_block(results: List[GitPullResult], facts_map: Dict[str, Dict]) -> str:
    lines = ["## 机器采集事实（git）\n"]
    for r in results:
        lines.append(f"### {r.repo_name}\n")
        if not r.success:
            lines.append(f"- **拉取状态**: 失败 — {r.error_message}\n")
            continue
        lines.append(f"- **分支**: {r.branch}")
        lines.append(f"- **范围**: `{r.old_commit_sha}` → `{r.new_commit_sha}`")
        lines.append(f"- **摘要**: {r.changes_summary}\n")
        if r.commit_list:
            lines.append("**Commits:**")
            for c in r.commit_list:
                lines.append(f"- `{c['hash']}` {c['message']}")
            lines.append("")
        if r.old_commit_sha == r.new_commit_sha:
            lines.append("- 无新 commit，未采集 diff。\n")
            continue
        f = facts_map.get(r.repo_name, {})
        if f.get("names_only"):
            lines.append(f"**变更文件数**: {len(f['names_only'])}")
            sample = f["names_only"][:80]
            lines.append("**变更路径（节选）**:\n```")
            lines.extend(sample)
            if len(f["names_only"]) > 80:
                lines.append(f"... 另有 {len(f['names_only']) - 80} 个文件未列出")
            lines.append("```\n")
        if f.get("diff_stat"):
            lines.append("**diff --stat:**\n```")
            stat = f["diff_stat"]
            if len(stat) > 15000:
                stat = stat[:15000] + "\n... [truncated]\n"
            lines.append(stat)
            lines.append("```\n")
        if f.get("patch_truncated"):
            lines.append(
                "*（patch 已按 DAILY_WORK_MAX_PATCH_CHARS / DAILY_WORK_MAX_PATCH_FILES 截断）*\n"
            )
    return "\n".join(lines) + "\n"


def build_llm_context(
    results: List[GitPullResult], facts_map: Dict[str, Dict[str, Any]]
) -> str:
    parts = [
        "以下是 Prismax 四个相关仓库在 testing 分支上，一次 daily pull 之后的新增 commit 与变更材料。"
        "请**严格基于**下列 commit 信息与 diff/路径进行分析，不要编造未出现的文件或接口。\n"
    ]
    for r in results:
        if not r.success:
            parts.append(f"\n## 仓库: {r.repo_name}\n拉取失败: {r.error_message}\n")
            continue
        parts.append(f"\n## 仓库: {r.repo_name}\n")
        parts.append(f"old..new: {r.old_commit_sha}..{r.new_commit_sha}\n")
        if r.old_commit_sha == r.new_commit_sha:
            parts.append("（无新 commit）\n")
            continue
        f = facts_map.get(r.repo_name, {})
        parts.append("### git log --oneline\n```\n" + f.get("log_oneline", "") + "\n```\n")
        parts.append("### git diff --stat\n```\n" + f.get("diff_stat", "") + "\n```\n")
        names = f.get("names_only") or []
        parts.append("### 变更路径（完整列表）\n```\n" + "\n".join(names) + "\n```\n")
        patch = f.get("patch_excerpt", "")
        parts.append("### 截断后的 unified diff 片段\n```\n" + patch + "\n```\n")
    return "\n".join(parts)


def call_openai(system: str, user: str) -> str:
    from openai import OpenAI

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    timeout = float(os.environ.get("LLM_TIMEOUT_SEC", "180"))
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=timeout)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def call_anthropic(system: str, user: str) -> str:
    import anthropic

    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    timeout = float(os.environ.get("LLM_TIMEOUT_SEC", "180"))
    client = anthropic.Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"], timeout=timeout
    )
    msg = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    out: List[str] = []
    for block in msg.content:
        t = getattr(block, "text", None)
        if t:
            out.append(t)
    return "".join(out)


def is_cursor_llm_mode() -> bool:
    p = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    return p in ("cursor", "none", "offline", "local")


def build_cursor_followup_section(context: str, any_new_commits: bool) -> str:
    """Markdown block：说明 + 可复制提示 + 原始材料（供 @ 本文件 时用）。"""
    if not any_new_commits:
        return (
            "## 分析与测试建议（Cursor 补全）\n\n"
            "> 当日四库在 testing 上均无新 commit，**无需**进行变更影响分析；若仍需记录，可手写当日测试计划。\n"
        )

    prompt = (
        "请严格根据本文件中「机器采集事实」与「供 Cursor 使用的原始材料」进行分析，"
        "用 **简体中文** 与 **Markdown** 输出（从 `## 总览` 起，勿用一级标题 `#`）："
        "总览；分仓库影响；跨仓库/API/网关联动风险；测试策略（单测、集成、手动、E2E 分层）；"
        "具体 E2E 用例建议（含目的、前置、步骤、预期）；回归测试建议（优先级 P0/P1/P2）。"
        "勿编造未在材料中出现的文件路径或接口名。"
    )
    lines = [
        "## 分析与测试建议（Cursor 补全）\n",
        "> **说明**：当前为 `LLM_PROVIDER=cursor`（或 none/offline/local），**未调用** OpenAI/Anthropic。"
        "在 Cursor 中打开本文件，使用 **Chat** 或 **Plan**，将本文件加入上下文（`@` 引用本文件），"
        "把下面「建议提示词」复制到对话中，并把模型生成内容**粘贴替换**本节占位以下正文（可删除提示框与原始材料块以简化文档）。\n",
        "### 建议提示词（复制到 Cursor）\n",
        "```text",
        prompt,
        "```\n",
        "### 供 Cursor 使用的原始材料（含 diff 片段）\n",
        "```text",
    ]
    # 避免无意中闭合 fence：材料内出现 ``` 时替换
    safe_ctx = context.replace("```", "``\\`")
    lines.append(safe_ctx)
    lines.append("```\n")
    return "\n".join(lines)


def run_llm_analysis(context: str) -> Tuple[Optional[str], Optional[str]]:
    if is_cursor_llm_mode():
        return None, None
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    system = (
        "你是资深 QA 与软件分析工程师，输出**简体中文** Markdown。"
        "根据用户提供的多仓库 git 材料，写出：总览；按仓库的影响分析；跨仓库/API/网关联动风险；"
        "测试策略（单测、集成、手动、E2E 分层）；具体 E2E 用例建议（含目的、前置、步骤、预期）；"
        "回归测试建议（优先级 P0/P1/P2）。不要捏造材料中未出现的文件路径或接口名。"
    )
    user = (
        "请基于下列材料撰写当日 Daily Work 分析报告（Markdown 标题从「## 总览」开始，"
        "不要使用一级标题 #，以便与文档.front matter 协调）：\n\n" + context
    )
    try:
        if provider == "anthropic":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                return None, "未设置 ANTHROPIC_API_KEY"
            return call_anthropic(system, user), None
        if not os.environ.get("OPENAI_API_KEY"):
            return None, "未设置 OPENAI_API_KEY"
        return call_openai(system, user), None
    except Exception as e:
        return None, str(e)


def write_daily_work_markdown(
    project_root: Path,
    results: List[GitPullResult],
    facts_map: Dict[str, Dict[str, Any]],
    llm_text: Optional[str],
    llm_error: Optional[str],
    *,
    cursor_followup_md: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> Path:
    out_path = output_path or daily_work_report_path(project_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title_date = _report_title_date(out_path)
    lines = [
        f"# PrismaX Daily Work — {title_date}\n",
        f"- **生成时间**: {now}",
        f"- **PROJECT_ROOT**: `{project_root}`",
        f"- **LLM 模式**: `{os.environ.get('LLM_PROVIDER', 'openai').strip() or 'openai'}`\n",
        "---\n",
        _facts_markdown_block(results, facts_map),
        "---\n",
    ]
    if cursor_followup_md is not None:
        lines.append(cursor_followup_md)
    else:
        lines.append("## LLM 分析与测试建议\n")
        if llm_error:
            lines.append(f"> **LLM 未生成**（{llm_error}）\n")
        if llm_text:
            lines.append(llm_text.strip() + "\n")
        elif not llm_error:
            lines.append("> 当日无新 commit 或已跳过 LLM。\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 已写入: {out_path}")
    return out_path


def main() -> None:
    print("=" * 60)
    print("Prismax Daily Work（拉取 + 分析与测试建议）")
    print("=" * 60)

    project_root = get_project_root()
    print(f"项目根目录: {project_root}")

    results: List[GitPullResult] = []
    for repo_name in REPOSITORIES:
        repo_path = project_root / repo_name
        print(f"\n处理仓库: {repo_name}")
        print(f"路径: {repo_path}")
        result = pull_testing_branch(repo_name, repo_path)
        results.append(result)
        if result.success:
            print(f"✅ {repo_name}: {result.changes_summary}")
            if result.latest_commit:
                print(f"   最新提交: {result.latest_commit} - {result.commit_message}")
        else:
            print(f"❌ {repo_name}: {result.error_message}")

    print("\n" + "=" * 60)
    print("发送邮件报告...")
    try:
        send_email_report(results)
    except Exception as e:
        print(f"⚠️  邮件发送失败（已忽略，继续写报告）: {e}")

    # 仅暂停“生成 Daily_Work_Reports”，但仍需要：拉取 git + 发邮件
    if _env_bool("DAILY_WORK_SKIP_REPORT", False):
        print("\n" + "=" * 60)
        print("已启用 DAILY_WORK_SKIP_REPORT：跳过生成 Daily_Work_Reports（仅拉取 git + 发送邮件）。")
        print("=" * 60)
        if any(not r.success for r in results):
            sys.exit(1)
        return

    facts_map: Dict[str, Dict[str, Any]] = {}
    for r in results:
        if (
            r.success
            and r.old_commit_sha
            and r.new_commit_sha
            and r.old_commit_sha != r.new_commit_sha
        ):
            facts_map[r.repo_name] = collect_repo_git_facts(
                Path(r.repo_path), r.old_commit_sha, r.new_commit_sha
            )
        else:
            facts_map[r.repo_name] = collect_repo_git_facts(
                Path(r.repo_path), "", ""
            )

    any_new = any(
        r.success and r.old_commit_sha and r.new_commit_sha and r.old_commit_sha != r.new_commit_sha
        for r in results
    )
    skip_no = _env_bool("SKIP_LLM_IF_NO_COMMITS", True)

    llm_text: Optional[str] = None
    llm_err: Optional[str] = None
    cursor_followup: Optional[str] = None

    if is_cursor_llm_mode():
        if any_new:
            ctx = build_llm_context(results, facts_map)
            cursor_followup = build_cursor_followup_section(ctx, True)
            print("LLM_PROVIDER=cursor：已写入供 Cursor 补全的材料与提示词（未调用 API）。")
        else:
            cursor_followup = build_cursor_followup_section("", False)
            print("LLM_PROVIDER=cursor：当日无新 commit，报告内为简短说明。")
    elif not any_new and skip_no:
        print("当日四库均无新 commit，跳过 LLM（SKIP_LLM_IF_NO_COMMITS）。")
    else:
        ctx = build_llm_context(results, facts_map)
        llm_text, llm_err = run_llm_analysis(ctx)
        if llm_err:
            print(f"⚠️  LLM: {llm_err}")

    write_daily_work_markdown(
        project_root,
        results,
        facts_map,
        llm_text,
        llm_err,
        cursor_followup_md=cursor_followup,
    )

    print("\n" + "=" * 60)
    print("执行总结:")
    print(f"  总计: {len(results)} 个仓库")
    print(f"  成功: {sum(1 for r in results if r.success)}")
    print(f"  失败: {sum(1 for r in results if not r.success)}")
    print("=" * 60)

    if any(not r.success for r in results):
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--regenerate-cursor":
        rp = Path(sys.argv[2]) if len(sys.argv) > 2 else daily_work_report_path(get_project_root())
        if not rp.is_file():
            print(f"错误: 找不到报告文件: {rp}", file=sys.stderr)
            sys.exit(1)
        regenerate_cursor_report(rp)
        sys.exit(0)
    main()
