#!/bin/bash
# ainews 数据预取脚本 - 统一拉取所有数据源
# 定时执行: 早(07:50) + 中(11:30) + 晚(19:30)

PYTHON=/opt/homebrew/bin/python3.12
FALLBACK_PYTHON=/Users/study/.pyenv/versions/3.11.5/bin/python3
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="/tmp/ainews_prefetch"
mkdir -p "$OUT_DIR"

# Use available Python
if [ -x "$PYTHON" ]; then
  PY=$PYTHON
elif [ -x "$FALLBACK_PYTHON" ]; then
  PY=$FALLBACK_PYTHON
else
  PY=python3
fi

export HTTP_PROXY="http://127.0.0.1:1087"
export HTTPS_PROXY="http://127.0.0.1:1087"

echo "[$(date)] Starting prefetch (Python: $PY)..."

# 1. RSS 聚合（100+ 源，并发抓取）
echo "[$(date)] Fetching RSS..."
$PY "$SCRIPT_DIR/build_digest_input.py" \
  --out "$OUT_DIR/digest_latest.json" \
  --workers 20 --timeout 10 --days 2 --max-total 40 \
  2>"$OUT_DIR/rss.log"

# 2. GitHub AI Trending
echo "[$(date)] Fetching GitHub Trending..."
$PY "$SCRIPT_DIR/github_trending.py" --ai-only --limit 10 --json \
  > "$OUT_DIR/github_trending.json" 2>>"$OUT_DIR/github.log" \
  || echo "[]" > "$OUT_DIR/github_trending.json"

# 3. ArXiv 论文（为午间 paper-digest 预取）
echo "[$(date)] Fetching ArXiv papers..."
$PY "$SCRIPT_DIR/arxiv_papers.py" --top 8 --json \
  > "$OUT_DIR/arxiv_papers.json" 2>>"$OUT_DIR/arxiv.log" \
  || echo "[]" > "$OUT_DIR/arxiv_papers.json"

# 4. 生成状态文件
$PY "$SCRIPT_DIR/gen_status.py" "$OUT_DIR"

echo "[$(date)] Prefetch done."
