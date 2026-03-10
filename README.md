# 知乎内容爬取工具

爬取知乎用户的所有文章和回答，生成 Markdown 和 PDF 报告。

## 特点

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

## 技术栈

- **浏览器自动化**: agent-browser (Chrome/Chromium)
- **调试模式**: Chrome Debug 模式 (端口 9222)
- **脚本语言**: Python
- **依赖管理**: uv + pyproject.toml
- **PDF 转换**: bunx mdpdf

## 目录结构

```
crawl-zhihu/
├── .plan/                          # 计划文档
├── browser_profiles/               # 浏览器配置
│   └── zhihu_profile/              # 知乎登录状态
├── skills/
│   └── zhihu-crawler/              # Skill 目录
│       ├── SKILL.md                # Skill 入口
│       ├── pyproject.toml          # uv 配置
│       ├── scripts/                # Python 脚本
│       ├── references/             # 参考资料
│       └── assets/                 # 资源文件
└── output/                         # 输出目录
    └── <username>/                 # 用户名层级
```

## 许可证

MIT License
