# CSS 选择器参考

## 列表页选择器

### 文章列表

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 文章链接 | `a.PostItem[href*="/p/"]` | 文章卡片链接 |
| 文章标题 | `a.PostItem .PostItem-title` | 文章标题文本 |
| 列表项容器 | `.List-item` | 单个列表项 |

### 回答列表

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 回答链接 | `a[href*="/question/"][href*="/answer/"]` | 回答卡片链接 |
| 问题标题 | `.ContentItem-title` | 问题标题 |
| 回答摘要 | `.RichText` | 回答摘要内容 |

## 详情页选择器

### 文章详情页

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 标题 | `h1` | 文章标题 |
| 正文 | `.RichText` | 文章正文 HTML |
| 作者 | `[itemprop="author"]` | 作者名称 |
| 发布时间 | `time` 或 `[itemprop="dateModified"]` | 发布日期时间 |
| 点赞数 | `[class*="Vote"]` | 赞同按钮及数量 |
| 评论数 | `[class*="Comment"]` | 评论按钮及数量 |
| 图片 | `.RichText img[data-original]` | 正文图片（高清） |

### 回答详情页

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 问题标题 | `h1.QuestionHeader-title` | 问题标题 |
| 回答正文 | `.RichText` | 回答正文 HTML |
| 作者 | `[itemprop="author"]` | 作者名称 |
| 发布时间 | `time` 或 `[itemprop="dateModified"]` | 发布日期时间 |
| 点赞数 | `[class*="Vote"]` | 赞同按钮及数量 |
| 评论数 | `[class*="Comment"]` | 评论按钮及数量 |
| 图片 | `.RichText img[data-original]` | 正文图片（高清） |

## 提取示例

### JavaScript 提取元数据

```javascript
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const metadata = {
  title: $('h1')?.textContent.trim(),
  author: $('[itemprop="author"]')?.textContent.trim(),
  publishTime: $('time')?.getAttribute('datetime'),
  voteCount: parseInt($('[class*="Vote"]')?.textContent.replace(/[^\d]/g, '')) || 0,
  commentCount: parseInt($('[class*="Comment"]')?.textContent.replace(/[^\d]/g, '')) || 0,
  contentHtml: $$('.RichText')[0]?.innerHTML,
  images: Array.from($$('.RichText img[data-original]'))
    .map(img => img.getAttribute('data-original'))
};
```

### 图片处理

```javascript
// 获取所有图片的高清 URL
const images = Array.from($$('.RichText img[data-original]'))
  .map(img => ({
    src: img.getAttribute('data-original') || img.src,
    alt: img.alt || ''
  }));
```

## 注意事项

1. **动态加载**: 知乎使用 Infinite Scroll，需要滚动加载所有内容
2. **高清图片**: 优先使用 `data-original` 属性获取高清图片
3. **类名变化**: 知乎的类名可能包含随机后缀，使用 `[class*="Vote"]` 等模糊匹配
4. **登录要求**: 部分选择器仅在登录后可用
