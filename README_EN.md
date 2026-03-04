# AI News Aggregator

English | [中文](./README.md)

High-performance AI news aggregation tool designed for OpenClaw/AI Agents. Concurrently fetches 100+ RSS sources with date filtering and smart caching.

## Features

- ⚡ **High Performance**: 10-thread concurrency, 100 sources in ~15 seconds
- 💾 **Smart Caching**: ETag/Last-Modified caching, subsequent runs complete in seconds
- 📅 **Date Filtering**: `--days N` to fetch only news from the last N days
- 📊 **100+ RSS Sources**: Covering OpenAI, Anthropic, Google, Hugging Face, etc.
- 🔬 **arXiv Integration**: Auto-fetch latest AI/ML/NLP papers
- 📈 **GitHub Trending**: Track trending AI projects
- 🐦 **Twitter Monitoring**: Track AI leaders via Nitter RSS
- 🧪 **Well Tested**: Unit test coverage

## Installation

### Via ClawHub (Recommended)

```bash
clawhub install ai-news-aggregator
```

Then add to your agent's SOUL.md:

```markdown
## Skills

- ai-news-aggregator
```

### Manual Install

```bash
# Clone repository
git clone https://github.com/lanyasheng/ai-news-aggregator.git
cd ai-news-aggregator/scripts

# No dependencies required (pure Python standard library)
python3 --version  # Requires Python 3.8+
```

## Usage

### In OpenClaw Agent

Once installed via ClawHub, the skill will be automatically available to your agent. The agent can:

- Fetch today's AI news with `python3 skills/ai-news-aggregator/scripts/rss_aggregator.py --category all --days 1`
- Search arXiv papers with `python3 skills/ai-news-aggregator/scripts/arxiv_papers.py --query "LLM" --top 5`
- Get GitHub trending with `python3 skills/ai-news-aggregator/scripts/github_trending.py --ai-only`

### Command Line

```bash
# Fetch today's news (good for daily reports)
python3 rss_aggregator.py --category all --days 1 --limit 10 --json

# Fetch last 3 days of news
python3 rss_aggregator.py --category all --days 3 --limit 10

# Fetch specific categories
python3 rss_aggregator.py --category company --days 1 --limit 5
python3 rss_aggregator.py --category papers --days 7 --limit 10

# Fetch arXiv papers
python3 arxiv_papers.py --limit 5 --top 10 --json

# GitHub trending AI projects
python3 github_trending.py --ai-only
```

### Categories

| Category | Sources | Description |
|----------|---------|-------------|
| company | 16 | Official blogs: OpenAI, Anthropic, Google, Meta, NVIDIA, etc. |
| papers | 6 | arXiv AI/ML/NLP/CV, HuggingFace Daily Papers |
| media | 16 | MIT Tech Review, TechCrunch, Wired, etc. |
| newsletter | 15 | Experts: Simon Willison, Lilian Weng, Andrew Ng, etc. |
| community | 12 | HN, GitHub, Product Hunt |
| cn_media | 5 | Chinese media: 机器之心, 36氪, 少数派, etc. |
| ai-agent | 5 | Agent frameworks: LangChain, LlamaIndex, Mem0 |
| twitter | 10 | AI leaders: Sam Altman, Karpathy, LeCun, etc. |

## Performance

| Version | 100 Sources | Cached |
|---------|-------------|--------|
| Original (sequential) | Timeout (>120s) | N/A |
| Optimized (concurrent) | ~15s | ~3s |

**8-10x performance improvement**

## Configuration

Edit `scripts/rss_sources.json` to add/remove sources:

```json
{
  "name": "OpenAI Blog",
  "url": "https://openai.com/blog/rss.xml",
  "category": "company"
}
```

## Running Tests

```bash
cd tests
python3 -m unittest test_rss_aggregator -v
```

## License

MIT License - see LICENSE file

## Acknowledgments

- Source references: [tech-news-digest](https://github.com/draco-agent/tech-news-digest)
- Architecture: OpenClaw Community
