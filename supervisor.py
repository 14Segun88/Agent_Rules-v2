#!/usr/bin/env python3
"""
AGENTS_RULES v2 — Supervisor

Periodic health-check of the knowledge base and agent compliance.
Runs mechanically (no LLM needed). Outputs a report that Jules or
a human can use to make smart decisions.

Checks performed:
  1. Agent compliance — did every active agent leave a check-out log?
  2. Wiki lint — broken links, orphan pages, oversized pages
  3. Stale entries — wiki records older than N days
  4. Duplicate entries — identical content in same wiki page
  5. Shared status — is it under 2KB, is it recent?
  6. False-positive errors — "Всё по плану" in wiki/errors/

Usage:
    python3 supervisor.py                    # Full check, output report
    python3 supervisor.py --fix              # Auto-fix safe issues
    python3 supervisor.py --json             # Output as JSON for automation
    python3 supervisor.py --age 14           # Stale threshold in days (default 14)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"
INDEX_FILE = BASE_DIR / "index.md"
STATUS_FILE = BASE_DIR / "shared_status.md"
SUPERVISOR_REPORT = BASE_DIR / "supervisor_report.md"

KNOWN_AGENTS = ["Antigravity", "KiloCode"]
STALE_DAYS_DEFAULT = 14
MAX_WIKI_PAGE_KB = 15
MAX_STATUS_KB = 2


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def file_age_days(filepath: Path) -> float:
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    return (datetime.now() - mtime).total_seconds() / 86400


def file_size_kb(filepath: Path) -> float:
    return filepath.stat().st_size / 1024


def extract_links(filepath: Path) -> list[str]:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    return re.findall(r"\[.*?\]\(([^)]+)\)", content)


def extract_dated_entries(filepath: Path) -> list[dict]:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    entries = []
    for m in re.finditer(
        r"###\s+[^\[]*\[(\d{4}-\d{2}-\d{2}[^\]]*)\]\s*\[([^\]]+)\]\s*\n(.+?)(?=\n###|\Z)",
        content,
        re.DOTALL,
    ):
        entries.append({
            "date": m.group(1).strip(),
            "agent": m.group(2).strip(),
            "content": m.group(3).strip(),
            "start": m.start(),
            "end": m.end(),
        })
    return entries


def check_agent_compliance() -> list[dict]:
    issues: list[dict] = []
    md_files = sorted(RAW_DIR.glob("*.md"))
    if not md_files:
        issues.append({
            "severity": "warn",
            "area": "compliance",
            "msg": "No session logs in raw/ — agents may not be checking out",
        })
        return issues

    latest = md_files[-1]
    age = file_age_days(latest)
    if age > 2:
        issues.append({
            "severity": "warn",
            "area": "compliance",
            "msg": f"Latest log is {age:.1f} days old — agents may not be active",
            "file": str(latest.relative_to(BASE_DIR)),
        })

    for filepath in md_files:
        if filepath.name.startswith("."):
            continue
        content = filepath.read_text(encoding="utf-8", errors="replace")

        if "## Что НЕ получилось" not in content:
            issues.append({
                "severity": "error",
                "area": "compliance",
                "msg": "Missing 'Что НЕ получилось' section",
                "file": str(filepath.relative_to(BASE_DIR)),
            })
        if "## Что получилось" not in content:
            issues.append({
                "severity": "error",
                "area": "compliance",
                "msg": "Missing 'Что получилось' section",
                "file": str(filepath.relative_to(BASE_DIR)),
            })
        if "## Следующий шаг" not in content:
            issues.append({
                "severity": "warn",
                "area": "compliance",
                "msg": "Missing 'Следующий шаг' section",
                "file": str(filepath.relative_to(BASE_DIR)),
            })

    return issues


def check_wiki_lint() -> list[dict]:
    issues: list[dict] = []

    if not INDEX_FILE.exists():
        issues.append({
            "severity": "error",
            "area": "lint",
            "msg": "index.md does not exist",
        })
        return issues

    index_links = extract_links(INDEX_FILE)
    for link in index_links:
        target = BASE_DIR / link
        if not target.exists():
            issues.append({
                "severity": "error",
                "area": "lint",
                "msg": f"Broken link in index.md: {link}",
                "file": "index.md",
            })

    all_wiki = set(str(p.relative_to(BASE_DIR)) for p in WIKI_DIR.rglob("*.md"))
    linked = set(l for l in index_links if not l.startswith("http"))
    orphans = all_wiki - linked
    for o in sorted(orphans):
        issues.append({
            "severity": "warn",
            "area": "lint",
            "msg": f"Orphan page (not in index.md): {o}",
            "file": o,
        })

    for filepath in WIKI_DIR.rglob("*.md"):
        internal_links = extract_links(filepath)
        for link in internal_links:
            if link.startswith("http"):
                continue
            target = filepath.parent / link
            if not target.exists():
                issues.append({
                    "severity": "error",
                    "area": "lint",
                    "msg": f"Broken internal link: {link}",
                    "file": str(filepath.relative_to(BASE_DIR)),
                })

    return issues


def check_oversized_pages() -> list[dict]:
    issues: list[dict] = []
    for filepath in WIKI_DIR.rglob("*.md"):
        size = file_size_kb(filepath)
        if size > MAX_WIKI_PAGE_KB:
            issues.append({
                "severity": "warn",
                "area": "size",
                "msg": f"Page too large: {size:.1f}KB (max {MAX_WIKI_PAGE_KB}KB)",
                "file": str(filepath.relative_to(BASE_DIR)),
            })
    return issues


def check_stale_entries(stale_days: int) -> list[dict]:
    issues: list[dict] = []
    for filepath in WIKI_DIR.rglob("*.md"):
        entries = extract_dated_entries(filepath)
        for entry in entries:
            date_str = entry["date"].split()[0]
            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            age_days = (datetime.now() - entry_date).days
            if age_days > stale_days:
                issues.append({
                    "severity": "info",
                    "area": "stale",
                    "msg": f"Entry older than {stale_days} days ({age_days}d ago) — consider archiving",
                    "file": str(filepath.relative_to(BASE_DIR)),
                    "date": entry["date"],
                    "content_preview": entry["content"][:80],
                })
    return issues


def check_duplicates() -> list[dict]:
    issues: list[dict] = []
    for filepath in WIKI_DIR.rglob("*.md"):
        entries = extract_dated_entries(filepath)
        seen: dict[str, list[int]] = {}
        for entry in entries:
            key = entry["content"].strip().lower()
            if key in seen:
                seen[key].append(entry["start"])
            else:
                seen[key] = [entry["start"]]
        for key, positions in seen.items():
            if len(positions) > 1:
                issues.append({
                    "severity": "warn",
                    "area": "duplicate",
                    "msg": f"Duplicate entry ({len(positions)}x): {key[:60]}...",
                    "file": str(filepath.relative_to(BASE_DIR)),
                })
    return issues


def check_shared_status() -> list[dict]:
    issues: list[dict] = []
    if not STATUS_FILE.exists():
        issues.append({
            "severity": "error",
            "area": "status",
            "msg": "shared_status.md does not exist",
        })
        return issues

    size = file_size_kb(STATUS_FILE)
    if size > MAX_STATUS_KB:
        issues.append({
            "severity": "error",
            "area": "status",
            "msg": f"shared_status.md is {size:.1f}KB (max {MAX_STATUS_KB}KB)",
        })

    age = file_age_days(STATUS_FILE)
    if age > 3:
        issues.append({
            "severity": "warn",
            "area": "status",
            "msg": f"shared_status.md is {age:.1f} days old — may be outdated",
        })

    content = STATUS_FILE.read_text(encoding="utf-8")
    if not re.search(r"\[\d{4}-\d{2}-\d{2}", content):
        issues.append({
            "severity": "warn",
            "area": "status",
            "msg": "shared_status.md missing timestamp in standard format",
        })

    return issues


def check_false_errors() -> list[dict]:
    issues: list[dict] = []
    errors_dir = WIKI_DIR / "errors"
    if not errors_dir.exists():
        return issues

    false_positive_patterns = [
        r"всё по плану",
        r"без блокеров",
        r"без ошибок",
        r"всё работает",
        r"нет проблем",
        r"no issues?",
        r"all good",
        r"everything works",
    ]

    for filepath in errors_dir.rglob("*.md"):
        content = filepath.read_text(encoding="utf-8")
        entries = extract_dated_entries(filepath)
        for entry in entries:
            text_lower = entry["content"].lower()
            for pattern in false_positive_patterns:
                if re.search(pattern, text_lower):
                    issues.append({
                        "severity": "error",
                        "area": "false_error",
                        "msg": f"False error entry: '{entry['content'][:60]}' matches pattern '{pattern}'",
                        "file": str(filepath.relative_to(BASE_DIR)),
                        "date": entry["date"],
                    })
                    break

    return issues


def auto_fix(issues: list[dict], dry_run: bool = False) -> list[str]:
    fixes: list[str] = []

    for issue in issues:
        if issue["area"] == "false_error" and "file" in issue:
            filepath = BASE_DIR / issue["file"]
            if not filepath.exists():
                continue
            content = filepath.read_text(encoding="utf-8")
            entries = extract_dated_entries(filepath)

            for entry in reversed(entries):
                text_lower = entry["content"].lower()
                is_false = any(
                    re.search(p, text_lower)
                    for p in [r"всё по плану", r"без блокеров", r"нет проблем"]
                )
                if is_false:
                    content = content[: entry["start"]] + content[entry["end"]:]
                    fixes.append(
                        f"Removed false error from {issue['file']}: {entry['content'][:40]}"
                    )

            if not dry_run:
                filepath.write_text(content, encoding="utf-8")

        elif issue["area"] == "duplicate" and "file" in issue:
            filepath = BASE_DIR / issue["file"]
            if not filepath.exists():
                continue
            content = filepath.read_text(encoding="utf-8")
            entries = extract_dated_entries(filepath)
            seen_content: dict[str, bool] = {}
            removals = []

            for entry in entries:
                key = entry["content"].strip().lower()
                if key in seen_content:
                    content = content[: entry["start"]] + content[entry["end"]:]
                    removals.append(key[:50])
                else:
                    seen_content[key] = True

            if removals:
                fixes.append(
                    f"Removed {len(removals)} duplicate(s) from {issue['file']}"
                )
                if not dry_run:
                    filepath.write_text(content, encoding="utf-8")

    return fixes


def run_all_checks(stale_days: int) -> list[dict]:
    all_issues: list[dict] = []
    all_issues.extend(check_agent_compliance())
    all_issues.extend(check_wiki_lint())
    all_issues.extend(check_oversized_pages())
    all_issues.extend(check_stale_entries(stale_days))
    all_issues.extend(check_duplicates())
    all_issues.extend(check_shared_status())
    all_issues.extend(check_false_errors())
    return all_issues


SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


def format_report(issues: list[dict]) -> str:
    if not issues:
        return f"# Supervisor Report — {ts()}\n\n✅ **All checks passed.** No issues found.\n"

    issues.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 3))

    counts = {"error": 0, "warn": 0, "info": 0}
    for i in issues:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1

    lines = [
        f"# Supervisor Report — {ts()}",
        "",
        f"**Errors:** {counts['error']} | **Warnings:** {counts['warn']} | **Info:** {counts['info']}",
        "",
    ]

    current_area = ""
    for issue in issues:
        area = issue["area"]
        if area != current_area:
            area_labels = {
                "compliance": "📋 Агент Compliance",
                "lint": "🔗 Wiki Lint",
                "size": "📏 Размер страниц",
                "stale": "⏰ Устаревшие записи",
                "duplicate": "🔄 Дубликаты",
                "status": "📄 Shared Status",
                "false_error": "❌ Ложные ошибки",
            }
            lines.append(f"## {area_labels.get(area, area)}")
            lines.append("")
            current_area = area

        icon = {"error": "🔴", "warn": "🟡", "info": "🔵"}.get(issue["severity"], "⚪")
        msg = issue["msg"]
        if "file" in issue:
            msg += f" ({issue['file']})"
        lines.append(f"- {icon} {msg}")

    return "\n".join(lines) + "\n"


def generate_jules_questions(issues: list[dict]) -> list[str]:
    """Generate questions for the user based on found issues."""
    questions: list[str] = []

    for issue in issues:
        if issue["area"] == "compliance" and "age" in issue.get("msg", ""):
            questions.append(
                "Агенты не активны > 2 дней. Хочешь отключить cron-мониторинг или отправить напоминание?"
            )
        elif issue["area"] == "false_error":
            questions.append(
                f"В {issue.get('file', 'wiki')} найдена ложная ошибка. Удалить автоматически или проверить вручную?"
            )
        elif issue["area"] == "lint" and "Orphan" in issue.get("msg", ""):
            questions.append(
                f"Страница {issue.get('file', '?')} не в index.md. Добавить ссылку или удалить страницу?"
            )
        elif issue["area"] == "status" and "outdated" in issue.get("msg", "").lower():
            questions.append("shared_status.md устарел. Обновить текущим статусом проекта?")
        elif issue["area"] == "stale":
            questions.append(
                f"Устаревшая запись в {issue.get('file', '?')}. Архивировать или оставить?"
            )

    if not questions and not issues:
        questions.append("Всё в порядке. Есть ли новые задачи для агентов?")

    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description="AGENTS_RULES v2 Supervisor")
    parser.add_argument("--fix", action="store_true", help="Auto-fix safe issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--jules-mode", action="store_true", help="Generate questions for user (Jules interaction)")
    parser.add_argument("--age", type=int, default=STALE_DAYS_DEFAULT, help="Stale threshold in days")
    args = parser.parse_args()

    issues = run_all_checks(args.age)

    if args.json:
        print(json.dumps({"timestamp": ts(), "issues": issues}, ensure_ascii=False, indent=2))
        return

    report = format_report(issues)
    SUPERVISOR_REPORT.write_text(report, encoding="utf-8")
    print(report)

    result_json = {"timestamp": ts(), "issues": issues}
    (BASE_DIR / "supervisor_result.json").write_text(
        json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if args.fix or args.dry_run:
        fixes = auto_fix(issues, dry_run=args.dry_run)
        if fixes:
            print("\n--- FIXES ---\n")
            for fix in fixes:
                label = "[DRY-RUN] " if args.dry_run else ""
                print(f"  {label}{fix}")
        else:
            print("\nNo auto-fixable issues found.")

    if args.jules_mode:
        questions = generate_jules_questions(issues)
        print("\n--- QUESTIONS FOR USER ---\n")
        for i, q in enumerate(questions, 1):
            print(f"  ❓ {i}. {q}")

    error_count = sum(1 for i in issues if i["severity"] == "error")
    if error_count > 0 and not args.fix:
        sys.exit(1)


if __name__ == "__main__":
    main()
