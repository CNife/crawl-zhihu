# zhihu-crawler Skill

**子项目**: 知乎内容爬取核心代码

## OVERVIEW

爬取知乎用户文章和回答，输出 Markdown 和 PDF。使用 agent-browser (CDP) 自动化。

## STRUCTURE

```
zhihu-crawler/
├── scripts/         # 7 个 Python 脚本（主要代码）
├── references/      # CSS 选择器参考
├── assets/          # PDF 样式文件
├── SKILL.md         # AI 触发条件和工作流定义
└── pyproject.toml   # uv 项目配置
```

## WHERE TO LOOK

| 需求 | 文件 |
|------|------|
| URL 收集逻辑 | `scripts/collect_urls.py` |
| 单项爬取逻辑 | `scripts/crawl_item.py` |
| 批量调度逻辑 | `scripts/batch_crawl.py` |
| HTML→MD 转换 | `scripts/convert_to_md.py` |
| 页面元素定位 | `references/css-selectors.md` |

## SCRIPTS

| 脚本 | 功能 | 调用 |
|------|------|------|
| `check_env.py` | 检查 Chrome 调试模式 | 独立 |
| `collect_urls.py` | 爬取 URL 列表 | 独立 |
| `crawl_item.py` | 爬取单项内容 | 被 batch_crawl 调用 |
| `batch_crawl.py` | 批量爬取调度 | 独立 |
| `convert_to_md.py` | HTML 转 Markdown | 独立 |
| `generate_index.py` | 生成 README 索引 | 独立 |
| `convert_to_pdf.py` | Markdown 转 PDF | 独立 |

## DEPENDENCIES

```toml
# pyproject.toml
requires-python = ">=3.10"
dependencies = [
    "html2text>=2020.1.16",
    "beautifulsoup4>=4.12.0",
    "requests>=2.31.0",
    "aiohttp>=3.9.0",
]
```

## CONVENTIONS

- **无 `__init__.py`**: 脚本独立运行，非 Python 包导入
- **argparse 参数**: 每个脚本独立处理命令行参数
- **subprocess 调用**: `batch_crawl.py` 通过 subprocess 调用 `crawl_item.py`
- **Chrome CDP**: 所有脚本通过 `agent-browser --cdp 9222` 操作浏览器

## NOTES

- **登录检测**: 脚本会检测登录状态，失败时提示重新登录
- **断点续爬**: 检查 `crawled-urls.txt` 过滤已爬 URL
- **图片存储**: 统一存入 `output/<username>/images/`，相对路径引用