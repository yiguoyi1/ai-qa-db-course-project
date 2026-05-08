# Facebook 全栈项目开发前端技术细节答辩说明

> 使用口径：项目名称是《Facebook 全栈项目开发》，当前真实前端实现是一个 AI 问答社区平台。前端页面没有使用 React/Vue，而是使用原生 HTML、CSS、JavaScript 实现页面布局、交互状态、接口请求和页面跳转。答辩时要如实说明，不要把它说成 React 项目。

## 一、前端整体说明

### 1.1 前端代码位置

当前项目的 Web 前端代码集中在：

```text
app/web/
├── index.html     # 产品介绍首页
├── login.html     # 登录 / 注册页面
├── home.html      # 社区首页：推荐、热榜、搜索、筛选、发帖
├── detail.html    # 问题详情页：回答、评论、收藏、点赞、AI 追问
├── profile.html   # 用户中心：资料、头像、问题、回答、收藏、推荐、历史
└── admin.html     # 管理后台：用户、分类、标签、内容、日志治理
```

桌面客户端前端入口在：

```text
desktop/src/index.html
```

它不是重新写一套社区页面，而是一个 Tauri 启动页，检测后端 `/health` 后跳转到服务器 `/home`。

答辩时可以这样说：

> 前端主要在 `app/web/` 目录下，采用原生 HTML、CSS、JavaScript。FastAPI 负责把这些页面通过 `/`、`/home`、`/login`、`/questions/{id}` 等路由返回给浏览器，页面加载后再用 JavaScript 调后端 API 获取真实数据。

### 1.2 前端技术栈

| 技术 | 项目中怎么使用 | 作用 |
|---|---|---|
| HTML5 | `app/web/*.html` | 定义页面结构、表单、按钮、列表、弹窗 |
| CSS3 | 每个 HTML 内部 `<style>` | 页面布局、颜色、卡片、响应式、交互状态 |
| 原生 JavaScript | 每个 HTML 内部 `<script>` | DOM 操作、接口请求、状态管理、页面跳转 |
| Fetch API | `fetch(...)` | 调用 FastAPI 后端接口 |
| sessionStorage | 登录页和业务页 | 保存登录 token、用户 ID、角色 |
| localStorage | 桌面端启动页 | 保存后端服务器地址 |
| marked | `detail.html` | 将 Markdown 回答渲染成 HTML |
| highlight.js | `detail.html` | 代码块高亮 |
| FastAPI FileResponse | `app/web_routes.py` | 由后端统一交付 HTML 页面 |

### 1.3 为什么没有使用 React / Vue

当前项目没有使用前端框架，原因可以这样解释：

1. 课程设计重点是完整业务闭环，而不是前端框架本身。
2. 原生 HTML/CSS/JS 更容易展示底层原理：DOM、事件、状态、请求、渲染。
3. 页面数量有限，用原生方式可以完成需求。
4. 项目仍然体现了组件化思想，只是没有框架组件。

答辩时可以这样说：

> 这个项目没有使用 React 或 Vue，所以没有真正的 props、state、hooks。我用原生 JavaScript 的函数、状态对象和 DOM 模板字符串组织页面逻辑。比如问题卡片、评论树、后台模块切换都被封装成函数，本质上是一种轻量级组件化。

## 二、前端页面路由原理

### 2.1 页面路由由后端提供

页面路由定义在：

```text
app/web_routes.py
```

主要页面映射：

| 浏览器路径 | 返回页面 | 页面作用 |
|---|---|---|
| `/` | `app/web/index.html` | 产品首页 |
| `/login` | `app/web/login.html` | 登录注册 |
| `/home` | `app/web/home.html` | 社区首页 |
| `/me` | `app/web/profile.html` | 用户中心 |
| `/admin` | `app/web/admin.html` | 管理后台 |
| `/questions/{question_id}` | `app/web/detail.html` | 问题详情 |

后端代码逻辑是：

```python
@web_router.get("/home")
@web_router.get("/home.html")
def home_page() -> FileResponse:
    return _page_response("home.html")
```

技术原理：

- 浏览器访问 `/home`。
- FastAPI 匹配路由。
- 后端用 `FileResponse` 返回 `home.html`。
- 浏览器解析 HTML、CSS、JavaScript。
- JavaScript 再请求 `/api/questions` 获取数据。

