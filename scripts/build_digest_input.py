#!/usr/bin/env python3
"""Build compact input for daily AI digest.

Pipeline:
1) Batch fetch RSS with ai-news-aggregator concurrent mode.
2) Clean and dedupe entries.
3) Attach category metadata.
4) Keep a bounded candidate set for LLM summarization.
5) Optionally fetch GitHub AI trending.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RSS_SCRIPT = ROOT / "rss_aggregator.py"
GH_SCRIPT = ROOT / "github_trending.py"
SOURCES_FILE = ROOT / "rss_sources.json"


def run_json_command(cmd: list[str], timeout: int) -> Any:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        env=os.environ.copy(),
        cwd=str(ROOT.parent.parent.parent),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"json parse failed: {e}\nstdout[:500]={proc.stdout[:500]}") from e


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    iso = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def load_source_categories() -> dict[str, str]:
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)
    mapping: dict[str, str] = {}
    for src in sources:
        mapping[src.get("name", "")] = src.get("category", "unknown")
    return mapping


def clean_items(items: list[dict[str, Any]], source_to_category: dict[str, str]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for it in items:
        title = (it.get("title") or "").strip()
        url = (it.get("url") or "").strip()
        if not title or not url or not url.startswith("http"):
            continue
        if url in seen_urls:
            continue

        source = (it.get("source") or "").strip() or "unknown"
        category = source_to_category.get(source, "unknown")
        dt = parse_dt(it.get("date") or "")

        cleaned.append(
            {
                "title": title,
                "url": url,
                "desc": (it.get("desc") or "").strip(),
                "date": (it.get("date") or "").strip(),
                "source": source,
                "category": category,
                "ts": dt.timestamp() if dt else 0,
            }
        )
        seen_urls.add(url)

    return cleaned




# User interest keywords for scoring - higher weight = more interesting
INTEREST_KEYWORDS = {
    # Core interests (weight 3)
    "agent": 3, "agents": 3, "agentic": 3, "multi-agent": 3,
    "mcp": 3, "model context protocol": 3,
    "skill": 3, "skills": 3,
    "openclaw": 3, "claude code": 3, "codex": 3, "cursor": 3,
    "workflow": 3, "orchestration": 3,
    # Engineering practice (weight 2)
    "rag": 2, "retrieval": 2, "embedding": 2, "vector": 2,
    "memory": 2, "knowledge graph": 2, "ontology": 2,
    "langchain": 2, "llamaindex": 2, "crewai": 2, "autogen": 2,
    "tool use": 2, "function calling": 2,
    "prompt engineering": 2, "prompt": 2,
    "fine-tuning": 2, "fine tuning": 2,
    "deployment": 2, "production": 2, "observability": 2,
    "evaluation": 2, "benchmark": 2,
    # Secondary interests (weight 1)
    "llm": 1, "gpt": 1, "claude": 1, "gemini": 1,
    "transformer": 1, "diffusion": 1,
    "quantitative": 1, "trading": 1, "finance": 1,
    "open source": 1, "open-source": 1, "github": 1,
}

DEDUP_FILE = "/tmp/ainews_prefetch/pushed_urls.json"
DEDUP_DAYS = 7


def score_interest(item: dict[str, Any]) -> int:
    """Score item based on user interest keywords."""
    text = (item.get("title", "") + " " + item.get("desc", "")).lower()
    score = 0
    for keyword, weight in INTEREST_KEYWORDS.items():
        if keyword in text:
            score += weight
    return score


def load_pushed_urls() -> set[str]:
    """Load previously pushed URLs for cross-day dedup."""
    if not os.path.exists(DEDUP_FILE):
        return set()
    try:
        with open(DEDUP_FILE, "r") as f:
            data = json.load(f)
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=DEDUP_DAYS)).timestamp()
        return {url for url, ts in data.items() if ts > cutoff}
    except Exception:
        return set()


def save_pushed_urls(urls: set[str], existing: set[str]) -> None:
    """Save pushed URLs with timestamps."""
    from datetime import datetime, timedelta
    data = {}
    if os.path.exists(DEDUP_FILE):
        try:
            with open(DEDUP_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass
    cutoff = (datetime.now() - timedelta(days=DEDUP_DAYS)).timestamp()
    data = {url: ts for url, ts in data.items() if ts > cutoff}
    now = datetime.now().timestamp()
    for url in urls:
        data[url] = now
    with open(DEDUP_FILE, "w") as f:
        json.dump(data, f)


def cap_candidates(items: list[dict[str, Any]], per_source: int, max_total: int) -> list[dict[str, Any]]:
    """Select candidates by interest score, not per-source hard cap.
    per_source is only used as anti-spam floor (max from single source = max_total//3).
    """
    pushed = load_pushed_urls()
    items = [it for it in items if it.get("url", "") not in pushed]

    for it in items:
        it["_interest"] = score_interest(it)

    items.sort(key=lambda x: (-x.get("_interest", 0), -x.get("ts", 0)))

    source_count: dict[str, int] = defaultdict(int)
    max_per_source = max(per_source, max_total // 3)
    result: list[dict[str, Any]] = []
    for it in items:
        src = it.get("source", "unknown")
        if source_count[src] >= max_per_source:
            continue
        result.append(it)
        source_count[src] += 1
        if len(result) >= max_total:
            break

    save_pushed_urls({it.get("url", "") for it in result}, pushed)

    for it in result:
        it.pop("_interest", None)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build compact input for AI digest")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--limit", type=int, default=2, help="per-source fetch cap")
    parser.add_argument("--per-source", type=int, default=1, help="per-source keep cap")
    parser.add_argument("--max-total", type=int, default=45)
    parser.add_argument("--out", default="/tmp/ainews_digest_input.json")
    parser.add_argument("--skip-github", action="store_true")
    args = parser.parse_args()

    source_to_category = load_source_categories()

    rss_cmd = [
        sys.executable,
        str(RSS_SCRIPT),
        "--category",
        "all",
        "--workers",
        str(args.workers),
        "--timeout",
        str(args.timeout),
        "--days",
        str(args.days),
        "--limit",
        str(args.limit),
        "--json",
    ]

    try:
        rss_raw = run_json_command(rss_cmd, timeout=max(30, args.timeout * 20))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1

    cleaned = clean_items(rss_raw, source_to_category)
    candidates = cap_candidates(cleaned, per_source=args.per_source, max_total=args.max_total)

    gh_items: list[dict[str, Any]] = []
    gh_error = ""
    if not args.skip_github:
        gh_cmd = [sys.executable, str(GH_SCRIPT), "--ai-only", "--limit", "10", "--json"]
        try:
            gh_items = run_json_command(gh_cmd, timeout=40)
        except Exception as e:
            gh_error = str(e)

    stats_raw = Counter(it.get("category", "unknown") for it in cleaned)
    stats_candidates = Counter(it.get("category", "unknown") for it in candidates)

    payload = {
        "ok": True,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "params": {
            "workers": args.workers,
            "timeout": args.timeout,
            "days": args.days,
            "limit": args.limit,
            "perSource": args.per_source,
            "maxTotal": args.max_total,
        },
        "stats": {
            "rawItems": len(rss_raw),
            "cleanItems": len(cleaned),
            "candidateItems": len(candidates),
            "byCategoryRaw": dict(stats_raw),
            "byCategoryCandidates": dict(stats_candidates),
            "githubTrendingCount": len(gh_items),
            "githubTrendingError": gh_error,
        },
        "candidates": [{k: v for k, v in it.items() if k != "ts"} for it in candidates],
        "githubTrending": gh_items,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(json.dumps({"ok": True, "out": str(out_path), "stats": payload["stats"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
