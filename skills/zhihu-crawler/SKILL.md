---
name: zhihu-crawler
description: 爬取知乎用户的所有文章和回答，生成 Markdown 和 PDF 报告。当用户提及知乎内容爬取、文章导出、回答备份、生成 PDF 报告、批量下载知乎内容时立即使用此技能
---

# zhihu-crawler

爬取知乎用户的所有文章和回答，保存为按类型分组的 Markdown 文件，并转换为 PDF 报告。

**特点**：
- 自动过滤已爬取内容，支持断点续爬
- 按类型分组输出（articles/answers）
- 图片平铺保存，相对路径引用
- 自动生成索引和 PDF 报告

## 快速开始

```bash
# 1. 检查环境
uv run python skills/zhihu-crawler/scripts/check_env.py

# 2. 收集 URL 列表
uv run python skills/zhihu-crawler/scripts/collect_urls.py mr-dang-77 --type all

# 3. 批量爬取内容
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77

# 4. 转换为 Markdown
uv run python skills/zhihu-crawler/scripts/convert_to_md.py --input output/mr-dang-77

# 5. 生成索引
uv run python skills/zhihu-crawler/scripts/generate_index.py output/mr-dang-77

# 6. 转换 PDF
uv run python skills/zhihu-crawler/scripts/convert_to_pdf.py --input output/mr-dang-77
```

## 何时使用

✅ **应该触发**：
- "帮我爬取知乎用户的所有文章"
- "把知乎回答导出为 Markdown"
- "生成知乎内容 PDF 报告"
- "备份知乎用户的文章和回答"

❌ **不应触发**：
- "打开知乎网站"（只需浏览器操作）
- "查看某个问题"（查询单一内容）
- "帮我登录知乎"（简单网页操作）

## AI 任务清单

1. ✅ **检查环境**：Chrome Debug 模式运行在端口 9222
2. ✅ **收集 URL**：运行 `collect_urls.py` 爬取文章/回答 URL 列表
3. ✅ **批量爬取**：运行 `batch_crawl.py`（自动调用 `crawl_item.py`）
4. ✅ **转换 Markdown**：运行 `convert_to_md.py`
5. ✅ **生成索引**：运行 `generate_index.py`
6. ✅ **转换 PDF**：运行 `convert_to_pdf.py`
7. ✅ **清理文件**：删除临时 item 文件夹

---

## 详细流程

### 1. 检查环境

```bash
uv run python skills/zhihu-crawler/scripts/check_env.py
```

确保：
- Chrome Debug 模式运行在端口 9222
- `browser_profiles/zhihu_profile/` 存在（保存登录状态）

**常见问题**：
- 端口 9222 被占用：关闭其他 Chrome 实例或更换端口
- Chrome 未启动：手动打开 Chrome 并访问 `chrome://version` 确认调试端口

### 2. 收集 URL 列表

```bash
# 爬取全部（文章 + 回答）
uv run python skills/zhihu-crawler/scripts/collect_urls.py mr-dang-77 --type all

# 仅爬取文章 URL
uv run python skills/zhihu-crawler/scripts/collect_urls.py mr-dang-77 --type articles

# 仅爬取回答 URL
uv run python skills/zhihu-crawler/scripts/collect_urls.py mr-dang-77 --type answers
```

**说明**：
- 使用 `agent-browser --cdp 9222` 滚动加载用户主页
- 自动处理无限滚动（最多 50 次）
- 保存 URL 到 `output/<username>/urls/`

**常见问题**：
- 页面提示登录：使用 `agent-browser --cdp 9222 open https://www.zhihu.com/signin` 手动登录
- 滚动加载无内容：检查网络连接，或增加 `--max-scrolls` 参数

### 3. 批量爬取内容

```bash
# 爬取全部（文章 + 回答）
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77

# 仅爬取文章
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77 --type articles

# 仅爬取回答
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77 --type answers
```

