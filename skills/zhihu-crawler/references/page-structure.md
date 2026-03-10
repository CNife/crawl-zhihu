# 知乎页面结构分析

## 用户主页结构

### 文章列表页 (`/people/{username}/posts`)

```html
<div class="List">
  <div class="List-item">
    <a class="PostItem" href="/p/{article_id}">
      <div class="PostItem-title">文章标题</div>
      <div class="PostItem-summary">文章摘要</div>
    </a>
  </div>
  <!-- 更多 List-item -->
</div>
```

**滚动加载机制**:
- 页面使用 Infinite Scroll
- 滚动到底部时自动加载更多内容
- 无分页按钮

### 回答列表页 (`/people/{username}/answers`)

```html
<div class="List">
  <div class="List-item">
    <div class="ContentItem">
      <a class="question_link" href="/question/{question_id}/answer/{answer_id}">
        <span class="question_link-title">问题标题</span>
      </a>
      <div class="RichText">回答摘要</div>
    </div>
  </div>
  <!-- 更多 List-item -->
</div>
```

## 文章详情页结构

```html
<html>
<head>
  <title>文章标题 - 知乎</title>
</head>
<body>
  <article>
    <h1>文章标题</h1>
    <div class="Post-Main">
      <div class="Post-Header">
        <meta itemprop="author" content="作者名">
        <time datetime="2024-01-15">发布时间</time>
      </div>
      <div class="Post-RichTextContainer">
        <div class="RichText">
          <!-- 文章正文 HTML -->
          <p>段落内容</p>
          <img data-original="https://..." alt="图片描述">
        </div>
      </div>
      <div class="Post-Buttons">
        <button class="VoteButton">赞同 X</button>
        <button class="CommentButton">评论 X</button>
      </div>
    </div>
  </article>
</body>
</html>
```

## 回答详情页结构

```html
<html>
<head>
  <title>问题标题 - 知乎</title>
</head>
<body>
  <div class="QuestionHeader">
    <h1 class="QuestionHeader-title">问题标题</h1>
  </div>
  <div class="Answer">
    <div class="AnswerHeader">
      <meta itemprop="author" content="作者名">
      <time datetime="2024-01-15">发布时间</time>
    </div>
    <div class="RichText">
      <!-- 回答正文 HTML -->
      <p>段落内容</p>
      <img data-original="https://..." alt="图片描述">
    </div>
    <div class="Answer-actions">
      <button class="VoteButton">赞同 X</button>
      <button class="CommentButton">评论 X</button>
    </div>
  </div>
</body>
</html>
```

## 关键元素说明

### 正文内容 (`.RichText`)

- 包含完整的 HTML 格式
- 包含段落、图片、链接等
- 图片使用 `data-original` 属性存储高清 URL

### 元数据

- **作者**: `[itemprop="author"]` 元素
- **时间**: `<time>` 标签，`datetime` 属性
- **点赞**: `[class*="Vote"]` 按钮
- **评论**: `[class*="Comment"]` 按钮

### 图片

```html
<!-- 知乎图片结构 -->
<img 
  data-original="https://picx.zhimg.com/v2-xxx_xxx.jpg" 
  src="https://picx.zhimg.com/v2-xxx_xs.jpg" 
  alt="图片描述"
  class="content_image"
>
```

- `data-original`: 高清原图 URL
- `src`: 缩略图 URL
- 优先使用 `data-original` 下载高清图片

## 滚动加载实现

```javascript
// 滚动到底部
window.scrollTo(0, document.body.scrollHeight);

// 检查元素数量
const count = document.querySelectorAll('a.PostItem, a[href*="/question/"][href*="/answer/"]').length;

// 等待网络空闲
// agent-browser --cdp 9222 wait --load networkidle
```

## 反爬措施

1. **登录要求**: 大部分内容需要登录后才能访问
2. **动态加载**: 内容通过 AJAX 动态加载
3. **图片防盗链**: 图片 URL 有 Referer 检查
4. **速率限制**: 频繁请求可能被限制

## 应对策略

1. **保持登录状态**: 使用 `browser_profiles/zhihu_profile/` 保存 Cookie
2. **模拟人工**: 添加延迟，模拟人工浏览行为
3. **滚动加载**: 使用浏览器自动化滚动页面
4. **本地下载**: 下载图片到本地，避免防盗链
