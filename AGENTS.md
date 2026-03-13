# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-13
**Commit:** a646eca
**Branch:** main

## OVERVIEW

知乎内容爬取工具。使用浏览器自动化爬取用户文章和回答，生成 Markdown 和 PDF 报告。

**技术栈**: Python 3.10+ / uv / agent-browser (CDP) / html2text / bunx mdpdf

## STRUCTURE

```
crawl-zhihu/
├── skills/zhihu-crawler/    # 核心代码（Skill 子项目）
│   ├── scripts/             # Python 脚本
│   ├── references/          # CSS 选择器参考
│   └── assets/              # PDF 样式文件
├── browser_profiles/        # 浏览器登录状态
└── output/                  # 爬取输出（gitignore）
```

## WHERE TO LOOK

| 任务 | 位置 | 说明 |
|------|------|------|
| 修改爬虫逻辑 | `skills/zhihu-crawler/scripts/` | 所有 Python 脚本 |
| CSS 选择器 | `skills/zhihu-crawler/references/css-selectors.md` | 页面元素定位参考 |
| PDF 样式 | `skills/zhihu-crawler/assets/github-markdown.css` | PDF 输出样式 |
| 登录状态 | `browser_profiles/zhihu_profile/` | Chrome 用户数据 |

## CONVENTIONS

**非标准项目结构**：
- 代码在 `skills/zhihu-crawler/` 子目录，非标准 src/ 或项目根
- 多脚本工作流模式，无统一 CLI 入口
- 使用 SKILL.md 定义 AI 触发条件和工作流

**运行方式**：
```bash
# 使用 uv 运行脚本
uv run python skills/zhihu-crawler/scripts/<script>.py

# 不使用 uv run ruff，直接调用
ruff format --line-length 100 skills/zhihu-crawler/scripts/
ruff check --fix skills/zhihu-crawler/scripts/
```

## COMMANDS

**⚠️ 重要：运行 scripts 目录下的脚本前，必须先 cd 到 `skills/zhihu-crawler/` 目录**

```bash
# 先进入工作目录
cd skills/zhihu-crawler/

# 检查环境（Chrome 调试模式）
uv run python scripts/check_env.py

# 收集 URL
uv run python scripts/collect_urls.py <username> --type all

# 批量爬取
uv run python scripts/batch_crawl.py --username <username>

# 转 Markdown
uv run python scripts/convert_to_md.py --input ../../output/<username>

# 生成索引
uv run python scripts/generate_index.py ../../output/<username>

# 转 PDF
uv run python scripts/convert_to_pdf.py --input ../../output/<username>
```

## NOTES

- **Chrome 调试端口**: 9222（agent-browser --cdp 9222）
- **登录状态**: 首次使用需手动登录 `https://www.zhihu.com/signin`
- **断点续爬**: 自动读取 `output/<username>/urls/crawled-urls.txt`
- **无测试/CI**: 项目无测试框架和 CI/CD 配置