#!/usr/bin/env python3
"""爬取单篇文章或回答"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests


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
        print(f"解析元数据失败：{e}, 原始内容：{result[0][:200]}")
        return {
            "title": "",
            "author": "",
            "publishTime": "",
            "voteCount": 0,
            "commentCount": 0,
            "contentHtml": "",
            "images": [],
        }


def download_image(image_url: str, save_path: Path) -> bool:
    """下载图片"""
    try:
        if not image_url.startswith("http"):
            image_url = (
                "https:" + image_url if image_url.startswith("//") else image_url
            )

        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"下载图片失败 {image_url}: {e}")
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

    print(f"去重：{len(images)} 张图片 -> {len(unique_images)} 张唯一图片")

    # 下载唯一图片
    for idx, img_url in enumerate(unique_images, 1):
        img_name = f"{item_id}-img-{idx:03d}.jpg"
        img_path = images_dir / img_name

        print(f"下载图片 {idx}/{len(unique_images)}: {img_name}")

        if download_image(img_url, img_path):
            # 记录 URL -> 本地路径的映射
            seen_urls[img_url] = f"../images/{img_name}"
        else:
            seen_urls[img_url] = None

    # 构建返回列表（按原始顺序，包含重复 URL 的映射）
    for img_url in images:
        local_path = seen_urls.get(img_url)
        if local_path:
            downloaded_images.append(
                {"original_url": img_url, "local_path": local_path}
            )
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
    print(f"✓ 已保存元数据到 {metadata_path}")


def save_content_html(html: str, output_dir: Path):
    """保存 HTML 内容"""
    html_path = output_dir / "content.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ 已保存 HTML 内容到 {html_path}")


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
    parser = argparse.ArgumentParser(description="爬取单篇文章或回答")
    parser.add_argument("url", help="文章/回答 URL")
    parser.add_argument("output_dir", help="输出目录")
    parser.add_argument("item_id", help="项目 ID（用于图片命名）")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images_dir = output_dir.parent.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    print(f"打开页面：{args.url}")
    run_agent_browser(["open", args.url])

    print("等待页面加载...")
    run_agent_browser(["wait", "--load", "networkidle"])

    # 滚动触发懒加载图片
    print("滚动页面触发懒加载...")
    for _ in range(5):
        run_agent_browser(["eval", "window.scrollTo(0, document.body.scrollHeight)"])
        time.sleep(0.5)
    run_agent_browser(["wait", "--load", "networkidle"])

    print("提取元数据...")
    metadata = extract_metadata()

    if not metadata["title"]:
        print("✗ 未找到标题，可能是页面结构变化或需要登录")
        return 1

    print(f"标题：{metadata['title']}")
    print(f"作者：{metadata['author']}")
    print(f"发布时间：{metadata['publishTime']}")
    print(f"点赞数：{metadata['voteCount']}")

    if metadata["images"]:
        print(f"\n下载 {len(metadata['images'])} 张图片...")
        downloaded_images = download_images(
            metadata["images"], images_dir, args.item_id
        )
        metadata["downloaded_images"] = downloaded_images
    else:
        print("没有找到图片")
        metadata["downloaded_images"] = []

    save_metadata(metadata, output_dir)
    save_content_html(metadata["contentHtml"], output_dir)

    print(f"\n✓ 爬取完成：{args.item_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