答辩时可以这样说：

> 项目不是前端单页应用路由，而是后端路由返回不同 HTML 页面。页面本身再通过 JavaScript 调 API 加载数据。这种方式简单稳定，适合课程项目，也方便后端统一提供页面和接口。

### 2.2 页面内部状态路由

首页 `home.html` 使用 URL 查询参数控制页面状态，例如：

```text
/home?section=recommend
/home?section=hot
/home?q=oracle
/home?category_id=1&status=OPEN
```

页面会根据 URL 参数决定：

- 当前是推荐还是热榜。
- 是否处于搜索模式。
- 当前分类筛选。
- 当前标签筛选。
- 当前问题状态筛选。

技术原理：

- 使用 `URLSearchParams` 读取地址栏参数。
- 页面初始化时根据参数设置筛选控件。
- 用户切换筛选时更新 URL 或重新请求接口。

答辩时可以这样说：

> 首页内部没有复杂路由库，而是用 URL 查询参数保存当前筛选状态。这样刷新页面或复制链接时，仍然能保留当前筛选条件。

## 三、整体页面布局设计

### 3.1 产品首页布局：`app/web/index.html`

产品首页主要结构：

```text
page-shell
├── navbar 顶部导航
├── main
│   ├── hero 首屏介绍区
│   ├── promo 产品视频区
│   ├── advantages 产品优势区
│   ├── features 核心功能区
│   ├── showcase 界面展示区
│   ├── scenes 使用场景区
│   ├── data highlights 数据亮点区
│   ├── tags 热门标签区
│   ├── how it works 使用流程区
│   └── faq 常见问题区
└── footer 页脚
```

真实结构片段包括：

- `header class="navbar"`
- `section class="hero"`
- `div class="hero-grid"`
- `div class="browser-card"`
- `section id="features"`
- `section id="faq"`

布局原理：

- 顶部导航固定品牌、功能锚点和入口按钮。
- Hero 区使用左右布局：左侧文案，右侧模拟产品界面。
- 功能区使用网格卡片展示。
- FAQ 使用折叠项增强交互。

答辩时可以这样说：

> 首页是产品介绍型布局，主要承担引导用户了解系统和进入社区的作用。它不是业务数据主页面，而是通过导航、Hero、功能卡片和 FAQ 展示项目能力。

### 3.2 登录页布局：`app/web/login.html`

登录页主要结构：

```text
auth-container
├── 返回首页按钮
├── header 标题区
├── login-section 登录表单
├── register-section 注册表单
└── result-message 提示区域
```

真实元素：

- `id="login-section"`
- `id="register-section"`
- `id="login-username"`
- `id="login-password"`
- `id="reg-username"`
- `id="reg-password"`
- `id="result-message"`

交互函数：

- `toggleForm(type)`：切换登录和注册。
- `handleLogin()`：提交登录。
- `handleRegister()`：提交注册。
- `showMessage(msg, isSuccess)`：显示错误或成功信息。

答辩时可以这样说：

> 登录页把登录和注册放在同一个页面里，通过 `toggleForm` 控制显示哪个表单。前端会做基本长度校验，真正的用户名重复、密码校验和 token 生成都在后端完成。

### 3.3 社区首页布局：`app/web/home.html`

首页是核心业务页面。主要结构：

```text
navbar 顶部导航
├── Logo
├── 推荐 / 热榜切换
├── 搜索框
└── 用户菜单 / 登录按钮

container 主体容器
├── main-feed 主信息流
│   ├── feed-header 标题和发帖按钮
│   ├── feed-filters 分类、状态筛选
│   ├── post-list 问题列表
│   └── question-pagination 分页
└── sidebar 侧边栏
    └── popular-tags 热门标签

post-modal 发帖弹窗
```

真实元素：

- `nav class="navbar"`
- `div class="main-feed"`
- `div id="post-list"`
- `div id="question-pagination"`
- `div class="sidebar"`
- `div id="popular-tags"`
- `div id="post-modal"`

页面核心功能：

- 浏览推荐 / 热榜。
- 搜索问题。
- 分类筛选。
- 状态筛选。
- 标签筛选。
- 登录后发帖。
- 普通发帖或 AI 首答发帖。
- 收藏或取消收藏。
- 选择问题配图。

