#!/usr/bin/env python3
"""批量爬取所有文章/回答"""

import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path


def load_urls(urls_file: Path) -> list[str]:
    """加载 URL 列表"""
    if not urls_file.exists():
        print(f"✗ URL 文件不存在：{urls_file}")
        return []

    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"✓ 已加载 {len(urls)} 个 URL")
    return urls


def load_crawled_urls(crawled_file: Path) -> set[str]:
    """加载已爬取的 URL"""
    if not crawled_file.exists():
        return set()

    with open(crawled_file, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_crawled_url(crawled_file: Path, url: str):
    """保存已爬取的 URL"""
    crawled_file.parent.mkdir(parents=True, exist_ok=True)
    with open(crawled_file, "a", encoding="utf-8") as f:
        f.write(url + "\n")


def crawl_item(url: str, output_dir: Path, item_id: str, item_type: str) -> bool:
    """爬取单个项目"""
    script_path = Path(__file__).parent / "crawl_item.py"

    cmd = [
        sys.executable,
        str(script_path),
        url,
        str(output_dir / item_type / item_id),
        item_id,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return True
        else:
            print(f"✗ 爬取失败：{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ 爬取超时")
        return False
    except Exception as e:
        print(f"✗ 爬取异常：{e}")
        return False


def get_item_type_and_id(url: str) -> tuple[str, str]:
    if match := re.search(r"/p/(\d+)", url):
        return "articles", f"article-{match.group(1)}"

    if match := re.search(r"/answer/(\d+)", url):
        return "answers", f"answer-{match.group(1)}"

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return "unknown", f"unknown-{url_hash}"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量爬取知乎用户的所有文章/回答")
    parser.add_argument("--username", required=True, help="用户名（如 mr-dang-77）")
    parser.add_argument(
        "--type",
        choices=["articles", "answers", "all"],
        default="all",
        help="内容类型（articles=文章，answers=回答，all=全部）",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=3,
        help="每篇文章/回答之间的延迟（秒）",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="最大重试次数",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent.parent
    output_dir = project_root / "output" / args.username
    urls_dir = output_dir / "urls"
    crawled_file = urls_dir / "crawled-urls.txt"

    crawled_urls = load_crawled_urls(crawled_file)

    urls_to_crawl = []

    if args.type in ["articles", "all"]:
        articles_urls_file = urls_dir / "articles-urls.txt"
        articles_urls = load_urls(articles_urls_file)
        new_articles = [url for url in articles_urls if url not in crawled_urls]
        urls_to_crawl.extend(("articles", url) for url in new_articles)
        print(f"文章：{len(new_articles)}/{len(articles_urls)} 个待爬取")

    if args.type in ["answers", "all"]:
        answers_urls_file = urls_dir / "answers-urls.txt"
        answers_urls = load_urls(answers_urls_file)
        new_answers = [url for url in answers_urls if url not in crawled_urls]
        urls_to_crawl.extend(("answers", url) for url in new_answers)
        print(f"回答：{len(new_answers)}/{len(answers_urls)} 个待爬取")

    if not urls_to_crawl:
        print("\n✓ 没有需要爬取的内容")
        return 0

    print(f"\n总计：{len(urls_to_crawl)} 个待爬取")
    print(f"{'=' * 50}")

    success_count = 0
    failed_count = 0

    for idx, (content_type, url) in enumerate(urls_to_crawl, 1):
        print(f"\n[{idx}/{len(urls_to_crawl)}] 爬取：{url}")

        item_type, item_id = get_item_type_and_id(url)

        for retry in range(args.max_retries):
            if crawl_item(url, output_dir, item_id, item_type):
                print(f"✓ 爬取成功：{item_id}")
                save_crawled_url(crawled_file, url)
                success_count += 1
                break
            else:
                print(f"重试 {retry + 1}/{args.max_retries}")
                time.sleep(5)
        else:
            print(f"✗ 爬取失败（已达到最大重试次数）: {url}")
            failed_count += 1

        if idx < len(urls_to_crawl):
            print(f"等待 {args.delay} 秒...")
            time.sleep(args.delay)

    print(f"\n{'=' * 50}")
    print("✓ 批量爬取完成")
    print(f"  成功：{success_count} 个")
    print(f"  失败：{failed_count} 个")
    print(f"{'=' * 50}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
