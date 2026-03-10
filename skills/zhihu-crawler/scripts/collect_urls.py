#!/usr/bin/env python3
"""爬取用户的所有文章/回答 URL"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_agent_browser(command: list[str], timeout: int = 60) -> tuple[str, str, int]:
    """运行 agent-browser 命令"""
    cmd = ["agent-browser", "--cdp", "9222"] + command
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def scroll_to_load_more(username: str, content_type: str, max_scrolls: int = 20):
    """滚动加载所有内容"""
    base_url = f"https://www.zhihu.com/people/{username}/{content_type}"

    print(f"打开用户主页：{base_url}")
    run_agent_browser(["open", base_url])

    print("等待页面加载...")
    run_agent_browser(["wait", "--load", "networkidle"])
    time.sleep(2)

    selector = (
        '.List-item a[href*="/p/"]'
        if content_type == "posts"
        else '.List-item a[href*="/question/"][href*="/answer/"]'
    )

    previous_count = 0
    current_count = 0
    for i in range(max_scrolls):
        count_result = run_agent_browser(
            ["eval", f"document.querySelectorAll({selector!r}).length"]
        )
        current_count = int(count_result[0]) if count_result[0].isdigit() else 0

        print(f"第 {i + 1} 次滚动，当前元素数量：{current_count}")

        if current_count == previous_count:
            print("没有更多内容，停止滚动")
            break

        previous_count = current_count

        run_agent_browser(["eval", "window.scrollTo(0, document.body.scrollHeight)"])
        time.sleep(2)

    return current_count


def extract_urls(username: str, content_type: str) -> list[str]:
    """提取所有 URL"""
    if content_type == "posts":
        selector = '.List-item a[href*="/p/"]'
    else:
        selector = '.List-item a[href*="/question/"][href*="/answer/"]'

    js_code = f"""
    const links = document.querySelectorAll({selector!r});
    const urls = Array.from(links).map(link => link.href);
    JSON.stringify(urls)
    """

    result = run_agent_browser(["eval", js_code])

    import json

    try:
        urls_str = result[0]
        if urls_str.startswith('"') and urls_str.endswith('"'):
            urls_str = json.loads(urls_str)
        urls = json.loads(urls_str)
        return urls
    except json.JSONDecodeError as e:
        print(f"解析 URL 失败：{e}, 原始内容：{result[0][:200]}")
        return []


def save_urls(urls: list[str], output_dir: Path, content_type: str):
    """保存 URL 到文件"""
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = "articles-urls.txt" if content_type == "posts" else "answers-urls.txt"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

    print(f"✓ 已保存 {len(urls)} 个 URL 到 {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="爬取知乎用户的所有文章/回答 URL")
    parser.add_argument("username", help="用户名（如 mr-dang-77）")
    parser.add_argument(
        "--type",
        choices=["articles", "answers", "all"],
        default="all",
        help="内容类型（articles=文章，answers=回答，all=全部）",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent.parent
    output_dir = project_root / "output" / args.username / "urls"

    content_types = []
    if args.type in ["articles", "all"]:
        content_types.append("posts")
    if args.type in ["answers", "all"]:
        content_types.append("answers")

    for content_type in content_types:
        type_name = "文章" if content_type == "posts" else "回答"
        print(f"\n{'=' * 50}")
        print(f"开始爬取{type_name}URL...")
        print(f"{'=' * 50}")

        scroll_to_load_more(args.username, content_type)
        urls = extract_urls(args.username, content_type)

        if urls:
            save_urls(urls, output_dir, content_type)
        else:
            print(f"✗ 未找到任何{type_name}")

    print(f"\n{'=' * 50}")
    print("✓ URL 爬取完成")
    print(f"{'=' * 50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