布局原理：

- 顶部导航承担全局入口。
- 主区域是信息流，适合浏览问题。
- 侧边栏展示热门标签，辅助筛选。
- 发帖使用弹窗，避免离开当前页面。
- 分页区域避免一次加载过多问题。

答辩时可以这样说：

> `home.html` 是社区主页面，布局上采用顶部导航 + 主信息流 + 侧边栏 + 发帖弹窗。信息流负责展示问题列表，侧边栏负责标签筛选，弹窗负责发布问题，这样用户不用离开首页就能完成主要操作。

### 3.4 详情页布局：`app/web/detail.html`

详情页是交互最复杂的页面。主要结构：

```text
navbar 顶部导航
├── 推荐 / 热榜入口
├── 搜索框
└── 用户菜单

detail container
├── 问题详情区域
│   ├── 标题、作者、状态、标签
│   ├── 正文
│   ├── 问题图片
│   └── 收藏 / 删除 / 采纳相关按钮
├── 回答列表
│   ├── AI 回答
│   ├── 人工回答
│   ├── 点赞 / 点踩
│   ├── 评论树
│   └── AI 追问面板
└── 回答发布区域
```

真实技术点：

- 使用 `marked` 渲染 Markdown。
- 使用 `highlight.js` 高亮代码。
- 使用 `sanitizeRenderedHtml` 清理渲染后的 HTML。
- 评论树用递归或层级渲染。
- AI 追问面板按回答 ID 管理状态。

页面核心函数类型：

- 加载问题详情。
- 渲染 Markdown。
- 渲染媒体图片。
- 渲染回答列表。
- 加载评论。
- 提交评论。
- 提交回答。
- 点赞 / 点踩。
- 收藏 / 取消收藏。
- 发起 AI 追问。

答辩时可以这样说：

> 详情页负责一个问题下的完整互动。它不仅展示问题，还展示回答、图片、评论、反馈和 AI 追问。因为回答内容可能是 Markdown，所以页面引入 Markdown 渲染和代码高亮，同时做 HTML 清洗，避免直接插入危险内容。

### 3.5 用户中心布局：`app/web/profile.html`

用户中心主要结构：

```text
顶部导航
├── 返回首页
├── 搜索
└── 用户菜单

profile 页面主体
├── 用户信息概览
│   ├── 头像
│   ├── 昵称、用户名、角色
│   └── 注册时间、登录时间、统计数据
├── 标签页导航
│   ├── 个人资料
│   ├── 我的问题
│   ├── 我的回答
│   ├── 我的收藏
│   ├── 我的推荐
│   ├── 最近浏览
│   └── 最近搜索
└── 对应列表或表单内容
```

核心能力：

- 查看个人资料。
- 修改昵称、邮箱、手机号。
- 上传和删除头像。
- 查看自己的问题、回答、收藏。
- 查看推荐。
- 重建兴趣画像。
- 查看浏览历史和搜索历史。

答辩时可以这样说：

> 用户中心采用概览卡片加标签页的布局。概览区展示用户身份和统计，标签页按业务拆分不同列表。这样可以避免页面过长，也让用户快速切换不同个人数据。

### 3.6 管理后台布局：`app/web/admin.html`

管理后台主要结构：

```text
admin layout
├── sidebar 侧边栏导航
│   ├── 总览
│   ├── 用户治理
│   ├── 分类管理
│   ├── 标签治理
│   ├── 内容治理
│   └── 审计日志
└── content 内容区
    ├── section-title
    ├── section-desc
    └── 当前模块表格 / 表单 / 分页
```

真实函数：

- `switchSection(section)`：切换后台模块。
- `adminFetch(path, options)`：统一管理员请求。
- `loadUsers()`：加载用户治理数据。
- `loadCategories()`：加载分类。
- `loadTags()`：加载标签。
- `loadContentQuestions()`：加载内容治理。
- `loadLoginLogs()`：加载登录日志。
- `loadOperationLogs()`：加载操作日志。

布局原理：

- 后台使用侧边栏导航，更适合管理系统。
- 每个 section 对应一个治理模块。
- 数据表格配合筛选和分页，适合大量后台数据。

答辩时可以这样说：

