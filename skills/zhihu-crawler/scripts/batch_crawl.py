#!/usr/bin/env python3
"""批量爬取所有文章/回答"""

import argparse
import hashlib
import logging
import re
import subprocess
import sys
import time
from pathlib import Path


logger = logging.getLogger(__name__)


def load_urls(urls_file: Path) -> list[str]:
    """加载 URL 列表"""
    if not urls_file.exists():
        logger.warning("URL 文件不存在：%s", urls_file)
        return []

    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    logger.info("已加载 %d 个 URL（来源：%s）", len(urls), urls_file)
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

        stderr_preview = (result.stderr or "").strip()[:500]
        logger.error(
            "爬取子进程返回非零退出码（code=%s，item_id=%s，type=%s，URL=%s），stderr 前缀：%s",
            result.returncode,
            item_id,
            item_type,
            url,
            stderr_preview,
        )
        return False
    except subprocess.TimeoutExpired:
        logger.error("爬取超时（item_id=%s，type=%s，URL=%s）", item_id, item_type, url)
        return False
    except Exception as e:
        logger.error("爬取异常（item_id=%s，type=%s，URL=%s）：%s", item_id, item_type, url, e)
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - batch_crawl - %(message)s",
    )

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

    batch_start = time.perf_counter()
    logger.info(
        "开始批量爬取，用户名：%s，类型：%s，最大重试次数：%d，间隔：%d 秒",
        args.username,
        args.type,
        args.max_retries,
        args.delay,
    )

    crawled_urls = load_crawled_urls(crawled_file)

    urls_to_crawl: list[tuple[str, str]] = []

    if args.type in ["articles", "all"]:
        articles_urls_file = urls_dir / "articles-urls.txt"
        articles_urls = load_urls(articles_urls_file)
        new_articles = [url for url in articles_urls if url not in crawled_urls]
        urls_to_crawl.extend(("articles", url) for url in new_articles)
        logger.info(
            "文章：%d/%d 个待爬取（未爬取/总数）",
            len(new_articles),
            len(articles_urls),
        )

    if args.type in ["answers", "all"]:
        answers_urls_file = urls_dir / "answers-urls.txt"
        answers_urls = load_urls(answers_urls_file)
        new_answers = [url for url in answers_urls if url not in crawled_urls]
        urls_to_crawl.extend(("answers", url) for url in new_answers)
        logger.info(
            "回答：%d/%d 个待爬取（未爬取/总数）",
            len(new_answers),
            len(answers_urls),
        )

    if not urls_to_crawl:
        logger.info("没有需要爬取的内容，直接退出")
        return 0

    total_to_crawl = len(urls_to_crawl)
    logger.info("总计：%d 个待爬取", total_to_crawl)

    success_count = 0
    failed_count = 0

    for idx, (content_type, url) in enumerate(urls_to_crawl, 1):
        logger.info("[%d/%d] 开始爬取：%s", idx, total_to_crawl, url)

        item_type, item_id = get_item_type_and_id(url)
        item_start = time.perf_counter()
        success = False

        for retry in range(args.max_retries):
            if crawl_item(url, output_dir, item_id, item_type):
                logger.info("✓ 爬取成功：%s（type=%s）", item_id, content_type)
                save_crawled_url(crawled_file, url)
                success_count += 1
                success = True
                break

            logger.warning(
                "爬取失败，准备重试 %d/%d（URL=%s，item_id=%s）",
                retry + 1,
                args.max_retries,
                url,
                item_id,
            )
            time.sleep(5)
        else:
            logger.error(
                "✗ 爬取失败（已达到最大重试次数），URL=%s，item_id=%s",
                url,
                item_id,
            )
            failed_count += 1

        item_end = time.perf_counter()
        logger.info(
            "本条 URL 耗时：%.3f 秒（type=%s，item_id=%s，结果=%s）",
            item_end - item_start,
            content_type,
            item_id,
            "成功" if success else "失败",
        )

        if idx < total_to_crawl:
            logger.info("等待 %d 秒后抓取下一条...", args.delay)
            time.sleep(args.delay)

    batch_end = time.perf_counter()
    logger.info(
        "批量爬取完成，总耗时：%.3f 秒，总计：%d 条，成功：%d 条，失败：%d 条",
        batch_end - batch_start,
        total_to_crawl,
        success_count,
        failed_count,
    )

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
