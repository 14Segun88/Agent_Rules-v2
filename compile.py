#!/usr/bin/env python3
"""
AGENTS_RULES v2 — Compiler (raw/ → wiki/)

Processes raw session logs from raw/ directory and compiles them
into structured wiki pages. Uses LLM for intelligent categorization
when available, falls back to rule-based parsing.

Usage:
    python3 compile.py                  # Process all unprocessed raw logs
    python3 compile.py --file <path>    # Process a specific file
    python3 compile.py --recompile      # Reprocess all files
    python3 compile.py --dry-run        # Show what would be done
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# --- Configuration ---
BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"
INDEX_FILE = BASE_DIR / "index.md"
STATUS_FILE = BASE_DIR / "shared_status.md"
PROCESSED_MARKER = BASE_DIR / "raw" / ".processed"

# LLM API configuration (same as project's LM Studio)
LLM_API_URL = os.environ.get("LLM_API_URL", "http://192.168.47.22:1234/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemma-4-31b-it")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("compile")


def get_processed_files() -> set[str]:
    """Return set of already processed filenames."""
    if PROCESSED_MARKER.exists():
        return set(PROCESSED_MARKER.read_text().strip().splitlines())
    return set()


def mark_as_processed(filename: str) -> None:
    """Mark a file as processed."""
    processed = get_processed_files()
    processed.add(filename)
    PROCESSED_MARKER.write_text("\n".join(sorted(processed)) + "\n")


def parse_raw_log(filepath: Path) -> dict:
    """Parse a raw session log into structured sections."""
    content = filepath.read_text(encoding="utf-8")
    sections: dict = {
        "filename": filepath.name,
        "date": "",
        "agent": "",
        "task": "",
        "successes": [],
        "failures": [],
        "technical_notes": [],
        "next_step": "",
        "blockers": [],
        "full_text": content,
    }

    # Extract metadata from filename: YYYY-MM-DD_HH-MM_AgentName.md
    match = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_(.+)\.md", filepath.name)
    if match:
        sections["date"] = f"{match.group(1)} {match.group(2).replace('-', ':')}"
        sections["agent"] = match.group(3)

    # Parse sections
    current_section = None
    for line in content.splitlines():
        line_stripped = line.strip()

        if re.match(r"^##\s+.*получилось\s*✅", line_stripped, re.IGNORECASE):
            current_section = "successes"
        elif re.match(r"^##\s+.*[нН][еЕ]\s+получилось\s*❌", line_stripped, re.IGNORECASE):
            current_section = "failures"
        elif re.match(r"^##\s+.*[Тт]ехнич", line_stripped):
            current_section = "technical_notes"
        elif re.match(r"^##\s+.*[Сс]ледующ", line_stripped):
            current_section = "next_step"
        elif re.match(r"^##\s+.*[Бб]локер", line_stripped):
            current_section = "blockers"
        elif re.match(r"^##\s+.*[Зз]адач", line_stripped):
            current_section = "task"
        elif line_stripped.startswith("# ") and not line_stripped.startswith("## "):
            # Title line
            continue
        elif current_section and line_stripped.startswith("- "):
            item = line_stripped[2:].strip()
            if current_section == "task":
                sections["task"] = item
            elif current_section == "next_step":
                sections["next_step"] = item
            elif isinstance(sections.get(current_section), list):
                sections[current_section].append(item)
        elif current_section == "task" and line_stripped:
            sections["task"] = line_stripped
        elif current_section == "next_step" and line_stripped:
            sections["next_step"] = line_stripped

    return sections


def categorize_content(sections: dict) -> list[dict]:
    """Categorize parsed content into wiki targets using rule-based logic."""
    updates: list[dict] = []

    # Map failures to wiki/errors/
    for failure in sections.get("failures", []):
        failure_lower = failure.lower()
        target = "wiki/errors/general.md"

        if any(kw in failure_lower for kw in ["контекст", "context", "overflow", "токен"]):
            target = "wiki/errors/context_overflow.md"
        elif any(kw in failure_lower for kw in ["галлюцин", "hallucin", "копир", "шаблон"]):
            target = "wiki/errors/hallucinations.md"
        elif any(kw in failure_lower for kw in ["kb", "matching", "score", "boost", "эталон"]):
            target = "wiki/errors/kb_conflicts.md"
        elif any(kw in failure_lower for kw in ["ocr", "скан", "scan", "tesseract"]):
            target = "wiki/errors/ocr_issues.md"

        updates.append({
            "target": target,
            "type": "error",
            "content": failure,
            "date": sections.get("date", ""),
            "agent": sections.get("agent", ""),
        })

    # Map successes to wiki/skills/
    for success in sections.get("successes", []):
        success_lower = success.lower()
        target = "wiki/skills/general.md"

        if any(kw in success_lower for kw in ["few-shot", "prompt", "промпт", "инъекция"]):
            target = "wiki/skills/few_shot_prompting.md"
        elif any(kw in success_lower for kw in ["xml", "structure", "hint"]):
            target = "wiki/skills/xml_structure_hints.md"
        elif any(kw in success_lower for kw in ["semantic", "matching", "семантик"]):
            target = "wiki/skills/semantic_matching.md"
        elif any(kw in success_lower for kw in ["kb override", "override", "direct_fields"]):
            target = "wiki/skills/kb_override.md"
        elif any(kw in success_lower for kw in ["benchmark", "бенчмарк", "scorer", "scoring"]):
            target = "wiki/benchmark_history.md"

        updates.append({
            "target": target,
            "type": "skill",
            "content": success,
            "date": sections.get("date", ""),
            "agent": sections.get("agent", ""),
        })

    # Map technical notes to relevant wiki pages
    for note in sections.get("technical_notes", []):
        note_lower = note.lower()
        target = "wiki/architecture.md"

        if any(kw in note_lower for kw in ["llm", "model", "api", "модел", "промпт"]):
            target = "wiki/llm_integration.md"

        updates.append({
            "target": target,
            "type": "note",
            "content": note,
            "date": sections.get("date", ""),
            "agent": sections.get("agent", ""),
        })

    return updates


def try_llm_categorize(sections: dict) -> Optional[list[dict]]:
    """
    Attempt to use LLM for intelligent categorization.
    Falls back to None if LLM is unavailable.
    """
    try:
        import urllib.request

        prompt = f"""Ты — компилятор базы знаний. Проанализируй лог сессии и категоризируй его содержимое.