> 管理后台采用典型后台系统布局：左侧导航，右侧内容。每个治理模块是一个 section，通过 `switchSection` 切换显示，并按需调用接口加载数据。管理员请求统一走 `adminFetch`，自动携带 JWT。

## 四、CSS 布局技术原理

### 4.1 使用的主要 CSS 技术

| 技术 | 项目中的作用 |
|---|---|
| Flexbox | 顶部导航、按钮组、用户菜单、卡片内部布局 |
| CSS Grid | 首页 Hero、卡片网格、数据统计、后台布局 |
| Media Query | 适配移动端和小屏幕 |
| CSS 变量 | 统一颜色、边框、阴影、主题变量 |
| border-radius / box-shadow | 卡片、弹窗、按钮视觉层次 |
| position | 弹窗、下拉菜单、固定导航等 |
| overflow | 弹窗内容滚动、列表区域滚动 |
| transition | 按钮 hover、菜单展开、状态切换 |

### 4.2 Flexbox 原理

Flexbox 适合一维布局，比如横向导航、按钮组和用户菜单。它解决的是“元素在一行或一列中如何排列”的问题。

在本项目中：

- 顶部导航使用 flex 排列 Logo、搜索框和用户菜单。
- 按钮组使用 flex 让按钮间距统一。
- 标签云使用 flex-wrap 自动换行。

答辩时可以这样说：

> Flexbox 主要用于一维排版，比如导航栏和按钮组。它可以很方便地控制元素水平或垂直对齐，也能处理剩余空间分配。

### 4.3 CSS Grid 原理

Grid 适合二维布局，比如首页 Hero 左右布局、卡片网格、后台内容区域。

在本项目中：

- 产品首页 `hero-grid` 实现左右两列。
- 功能卡片使用 `card-grid`。
- 管理后台使用侧边栏 + 内容区。

答辩时可以这样说：

> Grid 适合二维布局，能同时控制行和列。像首页首屏和功能卡片区，用 Grid 比单纯 Flexbox 更清晰。

### 4.4 响应式布局原理

页面通过 `@media` 媒体查询适配不同宽度。常见处理：

- 大屏使用双列或多列。
- 小屏改成单列。
- 导航链接折叠。
- 卡片宽度改为 100%。
- 弹窗和表单减少左右边距。

答辩时可以这样说：

> 响应式布局的核心是根据屏幕宽度改变布局规则。项目中大屏更适合双列和网格，小屏则改为单列，保证手机或窄屏浏览时不会溢出。

## 五、JavaScript 状态管理原理

### 5.1 当前项目的状态管理方式

当前项目没有框架级状态管理，而是使用：

- 全局变量。
- 页面级 `state` 对象。
- DOM 元素当前值。
- URL 查询参数。
- `sessionStorage` 中的登录态。

示例：

```javascript
const token = sessionStorage.getItem('access_token');
const userId = sessionStorage.getItem('user_id');
```

状态类型：

| 状态 | 保存位置 |
|---|---|
| 当前登录用户 | `sessionStorage` |
| 当前首页 section | URL 参数或页面变量 |
| 当前筛选条件 | select/input/URL 参数 |
| 管理后台当前模块 | `state.currentSection` |
| 评论面板展开状态 | 页面对象 |
| AI 追问会话状态 | 页面对象 |

答辩时可以这样说：

> 当前项目用原生 JS 管理状态，没有使用 Redux 或 Pinia。对于课程项目来说，页面状态数量可控，用普通对象、DOM 值和 URL 参数就能完成。

### 5.2 sessionStorage 原理

`sessionStorage` 是浏览器提供的会话级存储：

- 同一个标签页内有效。
- 页面刷新后仍存在。
- 关闭标签页后清空。
- 不同标签页之间相对隔离。

项目中用于保存：

- `access_token`
- `user_id`
- `username`
- `user_role`

答辩时可以这样说：

> 登录后我把 token 放到 `sessionStorage`，不是直接存在全局变量里。这样刷新页面后还能继续登录，但关闭标签页后会清掉，适合课程项目的登录态管理。

### 5.3 localStorage 原理

`localStorage` 是长期存储，关闭浏览器也不会自动清空。

当前项目主要在桌面端启动页 `desktop/src/index.html` 中保存后端地址：

```javascript
const BACKEND_STORAGE_KEY = 'aiqa.desktop.backendUrl';
```

