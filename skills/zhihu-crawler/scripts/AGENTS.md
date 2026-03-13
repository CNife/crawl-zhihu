# zhihu-crawler/scripts

**核心代码目录**: 7 个独立 Python 脚本组成完整爬虫工作流

## OVERVIEW

无 `__init__.py` 的独立脚本设计，通过 subprocess 链式调用。所有脚本共享 `run_agent_browser()` 模式操作 Chrome CDP。

## SCRIPTS

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `check_env.py` | 检查 Chrome 调试端口 | 无 | Chrome 运行在 9222 |
| `collect_urls.py` | 滚动加载获取 URL 列表 | username, --type | urls/*.txt |
| `crawl_item.py` | 爬取单篇内容+图片 | url, output_dir, item_id | metadata.json, content.html |
| `batch_crawl.py` | 批量调度+断点续爬 | --username, --type, --delay | 多个 item 目录 |
| `convert_to_md.py` | HTML→Markdown 转换 | --input | .md 文件 |
| `generate_index.py` | 生成 README 索引 | output_dir | README.md |
| `convert_to_pdf.py` | Markdown→PDF | --input | .pdf 文件 |

## CALL CHAIN

```
collect_urls.py          batch_crawl.py
       ↓                        ↓
urls/*.txt           →   subprocess.run(crawl_item.py)
                                  ↓
                          output/<user>/
                          ├── articles/<item_id>/
                          │   ├── metadata.json
                          │   └── content.html
                          └── images/
                                   ↓
convert_to_md.py  ← 读取 metadata.json + content.html
       ↓
  .md files
       ↓
generate_index.py  →  README.md
       ↓
convert_to_pdf.py  →  .pdf files
```

## RUNNING SCRIPTS

**⚠️ 必须先 cd 到 `skills/zhihu-crawler/` 目录再运行脚本**

```bash
cd skills/zhihu-crawler/

# 检查环境
uv run python scripts/check_env.py

# 收集 URL
uv run python scripts/collect_urls.py <username> --type all

# 批量爬取
uv run python scripts/batch_crawl.py --username <username>

# 转换 Markdown（注意路径变化）
uv run python scripts/convert_to_md.py --input ../../output/<username>

# 生成索引
uv run python scripts/generate_index.py ../../output/<username>

# 转换 PDF
uv run python scripts/convert_to_pdf.py --input ../../output/<username>
```

**注意**：当在 `skills/zhihu-crawler/` 目录下运行时，输出目录路径需要调整为 `../../output/<username>`

## KEY PATTERNS

### Agent-Browser 调用模式

```python
def run_agent_browser(command: list[str], timeout: int = 60) -> tuple[str, str, int]:
    cmd = ["agent-browser", "--cdp", "9222"] + command
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

# 常用命令
run_agent_browser(["open", url])
run_agent_browser(["eval", js_code])      # 执行 JavaScript
run_agent_browser(["wait", "--load", "networkidle"])
```

### Subprocess 调用链

```python
# batch_crawl.py 调用 crawl_item.py
cmd = [
    sys.executable,
    str(script_path),  # crawl_item.py
    url,
    str(output_dir / item_type / item_id),
    item_id,
]
subprocess.run(cmd, capture_output=True, text=True, timeout=120)
```

### 输出路径计算

```python
project_root = Path(__file__).parent.parent.parent.parent  # 定位到 crawl-zhihu/
output_dir = project_root / "output" / username / "urls"
```

## ANTI-PATTERNS

- **禁止在脚本内 import 其他脚本**: 独立运行设计，无 `__init__.py`
- **禁止修改 subprocess 调用的签名**: `crawl_item.py` 接收 3 个位置参数
- **禁止硬编码输出路径**: 使用 `Path(__file__).parent.parent.parent.parent` 计算

## WHERE TO LOOK

| 修改需求 | 文件 |
|---------|------|
| 添加 URL 提取逻辑 | `collect_urls.py:scroll_to_load_more()` |
| 修改元数据提取 | `crawl_item.py:extract_metadata()` |
| 调整批量延迟/重试 | `batch_crawl.py` argparse --delay, --max-retries |
| 修改 HTML→MD 转换 | `convert_to_md.py` |
| 更新页面选择器 | `../references/css-selectors.md` |

## NOTES

- **登录检测**: `crawl_item.py` 检查 `metadata["title"]` 为空时返回 exit code 1
- **图片去重**: `crawl_item.py:download_images()` 使用 `seen_urls` dict 去重
- **断点续爬**: `batch_crawl.py` 读取 `crawled-urls.txt` 过滤已爬 URL
