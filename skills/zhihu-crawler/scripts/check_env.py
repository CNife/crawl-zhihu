#!/usr/bin/env python3
"""检查并启动 Chromium 调试模式"""

import subprocess
import sys
import time
from pathlib import Path
import requests


def check_chrome_debug_mode(port: int = 9222) -> bool:
    """检查 Chrome Debug 模式是否已启动"""
    try:
        response = requests.get(f"http://localhost:{port}/json/version", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def start_chrome_debug_mode(port: int = 9222, profile_dir: Path | None = None, timeout: int = 10):
    """启动 Chromium 调试模式"""
    if profile_dir is None:
        profile_dir = (
            Path(__file__).parent.parent.parent.parent / "browser_profiles" / "zhihu_profile"
        )

    profile_dir.mkdir(parents=True, exist_ok=True)

    chrome_commands = [
        [
            "google-chrome",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-dev-shm-usage",
        ],
        [
            "chromium",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-dev-shm-usage",
        ],
        [
            "chromium-browser",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-dev-shm-usage",
        ],
    ]

    for cmd in chrome_commands:
        try:
            subprocess.Popen(cmd, start_new_session=True)
            print(f"正在启动 Chrome/Chromium 调试模式（端口 {port}）...")

            for i in range(timeout):
                if check_chrome_debug_mode(port):
                    print(f"✓ Chrome Debug 模式已启动（端口 {port}）")
                    print(f"✓ 浏览器配置文件：{profile_dir}")
                    return True
                time.sleep(1)

            print("✗ 启动超时，请手动检查 Chrome/Chromium 是否已启动")
        except FileNotFoundError:
            continue

    print("✗ 未找到 Chrome/Chromium，请安装后再试")
    print("  Ubuntu/Debian: sudo apt install chromium-browser")
    print("  macOS: brew install --cask google-chrome")
    return False


def main():
    """主函数"""
    port = 9222

    print("检查 Chrome Debug 模式...")

    if check_chrome_debug_mode(port):
        print(f"✓ Chrome Debug 模式已运行（端口 {port}）")
        return 0

    print(f"Chrome Debug 模式未运行，正在启动...（端口 {port}）")

    if start_chrome_debug_mode(port):
        print("\n✓ 环境检查完成")
        return 0
    else:
        print("\n✗ 环境检查失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