答辩时可以这样说：

> `localStorage` 更适合保存长期偏好，比如桌面端连接哪个后端地址；登录 token 则更适合放在 `sessionStorage`，减少长期泄露风险。

## 六、前端接口请求原理

### 6.1 fetch 基本流程

前端接口请求基本流程：

```text
用户点击按钮
  ↓
JavaScript 收集表单或页面参数
  ↓
fetch 调用后端 API
  ↓
等待 response
  ↓
判断 response.ok
  ↓
解析 JSON
  ↓
更新 DOM
```

示例：登录页 `app/web/login.html` 调用：

```javascript
const response = await fetch(buildApiUrl('/api/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: username,
        password: password
    })
});
```

答辩时可以这样说：

> `fetch` 是浏览器原生 HTTP 请求 API。项目中登录、发帖、评论、收藏、上传等操作都是通过 `fetch` 调 FastAPI 接口完成的。

### 6.2 GET 请求

GET 用于查询数据，例如：

- `GET /api/questions`
- `GET /api/questions/{question_id}`
- `GET /api/categories`
- `GET /api/tags`
- `GET /api/search/questions`

技术特点：

- 参数一般放在 URL 查询字符串。
- 不应该修改数据库。
- 适合列表、详情、筛选、搜索。

### 6.3 POST 请求

POST 用于新增或提交操作，例如：

- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/questions`
- `POST /api/questions/ask`
- `POST /api/answers/{answer_id}/comments`
- `POST /api/answers/{answer_id}/feedback`

技术特点：

- 参数一般放在 JSON body 或 multipart body。
- 可能修改数据库。
- 通常需要登录鉴权。

### 6.4 DELETE 请求

DELETE 用于删除或取消，例如：

- `DELETE /api/questions/{question_id}`
- `DELETE /api/comments/{comment_id}`
- `DELETE /api/questions/{question_id}/favorite`
- `DELETE /api/users/me/avatar`

当前项目很多删除是软删除，数据库不是直接物理删除，而是修改状态。

### 6.5 带 JWT 的请求

需要登录的请求会加：

```javascript
headers: {
    'Authorization': `Bearer ${token}`
}
```

后端通过 `app/api/auth_deps.py` 解析 JWT。

答辩时可以这样说：

> 前端只负责把 token 放进请求头，真正判断 token 是否有效、用户是否有权限，是后端完成的。

## 七、表单和用户交互细节

### 7.1 登录表单

文件：`app/web/login.html`

页面字段：

- 用户名：`login-username`
- 密码：`login-password`

交互流程：

1. 用户输入用户名和密码。
2. 点击登录按钮。
3. `handleLogin()` 调用 `/api/auth/login`。
4. 成功后保存 token。
5. 跳转到社区首页。
6. 失败时显示友好错误。

前端校验：

- 用户名不能为空。
- 密码不能为空。
- 注册时用户名 3 到 50 位。
- 注册时密码 6 到 128 位。

### 7.2 发帖表单

文件：`app/web/home.html`

发帖弹窗支持：

- 标题。
- 正文。
- 分类。
- 已有标签。
- 自定义标签。
- 是否 AI 首答。
- 问题配图。

前端处理：

- 打开发帖弹窗。
- 选择是否 AI 发帖。
- 收集表单数据。
- 调用 `/api/questions` 或 `/api/questions/ask`。
- 若有图片，再调用图片上传接口。
- 成功后刷新列表或进入详情页。

答辩时可以这样说：

> 发帖弹窗把普通社区发帖和 AI 首答发帖合并在一个入口里。区别在于普通发帖只创建问题，AI 发帖会额外让后端调用 DeepSeek 生成首答。

### 7.3 评论表单

文件：`app/web/detail.html`

评论支持：

- 一级评论。
- 回复评论。
- 子回复折叠和展开。
- 删除自己的评论。

交互流程：

1. 用户点击评论或回复。
2. 前端打开输入框。
3. 提交到 `/api/answers/{answer_id}/comments`。
4. 后端返回新评论。
5. 前端重新加载评论树。

### 7.4 图片上传交互

文件：

- `app/web/home.html`
- `app/web/detail.html`
- `app/web/profile.html`

图片上传类型：

- 头像。
- 问题图片。
- 回答图片。

前端交互：

- 选择图片。
- 前端显示预览。
- 检查文件大小和数量。
- 通过 `FormData` 上传。
- 上传成功后用返回的 `public_url` 显示图片。

答辩时可以这样说：

> 图片上传前端使用 multipart 表单，后端使用 FastAPI `UploadFile` 接收。前端负责选择和预览，后端负责类型、大小和权限校验。

## 八、每个重要页面的答辩讲法

### 8.1 `index.html` 产品首页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/index.html` |
| 页面定位 | 产品介绍和入口页 |
| 布局 | 顶部导航 + Hero + 功能区 + 场景区 + FAQ + 页脚 |
| 技术点 | CSS Grid、卡片布局、锚点导航、FAQ 交互 |
| 接口 | 主要是静态页面，部分下载和宣传资源由后端路由提供 |