Доступные целевые файлы wiki:
- wiki/errors/context_overflow.md — ошибки контекстного окна
- wiki/errors/hallucinations.md — галлюцинации LLM
- wiki/errors/kb_conflicts.md — конфликты KB matching
- wiki/errors/ocr_issues.md — проблемы OCR
- wiki/errors/general.md — прочие ошибки
- wiki/skills/few_shot_prompting.md — техники Few-Shot
- wiki/skills/xml_structure_hints.md — XML хинты
- wiki/skills/semantic_matching.md — семантический matching
- wiki/skills/kb_override.md — KB override
- wiki/skills/general.md — прочие навыки
- wiki/llm_integration.md — настройки LLM
- wiki/benchmark_history.md — бенчмарки
- wiki/architecture.md — архитектура

Лог сессии:
```
{sections['full_text'][:3000]}
```

Верни JSON массив объектов:
[{{"target": "wiki/...", "type": "error|skill|note", "content": "краткое описание", "is_new_topic": true/false}}]

ТОЛЬКО JSON, без markdown блоков."""

        payload = json.dumps({
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.1,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{LLM_API_URL}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            answer = result["choices"][0]["message"]["content"]

            # Extract JSON from response
            json_match = re.search(r"\[.*\]", answer, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                updates = []
                for item in items:
                    updates.append({
                        "target": item.get("target", "wiki/skills/general.md"),
                        "type": item.get("type", "note"),
                        "content": item.get("content", ""),
                        "date": sections.get("date", ""),
                        "agent": sections.get("agent", ""),
                    })
                log.info("LLM categorization successful (%d items)", len(updates))
                return updates

    except Exception as e:
        log.warning("LLM unavailable (%s), using rule-based categorization", e)

    return None


def append_to_wiki(target: str, update: dict) -> None:
    """Append an update to a wiki page."""
    filepath = BASE_DIR / target
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create file with header if it doesn't exist
    if not filepath.exists():
        category = "❌ Ошибки" if "errors" in target else "✅ Навыки" if "skills" in target else "📝 Заметки"
        title = filepath.stem.replace("_", " ").title()
        filepath.write_text(
            f"# {category}: {title}\n\n"
            f"> Автоматически создано compile.py | {datetime.now().strftime('%Y-%m-%d')}\n\n---\n\n",
            encoding="utf-8",
        )

    # Append the update
    type_icon = {"error": "❌", "skill": "✅", "note": "📝"}.get(update["type"], "📝")
    entry = (
        f"\n### {type_icon} [{update.get('date', 'N/A')}] [{update.get('agent', 'Unknown')}]\n"
        f"{update['content']}\n"
    )

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(entry)

    log.info("  → Appended to %s", target)


def rebuild_index() -> None:
    """Rebuild index.md from current wiki/ contents."""
    sections: dict[str, list[str]] = {
        "architecture": [],
        "llm": [],
        "benchmark": [],
        "errors": [],
        "skills": [],
    }

    for filepath in sorted(WIKI_DIR.rglob("*.md")):
        rel_path = filepath.relative_to(BASE_DIR)
        name = filepath.stem.replace("_", " ").title()
        link = f"- [{name}]({rel_path})"

        if "errors" in str(rel_path):
            sections["errors"].append(link)
        elif "skills" in str(rel_path):
            sections["skills"].append(link)
        elif "benchmark" in filepath.stem:
            sections["benchmark"].append(link)
        elif "llm" in filepath.stem:
            sections["llm"].append(link)
        else:
            sections["architecture"].append(link)

    index_content = f"""# 📖 Карта знаний (Knowledge Index)

