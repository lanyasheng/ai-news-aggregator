#!/usr/bin/env python3
"""URL 文章抓取和预处理脚本"""

import json
import sys
import os
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser


class ArticleExtractor(HTMLParser):
    """简单的文章正文提取器"""
    def __init__(self):
        super().__init__()
        self.title = ""
        self.text_parts = []
        self.in_title = False
        self.in_article = False
        self.in_script = False
        self.in_style = False
        self.in_p = False
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag in ("script", "noscript"):
            self.in_script = True
        elif tag == "style":
            self.in_style = True
        elif tag in ("article", "main"):
            self.in_article = True
            self.depth += 1
        elif tag == "p":
            self.in_p = True

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_script or self.in_style:
            return
        elif self.in_p or self.in_article:
            text = data.strip()
            if text and len(text) > 10:
                self.text_parts.append(text)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ("script", "noscript"):
            self.in_script = False
        elif tag == "style":
            self.in_style = False
        elif tag in ("article", "main"):
            self.depth -= 1
            if self.depth <= 0:
                self.in_article = False
        elif tag == "p":
            self.in_p = False


def fetch_article(url, timeout=15):
    """抓取 URL 内容"""
    proxy = None
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if http_proxy:
        proxy = urllib.request.ProxyHandler({"http": http_proxy, "https": http_proxy})

    opener = urllib.request.build_opener(proxy) if proxy else urllib.request.build_opener()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })

    try:
        resp = opener.open(req, timeout=timeout)
        content_type = resp.headers.get("Content-Type", "")
        encoding = "utf-8"
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].split(";")[0].strip()
        return resp.read().decode(encoding, errors="replace")
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def extract_article(html_content):
    """从 HTML 中提取文章内容"""
    parser = ArticleExtractor()
    parser.feed(html_content)

    title = parser.title.strip()
    content = "\n\n".join(parser.text_parts)

    content = re.sub(r"\s+", " ", content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    return {"title": title, "content": content[:5000]}


def try_jina_reader(url):
    """尝试使用 Jina Reader API 获取更好的解析结果"""
    jina_url = f"https://r.jina.ai/{url}"
    proxy = None
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if http_proxy:
        proxy = urllib.request.ProxyHandler({"http": http_proxy, "https": http_proxy})

    opener = urllib.request.build_opener(proxy) if proxy else urllib.request.build_opener()
    req = urllib.request.Request(jina_url, headers={
        "Accept": "text/plain",
        "User-Agent": "AI-News-Aggregator/1.0",
    })

    try:
        resp = opener.open(req, timeout=20)
        return resp.read().decode("utf-8", errors="replace")[:5000]
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="文章抓取和预处理")
    parser.add_argument("url", help="要抓取的文章 URL")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--jina", action="store_true", help="优先使用 Jina Reader")
    args = parser.parse_args()

    result = {"url": args.url, "title": "", "content": "", "method": "direct"}

    if args.jina:
        print("尝试 Jina Reader...", file=sys.stderr)
        jina_content = try_jina_reader(args.url)
        if jina_content and len(jina_content) > 100:
            result["content"] = jina_content
            result["method"] = "jina"
            lines = jina_content.split("\n")
            for line in lines[:5]:
                line = line.strip()
                if line and not line.startswith("http") and len(line) > 5:
                    result["title"] = line
                    break
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"📖 文章内容 (via Jina Reader)")
                print(f"📌 标题: {result['title']}")
                print(f"🔗 URL: {result['url']}")
                print("=" * 60)
                print(result["content"])
            return

    print("直接抓取文章...", file=sys.stderr)
    html = fetch_article(args.url)
    if html:
        article = extract_article(html)
        result["title"] = article["title"]
        result["content"] = article["content"]

    if not result["content"] or len(result["content"]) < 100:
        print("直接抓取内容不足，尝试 Jina Reader...", file=sys.stderr)
        jina_content = try_jina_reader(args.url)
        if jina_content and len(jina_content) > len(result.get("content", "")):
            result["content"] = jina_content
            result["method"] = "jina"

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"📖 文章内容 (via {result['method']})")
        print(f"📌 标题: {result['title']}")
        print(f"🔗 URL: {result['url']}")
        print("=" * 60)
        if result["content"]:
            print(result["content"][:3000])
        else:
            print("⚠️ 无法获取文章内容")


if __name__ == "__main__":
    main()