答辩时可以这样说：

> 产品首页主要承担介绍系统和引导进入社区的作用，不是主要数据页面。它使用分区式布局，让老师或用户能快速看到项目定位、核心能力和使用入口。

### 8.2 `login.html` 登录注册页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/login.html` |
| 页面定位 | 用户认证入口 |
| 布局 | 居中认证卡片，登录和注册两个表单 |
| 技术点 | 表单校验、fetch、sessionStorage、错误提示 |
| 接口 | `POST /api/auth/login`、`POST /api/auth/register` |

答辩时可以这样说：

> 登录页主要完成注册和登录。登录成功后保存 JWT，后续接口通过 Authorization 请求头携带 token。前端只保存和传递 token，真正认证由后端完成。

### 8.3 `home.html` 社区首页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/home.html` |
| 页面定位 | 社区主信息流 |
| 布局 | 顶部导航 + 主信息流 + 侧边栏 + 发帖弹窗 |
| 技术点 | 搜索、筛选、分页、弹窗、图片预览、登录态判断 |
| 接口 | `/api/questions`、`/api/search/questions`、`/api/categories`、`/api/tags`、`/api/questions/ask` |

答辩时可以这样说：

> 首页是用户最常用的页面。它把浏览问题、搜索筛选、推荐热榜和发帖集中在一起。页面数据不是写死的，而是从后端 API 加载，支持分页和筛选。

### 8.4 `detail.html` 问题详情页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/detail.html` |
| 页面定位 | 单个问题的互动中心 |
| 布局 | 问题详情 + 回答列表 + 评论树 + AI 追问 + 回答框 |
| 技术点 | Markdown 渲染、代码高亮、评论树、反馈状态、AI 会话 |
| 接口 | `/api/questions/{id}`、`/api/answers/{id}/comments`、`/api/answers/{id}/feedback`、AI follow-up 接口 |

答辩时可以这样说：

> 详情页最能体现前端交互复杂度。它既要展示问题和回答，又要处理评论、点赞、收藏、采纳、图片和 AI 追问，所以前端把这些功能拆成多个函数按需渲染。

### 8.5 `profile.html` 用户中心

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/profile.html` |
| 页面定位 | 当前登录用户的个人中心 |
| 布局 | 用户概览 + 标签页 + 列表/表单 |
| 技术点 | 资料修改、头像上传、分页列表、推荐刷新 |
| 接口 | `/api/users/me/profile`、用户问题/回答/收藏/历史/推荐接口 |

答辩时可以这样说：

> 用户中心把个人资料和个人行为数据集中展示，用标签页区分不同内容。这样页面结构清晰，用户可以快速查看自己的问题、回答、收藏、推荐和历史。

### 8.6 `admin.html` 管理后台

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/admin.html` |
| 页面定位 | 管理员治理平台 |
| 布局 | 左侧导航 + 右侧内容区 |
| 技术点 | 管理员鉴权、统一 adminFetch、表格、筛选、分页、状态修改 |
| 接口 | `/api/admin/users`、`/api/admin/categories`、`/api/admin/tags`、日志和内容治理接口 |

答辩时可以这样说：

> 管理后台采用典型后台布局。左侧是治理模块导航，右侧显示当前模块内容。所有后台请求都走统一的 `adminFetch`，自动携带 token，后端还会校验管理员角色。

## 九、前端安全设计

### 9.1 前端不能作为安全边界

前端会做：