> Автоматически обновляется `compile.py`. Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M')}.

---

## 🏗️ Архитектура
{chr(10).join(sections['architecture']) or '- *(пусто)*'}

## 🤖 LLM интеграция
{chr(10).join(sections['llm']) or '- *(пусто)*'}

## 📊 Бенчмарки
{chr(10).join(sections['benchmark']) or '- *(пусто)*'}

---

## ❌ Ошибки (wiki/errors/)
{chr(10).join(sections['errors']) or '- *(пусто)*'}

---

## ✅ Навыки (wiki/skills/)
{chr(10).join(sections['skills']) or '- *(пусто)*'}

---

## 📁 Сырые логи (raw/)
*Необработанные логи сессий. Автоматически компилируются в wiki/.*
"""
    INDEX_FILE.write_text(index_content, encoding="utf-8")
    log.info("Index rebuilt: %s", INDEX_FILE)


def git_auto_commit(message: str) -> None:
    """Auto-commit and push changes if in a git repo."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=10,
        )
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:  # There are staged changes
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(BASE_DIR),
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=str(BASE_DIR),
                capture_output=True,
                timeout=30,
            )
            log.info("Git: committed and pushed — %s", message)
        else:
            log.info("Git: no changes to commit")
    except Exception as e:
        log.warning("Git auto-commit failed: %s", e)


def process_file(filepath: Path, dry_run: bool = False) -> int:
    """Process a single raw log file. Returns number of updates."""
    log.info("Processing: %s", filepath.name)
    sections = parse_raw_log(filepath)

    # Try LLM first, fallback to rules
    updates = try_llm_categorize(sections)
    if updates is None:
        updates = categorize_content(sections)

    if not updates:
        log.info("  No categorizable content found in %s", filepath.name)
        return 0

    if dry_run:
        for u in updates:
            log.info("  [DRY-RUN] Would append to %s: %s", u["target"], u["content"][:60])
        return len(updates)

    for u in updates:
        append_to_wiki(u["target"], u)

    mark_as_processed(filepath.name)
    return len(updates)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AGENTS_RULES v2 Compiler")
    parser.add_argument("--file", type=str, help="Process a specific raw file")
    parser.add_argument("--recompile", action="store_true", help="Reprocess all files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--no-git", action="store_true", help="Skip git commit/push")
    args = parser.parse_args()

    RAW_DIR.mkdir(exist_ok=True)
    (WIKI_DIR / "errors").mkdir(parents=True, exist_ok=True)
    (WIKI_DIR / "skills").mkdir(parents=True, exist_ok=True)

    processed = set() if args.recompile else get_processed_files()
    total_updates = 0

    if args.file:
        filepath = Path(args.file)
        if filepath.exists():
            total_updates = process_file(filepath, args.dry_run)
        else:
            log.error("File not found: %s", filepath)
            sys.exit(1)
    else:
        raw_files = sorted(RAW_DIR.glob("*.md"))
        if not raw_files:
            log.info("No raw logs to process in %s", RAW_DIR)
            return

        for filepath in raw_files:
            if filepath.name.startswith("."):
                continue
            if filepath.name in processed:
                log.info("Skipping (already processed): %s", filepath.name)
                continue
            total_updates += process_file(filepath, args.dry_run)

    if total_updates > 0 and not args.dry_run:
        rebuild_index()
        if not args.no_git:
            git_auto_commit(f"[compile] Processed {total_updates} updates from raw logs")

    log.info("Done. Total updates: %d", total_updates)


if __name__ == "__main__":
    main()
