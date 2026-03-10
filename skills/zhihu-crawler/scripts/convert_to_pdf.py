#!/usr/bin/env python3
"""将 Markdown 转换为 PDF"""

import argparse
import subprocess
import sys
from pathlib import Path


def convert_md_to_pdf(md_file: Path, css_file: Path) -> bool:
    """将单个 Markdown 文件转换为 PDF"""
    pdf_file = md_file.with_suffix(".pdf")

    cmd = [
        "bunx",
        "mdpdf",
        "--output",
        str(pdf_file),
        "--stylesheet",
        str(css_file),
        str(md_file),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print(f"✓ 已转换：{md_file.name} -> {pdf_file.name}")
            return True
        else:
            print(f"✗ 转换失败：{md_file.name}")
            if result.stderr:
                print(f"  错误：{result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ 转换超时：{md_file.name}")
        return False
    except FileNotFoundError:
        print("✗ 未找到 bunx 命令，请安装 Bun: https://bun.sh")
        print("  或手动安装 mdpdf: npm install -g mdpdf")
        return False
    except Exception as e:
        print(f"✗ 转换异常：{e}")
        return False


def scan_markdown_files(directory: Path) -> list[Path]:
    """扫描目录下的所有 Markdown 文件"""
    md_files = []

    for subdir in ["articles", "answers"]:
        subdir_path = directory / subdir
        if not subdir_path.exists():
            continue

        md_files.extend(subdir_path.glob("*.md"))

    return sorted(md_files)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="将 Markdown 转换为 PDF")
    parser.add_argument("--input", required=True, help="输入目录（包含 articles/answers 子目录）")
    parser.add_argument(
        "--css",
        help="CSS 样式文件（默认使用 assets/github-markdown.css）",
    )
    args = parser.parse_args()

    input_dir = Path(args.input)

    if not input_dir.exists():
        print(f"✗ 输入目录不存在：{input_dir}")
        return 1

    if args.css:
        css_file = Path(args.css)
    else:
        css_file = Path(__file__).parent.parent / "assets" / "github-markdown.css"

    if not css_file.exists():
        print(f"✗ CSS 样式文件不存在：{css_file}")
        return 1

    print(f"使用 CSS 样式：{css_file}")

    md_files = scan_markdown_files(input_dir)

    if not md_files:
        print("✗ 未找到任何 Markdown 文件")
        return 1

    print(f"找到 {len(md_files)} 个 Markdown 文件")
    print(f"{'=' * 50}")

    converted_count = 0
    failed_count = 0

    for md_file in md_files:
        if convert_md_to_pdf(md_file, css_file):
            converted_count += 1
        else:
            failed_count += 1

    print(f"{'=' * 50}")
    print("✓ PDF 转换完成")
    print(f"  成功：{converted_count} 个")
    print(f"  失败：{failed_count} 个")
    print(f"{'=' * 50}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