- 隐藏未登录用户不能操作的按钮。
- 未登录时跳转登录。
- 管理员入口只对管理员显示。
- 上传前做基础文件检查。

但真正安全必须在后端：

- JWT 校验。
- 用户角色校验。
- 作者权限校验。
- 数据库约束。

答辩时可以这样说：

> 前端权限判断只是用户体验，不是真正安全。因为用户可以绕过页面直接调接口，所以所有关键操作必须由后端再次校验。

### 9.2 XSS 防护

前端存在用户输入内容：

- 问题标题。
- 问题正文。
- 回答正文。
- 评论内容。
- 昵称。

项目中防护方式：

- 多处使用 `escapeHtml`。
- `detail.html` 对 Markdown 渲染结果做清理。
- 后端配置 CSP 响应头。

答辩时可以这样说：

> 因为社区内容是用户输入的，所以前端渲染时需要转义，不能直接把用户输入当 HTML 执行。详情页 Markdown 渲染后也做了基础清理。

### 9.3 当前前端安全不足

当前仍有不足：

- 页面内联脚本较多。
- CSP 为兼容内联脚本允许了 `unsafe-inline`。
- 前端 JS 体积较大，未模块化。
- 部分功能依赖前端提示，仍需继续补自动化测试。

答辩时可以这样说：

> 当前前端安全已经做了基础处理，但生产级还可以继续优化，比如把内联 JS 拆成独立文件，收紧 CSP，增加前端单元测试和端到端测试。

## 十、前端性能设计

### 10.1 已有性能设计

| 设计 | 说明 |
|---|---|
| 分页加载 | 问题列表、用户中心、后台列表都分页 |
| 按需加载 | 评论、AI 追问、后台模块按需请求 |
| 局部刷新 | 操作后只刷新当前列表或详情区域 |
| 图片预览管理 | 上传前先本地预览，上传后用后端 URL |
| URL 参数保存筛选 | 避免重复手动设置筛选状态 |

### 10.2 可能存在的问题

| 问题 | 说明 |
|---|---|
| 单个 HTML 文件较大 | `detail.html`、`profile.html`、`admin.html` 行数较多 |
| JS 未模块化 | 公共逻辑在多个页面中重复 |
| 无构建压缩 | 当前没有 bundler，生产压缩能力有限 |
| 评论/回答多时 DOM 可能较重 | 大量节点会增加渲染成本 |

### 10.3 后续优化方向

- 拆分公共 JS，例如认证、请求、用户菜单、搜索框。
- 拆分公共 CSS。
- 引入 Vite 或轻量构建工具。
- 将大型页面拆成模块。
- 对长列表做虚拟滚动或更细分页。
- 图片使用缩略图。

答辩时可以这样说：

> 当前性能优化主要依靠分页和按需加载。后续如果数据量增大，我会拆分 JS/CSS，增加构建压缩，并对长列表和图片做更精细的优化。

## 十一、前端与后端接口对应关系

| 页面 | 用户操作 | 调用接口 | 是否需要登录 |
|---|---|---|---|
| `login.html` | 注册 | `POST /api/auth/register` | 否 |
| `login.html` | 登录 | `POST /api/auth/login` | 否 |
| `home.html` | 加载问题列表 | `GET /api/questions` | 可选 |
| `home.html` | 搜索问题 | `GET /api/search/questions` | 可选 |
| `home.html` | 加载分类 | `GET /api/categories` | 否 |
| `home.html` | 加载标签 | `GET /api/tags` | 否 |
| `home.html` | 发布普通问题 | `POST /api/questions` | 是 |
| `home.html` | 发布 AI 首答问题 | `POST /api/questions/ask` | 是 |
| `home.html` | 收藏问题 | `POST /api/questions/{id}/favorite` | 是 |
| `detail.html` | 加载详情 | `GET /api/questions/{id}` | 可选 |
| `detail.html` | 发布回答 | `POST /api/questions/{id}/answers` | 是 |
| `detail.html` | 点赞/点踩 | `POST /api/answers/{id}/feedback` | 是 |
| `detail.html` | 加载评论 | `GET /api/answers/{id}/comments` | 否 |
| `detail.html` | 发布评论 | `POST /api/answers/{id}/comments` | 是 |
| `detail.html` | AI 追问 | `POST /api/questions/{qid}/answers/{aid}/follow-up` | 是 |
| `profile.html` | 加载用户资料 | `GET /api/users/me/profile` | 是 |
| `profile.html` | 修改资料 | `PATCH /api/users/me/profile` | 是 |
| `profile.html` | 上传头像 | `POST /api/users/me/avatar` | 是 |
| `profile.html` | 加载推荐 | `GET /api/users/{id}/recommendations` | 是 |
| `admin.html` | 用户治理 | `GET /api/admin/users` | 管理员 |
| `admin.html` | 分类管理 | `/api/admin/categories` | 管理员 |
| `admin.html` | 标签治理 | `/api/admin/tags` | 管理员 |
| `admin.html` | 日志查看 | `/api/admin/logs/login`、`/api/admin/logs/operations` | 管理员 |

