---
name: zhihu-crawler
description: 爬取知乎用户的所有文章和回答，生成 Markdown 和 PDF 报告。当用户提及知乎内容爬取、文章导出、回答备份、生成 PDF 报告时立即使用此技能
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

# 2. 爬取用户内容
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77

# 3. AI 自动读取、生成索引、转换 PDF
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

1. ✅ **检查环境**：Chrome Debug 模式 + agent-browser
2. ✅ **执行爬取**：运行 `batch_crawl.py`
3. ✅ **读取文件**：读取生成的 Markdown 文件
4. ✅ **生成索引**：运行 `generate_index.py`
5. ✅ **转换 PDF**：运行 `convert_to_pdf.py`
6. ✅ **清理文件**：删除临时 JSON 文件夹

---

## 详细流程

### 1. 检查环境

```bash
uv run python skills/zhihu-crawler/scripts/check_env.py
```

确保：
- Chrome Debug 模式运行在端口 9222
- `browser_profiles/zhihu_profile/` 存在（保存登录状态）

### 2. 爬取用户内容

```bash
# 爬取全部（文章 + 回答）
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77

# 仅爬取文章
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77 --type articles

# 仅爬取回答
uv run python skills/zhihu-crawler/scripts/batch_crawl.py --username mr-dang-77 --type answers
```

### 3. 生成索引

```bash
uv run python skills/zhihu-crawler/scripts/generate_index.py output/mr-dang-77
```

### 4. 转换 PDF

```bash
uv run python skills/zhihu-crawler/scripts/convert_to_pdf.py --input output/mr-dang-77
```

### 5. 清理临时文件

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

## 配置

### 依赖

在 `skills/zhihu-crawler/` 目录下：

```bash
uv add html2text beautifulsoup4 requests aiohttp
```

### PDF 样式

使用 `skills/zhihu-crawler/assets/github-markdown.css` 作为 PDF 样式文件。

### 登录状态

登录状态由 `browser_profiles/zhihu_profile/` 自动维护，无需手动 save/load。

首次使用需手动登录：
```bash
agent-browser --cdp 9222 open https://www.zhihu.com/signin
```

---

## 参考资料

- `references/css-selectors.md` - CSS 选择器详解
- `references/page-structure.md` - 页面结构分析
- `assets/github-markdown.css` - PDF 样式文件