**说明**：
- 自动过滤已爬取的 URL（检查 `crawled-urls.txt`）
- 每篇文章/回答之间延迟 3 秒（可配置 `--delay`）
- 失败自动重试 3 次（可配置 `--max-retries`）
- 调用 `crawl_item.py` 爬取单项内容

**常见问题**：
- 登录失效：脚本会检测到并提示重新登录
- 网络超时：自动重试 3 次，失败后记录到 `crawled-urls.txt` 以便下次续爬
- 元素未找到：可能是页面结构变化，检查 `references/css-selectors.md`

### 4. 转换为 Markdown

```bash
uv run python skills/zhihu-crawler/scripts/convert_to_md.py --input output/mr-dang-77
```

**说明**：
- 读取 `metadata.json` 和 `content.html`
- 使用 `html2text` 转换 HTML 为 Markdown
- 替换图片 URL 为本地相对路径
- 生成 `<YYYY-MM-DD>_<title>.md` 文件

### 5. 生成索引

```bash
uv run python skills/zhihu-crawler/scripts/generate_index.py output/mr-dang-77
```

**说明**：
- 扫描所有 Markdown 文件
- 提取标题、作者、发布时间、点赞数
- 按日期降序生成索引表格
- 保存为 `README.md`

### 6. 转换 PDF

```bash
uv run python skills/zhihu-crawler/scripts/convert_to_pdf.py --input output/mr-dang-77
```

**说明**：
- 使用 `bunx mdpdf` 转换
- 应用 `github-markdown.css` 样式
- PDF 与 MD 并存（不删除源文件）

### 7. 清理临时文件

```bash
rm -rf output/mr-dang-77/articles/*/
rm -rf output/mr-dang-77/answers/*/
```

---

## 输出结构

```
output/<username>/
├── urls/
│   ├── articles-urls.txt
│   ├── answers-urls.txt
│   └── crawled-urls.txt
├── articles/
│   ├── 2024-01-15_article-title.md
│   ├── 2024-01-15_article-title.pdf
│   └── ...
├── answers/
│   ├── 2024-01-15_question-title.md
│   ├── 2024-01-15_question-title.pdf
│   └── ...
├── images/
│   ├── article-001-img-001.jpg
│   ├── answer-001-img-001.jpg
│   └── ...
└── README.md
```

---

## 脚本说明

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `check_env.py` | 检查并启动 Chrome Debug 模式 | 无 | Chrome 运行在端口 9222 |
| `collect_urls.py` | 爬取文章/回答 URL 列表 | 用户名、类型 | URL 文件 |
| `crawl_item.py` | 爬取单项内容 | URL、输出目录 | metadata.json + 图片 |
| `batch_crawl.py` | 批量爬取 | 用户名、类型 | 多个 item 文件夹 |
| `convert_to_md.py` | HTML 转 Markdown | 输出目录 | Markdown 文件 |
| `generate_index.py` | 生成索引 | 输出目录 | README.md |
| `convert_to_pdf.py` | Markdown 转 PDF | 输出目录 | PDF 文件 |

---

## 配置

### 依赖

在 `skills/zhihu-crawler/` 目录下：

```bash
uv add html2text beautifulsoup4 requests aiohttp
```

### PDF 转换工具

需要安装 [Bun](https://bun.sh)：

```bash
curl -fsSL https://bun.sh/install | bash
```

### PDF 样式

使用 `skills/zhihu-crawler/assets/github-markdown.css` 作为 PDF 样式文件。

### 登录状态

登录状态由 `browser_profiles/zhihu_profile/` 自动维护，无需手动 save/load。

首次使用需手动登录：
```bash
agent-browser --cdp 9222 open https://www.zhihu.com/signin
```

**登录失效处理**：
- 重新执行上述登录命令
- 登录成功后关闭浏览器，后续命令自动复用 Cookie

---

## 参考资料

- `references/css-selectors.md` - CSS 选择器详解
- `references/page-structure.md` - 页面结构分析
- `assets/github-markdown.css` - PDF 样式文件
