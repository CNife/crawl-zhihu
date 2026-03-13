#!/usr/bin/env python3
"""爬取单篇文章或回答"""

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


logger = logging.getLogger(__name__)

MAX_IMAGE_DOWNLOAD_WORKERS = 4
SCROLL_MAX_TIMES = 10
SCROLL_INTERVAL_SEC = 0.5
SCROLL_STABLE_ROUNDS = 3


def run_agent_browser(command: list[str], timeout: int = 60) -> tuple[str, str, int]:
    """运行 agent-browser 命令"""
    cmd = ["agent-browser", "--cdp", "9222"] + command
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def extract_metadata() -> dict:
    """提取页面元数据"""
    js_code = """
    const $ = (s) => document.querySelector(s);
    const $$ = (s) => document.querySelectorAll(s);
    
    const voteElement = $('[class*="Vote"]');
    const commentElement = $('[class*="Comment"]');
    
    JSON.stringify({
        title: $('h1')?.textContent.trim() || '',
        author: $('[itemprop="author"]')?.textContent.trim() || '',
        publishTime: $('time')?.getAttribute('datetime') || $('[itemprop="dateModified"]')?.getAttribute('datetime') || '',
        voteCount: parseInt((voteElement?.textContent || '0').replace(/[^\\d]/g, '')) || 0,
        commentCount: parseInt((commentElement?.textContent || '0').replace(/[^\\d]/g, '')) || 0,
        contentHtml: $$('.RichText')[0]?.innerHTML || '',
        images: Array.from($$('.RichText img[data-original]'))
            .map(img => img.getAttribute('data-original') || img.src)
    }, null, 2)
    """

    result = run_agent_browser(["eval", js_code])

    try:
        metadata_str = result[0]
        if metadata_str.startswith('"') and metadata_str.endswith('"'):
            metadata_str = json.loads(metadata_str)
        return json.loads(metadata_str)
    except json.JSONDecodeError as e:
        raw_preview = result[0][:200] if result and result[0] else ""
        logger.error("解析元数据失败：%s，原始内容前缀：%s", e, raw_preview)
        return {
            "title": "",
            "author": "",
            "publishTime": "",
            "voteCount": 0,
            "commentCount": 0,
            "contentHtml": "",
            "images": [],
        }


def get_page_state() -> tuple[int, int]:
    """获取页面高度和图片数量"""
    js_code = """
    JSON.stringify({
      height: document.body ? (document.body.scrollHeight || 0) : 0,
      images: document.querySelectorAll('.RichText img[data-original], .RichText img').length
    })
    """
    stdout, stderr, code = run_agent_browser(["eval", js_code])

    try:
        data_str = stdout or ""
        if data_str.startswith('"') and data_str.endswith('"'):
            data_str = json.loads(data_str)
        data = json.loads(data_str)
        height = int(data.get("height", 0))
        images = int(data.get("images", 0))
        return height, images
    except Exception as e:  # noqa: BLE001
        logger.warning("获取页面状态失败：%s，stdout 前缀：%s", e, (stdout or "")[:200])
        return 0, 0


def smart_scroll_to_load_images():
    """智能滚动页面，尽量触发懒加载并在稳定后提前结束"""
    logger.info("滚动页面触发懒加载（智能策略）...")

    last_height, last_images = get_page_state()
    stable_rounds = 0
    t_start = time.perf_counter()

    for i in range(1, SCROLL_MAX_TIMES + 1):
        logger.info(
            "第 %d 次滚动前，高度=%d, 图片数=%d",
            i,
            last_height,
            last_images,
        )

        run_agent_browser(["eval", "window.scrollTo(0, document.body.scrollHeight)"])
        time.sleep(SCROLL_INTERVAL_SEC)

        height, images = get_page_state()
        logger.info(
            "第 %d 次滚动后，高度=%d, 图片数=%d（Δheight=%d, Δimages=%d）",
            i,
            height,
            images,
            height - last_height,
            images - last_images,
        )

        if height <= last_height and images <= last_images:
            stable_rounds += 1
            logger.info("页面状态无明显变化，稳定计数=%d", stable_rounds)
        else:
            stable_rounds = 0
            last_height, last_images = height, images

        if stable_rounds >= SCROLL_STABLE_ROUNDS:
            logger.info("检测到页面高度和图片数连续稳定，提前结束滚动")
            break
    else:
        logger.info("达到最大滚动次数 %d，结束滚动", SCROLL_MAX_TIMES)

    elapsed = time.perf_counter() - t_start
    logger.info("智能滚动结束，总耗时：%.3f 秒", elapsed)


def download_image(image_url: str, save_path: Path) -> bool:
    """下载图片"""
    try:
        if not image_url.startswith("http"):
            image_url = "https:" + image_url if image_url.startswith("//") else image_url

        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return True
    except Exception as e:
        logger.warning("下载图片失败 %s: %s", image_url, e)
        return False


