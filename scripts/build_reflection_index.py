#!/usr/bin/env python3
"""Build weekly reflection index for ai-news agent.

Input:
- memory/YYYY-MM-DD.md
- MEMORY.md (long-term lessons)

Output:
- knowledge/weekly/reflection-index-YYYY-Www.md
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
LONG_MEMORY = ROOT / "MEMORY.md"
OUT_DIR = ROOT / "knowledge" / "weekly"


def week_dates(today: date) -> list[date]:
    start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(7)]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def pick_lines(text: str, limit: int = 6) -> list[str]:
    picks: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        if len(s) < 8:
            continue
        if s.startswith("- ") or s.startswith("* ") or re.match(r"^\d+[\.)]", s):
            picks.append(s)
        if len(picks) >= limit:
            break
    if not picks:
        fallback = [ln.strip() for ln in text.splitlines() if ln.strip()][:limit]
        picks.extend(fallback)
    return picks[:limit]


def build() -> Path:
    today = date.today()
    dates = week_dates(today)
    iso_year, iso_week, _ = today.isocalendar()

    lines: list[str] = []
    lines.append(f"# Reflection Index - {iso_year}-W{iso_week:02d}")
    lines.append("")
    lines.append("## This Week Daily Reflections")

    for d in dates:
        p = MEMORY_DIR / f"{d.isoformat()}.md"
        text = read_text(p)
        if not text:
            lines.append(f"- {d.isoformat()}: (no file)")
            continue
        picks = pick_lines(text, limit=4)
        lines.append(f"- {d.isoformat()}:")
        for item in picks:
            lines.append(f"  - {item}")

    lines.append("")
    lines.append("## Long-Term Lessons Snapshot")
    long_text = read_text(LONG_MEMORY)
    lessons = []
    in_section = False
    for line in long_text.splitlines():
        s = line.strip()
        if s.startswith("## 经验教训") or s.lower().startswith("## lessons"):
            in_section = True
            continue
        if in_section and s.startswith("## "):
            break
        if in_section and (s.startswith("- ") or s.startswith("* ")):
            lessons.append(s)
    for item in lessons[-10:]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Next Actions")
    lines.append("- Keep daily reflection concise: issue -> fix -> learning.")
    lines.append("- Promote repeated failures into MEMORY.md lessons.")
    lines.append("- Review this index every Sunday.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"reflection-index-{iso_year}-W{iso_week:02d}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    out = build()
    print(out)
