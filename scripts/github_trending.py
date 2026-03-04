#!/usr/bin/env python3
"""GitHub Trending 抓取脚本 - 获取每日趋势项目"""

import json
import sys
import urllib.request
import urllib.error
import re


def _parse_trending_html(html: str) -> list[dict]:
    """用正则解析 GitHub Trending 页面（HTMLParser 因 GitHub 改版不再可靠）"""
    articles = re.findall(r"<article class=.*?Box-row.*?</article>", html, re.DOTALL)
    repos = []
    for article in articles:
        h2_link = re.search(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"', article, re.DOTALL)
        if not h2_link:
            continue
        href = h2_link.group(1)
        name = href.strip("/")

        desc_match = re.search(r'<p class="[^"]*col-9[^"]*">(.*?)</p>', article, re.DOTALL)
        desc = desc_match.group(1).strip() if desc_match else ""

        stars_match = re.search(r'([\d,]+)\s+stars\s+today', article)
        stars = stars_match.group(1) if stars_match else ""

        lang_match = re.search(r'itemprop="programmingLanguage">(.*?)</span>', article)
        lang = lang_match.group(1).strip() if lang_match else ""

        repos.append({
            "name": name,
            "desc": desc,
            "stars": stars,
            "lang": lang,
            "url": f"https://github.com{href}",
        })
    return repos


def fetch_trending(language="", since="daily"):
    """从 GitHub Trending 页面抓取趋势项目"""
    url = f"https://github.com/trending/{language}?since={since}"

    proxy = None
    import os
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if http_proxy:
        proxy = urllib.request.ProxyHandler({"http": http_proxy, "https": http_proxy})

    opener = urllib.request.build_opener(proxy) if proxy else urllib.request.build_opener()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
    })

    try:
        resp = opener.open(req, timeout=15)
        html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching trending: {e}", file=sys.stderr)
        return []

    return _parse_trending_html(html)


def filter_ai_repos(repos):
    """筛选 AI/ML 相关的项目"""
    ai_keywords = [
        "ai", "ml", "llm", "gpt", "agent", "transformer", "diffusion",
        "neural", "deep-learning", "machine-learning", "nlp", "cv",
        "rag", "embedding", "vector", "langchain", "autogen", "crewai",
        "openai", "anthropic", "gemini", "claude", "ollama", "llama",
        "stable-diffusion", "midjourney", "workflow", "memory", "mcp",
        "copilot", "cursor", "agentic", "reasoning", "cot", "chain-of-thought",
    ]
    filtered = []
    for repo in repos:
        text = (repo["name"] + " " + repo["desc"]).lower()
        if any(kw in text for kw in ai_keywords):
            filtered.append(repo)
    return filtered


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GitHub Trending 抓取")
    parser.add_argument("--language", default="", help="编程语言筛选")
    parser.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--ai-only", action="store_true", help="仅显示 AI 相关项目")
    parser.add_argument("--limit", type=int, default=15, help="最多显示数量")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    repos = fetch_trending(args.language, args.since)

    if args.ai_only:
        repos = filter_ai_repos(repos)

    repos = repos[:args.limit]

    if args.json:
        print(json.dumps(repos, ensure_ascii=False, indent=2))
    else:
        if not repos:
            print("未获取到趋势项目（可能是网络问题或页面结构变化）")
            return

        print(f"🔥 GitHub Trending ({args.since}) - {'AI/ML 相关' if args.ai_only else '全部'}")
        print("=" * 60)
        for i, repo in enumerate(repos, 1):
            stars_str = f" ⭐ {repo['stars']} today" if repo.get("stars") else ""
            print(f"\n{i}. **{repo['name']}**{stars_str}")
            if repo["desc"]:
                print(f"   {repo['desc']}")
            print(f"   {repo['url']}")


if __name__ == "__main__":
    main()