def download_images(images: list[str], images_dir: Path, item_id: str) -> list[dict]:
    """下载所有图片（带 URL 去重）"""
    # URL 去重：记录已下载的 URL 和对应的本地路径
    seen_urls: dict[str, str | None] = {}
    downloaded_images = []

    # 先过滤出需要实际下载的图片（去重）
    unique_images = []
    for img_url in images:
        if img_url not in seen_urls:
            unique_images.append(img_url)
            seen_urls[img_url] = None  # 占位，后面填充

    logger.info("图片 URL 去重：%d 张原始图片 -> %d 张唯一图片", len(images), len(unique_images))

    # 并行下载唯一图片
    with ThreadPoolExecutor(max_workers=MAX_IMAGE_DOWNLOAD_WORKERS) as executor:
        future_to_url: dict = {}
        for idx, img_url in enumerate(unique_images, 1):
            img_name = f"{item_id}-img-{idx:03d}.jpg"
            img_path = images_dir / img_name
            logger.info("提交下载任务 %d/%d: %s", idx, len(unique_images), img_name)
            future = executor.submit(download_image, img_url, img_path)
            future_to_url[future] = (img_url, img_name)

        for future in as_completed(future_to_url):
            img_url, img_name = future_to_url[future]
            success = future.result()
            if success:
                seen_urls[img_url] = f"../images/{img_name}"
                logger.info("下载完成: %s", img_name)
            else:
                seen_urls[img_url] = None

    # 构建返回列表（按原始顺序，包含重复 URL 的映射）
    for img_url in images:
        local_path = seen_urls.get(img_url)
        if local_path:
            downloaded_images.append({"original_url": img_url, "local_path": local_path})
        else:
            downloaded_images.append(
                {"original_url": img_url, "local_path": None, "error": "下载失败"}
            )

    return downloaded_images


def save_metadata(metadata: dict, output_dir: Path):
    """保存元数据到 JSON 文件"""
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info("已保存元数据到 %s", metadata_path)


def save_content_html(html: str, output_dir: Path):
    """保存 HTML 内容"""
    html_path = output_dir / "content.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("已保存 HTML 内容到 %s", html_path)


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """清理文件名"""
    filename = re.sub(r"[^\\w\\u4e00-\\u9fff\\-\\s]", "", filename)
    filename = filename.replace(" ", "-").replace("_", "-")
    filename = re.sub(r"-+", "-", filename)
    return filename[:max_length].strip("-")


def extract_date_from_url(url: str) -> str:
    """从 URL 提取日期（如果有）"""
    match = re.search(r"/(\d{4}-\d{2}-\d{2})/", url)
    if match:
        return match.group(1)
    return time.strftime("%Y-%m-%d")


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - crawl_item - %(message)s",
    )

    parser = argparse.ArgumentParser(description="爬取单篇文章或回答")
    parser.add_argument("url", help="文章/回答 URL")
    parser.add_argument("output_dir", help="输出目录")
    parser.add_argument("item_id", help="项目 ID（用于图片命名）")
    args = parser.parse_args()

    t_start = time.perf_counter()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images_dir = output_dir.parent.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    logger.info("打开页面：%s", args.url)
    t_open_start = time.perf_counter()
    run_agent_browser(["open", args.url])

    logger.info("等待页面加载...")
    run_agent_browser(["wait", "--load", "networkidle"])
    t_open_done = time.perf_counter()
    logger.info("打开页面并初次等待耗时：%.3f 秒", t_open_done - t_open_start)

    # 滚动触发懒加载图片（智能策略）
    t_scroll_start = time.perf_counter()
    smart_scroll_to_load_images()
    t_scroll_done = time.perf_counter()
    logger.info("滚动懒加载耗时：%.3f 秒", t_scroll_done - t_scroll_start)

    logger.info("提取元数据...")
    t_meta_start = time.perf_counter()
    metadata = extract_metadata()
    t_meta_done = time.perf_counter()
    logger.info("提取元数据耗时：%.3f 秒", t_meta_done - t_meta_start)

    if not metadata["title"]:
        logger.error("未找到标题，可能是页面结构变化或需要登录")
        return 1

    logger.info("标题：%s", metadata["title"])
    logger.info("作者：%s", metadata["author"])
    logger.info("发布时间：%s", metadata["publishTime"])
    logger.info("点赞数：%d", metadata["voteCount"])

    if metadata["images"]:
        logger.info("检测到 %d 张图片，开始下载...", len(metadata["images"]))
        t_images_start = time.perf_counter()
        downloaded_images = download_images(metadata["images"], images_dir, args.item_id)
        t_images_done = time.perf_counter()
        logger.info("下载图片耗时：%.3f 秒", t_images_done - t_images_start)
        metadata["downloaded_images"] = downloaded_images
    else:
        logger.info("没有找到图片")
        metadata["downloaded_images"] = []

    save_metadata(metadata, output_dir)
    save_content_html(metadata["contentHtml"], output_dir)

    t_end = time.perf_counter()
    logger.info("爬取完成：%s，单篇总耗时：%.3f 秒", args.item_id, t_end - t_start)

    return 0


if __name__ == "__main__":
    sys.exit(main())