## 十二、常见前端答辩问题

Q1：你的前端技术栈是什么？  
A1：前端使用原生 HTML、CSS 和 JavaScript。页面在 `app/web/` 下，由 FastAPI 返回。JavaScript 使用 `fetch` 调接口，使用 `sessionStorage` 保存登录态，详情页使用 Markdown 渲染和代码高亮。

Q2：为什么不用 React 或 Vue？  
A2：项目重点是全栈课程设计，原生前端能更直接展示页面布局、DOM 操作、接口请求和状态管理。页面规模虽然不小，但仍能通过函数和状态对象组织逻辑。后续如果继续工程化，可以迁移到 Vue 或 React。

Q3：项目有没有组件化？  
A3：没有框架层面的组件化，但有函数级组件化。比如问题卡片、评论树、媒体图片、后台表格都通过函数生成和渲染。可以理解为用原生 JS 手写轻量组件。

Q4：登录状态怎么保存？  
A4：登录成功后前端保存 `access_token`、`user_id`、`username`、`user_role`。后续请求需要登录的接口时，把 token 放到 `Authorization: Bearer ...` 请求头中。后端负责校验 token。

Q5：前端怎么判断游客和登录用户？  
A5：前端会检查是否存在 token。如果没有 token，就进入游客模式，只能浏览、搜索和查看详情；如果有 token，会显示用户菜单，并允许发帖、收藏、评论、回答等操作。但真正权限仍然后端校验。

Q6：页面如何做到响应式？  
A6：项目主要通过 CSS Grid、Flexbox 和 media query 实现。大屏使用双列、网格和侧边栏，小屏时改为单列，导航、卡片和表单也会适配宽度。

Q7：详情页为什么要做 Markdown 渲染？  
A7：AI 回答和用户回答可能包含列表、代码块、加粗等格式，用 Markdown 可以让内容更易读。详情页使用 Markdown 渲染，并结合 highlight.js 做代码高亮，同时对渲染后的 HTML 做清理。

Q8：前端如何上传文件？  
A8：前端用文件选择器拿到图片文件，先做预览和基础校验，再用 `FormData` 通过 multipart 请求上传。后端校验 MIME 类型、大小和权限后，把图片保存到 Oracle BLOB。

Q9：管理后台前端怎么保证只有管理员能用？  
A9：前端会根据 `user_role` 控制后台入口展示，后台请求也会统一带 token。但真正保证安全的是后端 `get_admin_user`，它会检查当前用户角色是否为 `ADMIN`。

Q10：前端当前有什么不足？  
A10：主要不足是没有使用模块化构建工具，多个页面里有重复的认证、请求、搜索和用户菜单逻辑；大型 HTML 文件较长，不利于长期维护。后续可以拆分公共 JS/CSS，或者迁移到 Vue/React。

## 十三、答辩时可以背的前端总结

可以背这一段：

> 本项目前端采用原生 HTML、CSS 和 JavaScript，页面代码在 `app/web/` 下。整体不是 React/Vue 单页应用，而是由 FastAPI 提供多页面路由，每个页面加载后再用 `fetch` 调后端接口获取真实数据。布局上使用顶部导航、信息流、侧边栏、弹窗、标签页和后台表格等结构；CSS 主要使用 Flexbox、Grid 和媒体查询实现响应式。登录后前端把 JWT 保存到 `sessionStorage`，请求受保护接口时放到 Authorization 请求头。前端负责用户体验和基础校验，真正的权限、安全和数据一致性由后端和数据库保证。

