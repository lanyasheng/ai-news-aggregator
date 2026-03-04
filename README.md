# AI News Aggregator

[English](./README_EN.md) | 中文

高性能 AI/技术新闻聚合引擎，专为 OpenClaw Agent 设计。并发抓取 100+ RSS 源，支持兴趣评分、跨天去重、日期过滤。

## 特性

- ⚡ **高性能**: 20 线程并发，100+ 源 12 秒完成
- 💾 **智能缓存**: ETag/Last-Modified + 跨天 URL 去重（7 天窗口）
- 🎯 **兴趣评分**: 按用户兴趣标签排序（agent/skills/mcp/工程实践等）
- 📅 **日期过滤**: `--days N` 抓取最近 N 天新闻
- 📊 **100+ RSS 源**: 8 大分类覆盖 AI 全生态
- 🔬 **arXiv 集成**: AI/ML/NLP 最新论文
- 📈 **GitHub Trending**: AI 热门项目追踪
- 🔄 **统一预取**: `prefetch_data.sh` 一键并行获取所有数据源

## 安装

### 通过 ClawHub（推荐）

```bash
clawhub install ai-news-aggregator
clawhub update ai-news-aggregator
```

### 手动克隆

```bash
git clone https://github.com/lanyasheng/ai-news-aggregator.git
cd ai-news-aggregator
# 纯标准库，无需安装依赖，需要 Python 3.8+
```

## 使用

### 统一预取（推荐，用于定时任务）

```bash
# 一键并行获取 RSS + GitHub + arXiv，输出到 /tmp/ainews_prefetch/
bash scripts/prefetch_data.sh
```

### 单独使用

```bash
# RSS 聚合（支持分类和日期过滤）
python3 scripts/rss_aggregator.py --category all --days 1 --limit 10 --json

# 构建摘要输入（兴趣评分 + 去重 + 排序）
python3 scripts/build_digest_input.py --out /tmp/digest.json --days 2 --max-total 40

# arXiv 论文
python3 scripts/arxiv_papers.py --top 8 --json

# GitHub AI Trending
python3 scripts/github_trending.py --ai-only --limit 10 --json
```

### 分类说明

| 分类 | 源数 | 说明 |
|------|------|------|
| company | 16 | OpenAI, Anthropic, Google, Meta, NVIDIA 等官方博客 |
| papers | 6 | arXiv, HuggingFace Daily Papers, BAIR |
| media | 16 | MIT Tech Review, TechCrunch, Wired, VentureBeat |
| newsletter | 15 | Simon Willison, Lilian Weng, Andrew Ng, Karpathy |
| community | 12 | HN, GitHub Trending, Product Hunt, V2EX |
| cn_media | 5 | 机器之心, 量子位, 36氪, 少数派, InfoQ |
| ai-agent | 5 | LangChain, LlamaIndex, Mem0, Ollama, vLLM |
| twitter | 10 | Sam Altman, Karpathy, LeCun, Hassabis |

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `rss_aggregator.py` | 核心 RSS 抓取器（并发 + 缓存） |
| `build_digest_input.py` | 构建摘要：兴趣评分 + 跨天去重 + per_source 限制 |
| `github_trending.py` | GitHub Trending AI 项目 |
| `arxiv_papers.py` | arXiv 论文搜索 |
| `summarize_url.py` | 单篇文章摘要（Jina/直接抓取） |
| `gen_status.py` | 预取状态文件生成 |
| `prefetch_data.sh` | 统一预取入口（并行执行以上脚本） |

## 配置

编辑 `scripts/rss_sources.json` 管理 RSS 源：

```json
{
  "name": "OpenAI Blog",
  "url": "https://openai.com/blog/rss.xml",
  "category": "company"
}
```

## 许可

MIT License
