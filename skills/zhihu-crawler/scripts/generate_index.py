#!/usr/bin/env python3
"""生成 Markdown 索引文件"""

import argparse
import re
import sys
from pathlib import Path


def extract_metadata_from_md(file_path: Path) -> dict:
    """从 Markdown 文件提取元数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    title = ""
    author = ""
    publish_date = ""
    vote_count = 0

    for i, line in enumerate(lines[:20]):
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("**作者**:") or line.startswith("**作者**:"):
            author = line.split(":", 1)[1].strip()
        elif line.startswith("**发布时间**:") or line.startswith("**发布时间**:"):
            publish_date = line.split(":", 1)[1].strip()
        elif line.startswith("**点赞数**:") or line.startswith("**点赞数**:"):
            vote_str = line.split(":", 1)[1].strip()
            vote_count = int(re.sub(r"[^\d]", "", vote_str)) or 0

    if not publish_date and file_path.stem:
        match = re.match(r"(\d{4}-\d{2}-\d{2})", file_path.stem)
        if match:
            publish_date = match.group(1)

    return {
        "title": title,
        "author": author,
        "publish_date": publish_date,
        "vote_count": vote_count,
        "filename": file_path.name,
    }


def scan_markdown_files(directory: Path, subdir: str) -> list[dict]:
    """扫描指定目录下的所有 Markdown 文件"""
    md_dir = directory / subdir

    if not md_dir.exists():
        return []

    files = []
    for md_file in md_dir.glob("*.md"):
        metadata = extract_metadata_from_md(md_file)
        files.append(metadata)

    files.sort(key=lambda x: x["publish_date"], reverse=True)

    return files


def generate_index_table(files: list[dict], content_type: str) -> str:
    """生成索引表格"""
    if not files:
        return ""

    type_name = "文章" if content_type == "articles" else "回答"

    md = f"## {type_name}\n\n"
    md += "| 发布日期 | 标题 | 点赞数 |\n"
    md += "|----------|------|--------|\n"

    for file_info in files:
        date = file_info["publish_date"] or "未知日期"
        title = file_info["title"] or file_info["filename"]
        vote = file_info["vote_count"] if file_info["vote_count"] > 0 else "-"

        filename = file_info["filename"].replace(".md", "")
        md += f"| {date} | [{title}]({content_type}/{filename}) | {vote} |\n"

    md += "\n"

    return md


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成 Markdown 索引文件")
    parser.add_argument("output_dir", help="输出目录（包含 articles/answers 子目录）")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if not output_dir.exists():
        print(f"✗ 输出目录不存在：{output_dir}")
        return 1

    print("扫描文章...")
    articles = scan_markdown_files(output_dir, "articles")
    print(f"找到 {len(articles)} 篇文章")

    print("扫描回答...")
    answers = scan_markdown_files(output_dir, "answers")
    print(f"找到 {len(answers)} 个回答")

    print("\n生成索引文件...")

    index_content = "# 知乎内容索引\n\n"

    username = output_dir.name
    index_content += f"**用户名**: {username}\n\n"

    total = len(articles) + len(answers)
    index_content += f"**总计**: {total} 篇内容\n"
    index_content += f"- 文章：{len(articles)} 篇\n"
    index_content += f"- 回答：{len(answers)} 篇\n\n"

    index_content += "---\n\n"

    if articles:
        index_content += generate_index_table(articles, "articles")

    if answers:
        index_content += generate_index_table(answers, "answers")

    index_file = output_dir / "README.md"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"✓ 已生成索引文件：{index_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
