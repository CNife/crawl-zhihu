#!/usr/bin/env python3
"""将 HTML 转换为 Markdown"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import html2text
from bs4 import BeautifulSoup


def html_to_markdown(html: str, images: list[dict] | None = None) -> str:
    """将 HTML 转换为 Markdown"""
    if not html:
        return ""

    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_images = False
    h.ignore_links = False
    h.ignore_emphasis = False

    if images:
        image_map = {
            img["original_url"]: img["local_path"] for img in images if img.get("local_path")
        }

        soup = BeautifulSoup(html, "html.parser")
        for img_tag in soup.find_all("img"):
            original_src = img_tag.get("data-original") or img_tag.get("src") or ""

            if original_src in image_map:
                img_tag["src"] = image_map[original_src]
                if "data-original" in img_tag.attrs:
                    del img_tag["data-original"]

        html = str(soup)

    markdown = h.handle(html)

    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    return markdown.strip()


def sanitize_title(title: str, max_length: int = 50) -> str:
    """清理标题作为文件名"""
    title = re.sub(r"[^\w\u4e00-\u9fff\-_\s]", "", title)
    title = title.replace(" ", "-").replace("_", "-")
    title = re.sub(r"-+", "-", title)
    return title[:max_length].strip("-")


def generate_filename(publish_time: str, title: str) -> str:
    """生成文件名"""
    if publish_time:
        try:
            date = publish_time[:10]
            datetime.strptime(date, "%Y-%m-%d")
        except (ValueError, IndexError):
            date = datetime.now().strftime("%Y-%m-%d")
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    slug = sanitize_title(title)

    return f"{date}_{slug}.md"


def convert_item(item_dir: Path, output_dir: Path) -> bool:
    """转换单个项目"""
    metadata_file = item_dir / "metadata.json"

    if not metadata_file.exists():
        print(f"✗ 跳过（无元数据）: {item_dir}")
        return False

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    title = metadata.get("title", "无标题")
    author = metadata.get("author", "未知作者")
    publish_time = metadata.get("publishTime", "")
    vote_count = metadata.get("voteCount", 0)
    content_html = metadata.get("contentHtml", "")
    downloaded_images = metadata.get("downloaded_images", [])

    content_md = html_to_markdown(content_html, downloaded_images)

    md_content = f"# {title}\n\n"
    md_content += f"**作者**: {author}\n\n"

    if publish_time:
        md_content += f"**发布时间**: {publish_time[:10]}\n\n"

    if vote_count > 0:
        md_content += f"**点赞数**: {vote_count}\n\n"

    if content_md:
        md_content += f"---\n\n{content_md}\n\n"

    original_url = metadata.get("url", "")
    if not original_url and item_dir.name.startswith(("article-", "answer-")):
        crawled_file = item_dir.parent.parent.parent / "urls" / "crawled-urls.txt"
        if crawled_file.exists():
            with open(crawled_file, "r", encoding="utf-8") as f:
                for line in f:
                    if item_dir.name.replace("-", "/") in line:
                        original_url = line.strip()
                        break

    if original_url:
        md_content += f"\n---\n\n**原文链接**: {original_url}\n"

    filename = generate_filename(publish_time, title)

    if item_dir.parent.name == "articles":
        output_subdir = output_dir / "articles"
    elif item_dir.parent.name == "answers":
        output_subdir = output_dir / "answers"
    else:
        output_subdir = output_dir / item_dir.parent.name

    output_subdir.mkdir(parents=True, exist_ok=True)
    output_file = output_subdir / filename

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✓ 已转换：{filename}")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="将 HTML 转换为 Markdown")
    parser.add_argument("--input", required=True, help="输入目录（包含 articles/answers 子目录）")
    args = parser.parse_args()

    input_dir = Path(args.input)

    if not input_dir.exists():
        print(f"✗ 输入目录不存在：{input_dir}")
        return 1

    converted_count = 0

    for content_type in ["articles", "answers"]:
        content_dir = input_dir / content_type

        if not content_dir.exists():
            continue

        print(f"\n处理 {content_type}...")

        for item_dir in content_dir.iterdir():
            if item_dir.is_dir():
                if convert_item(item_dir, input_dir):
                    converted_count += 1

    print(f"\n{'=' * 50}")
    print(f"✓ 转换完成，共 {converted_count} 个文件")
    print(f"{'=' * 50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
