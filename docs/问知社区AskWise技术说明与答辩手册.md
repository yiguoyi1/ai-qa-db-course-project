# 问知社区 AskWise Community 技术说明与答辩手册

> 说明：本文档基于当前仓库真实代码编写。项目正式名称为《问知社区 AskWise Community》，当前真实业务是一个带 AI 首答、问答社区、行为记录、推荐、用户中心和管理员后台的全栈项目。旧文件名或课程模板中出现的“Facebook 全栈项目开发”只作为早期课程命名背景，不代表本项目复刻 Facebook。

# 一、项目概述

### 1.1 项目名称

项目名称：`问知社区 AskWise Community`

当前代码中的产品名称主要是：

- `问知社区 AskWise Community`
- `AI QA Community`
- `智能问答记录与推荐管理系统`
- `AI QA 社区`

答辩时建议表达为：

> 我的项目名称是《问知社区 AskWise Community》，当前实现形态是一个类似社区信息流的 AI 问答社区系统。它包含用户登录、内容发布、AI 首答、回答、评论、收藏、图片上传、推荐和后台治理等典型社区平台能力。早期模板里出现过 Facebook 字样，但系统本身不是 Facebook 复刻项目。

### 1.2 项目定位

当前项目是一个面向课程设计和演示的全栈问答社区 MVP。它不是只有页面，也不是只有数据库脚本，而是同时包含：

- 前端页面：`app/web/*.html`
- 后端服务：`app/main.py`、`app/api/routes/`、`app/services/`
- 数据库设计：`sql/create_tables.sql`、`sql/procedures.sql`、`sql/triggers.sql`、`sql/views.sql`
- 桌面客户端：`desktop/`
- CLI 测试前端：`frontend_cli/`
- 部署与运维脚本：`compose.yaml`、`scripts/`

### 1.3 项目目标

项目目标是实现一个完整的社区问答平台闭环：

- 用户可以注册、登录和维护个人资料。
- 用户可以发布问题，类似社区动态或帖子。
- 用户可以选择普通发帖，也可以触发 AI 首答。
- 其他用户可以回答、评论、收藏、浏览和反馈。
- 系统记录用户行为，并基于标签画像生成推荐。
- 管理员可以治理用户、分类、标签、内容和日志。
- 前端、后端、数据库之间形成完整的数据流。

### 1.4 主要用户角色

| 角色 | 说明 | 主要能力 |
|---|---|---|
| 游客 | 未登录用户 | 浏览首页、搜索、筛选、查看问题详情、查看回答和评论 |
| 普通用户 | 登录后的 `USER` | 发帖、AI 首答提问、回答、评论、收藏、点赞/点踩、上传头像和图片、查看个人中心、生成推荐 |
| 管理员 | `ADMIN` 用户 | 管理用户、分类、标签、问题状态、评论状态、查看登录日志和操作日志 |

角色和状态由 `sql/create_tables.sql` 中的 `users` 表定义：

- `role`：`USER`、`ADMIN`
- `status`：`ACTIVE`、`INACTIVE`、`LOCKED`、`DISABLED`

### 1.5 核心功能模块

| 模块 | 真实代码位置 | 当前实现情况 |
|---|---|---|
| 注册登录 | `app/api/routes/auth.py`、`app/services/auth_service.py` | 已实现 |
| 问题发布 | `app/api/routes/questions.py`、`app/services/question_service.py` | 已实现 |
| AI 首答 | `app/services/ai_answer_service.py`、`app/integrations/llm/openai_client.py` | 已实现，依赖 DeepSeek API Key |
| AI 自动标签 | `app/services/ai_tagging_service.py` | 已实现 |
| 人工回答 | `app/api/routes/answers.py`、`app/services/answer_service.py` | 已实现 |
| 采纳答案 | `app/services/question_service.py` 的 `accept_answer` | 已实现 |
| 评论楼中楼 | `app/api/routes/comments.py`、`app/services/comment_service.py` | 已实现 |
| 收藏 | `app/api/routes/favorites.py`、`app/services/favorite_service.py` | 已实现 |
| 点赞/点踩 | `app/api/routes/feedback.py`、`app/services/feedback_service.py` | 已实现，作用于回答 |
| 搜索 | `app/api/routes/search.py`、`app/services/search_service.py` | 已实现 |
| 用户中心 | `app/api/routes/users.py`、`app/services/user_center_service.py` | 已实现 |
| 图片上传 | `app/api/routes/media.py`、`app/services/media_service.py` | 已实现头像、问题图、回答图 |
| 推荐 | `app/api/routes/recommendations.py`、`sql/procedures.sql` | 已实现 |
| 管理后台 | `app/api/routes/admin.py`、`app/web/admin.html` | 已实现基础治理 |
| 好友/关注 | 未发现对应表、接口或页面 | 当前项目未实现 |
| 通知/站内信 | 未发现对应表、接口或页面 | 当前项目未实现 |

### 1.6 整体技术路线

| 层次 | 技术 | 真实文件 |
|---|---|---|
| 前端 | 原生 HTML + CSS + JavaScript | `app/web/` |
| 后端 | FastAPI | `app/main.py` |
| 接口模型 | Pydantic | `app/schemas/` |
| 数据库 | Oracle AI Database 26ai Free | `sql/` |
| 数据库访问 | `python-oracledb` | `app/db/connection.py` |
| AI 接入 | OpenAI SDK 兼容 DeepSeek | `app/integrations/llm/openai_client.py` |
| 登录鉴权 | JWT + Bearer Token | `app/services/auth_service.py`、`app/api/auth_deps.py` |
| 密码存储 | bcrypt 哈希 | `app/services/auth_service.py` |
| 桌面端 | Tauri 2 | `desktop/` |
| 数据库容器 | Docker Compose | `compose.yaml` |

### 1.7 为什么这是一个全栈项目

全栈项目的核心特征是：前端、后端、数据库三层都参与实际业务闭环。

本项目中：

- 前端负责页面展示、用户交互、表单输入、接口调用、登录态保存。
- 后端负责 API 路由、业务校验、鉴权、事务控制、AI 调用、异常处理。
- 数据库负责持久化用户、问题、回答、评论、收藏、推荐、日志等数据，并通过约束、索引、触发器和存储过程保证数据质量和业务效率。

答辩时可以这样说：

> 这个项目不是静态页面，也不是单纯的后端接口。用户从浏览器发起操作，前端调用 FastAPI 接口，后端完成鉴权和业务逻辑，再通过 Oracle 数据库存取数据，最后把结果返回给前端展示。因此它覆盖了前端、后端、数据库和部署运行，是一个完整的全栈项目。

# 二、项目目录结构说明

当前仓库主项目目录是 `ai-qa-db-course-project/`。主要目录结构如下：

```text
ai-qa-db-course-project/
├── app/                              # FastAPI 后端主目录
│   ├── main.py                       # 后端应用入口，注册路由、中间件和健康检查
│   ├── web_routes.py                 # Web 页面路由，把 app/web 下的 HTML 交给浏览器
│   ├── api/                          # API 层
│   │   ├── router.py                 # /api 路由聚合入口
│   │   ├── auth_deps.py              # JWT 鉴权依赖、管理员权限校验
│   │   ├── deps.py                   # Service 依赖注入工厂
│   │   └── routes/                   # 具体业务路由文件
│   ├── services/                     # 业务逻辑层，处理事务、校验和业务流程
│   ├── repositories/                 # 数据访问层，集中编写 Oracle SQL
│   ├── schemas/                      # Pydantic 请求和响应模型
│   ├── db/                           # 数据库连接池
│   ├── core/                         # 配置和异常定义
│   ├── integrations/llm/             # DeepSeek / OpenAI SDK 接入
│   ├── prompts/                      # AI 首答和自动标签提示词
│   └── web/                          # 前端页面代码，原生 HTML/CSS/JS
│       ├── index.html                # 产品首页
│       ├── login.html                # 登录注册页
│       ├── home.html                 # 社区首页、推荐、热榜、搜索、发帖
│       ├── detail.html               # 问题详情、回答、评论、AI 追问
│       ├── profile.html              # 用户中心
│       └── admin.html                # 管理后台
├── sql/                              # 数据库脚本目录
│   ├── create_tables.sql             # 建表、主键、外键、检查约束、索引
│   ├── procedures.sql                # PL/SQL 包和推荐生成过程
│   ├── triggers.sql                  # 统计同步和登录时间触发器
│   ├── views.sql                     # 汇总视图、展示视图、统计视图
│   ├── seed_data.sql                 # 演示种子数据
│   └── migrations/                   # 增量迁移脚本
├── desktop/                          # Tauri 桌面客户端
│   ├── src/index.html                # 桌面启动页
│   ├── src-tauri/                    # Rust/Tauri 配置和入口
│   ├── package.json                  # 桌面端 npm 脚本
│   └── scripts/                      # 桌面端开发和打包脚本
├── frontend_cli/                     # Python CLI 测试前端
│   ├── api_client.py                 # CLI HTTP 客户端
│   ├── main.py                       # CLI 菜单入口
│   ├── config.py                     # CLI 配置
│   └── render.py                     # CLI 输出渲染
├── scripts/                          # 数据库、测试、管理辅助脚本
├── docker/oracle/startup/            # Oracle 容器启动初始化脚本
├── docs/                             # 项目文档目录
├── downloads/desktop/                # 桌面端安装包下载目录
├── promo/                            # 产品宣传视频和相关资源
├── compose.yaml                      # Oracle Docker Compose 配置
├── requirements.txt                  # Python 后端依赖
├── .env.example                      # 环境变量示例
└── README.md                         # 项目总说明
```

### 2.1 前端代码位置

主要前端页面在：

- `app/web/index.html`
- `app/web/login.html`
- `app/web/home.html`
- `app/web/detail.html`
- `app/web/profile.html`
- `app/web/admin.html`

桌面端前端入口在：

- `desktop/src/index.html`

### 2.2 后端代码位置

后端入口：

- `app/main.py`

API 路由：

- `app/api/routes/*.py`

业务逻辑：

- `app/services/*.py`

数据库访问：

- `app/repositories/*.py`

### 2.3 数据库文件位置

- `sql/create_tables.sql`：建表和索引。
- `sql/procedures.sql`：PL/SQL 包 `qa_app_pkg`。
- `sql/triggers.sql`：触发器。
- `sql/views.sql`：视图。
- `sql/seed_data.sql`：演示数据。
- `sql/migrations/`：迁移脚本。

### 2.4 配置文件位置

- `.env.example`：环境变量示例。
- `compose.yaml`：Oracle Docker 容器配置。
- `requirements.txt`：Python 依赖。
- `desktop/package.json`：桌面端 npm 依赖和脚本。
- `desktop/src-tauri/tauri.conf.json`：Tauri 配置。
- `app/core/settings.py`：后端读取环境变量。

### 2.5 脚本文件位置

- `scripts/load-oracle-schema.ps1`：加载数据库 schema。
- `scripts/load-seed-data.ps1`：加载种子数据。
- `scripts/validate-oracle-schema.ps1`：校验数据库结构。
- `scripts/test-admin-api.ps1`：测试管理员 API。
- `scripts/start_business_test.py`：启动业务测试 CLI。
- `desktop/scripts/dev-with-backend.sh`：桌面端开发辅助脚本。

### 2.6 静态资源或上传文件位置

当前项目的图片上传不是存到本地静态目录，而是存入 Oracle 数据库的 `media_assets.file_content` BLOB 字段。后端通过：

- `POST /api/users/me/avatar`
- `POST /api/questions/{question_id}/images`
- `POST /api/answers/{answer_id}/images`
- `GET /api/media/files/{file_name}`

进行上传和读取。媒体元数据和二进制内容都在 `media_assets` 表中。

答辩时可以这样说：

> 本项目上传图片没有直接落到服务器磁盘，而是把图片内容作为 BLOB 存到 Oracle 的 `media_assets` 表中。前端拿到的是 `/api/media/files/{file_name}` 这样的地址，真正读取时仍然经过后端接口，由后端从数据库取出二进制内容并返回。

# 三、整体架构设计

### 3.1 项目采用的架构方式

项目采用 B/S 架构，也就是 Browser/Server 架构：

```text
浏览器 / Tauri 桌面壳
        ↓ HTTP 请求
FastAPI 后端
        ↓ python-oracledb
Oracle 26ai 数据库
        ↓
FastAPI 组装响应
        ↓ JSON / HTML / 图片二进制
浏览器展示结果
```

后端内部采用分层架构：

```text
routes 路由层
  ↓
services 业务逻辑层
  ↓
repositories 数据访问层
  ↓
Oracle 数据库
```

真实代码对应关系：

- `app/api/routes/questions.py`：接收 HTTP 请求。
- `app/services/question_service.py`：处理发帖、AI 首答、删除、采纳。
- `app/repositories/question_repository.py`：执行 SQL。
- `app/db/connection.py`：提供 Oracle 连接池。

答辩时可以这样说：

> 我把项目分成路由层、业务层和数据访问层。路由层只负责 HTTP 参数和鉴权，业务层负责校验、事务和流程编排，repository 层负责 SQL。这样代码职责清晰，后期扩展和排查问题会更容易。

### 3.2 浏览器、前端、后端、数据库请求流程

以问题列表为例：

1. 用户访问 `/home`。
2. `app/web_routes.py` 返回 `app/web/home.html`。
3. 页面中的 JavaScript 调用 `/api/questions` 或 `/api/search/questions`。
4. `app/api/routes/questions.py` 接收请求。
5. `QuestionService.list_questions` 校验分页、分类、标签、状态参数。
6. `QuestionRepository.list_questions` 查询 Oracle。
7. 后端返回 `QuestionListResponse` JSON。
8. `home.html` 将 JSON 渲染成问题卡片。

答辩时可以这样说：

> 用户访问页面时，FastAPI 先返回 HTML。页面加载后，JavaScript 再调用后端 API 获取真实业务数据。后端从 Oracle 查询数据，封装成 JSON 返回，前端再把 JSON 渲染成页面内容。

### 3.3 用户访问页面时数据如何从数据库返回前端

以详情页 `/questions/{question_id}` 为例：

- 页面路由：`app/web_routes.py` 的 `question_detail_page`
- 前端页面：`app/web/detail.html`
- 数据接口：`GET /api/questions/{question_id}`
- 后端路由：`app/api/routes/questions.py`
- 业务逻辑：`QuestionService.get_question_detail`
- SQL 查询：`QuestionRepository.get_question_detail`
- 回答查询：`AnswerRepository.list_answers_by_question`
- 图片查询：`MediaRepository.list_active_media_by_owner`

返回的数据包括：

- 问题基本信息
- 作者信息
- 标签列表
- 图片列表
- 回答列表
- 回答图片
- 当前用户是否收藏

答辩时可以这样说：

> 详情页不是把数据写死在 HTML 里，而是页面加载后调用后端接口。后端一次组装问题、标签、回答、图片和收藏状态，再返回给前端，所以页面展示的是数据库中的实时数据。

### 3.4 登录认证流程

登录流程如下：

```text
用户填写用户名密码
  ↓
前端 POST /api/auth/login
  ↓
AuthService 查询 users 表
  ↓
bcrypt 校验密码哈希
  ↓
生成 JWT
  ↓
写入 login_log
  ↓
前端保存 access_token
  ↓
后续请求携带 Authorization: Bearer <token>
```

真实代码：

- 登录页面：`app/web/login.html`
- 登录路由：`app/api/routes/auth.py`
- 登录业务：`app/services/auth_service.py`
- JWT 校验：`app/api/auth_deps.py`
- 登录日志：`app/repositories/log_repository.py`
- 登录时间触发器：`sql/triggers.sql` 的 `trg_login_log_update_last_login`

答辩时可以这样说：

> 项目使用 JWT，而不是传统服务器 session。登录成功后后端签发 token，前端保存 token，之后访问受保护接口时放到 Authorization 请求头中。后端每次都会解析 token 并从数据库重新加载用户，确认用户仍然存在且状态是 ACTIVE。

### 3.5 数据增删改查流程

以发布问题为例：

- 增：`INSERT INTO questions`
- 查：`SELECT ... FROM questions`
- 改：采纳答案时 `UPDATE questions SET accepted_answer_id = ...`
- 删：作者删除问题时不是物理删除，而是 `UPDATE questions SET status = 'DELETED'`

项目采用软删除设计的地方包括：

- 问题：状态改为 `DELETED`
- 回答：状态改为 `DELETED`
- 评论：状态改为 `DELETED`
- 图片：状态改为 `DELETED`

答辩时可以这样说：

> 本项目不是所有删除都直接 DELETE。像问题、评论、图片这类和社区内容相关的数据，会采用状态字段做软删除，这样可以保留审计和关联数据，也避免破坏外键关系。

### 3.6 项目运行和部署方式

本地运行通常包括三部分：

1. Oracle 数据库：通过 `compose.yaml` 或脚本启动。
2. FastAPI 后端：通过 `uvicorn app.main:app` 启动。
3. Web 前端：由 FastAPI 直接提供 `/`、`/home`、`/login` 等页面。

桌面端通过 `desktop/` 下的 Tauri 项目启动，默认检测服务器 `/health` 后跳转到 `/home`。

答辩时可以这样说：

> 本项目的 Web 前端由 FastAPI 统一交付，不需要单独启动 Vite 或 React 开发服务器。数据库用 Oracle Docker 容器运行，后端启动后既提供 API，也提供 HTML 页面。桌面端是一个 Tauri 轻量客户端壳，复用服务器上的 Web 页面。

# 四、前端技术细节及原理

### 4.1 前端技术栈

当前前端不是 React、Vue 或 Angular，而是原生：

- HTML
- CSS
- JavaScript
- `fetch` API
- `sessionStorage` / `localStorage`
- Markdown 渲染和代码高亮：`detail.html` 中使用 `marked` 和 `highlight.js` 相关逻辑

真实页面目录：

- `app/web/index.html`
- `app/web/login.html`
- `app/web/home.html`
- `app/web/detail.html`
- `app/web/profile.html`
- `app/web/admin.html`

答辩时可以这样说：

> 前端采用原生 HTML、CSS 和 JavaScript，没有引入大型前端框架。这样适合课程设计展示底层原理：页面结构、DOM 操作、状态管理、接口请求和登录态保存都可以直接在代码中看到。

### 4.2 页面结构

| 页面 | 文件路径 | 功能 |
|---|---|---|
| 产品首页 | `app/web/index.html` | 项目介绍、功能展示、入口按钮 |
| 登录注册页 | `app/web/login.html` | 用户登录、注册、错误提示 |
| 社区首页 | `app/web/home.html` | 推荐、热榜、搜索、筛选、发帖 |
| 问题详情页 | `app/web/detail.html` | 问题、回答、图片、评论、采纳、反馈、AI 追问 |
| 用户中心 | `app/web/profile.html` | 个人资料、头像、我的问题、回答、收藏、推荐、历史 |
| 管理后台 | `app/web/admin.html` | 用户治理、分类管理、标签治理、内容治理、审计日志 |

### 4.3 核心组件和组件化思想

当前项目没有使用 React 组件，也没有 `props`、`hooks` 这些框架概念。它使用的是“函数 + DOM 模板字符串 + 页面状态对象”的方式模拟组件化。

例如：

- `home.html` 中用函数渲染问题列表、标签筛选、发帖弹窗。
- `detail.html` 中用函数渲染回答、评论树、图片网格、AI 追问面板。
- `profile.html` 中用函数切换用户中心不同标签页。
- `admin.html` 中用 `switchSection(section)` 切换后台模块。

这种方式的“组件”不是框架组件，而是页面内的函数级组件。

答辩时可以这样说：

> 当前前端没有使用 React，所以没有真正的 props、state、hooks。项目用原生 JavaScript 的对象保存页面状态，用函数封装重复 UI 渲染逻辑，本质上是手写轻量组件化。这样能说明我理解组件化思想，但实现方式更接近原生 DOM 开发。

### 4.4 props、state、hooks 或类似机制

当前项目没有 React 的：

- `props`
- `useState`
- `useEffect`
- hooks

类似机制如下：

| React 概念 | 当前项目中的类似实现 |
|---|---|
| props | 函数参数，例如渲染问题卡片时把问题对象传入渲染函数 |
| state | 页面内 `state` 对象或全局变量，如 `admin.html` 中的分页和筛选状态 |
| effect | 页面初始化函数，例如加载页面时调用接口并渲染 |
| router | FastAPI 的页面路由 + URL 查询参数 |

答辩时可以这样说：

> 如果老师问 hooks，我会说明当前项目没有使用 React hooks。这里是原生 JS 项目，页面状态由普通对象和 DOM 管理，生命周期逻辑通过页面初始化函数完成。

### 4.5 前端路由

前端不是单页应用路由，而是由 FastAPI 提供页面路由：

| URL | 对应 HTML | 后端文件 |
|---|---|---|
| `/` | `app/web/index.html` | `app/web_routes.py` |
| `/login` | `app/web/login.html` | `app/web_routes.py` |
| `/home` | `app/web/home.html` | `app/web_routes.py` |
| `/me` | `app/web/profile.html` | `app/web_routes.py` |
| `/admin` | `app/web/admin.html` | `app/web_routes.py` |
| `/questions/{question_id}` | `app/web/detail.html` | `app/web_routes.py` |

首页还使用查询参数控制状态：

- `/home?section=recommend`
- `/home?section=hot`
- `/home?q=关键词`
- `/home?category_id=1`

### 4.6 前端如何请求后端接口

前端主要通过 `fetch` 调用后端接口。例如：

- 登录：`POST /api/auth/login`
- 问题列表：`GET /api/questions`
- 搜索：`GET /api/search/questions`
- 详情：`GET /api/questions/{question_id}`
- 收藏：`POST /api/questions/{question_id}/favorite`
- 回答：`POST /api/questions/{question_id}/answers`

对于需要登录的接口，前端会加请求头：

```javascript
Authorization: `Bearer ${token}`
```

答辩时可以这样说：

> 前端通过浏览器原生 `fetch` 发送 HTTP 请求。读接口有些允许游客访问，写接口一般需要登录，前端会从 `sessionStorage` 取出 JWT token 并放到 Authorization 请求头中。

### 4.7 表单提交、输入校验、加载状态、错误提示、页面跳转

#### 表单提交

登录页 `app/web/login.html` 负责收集用户名和密码，调用 `/api/auth/login`。

发帖弹窗在 `app/web/home.html` 中，提交时根据用户选择调用：

- 普通发帖：`POST /api/questions`
- AI 首答提问：`POST /api/questions/ask`

#### 输入校验

前端做基础校验，例如：

- 标题不能为空。
- 正文不能为空。
- 文件大小限制。
- 图片类型限制。

后端也会通过 Pydantic 和 service 层再次校验。例如 `AskQuestionRequest` 中：

- `title`: 最少 1，最多 200
- `content`: 最少 1，最多 10000
- `category_id`: 必须大于 0

#### 加载状态和错误提示

前端页面中存在 loading 文案和 toast 提示，例如 `admin.html` 中有 `showToast`、`setLoading`、`adminFetch` 等函数。

#### 页面跳转

常见跳转：

- 登录成功跳转 `/home`
- 点击问题卡片跳转 `/questions/{question_id}`
- 点击用户中心跳转 `/me`
- 管理员入口跳转 `/admin`

### 4.8 登录状态如何保存

前端登录成功后保存：

- `access_token`
- `user_id`
- `username`
- `user_role`

根据 `docs/current_status.md` 的说明，登录页使用 `sessionStorage` 保存登录态。桌面启动页 `desktop/src/index.html` 使用 `localStorage` 保存后端地址。

答辩时可以这样说：

> 用户登录后，前端把后端返回的 JWT 保存到浏览器 `sessionStorage`。之后请求受保护接口时从 `sessionStorage` 取出 token，放到 Authorization 头中。这样刷新页面后仍能保持当前标签页登录态，但关闭标签页后登录态会消失。

### 4.9 重要页面说明

#### 4.9.1 产品首页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/index.html` |
| 页面功能 | 产品介绍、功能展示、使用场景、FAQ、下载入口 |
| 主要组件 | Hero 区、功能卡片、宣传视频、热门标签、FAQ |
| 用户流程 | 用户访问 `/`，了解系统，然后点击入口进入登录或社区 |
| 调用接口 | 主要是静态展示，部分资源通过 `/promo/{filename}`、`/downloads/desktop/{platform}` 获取 |

#### 4.9.2 登录注册页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/login.html` |
| 页面功能 | 注册、登录、错误提示 |
| 主要组件 | 登录表单、注册表单、切换按钮、提示信息 |
| 用户流程 | 输入账号密码，提交，成功后保存 token 并跳转 |
| 调用接口 | `POST /api/auth/register`、`POST /api/auth/login` |

#### 4.9.3 社区首页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/home.html` |
| 页面功能 | 问题列表、推荐、热榜、搜索、分类筛选、标签筛选、发帖、收藏 |
| 主要组件 | 顶部导航、问题流、筛选栏、发帖弹窗、图片选择 |
| 用户流程 | 浏览问题或登录后发帖、收藏、搜索 |
| 调用接口 | `GET /api/questions`、`GET /api/search/questions`、`GET /api/categories`、`GET /api/tags`、`GET /api/tags/suggestions`、`POST /api/questions`、`POST /api/questions/ask`、`POST /api/questions/{id}/favorite` |

#### 4.9.4 问题详情页

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/detail.html` |
| 页面功能 | 查看问题、回答、图片、评论、采纳、点赞/点踩、AI 追问 |
| 主要组件 | 问题详情、回答列表、评论树、图片网格、追问面板 |
| 用户流程 | 打开详情，查看回答，登录后回答/评论/反馈/追问 |
| 调用接口 | `GET /api/questions/{id}`、`POST /api/questions/{id}/answers`、`POST /api/answers/{id}/feedback`、`GET /api/answers/{id}/comments`、`POST /api/answers/{id}/comments`、`POST /api/questions/{qid}/answers/{aid}/follow-up` |

#### 4.9.5 用户中心

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/profile.html` |
| 页面功能 | 资料、头像、我的问题、我的回答、我的收藏、推荐、浏览历史、搜索历史 |
| 主要组件 | 用户资料卡、标签页、列表、头像上传 |
| 用户流程 | 登录后进入 `/me`，查看和修改个人数据 |
| 调用接口 | `GET /api/users/me/profile`、`PATCH /api/users/me/profile`、`GET /api/users/{id}/questions`、`GET /api/users/{id}/answers`、`GET /api/users/{id}/favorites`、`POST /api/users/{id}/profile/rebuild`、`GET /api/users/{id}/recommendations` |

#### 4.9.6 管理后台

| 项目 | 内容 |
|---|---|
| 文件路径 | `app/web/admin.html` |
| 页面功能 | 用户治理、分类管理、标签治理、内容治理、日志查看 |
| 主要组件 | 侧边导航、数据表格、筛选表单、状态修改控件 |
| 用户流程 | 管理员登录后进入 `/admin`，查看和修改后台数据 |
| 调用接口 | `/api/admin/users`、`/api/admin/categories`、`/api/admin/tags`、`/api/admin/questions/{id}/status`、`/api/admin/comments/{id}/status`、`/api/admin/logs/login`、`/api/admin/logs/operations` |

### 4.10 前端常见答辩问题与回答

Q：你的前端为什么不用 Vue 或 React？  
A：当前项目重点是课程设计闭环，我选择原生 HTML、CSS、JavaScript，能更直接展示 DOM 操作、接口请求和登录态管理。虽然没有框架组件，但通过函数和状态对象实现了类似组件化的组织方式。

Q：前端是否能保证用户权限？  
A：前端只能做用户体验层面的控制，比如隐藏按钮。真正权限必须由后端校验，因为浏览器代码可以被用户修改或绕过。

Q：你的前端路由是什么方式？  
A：不是 SPA 路由，而是 FastAPI 提供页面路由。比如 `/home` 返回 `home.html`，`/questions/{question_id}` 返回 `detail.html`，页面内部再用 JavaScript 请求接口加载数据。

# 五、后端技术细节及原理

### 5.1 后端技术栈

| 技术 | 用途 | 真实文件 |
|---|---|---|
| FastAPI | Web 后端框架 | `app/main.py` |
| Pydantic | 请求和响应校验 | `app/schemas/` |
| python-oracledb | Oracle 数据库访问 | `app/db/connection.py` |
| passlib bcrypt | 密码哈希 | `app/services/auth_service.py` |
| python-jose | JWT 编码和解码 | `app/services/auth_service.py`、`app/api/auth_deps.py` |
| OpenAI SDK | 调用 DeepSeek 兼容接口 | `app/integrations/llm/openai_client.py` |
| python-dotenv | 读取 `.env` | `app/core/settings.py` |

### 5.2 后端入口文件

入口文件：`app/main.py`

主要职责：

- 创建 FastAPI 应用。
- 注册 Web 页面路由。
- 注册认证路由。
- 配置 CORS。
- 添加安全响应头中间件。
- 提供 `/health` 健康检查。
- 注册 `/api` 聚合路由。

### 5.3 路由文件

| 文件 | 职责 |
|---|---|
| `app/api/routes/auth.py` | 注册、登录 |
| `app/api/routes/questions.py` | 问题发布、列表、详情、删除、采纳 |
| `app/api/routes/answers.py` | 人工回答、回答软删除 |
| `app/api/routes/comments.py` | 评论、楼中楼、软删除 |
| `app/api/routes/favorites.py` | 收藏、取消收藏 |
| `app/api/routes/feedback.py` | 回答点赞、点踩、评分 |
| `app/api/routes/search.py` | 搜索问题、搜索历史 |
| `app/api/routes/recommendations.py` | 用户画像和推荐 |
| `app/api/routes/users.py` | 用户中心 |
| `app/api/routes/media.py` | 头像、问题图、回答图、图片读取 |
| `app/api/routes/admin.py` | 管理员后台接口 |
| `app/api/routes/meta.py` | 分类、标签、标签建议 |
| `app/api/routes/chat.py` | AI 多轮追问 |

### 5.4 控制器或业务逻辑文件

FastAPI 中没有单独叫 Controller 的目录，本项目的路由层相当于 Controller，业务逻辑集中在 `app/services/`。

| Service | 作用 |
|---|---|
| `AuthService` | 注册、登录、JWT 签发、登录限流、登录日志 |
| `QuestionService` | 发帖、AI 首答、标签绑定、删帖、采纳答案 |
| `AnswerService` | 人工回答 |
| `CommentService` | 评论、回复、评论树、软删除 |
| `FeedbackService` | 点赞、点踩、评分和状态回显 |
| `FavoriteService` | 收藏和取消收藏 |
| `SearchService` | 关键词搜索和搜索历史 |
| `RecommendationService` | 用户画像重建和推荐生成 |
| `MediaService` | 图片上传、删除、读取 |
| `AdminService` | 用户、分类、标签、内容、日志治理 |
| `ChatService` | AI 首答后的多轮追问 |

### 5.5 数据库连接文件

数据库连接在 `app/db/connection.py` 中实现。它使用全局 Oracle 连接池：

- 通过 `oracledb.create_pool` 创建连接池。
- 从 `.env` 读取数据库地址、端口、服务名、用户名和密码。
- `get_connection()` 是上下文管理器，用完自动关闭连接。
- 异常时自动 rollback。

答辩时可以这样说：

> 数据库连接没有每次请求都新建 TCP 连接，而是使用 Oracle 连接池。连接池可以复用连接，减少频繁创建连接的开销，也能限制最大连接数，保护数据库。

### 5.6 工具函数和配置文件

配置文件：`app/core/settings.py`

它通过 `python-dotenv` 加载 `.env`，并把配置封装成 `Settings`：

- 应用名称、端口
- Oracle 连接信息
- DeepSeek API 配置
- JWT 配置
- CORS 配置
- CSP 配置
- 是否启用 Oracle Text 搜索

异常定义：`app/core/errors.py`

主要自定义异常：

- `AppError`
- `ValidationError`
- `NotFoundError`
- `ConfigurationError`
- `ExternalServiceError`

### 5.7 中间件机制

`app/main.py` 中配置了：

- `CORSMiddleware`：控制跨域访问。
- 自定义 HTTP 中间件 `add_security_headers`：添加安全响应头。

安全响应头包括：

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `X-Frame-Options: DENY`

答辩时可以这样说：

> 中间件是在请求进入路由前后统一执行的逻辑。本项目用中间件统一处理 CORS 和安全响应头，这样不用每个接口重复写。

### 5.8 参数校验

参数校验主要有两层：

1. Pydantic schema 校验，例如 `app/schemas/question.py`。
2. Service 层业务校验，例如 `QuestionService.list_questions` 检查分页、状态、分类是否合法。

例如 `AskQuestionRequest`：

- `category_id` 必须大于 0。
- `title` 长度 1 到 200。
- `content` 长度 1 到 10000。
- `auto_tag` 默认开启。

### 5.9 异常处理

路由层捕获 `AppError`，转换成 `HTTPException`：

```python
except AppError as exc:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

数据库异常在 service 层被翻译成更友好的错误：

- `ORA-02291`：外键引用无效。
- `ORA-00001`：唯一约束冲突。
- `ORA-02290`：检查约束失败。

### 5.10 API 接口表格

| 模块 | 方法 | 路径 | 功能 | 参数 | 返回值 | 是否鉴权 | 对应文件 |
|---|---|---|---|---|---|---|---|
| 健康检查 | GET | `/health` | 检查后端是否可用 | 无 | `{status: ok}` | 否 | `app/main.py` |
| 认证 | POST | `/api/auth/register` | 用户注册 | `username,password,nickname` | `user_id,message` | 否 | `app/api/routes/auth.py` |
| 认证 | POST | `/api/auth/login` | 用户登录并返回 JWT | `username,password` | `TokenResponse` | 否 | `app/api/routes/auth.py` |
| 元数据 | GET | `/api/categories` | 分类列表 | 无 | `CategoryListResponse` | 否 | `app/api/routes/meta.py` |
| 元数据 | GET | `/api/tags` | 标签列表 | `limit` | `TagListResponse` | 否 | `app/api/routes/meta.py` |
| 元数据 | GET | `/api/tags/suggestions` | 标签建议 | `keyword,limit` | `TagSuggestionResponse` | 否 | `app/api/routes/meta.py` |
| 问题 | POST | `/api/questions/ask` | 发布问题并生成 AI 首答 | `AskQuestionRequest` | `QuestionDetailResponse` | 是 | `app/api/routes/questions.py` |
| 问题 | POST | `/api/questions` | 发布普通社区问题 | `QuestionCreate` | `question_id,message` | 是 | `app/api/routes/questions.py` |
| 问题 | GET | `/api/questions` | 查询问题列表 | `page,page_size,category_id,tag_id,status` | `QuestionListResponse` | 可选 | `app/api/routes/questions.py` |
| 问题 | GET | `/api/questions/{question_id}` | 查询问题详情 | `question_id` | `QuestionDetailResponse` | 可选 | `app/api/routes/questions.py` |
| 问题 | DELETE | `/api/questions/{question_id}` | 作者删除问题 | `question_id` | `QuestionDeleteResponse` | 是 | `app/api/routes/questions.py` |
| 问题 | POST | `/api/questions/{question_id}/accept-answer` | 采纳答案 | `answer_id` | `QuestionDetailResponse` | 是 | `app/api/routes/questions.py` |
| 回答 | POST | `/api/questions/{question_id}/answers` | 发布人工回答 | `content,confidence_score` | `QuestionDetailResponse` | 是 | `app/api/routes/answers.py` |
| 回答 | DELETE | `/api/answers/{answer_id}` | 作者或管理员删除回答 | `reason` 可选 | `DeleteAnswerResponse` | 是 | `app/api/routes/answers.py` |
| 浏览 | POST | `/api/questions/{question_id}/browse` | 记录浏览行为 | `duration,click_depth` | `BrowseRecordResponse` | 是 | `app/api/routes/browse.py` |
| 收藏 | POST | `/api/questions/{question_id}/favorite` | 收藏问题 | `user_id` 兼容字段 | `FavoriteRecordResponse` | 是 | `app/api/routes/favorites.py` |
| 收藏 | DELETE | `/api/questions/{question_id}/favorite` | 取消收藏 | `user_id` 兼容参数 | `FavoriteDeleteResponse` | 是 | `app/api/routes/favorites.py` |
| 反馈 | POST | `/api/answers/{answer_id}/feedback` | 点赞/点踩/评分 | `is_like,rating,comment_text` | `AnswerFeedbackResponse` | 是 | `app/api/routes/feedback.py` |
| 反馈 | GET | `/api/questions/{question_id}/feedbacks` | 当前用户对问题下回答的反馈状态 | `question_id` | `dict[int,str]` | 是 | `app/api/routes/feedback.py` |
| 评论 | POST | `/api/answers/{answer_id}/comments` | 发布评论或回复 | `content,parent_comment_id` | `CommentItem` | 是 | `app/api/routes/comments.py` |
| 评论 | GET | `/api/answers/{answer_id}/comments` | 查询评论树 | `answer_id` | `CommentTreeResponse` | 否 | `app/api/routes/comments.py` |
| 评论 | DELETE | `/api/comments/{comment_id}` | 删除自己的评论 | `comment_id` | `DeleteCommentResponse` | 是 | `app/api/routes/comments.py` |
| 搜索 | GET | `/api/search/questions` | 搜索问题 | `q,page,page_size,category_id,tag_id,status` | `QuestionListResponse` | 可选 | `app/api/routes/search.py` |
| 搜索 | GET | `/api/search/history` | 查询当前用户搜索历史 | 无 | `list[str]` | 是 | `app/api/routes/search.py` |
| 推荐 | POST | `/api/users/{user_id}/profile/rebuild` | 重建用户标签画像 | `user_id` | `ProfileRebuildResponse` | 是 | `app/api/routes/recommendations.py` |
| 推荐 | POST | `/api/users/{user_id}/recommendations/generate` | 生成推荐 | `limit` | `RecommendationGenerationResponse` | 是 | `app/api/routes/recommendations.py` |
| 推荐 | GET | `/api/users/{user_id}/recommendations` | 查看推荐 | `status,limit` | `RecommendationListResponse` | 是 | `app/api/routes/recommendations.py` |
| 用户中心 | GET | `/api/users/me/profile` | 当前用户资料 | 无 | `UserCenterProfileResponse` | 是 | `app/api/routes/users.py` |
| 用户中心 | PATCH | `/api/users/me/profile` | 修改当前用户资料 | `nickname,email,phone` | `UserCenterProfileResponse` | 是 | `app/api/routes/users.py` |
| 用户中心 | GET | `/api/users/{user_id}/questions` | 我的提问 | `page,page_size` | `UserQuestionListResponse` | 是 | `app/api/routes/users.py` |
| 用户中心 | GET | `/api/users/{user_id}/answers` | 我的回答 | `page,page_size` | `UserAnswerListResponse` | 是 | `app/api/routes/users.py` |
| 用户中心 | GET | `/api/users/{user_id}/favorites` | 我的收藏 | `page,page_size` | `UserFavoriteListResponse` | 是 | `app/api/routes/users.py` |
| 用户中心 | GET | `/api/users/{user_id}/browse-history` | 浏览历史 | `limit` | `UserBrowseHistoryResponse` | 是 | `app/api/routes/users.py` |
| 用户中心 | GET | `/api/users/{user_id}/search-history` | 搜索历史 | `limit` | `UserSearchHistoryResponse` | 是 | `app/api/routes/users.py` |
| 媒体 | POST | `/api/users/me/avatar` | 上传头像 | multipart `file` | `AvatarMediaResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | GET | `/api/users/me/avatar` | 获取当前头像 | 无 | `AvatarMediaResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | DELETE | `/api/users/me/avatar` | 删除头像 | 无 | `AvatarDeleteResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | POST | `/api/questions/{question_id}/images` | 上传问题图片 | multipart `file` | `QuestionImageListResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | GET | `/api/questions/{question_id}/images` | 查看问题图片 | `question_id` | `QuestionImageListResponse` | 否 | `app/api/routes/media.py` |
| 媒体 | DELETE | `/api/questions/{question_id}/images/{media_id}` | 删除问题图片 | `question_id,media_id` | `QuestionImageDeleteResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | POST | `/api/answers/{answer_id}/images` | 上传回答图片 | multipart `file` | `AnswerImageListResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | GET | `/api/answers/{answer_id}/images` | 查看回答图片 | `answer_id` | `AnswerImageListResponse` | 否 | `app/api/routes/media.py` |
| 媒体 | DELETE | `/api/answers/{answer_id}/images/{media_id}` | 删除回答图片 | `answer_id,media_id` | `AnswerImageDeleteResponse` | 是 | `app/api/routes/media.py` |
| 媒体 | GET | `/api/media/files/{file_name}` | 读取图片二进制 | `file_name` | 图片内容 | 否 | `app/api/routes/media.py` |
| AI 追问 | POST | `/api/questions/{question_id}/answers/{answer_id}/follow-up` | 发起或继续追问 | `content,session_id` | `ChatSessionDetailResponse` | 是 | `app/api/routes/chat.py` |
| AI 追问 | GET | `/api/questions/{question_id}/answers/{answer_id}/follow-up-sessions` | 查看追问会话 | `question_id,answer_id` | `ChatSessionListResponse` | 是 | `app/api/routes/chat.py` |
| AI 追问 | GET | `/api/chat/sessions/{session_id}` | 查看会话详情 | `session_id` | `ChatSessionDetailResponse` | 是 | `app/api/routes/chat.py` |
| 管理员 | GET | `/api/admin/users` | 用户列表 | `page,page_size,role,status` | `AdminUserListResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | PATCH | `/api/admin/users/{user_id}/status` | 修改用户状态 | `status` | `AdminUserMutationResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | PATCH | `/api/admin/users/{user_id}/role` | 修改用户角色 | `role` | `AdminUserMutationResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | GET | `/api/admin/categories` | 分类管理列表 | `page,page_size,status` | `AdminCategoryListResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | POST | `/api/admin/categories` | 创建分类 | `category_name,description,status` | `AdminCategoryMutationResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | PATCH | `/api/admin/categories/{category_id}` | 修改分类 | `category_name,description,status` | `AdminCategoryMutationResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | GET | `/api/admin/tags` | 标签治理列表 | `page,page_size,source,status,keyword` | `AdminTagListResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | PATCH | `/api/admin/tags/{tag_id}` | 修改标签 | `tag_name,description,status` | `AdminTagMutationResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | PATCH | `/api/admin/questions/{question_id}/status` | 修改问题状态 | `status,reason` | `AdminQuestionStatusResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | DELETE | `/api/admin/questions/{question_id}` | 管理员删帖 | `reason` | `AdminQuestionStatusResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | DELETE | `/api/admin/answers/{answer_id}` | 管理员删除回答 | `reason` | `DeleteAnswerResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | PATCH | `/api/admin/comments/{comment_id}/status` | 修改评论状态 | `status,reason` | `AdminCommentStatusResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | GET | `/api/admin/logs/login` | 登录日志 | `page,page_size,user_id,result` | `AdminLoginLogListResponse` | 管理员 | `app/api/routes/admin.py` |
| 管理员 | GET | `/api/admin/logs/operations` | 操作日志 | `page,page_size,user_id,op_type` | `AdminOperationLogListResponse` | 管理员 | `app/api/routes/admin.py` |

# 六、登录认证与权限控制

### 6.1 项目使用什么认证方式

当前项目使用 JWT，不是传统 session，也不是 cookie session。

真实依赖：

- `python-jose[cryptography]`
- `passlib[bcrypt]`

真实代码：

- JWT 签发：`app/services/auth_service.py`
- JWT 解码和用户加载：`app/api/auth_deps.py`

### 6.2 用户登录后后端如何识别身份

登录成功后，后端生成 JWT：

- `sub`：用户 ID
- `exp`：过期时间

后续请求中前端携带：

```text
Authorization: Bearer <access_token>
```

后端在 `get_current_user` 中：

1. 从请求头读取 Bearer Token。
2. 用 `JWT_SECRET_KEY` 和 `JWT_ALGORITHM` 解码。
3. 从 `sub` 得到用户 ID。
4. 查询 `users` 表。
5. 检查用户状态是否为 `ACTIVE`。

### 6.3 前端如何保存登录状态

登录成功后前端保存 token 和用户信息。根据项目文档和页面逻辑，主要保存在 `sessionStorage`：

- `access_token`
- `user_id`
- `username`
- `user_role`

后续前端请求时把 token 放到请求头。

### 6.4 后端如何保护需要登录的接口

后端通过 FastAPI 的 `Depends` 依赖注入保护接口：

- `get_current_user`
- `get_current_user_id`
- `get_admin_user`
- `get_admin_user_id`

例如发布回答接口需要：

```python
current_user_id: int = Depends(get_current_user_id)
```

管理员接口需要：

```python
_: AuthenticatedUser = Depends(get_admin_user)
```

### 6.5 用户未登录时会发生什么

对于必须登录的接口，如果没有 token，后端返回：

- HTTP 401
- 错误信息：`请先登录后再执行该操作。`

前端通常会：

- 显示登录提示。
- 跳转到 `/login`。
- 或进入游客浏览模式。

### 6.6 为什么不能只在前端判断用户是否登录

因为前端代码运行在用户浏览器里，用户可以：

- 修改 JavaScript。
- 伪造按钮点击。
- 直接用 Postman 或 curl 调接口。
- 修改本地 storage。

如果只靠前端隐藏按钮，攻击者仍然可以直接调用后端接口。因此真正的权限必须在后端做。

答辩时可以这样说：

> 前端判断只能改善用户体验，不能保证安全。真正的安全边界在服务端，所有写操作和管理员操作都必须由后端解析 JWT 并检查用户角色。

### 6.7 后端权限校验为什么重要

后端权限校验可以防止：

- 未登录用户发帖、评论、上传图片。
- A 用户修改 B 用户资料。
- 普通用户访问管理员后台接口。
- 非作者删除别人问题或图片。
- 非提问者采纳答案。

真实代码中有这些校验：

- `ensure_path_user_access`：只能访问自己的用户中心资源。
- `resolve_authenticated_user_id`：旧 `user_id` 参数必须和当前 token 一致。
- `get_admin_user`：只有 `ADMIN` 能访问后台。
- `MediaService._ensure_question_author`：只有作者能管理问题图片。
- `QuestionService.accept_answer`：只有提问者或管理员能采纳答案。

# 七、数据库设计及原理

### 7.1 使用的数据库类型

当前项目使用：

- Oracle AI Database 26ai Free
- Docker 镜像配置在 `compose.yaml`
- Python 通过 `python-oracledb` 访问

### 7.2 核心数据表

数据库主 schema 在 `sql/create_tables.sql`。

| 表名 | 作用 | 关键字段 | 主键 | 外键 | 说明 |
|---|---|---|---|---|---|
| `users` | 用户表 | `user_id, username, password_hash, role, status, avatar_media_id` | `user_id` | `avatar_media_id -> media_assets.media_id` | 保存账号、密码哈希、角色、状态、头像 |
| `categories` | 分类表 | `category_id, category_name, status` | `category_id` | 无 | 问题分类 |
| `tags` | 标签表 | `tag_id, tag_name, source, status, create_user_id` | `tag_id` | `create_user_id -> users.user_id` | 支持系统、用户、AI、管理员标签 |
| `media_assets` | 媒体资源表 | `media_id, owner_type, owner_id, file_content, public_url, status` | `media_id` | `uploader_user_id -> users.user_id` | 头像、问题图、回答图，BLOB 存储 |
| `questions` | 问题/帖子表 | `question_id, user_id, category_id, title, content, status, accepted_answer_id` | `question_id` | `user_id -> users`，`category_id -> categories`，`accepted_answer` 复合外键 | 社区动态主体 |
| `answers` | 回答表 | `answer_id, question_id, user_id, answer_type, content, status, like_count` | `answer_id` | `question_id -> questions`，`user_id -> users` | AI 回答、人工回答、系统回答和软删除状态 |
| `question_tags` | 问题标签关联表 | `qt_id, question_id, tag_id, source, confidence_score` | `qt_id` | `question_id -> questions`，`tag_id -> tags` | 实现问题和标签多对多 |
| `answer_feedback` | 回答反馈表 | `feedback_id, answer_id, user_id, is_like, rating` | `feedback_id` | `answer_id -> answers`，`user_id -> users` | 点赞、点踩、评分 |
| `answer_comments` | 回答评论表 | `comment_id, answer_id, user_id, parent_comment_id, root_comment_id, status` | `comment_id` | `answer_id -> answers`，`user_id -> users`，自引用评论外键 | 评论和楼中楼回复 |
| `favorites` | 收藏表 | `favorite_id, user_id, question_id` | `favorite_id` | `user_id -> users`，`question_id -> questions` | 用户收藏问题 |
| `browse_history` | 浏览历史表 | `history_id, user_id, question_id, duration, click_depth` | `history_id` | `user_id -> users`，`question_id -> questions` | 行为记录，用于统计和推荐 |
| `search_history` | 搜索历史表 | `search_id, user_id, keyword` | `search_id` | `user_id -> users` | 记录用户搜索关键词 |
| `recommendations` | 推荐结果表 | `rec_id, user_id, question_id, rec_type, rec_score, status` | `rec_id` | `user_id -> users`，`question_id -> questions` | 保存推荐生成结果 |
| `user_tag_profile` | 用户标签画像表 | `profile_id, user_id, tag_id, weight` | `profile_id` | `user_id -> users`，`tag_id -> tags` | 基于行为计算兴趣权重 |
| `chat_session` | AI 追问会话表 | `session_id, user_id, question_id, seed_answer_id, status` | `session_id` | `user_id -> users`，`question_id -> questions`，`seed_answer` 复合外键 | AI 首答后的多轮追问 |
| `chat_message` | AI 追问消息表 | `message_id, session_id, sender_type, content` | `message_id` | `session_id -> chat_session` | 保存用户和 AI 的多轮消息 |
| `ai_prompt_log` | AI 调用日志表 | `prompt_id, question_id, prompt_text, response_text, token_usage` | `prompt_id` | `question_id -> questions` | 记录 AI prompt、回答和 token |
| `login_log` | 登录日志表 | `log_id, user_id, ip_address, result` | `log_id` | `user_id -> users` | 记录成功、失败、锁定登录 |
| `operation_log` | 操作日志表 | `op_id, user_id, op_type, op_content` | `op_id` | `user_id -> users` | 管理员和关键操作审计 |

### 7.3 字段含义示例

以 `questions` 表为例：

- `question_id`：问题主键。
- `user_id`：提问者。
- `category_id`：所属分类。
- `title`：标题。
- `content`：正文，CLOB 类型。
- `status`：状态，支持 `OPEN`、`RESOLVED`、`CLOSED`、`ARCHIVED`、`DELETED`。
- `accepted_answer_id`：被采纳的答案。
- `view_count`：浏览数。
- `favorite_count`：收藏数。
- `answer_count`：回答数。

### 7.4 主键、外键、索引

主键用于唯一标识一行数据。例如 `users.user_id`。

外键用于保证关联数据真实存在。例如 `questions.user_id` 必须引用 `users.user_id`。

索引用于提升查询性能。例如：

- `idx_questions_user_id`
- `idx_questions_category_id`
- `idx_questions_status`
- `idx_questions_ask_time`
- `idx_answers_question_id`
- `idx_favorites_user_id`
- `idx_recommendations_user_id`

答辩时可以这样说：

> 主键保证每条记录唯一，外键保证表之间关系合法，索引用来提高查询速度。比如问题列表经常按状态、分类和时间查询，所以 `questions` 表上建立了相关索引。

### 7.5 表之间的关系

#### 一对多关系

| 关系 | 实现方式 |
|---|---|
| 一个用户发布多个问题 | `questions.user_id -> users.user_id` |
| 一个问题有多个回答 | `answers.question_id -> questions.question_id` |
| 一个回答有多个评论 | `answer_comments.answer_id -> answers.answer_id` |
| 一个用户有多条浏览历史 | `browse_history.user_id -> users.user_id` |

#### 多对多关系

问题和标签是多对多：

- 一个问题可以有多个标签。
- 一个标签可以绑定多个问题。

通过中间表 `question_tags` 实现：

```text
questions 1 -- N question_tags N -- 1 tags
```

### 7.6 SELECT、INSERT、UPDATE、DELETE 的作用

- `SELECT`：查询数据，例如查询问题列表。
- `INSERT`：新增数据，例如注册用户、发布问题、发表评论。
- `UPDATE`：修改数据，例如采纳答案、修改用户状态、软删除问题。
- `DELETE`：物理删除数据。当前项目部分业务更倾向软删除，如问题和评论一般改状态。

### 7.7 JOIN、WHERE、ORDER BY、分页、索引原理

- `JOIN`：连接多张表，例如问题详情需要连接 `questions` 和 `users` 获取作者信息。
- `WHERE`：过滤条件，例如只查 `status = 'OPEN'` 的问题。
- `ORDER BY`：排序，例如按 `ask_time DESC` 展示最新问题。
- 分页：使用 `OFFSET ... FETCH NEXT ... ROWS ONLY`，避免一次返回全部数据。
- 索引：让数据库快速定位数据，减少全表扫描。

### 7.8 `sql/migrations` 目录的作用

`sql/migrations/` 保存增量变更脚本。例如：

- `20260405_add_answer_comments.sql`
- `20260422_add_media_assets.sql`
- `20260428_add_question_oracle_text_indexes.sql`
- `20260502_improve_recommendation_scoring.sql`

迁移脚本用于旧数据库升级，而不是每次都删库重建。

答辩时可以这样说：

> 初始建表脚本适合新环境，迁移脚本适合已有环境升级。这样数据库结构变更可以被记录和复现，避免手动改库导致环境不一致。

### 7.9 seed 数据的作用

`sql/seed_data.sql` 用于导入演示数据：

- 演示用户
- 分类
- 标签
- 问题
- 回答
- 行为数据

作用：

- 方便课堂演示。
- 方便测试接口。
- 方便新环境快速看到页面效果。

### 7.10 数据库迁移脚本为什么重要

如果项目上线后已经有真实数据，不能随便删除表重建。迁移脚本可以：

- 保留已有数据。
- 增加新表或字段。
- 增加索引。
- 修复旧结构。
- 保证开发、测试、生产环境一致。

# 八、核心功能完整流程讲解

### 8.1 用户注册流程

1. 前端触发什么操作  
   用户在 `app/web/login.html` 注册表单输入用户名、密码、昵称，点击注册。

2. 调用哪个接口  
   `POST /api/auth/register`

3. 后端如何处理  
   `app/api/routes/auth.py` 调用 `AuthService.register`。

4. 后端如何访问数据库  
   `UserRepository.get_user_by_username` 检查用户名是否存在，`UserRepository.create_user` 插入用户。

5. 数据库发生什么变化  
   `users` 表新增一条用户记录，密码保存为 bcrypt 哈希。

6. 后端返回什么数据  
   返回 `user_id` 和 `message`。

7. 前端如何展示结果  
   前端提示注册成功，并让用户登录。

8. 可能出现哪些异常情况  
   用户名重复、密码长度不符合、数据库连接失败。

答辩时可以这样说：

> 注册时后端不会保存明文密码，而是使用 bcrypt 生成哈希后写入 `users.password_hash`。登录时再用 bcrypt 校验用户输入和哈希是否匹配。

### 8.2 用户登录流程

1. 前端触发什么操作  
   用户在 `login.html` 输入用户名和密码，点击登录。

2. 调用哪个接口  
   `POST /api/auth/login`

3. 后端如何处理  
   `AuthService.login` 查询用户，检查状态，验证密码，生成 JWT。

4. 后端如何访问数据库  
   `UserRepository.get_user_by_username` 查询 `users`，`LogRepository.create_login_log` 写入 `login_log`。

5. 数据库发生什么变化  
   登录成功或失败都会尝试写登录日志；成功登录时触发器 `trg_login_log_update_last_login` 更新 `users.last_login_time`。

6. 后端返回什么数据  
   返回 `access_token`、`token_type`、`user_id`、`username`、`role`。

7. 前端如何展示结果  
   保存 token，跳转到 `/home`，右上角显示用户信息。

8. 可能出现哪些异常情况  
   用户名或密码错误、账号锁定、账号停用、JWT 密钥未配置、登录失败次数过多。

### 8.3 发布动态流程

说明：当前项目没有传统朋友圈“动态”表，真实实现是发布“问题/帖子”，存入 `questions` 表。

1. 前端触发什么操作  
   用户在 `home.html` 点击发帖，填写标题、正文、分类、标签和图片。

2. 调用哪个接口  
   普通发布：`POST /api/questions`  
   AI 首答发布：`POST /api/questions/ask`

3. 后端如何处理  
   `QuestionService.publish_question` 或 `QuestionService.ask_question` 创建问题，绑定标签。AI 模式还会调用 DeepSeek 生成首答。

4. 后端如何访问数据库  
   `QuestionRepository.create_question` 插入 `questions`；`QuestionRepository.add_tags` 插入 `question_tags`；AI 模式下 `AnswerRepository.create_ai_answer` 插入 `answers`。

5. 数据库发生什么变化  
   新增问题、标签绑定；AI 模式新增 AI 回答和 prompt 日志。

6. 后端返回什么数据  
   普通发帖返回 `question_id,message`；AI 首答返回完整 `QuestionDetailResponse`。

7. 前端如何展示结果  
   首页刷新问题列表，或跳转到详情页查看新问题。

8. 可能出现哪些异常情况  
   未登录、分类不存在、标签非法、AI API Key 未配置、DeepSeek 调用失败。

### 8.4 查询动态列表流程

说明：动态列表对应问题列表。

1. 前端触发什么操作  
   用户打开 `/home`，切换推荐、热榜、分类、状态、标签或输入搜索关键词。

2. 调用哪个接口  
   普通列表：`GET /api/questions`  
   搜索：`GET /api/search/questions`

3. 后端如何处理  
   `QuestionService.list_questions` 或 `SearchService.search_questions` 校验分页和筛选条件。

4. 后端如何访问数据库  
   `QuestionRepository.list_questions` 查询 `questions`、`users`、`tags` 等数据。

5. 数据库发生什么变化  
   普通列表查询不改变数据；搜索接口在登录时会写入 `search_history`。

6. 后端返回什么数据  
   返回分页列表 `items,page,page_size,total`。

7. 前端如何展示结果  
   `home.html` 渲染成问题卡片。

8. 可能出现哪些异常情况  
   分页参数非法、状态参数非法、搜索关键词为空、数据库异常。

### 8.5 评论流程

1. 前端触发什么操作  
   用户在 `detail.html` 的某个回答下输入评论或回复。

2. 调用哪个接口  
   `POST /api/answers/{answer_id}/comments`

3. 后端如何处理  
   `CommentService.create_comment` 检查回答是否存在、问题是否允许评论、父评论是否合法。

4. 后端如何访问数据库  
   `CommentRepository.create_comment` 插入 `answer_comments`。

5. 数据库发生什么变化  
   新增评论。如果是回复，会设置 `parent_comment_id`、`root_comment_id`、`reply_to_user_id`，并增加父评论 `reply_count`。

6. 后端返回什么数据  
   返回 `CommentItem`。

7. 前端如何展示结果  
   详情页重新加载评论树，展示新评论，并可高亮。

8. 可能出现哪些异常情况  
   未登录、评论内容为空、回答不存在、父评论不存在、父评论不是 ACTIVE。

### 8.6 点赞流程

说明：当前项目的点赞/点踩作用于回答，不是对问题动态本身点赞。

1. 前端触发什么操作  
   用户在 `detail.html` 点击回答下方的点赞或点踩按钮。

2. 调用哪个接口  
   `POST /api/answers/{answer_id}/feedback`

3. 后端如何处理  
   `FeedbackService.save_feedback` 判断用户是否已有反馈。没有就新增，有就更新，相同操作且无评分/评论时取消反馈。

4. 后端如何访问数据库  
   `FeedbackRepository` 操作 `answer_feedback`。

5. 数据库发生什么变化  
   新增、更新或删除 `answer_feedback`。触发器 `trg_answer_feedback_refresh_stats` 自动更新 `answers.like_count`、`dislike_count`、`avg_rating`。

6. 后端返回什么数据  
   返回反馈记录、回答最新统计和操作类型 `CREATED/UPDATED/DELETED`。

7. 前端如何展示结果  
   更新点赞/点踩按钮状态和数量。

8. 可能出现哪些异常情况  
   未登录、回答不存在、外键约束失败、评分范围非法。

### 8.7 个人主页流程

说明：当前项目实现的是用户中心，不是公开社交主页。

1. 前端触发什么操作  
   用户点击头像菜单进入 `/me`。

2. 调用哪个接口  
   `GET /api/users/me/profile` 和用户中心相关列表接口。

3. 后端如何处理  
   `UserCenterService` 校验用户 ID，并查询资料、问题、回答、收藏、历史和推荐。

4. 后端如何访问数据库  
   `UserCenterRepository` 查询 `users`、`questions`、`answers`、`favorites`、`browse_history`、`search_history`。

5. 数据库发生什么变化  
   查看资料不改变数据。修改资料时会更新 `users.nickname`、`email`、`phone`。

6. 后端返回什么数据  
   返回用户资料和分页列表。

7. 前端如何展示结果  
   `profile.html` 按标签页展示资料、列表和推荐。

8. 可能出现哪些异常情况  
   未登录、访问他人路径用户 ID、邮箱或手机号重复、分页参数非法。

### 8.8 好友或关注流程

当前项目未实现好友或关注功能。

代码中未发现：

- 好友表，例如 `friends`
- 关注表，例如 `follows`
- 好友/关注 API
- 好友/关注页面组件

答辩时可以这样说：

> 当前版本没有实现好友或关注系统。项目重点放在问答内容、AI 首答、评论、收藏、推荐和后台治理上。如果后续扩展，可以新增 `follows` 表，用 `follower_id` 和 `followee_id` 表示关注关系，再增加关注列表和信息流推荐。

### 8.9 文件上传流程

当前项目已实现头像、问题图片和回答图片上传。

1. 前端触发什么操作  
   用户在用户中心上传头像，或在发帖/回答时选择图片。

2. 调用哪个接口  
   头像：`POST /api/users/me/avatar`  
   问题图片：`POST /api/questions/{question_id}/images`  
   回答图片：`POST /api/answers/{answer_id}/images`

3. 后端如何处理  
   `media.py` 用 `UploadFile` 读取文件，并限制最大大小。`MediaService` 校验 MIME 类型、大小和用户权限。

4. 后端如何访问数据库  
   `MediaRepository.create_media_asset` 插入 `media_assets`，二进制内容写入 `file_content` BLOB。

5. 数据库发生什么变化  
   `media_assets` 新增记录。头像上传还会更新 `users.avatar_media_id`。

6. 后端返回什么数据  
   返回媒体 ID、地址、类型、大小、状态和时间。

7. 前端如何展示结果  
   前端使用 `public_url`，即 `/api/media/files/{file_name}` 加载图片。

8. 可能出现哪些异常情况  
   未登录、文件为空、文件过大、类型不是 JPEG/PNG/WebP、不是作者无权上传或删除。

# 九、安全性设计及原理

### 9.1 密码是否加密存储

是。项目使用 bcrypt 哈希密码。

真实代码：

- `app/services/auth_service.py`
- `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`
- 注册时 `pwd_context.hash(payload.password)`
- 登录时 `pwd_context.verify(payload.password, user["password_hash"])`

答辩时可以这样说：

> 数据库中不保存明文密码，而是保存 bcrypt 哈希。bcrypt 会自动加盐，并且计算成本较高，可以降低密码泄露后的暴力破解风险。

### 9.2 是否使用 JWT、session 或 cookie

当前使用 JWT Bearer Token，不使用服务端 session。

优势：

- 后端无状态。
- API 调用方便。
- 适合 Web 和桌面壳共同访问。

风险：

- token 一旦泄露，在过期前可能被冒用。
- 当前项目未实现刷新 token 和主动失效黑名单。

### 9.3 接口是否做权限校验

是。写接口和管理员接口通过 `Depends` 校验。

例子：

- 发帖：`get_current_user_id`
- 上传图片：`get_current_user`
- 管理员后台：`get_admin_user`
- 用户中心路径：`ensure_path_user_access`

### 9.4 是否防止 SQL 注入

项目中 SQL 使用绑定变量，而不是直接拼接用户输入到 SQL 中。例如：

```python
WHERE username = :1
```

或：

```python
WHERE q.question_id = :question_id
```

这可以有效降低 SQL 注入风险。需要注意的是，有些动态 SQL 会拼接过滤片段或 IN 占位符，但值仍然通过绑定变量传入。

### 9.5 是否防止 XSS

项目有一定 XSS 防护：

- `app/main.py` 设置 Content-Security-Policy。
- 前端多个页面有 `escapeHtml` 函数。
- `detail.html` 中 Markdown 渲染后有 `sanitizeRenderedHtml` 清洗逻辑。

但当前项目仍有风险：

- 前端原生字符串模板较多，如果后续新增渲染逻辑忘记转义，可能引入 XSS。
- CSP 中允许 `'unsafe-inline'`，这是为了兼容当前内联脚本，但生产环境安全性不够强。

### 9.6 是否做输入校验

是。校验位置包括：

- Pydantic schema，例如 `Field(min_length=1, max_length=200)`。
- Service 层业务校验。
- 数据库检查约束，例如 `ck_users_role`、`ck_questions_status`、`ck_answer_feedback_rating`。

### 9.7 是否保护敏感环境变量

项目使用 `.env` 管理敏感配置，`.env.example` 只提供示例值。敏感项包括：

- `APP_USER_PASSWORD`
- `JWT_SECRET_KEY`
- `DEEPSEEK_API_KEY`
- `ORACLE_PWD`

`app/core/settings.py` 会读取这些环境变量。

### 9.8 是否配置 CORS

是。`app/main.py` 使用 `CORSMiddleware`，允许来源从 `CORS_ALLOW_ORIGINS` 配置中读取。默认包括：

- `http://127.0.0.1:8000`
- `http://localhost:8000`
- Tauri 相关来源

### 9.9 当前项目存在的安全风险

| 风险 | 说明 | 改进方向 |
|---|---|---|
| CSP 允许 `unsafe-inline` | 为兼容内联 HTML 脚本，但生产安全性一般 | 拆分独立 JS 文件，使用 nonce 或 hash |
| JWT 无刷新和主动吊销机制 | token 泄露后过期前可被使用 | 增加 refresh token、黑名单或 token 版本号 |
| 邮箱和手机号格式校验较弱 | 当前主要做长度和重复检查 | 增加格式校验 |
| 不存在用户名登录失败无法写入 `login_log` | `login_log.user_id` 非空，未知用户没有 ID | 设计匿名登录失败日志表或允许 user_id 为空 |
| 缺少媒体审核 | 图片上传后直接可显示 | 增加审核状态、管理员审核接口 |
| 缺少自动化安全测试 | 当前没有正式 pytest 套件 | 增加 Auth、权限、上传相关测试 |

### 9.10 答辩时如何解释安全设计

答辩时可以这样说：

> 项目安全主要分为四层：第一，密码用 bcrypt 哈希存储；第二，登录后使用 JWT 识别身份；第三，后端用依赖注入保护接口，管理员接口还会检查角色；第四，数据库层通过外键、唯一约束和检查约束保证数据合法。同时项目配置了 CORS、CSP 和基础安全响应头。当前不足是 JWT 刷新、媒体审核和更严格 CSP 还可以继续增强。

# 十、性能优化设计及原理

### 10.1 前端如何减少重复渲染

当前项目是原生 JS，不存在虚拟 DOM。减少重复渲染主要通过：

- 分页加载列表。
- 只有切换模块时才请求对应数据。
- 管理后台 `admin.html` 中使用 section 状态切换，不是每次都刷新整个页面。
- 详情页按需加载评论和 AI 追问会话。

### 10.2 接口如何减少重复请求

项目中有一些按需加载策略：

- 评论面板展开时加载评论。
- AI 追问会话展开时加载会话。
- 用户中心不同标签页按需加载对应列表。
- 推荐生成需要用户主动触发。

### 10.3 数据库是否使用索引

是。`sql/create_tables.sql` 中创建了大量索引：

- `idx_questions_status`
- `idx_questions_ask_time`
- `idx_answers_question_id`
- `idx_favorites_user_id`
- `idx_browse_history_user_id`
- `idx_search_history_keyword`
- `idx_recommendations_user_id`
- `idx_user_tag_profile_user_id`

这些索引覆盖了列表、详情、用户中心、推荐等常用查询。

### 10.4 查询列表是否分页

是。问题列表、搜索、用户中心列表、管理员列表都支持分页。

后端常用参数：

- `page`
- `page_size`

SQL 中使用：

```sql
OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
```

### 10.5 静态资源如何处理

Web 页面由 FastAPI 的 `FileResponse` 返回：

- `app/web_routes.py`
- `_page_response`

页面响应设置了：

- `Cache-Control: no-store, max-age=0`
- `Pragma: no-cache`

这样开发和演示时页面不会被浏览器长期缓存。

### 10.6 是否存在 N+1 查询问题

当前项目部分地方存在潜在 N+1 查询风险。例如：

- `QuestionService._attach_answer_images` 对每个回答查询一次图片。
- 问题详情中回答较多时，可能产生多次媒体查询。

当前数据规模较小，课程演示可以接受。但生产环境可以优化为：

- 一次性按多个 `answer_id` 批量查询媒体。
- 后端组装 map 后批量挂载。

答辩时可以这样说：

> 当前项目已经做了分页和索引，但在回答图片挂载上还有潜在 N+1 查询。课程设计数据量小影响不明显，后续可以把多次单条查询优化成批量查询。

### 10.7 当前项目可以如何继续优化

- 前端拆分公共 JS，减少重复代码。
- 使用批量查询减少 N+1。
- 给热门问题、标签列表增加缓存。
- 启用 Oracle Text 全文索引，提高搜索性能。
- 图片从数据库 BLOB 改为对象存储，数据库只保存元数据。
- 增加异步任务处理 AI 调用，避免请求阻塞。
- 增加自动化测试和性能压测。

# 十一、部署与运行原理

### 11.1 本地如何启动前端

Web 前端由 FastAPI 提供，不需要单独启动前端服务器。

```bash
# 进入项目根目录
cd /path/to/ai-qa-db-course-project

# 启动 FastAPI，前端页面和 API 都由这个服务提供
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/login
http://127.0.0.1:8000/home
http://127.0.0.1:8000/me
http://127.0.0.1:8000/admin
```

### 11.2 本地如何启动后端

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

命令解释：

- `pip install -r requirements.txt`：安装 FastAPI、oracledb、OpenAI SDK、JWT、bcrypt 等依赖。
- `uvicorn app.main:app`：启动 FastAPI 应用。
- `--reload`：代码变更后自动重载，适合开发环境。
- `--host 0.0.0.0`：允许局域网访问。
- `--port 8000`：监听 8000 端口。

### 11.3 数据库如何启动

`compose.yaml` 定义了 Oracle 容器：

```bash
# 复制环境变量示例
cp .env.example .env

# 启动 Oracle 容器
docker compose up -d oracle26ai
```

如果在 Windows PowerShell 环境，项目提供了脚本：

```powershell
# 启动 Oracle 26ai
.\scripts\start-oracle26ai.ps1
```

### 11.4 Docker 是否参与部署

是。Docker 主要用于启动 Oracle 数据库容器：

- 服务名：`oracle26ai`
- 镜像：`container-registry.oracle.com/database/free:${ORACLE_IMAGE_TAG:-23.26.1.0}`
- 端口：`${ORACLE_PORT:-1521}:1521`
- 数据卷：`oracle26ai-data`

FastAPI 本身当前没有 Dockerfile，主要通过本机 Python 环境运行。

### 11.5 环境变量如何配置

环境变量示例在 `.env.example`：

```bash
# 复制示例配置
cp .env.example .env
```

关键配置：

- `ORACLE_DB_HOST`
- `ORACLE_PORT`
- `ORACLE_SERVICE_NAME`
- `APP_USER`
- `APP_USER_PASSWORD`
- `JWT_SECRET_KEY`
- `DEEPSEEK_API_KEY`
- `CORS_ALLOW_ORIGINS`
- `SEARCH_USE_ORACLE_TEXT`

特别注意：

```text
JWT_SECRET_KEY=please-set-a-strong-random-secret-per-env
```

这个示例值不能用于真实运行。代码会检查 JWT 密钥长度和占位符。

### 11.6 GitHub 仓库如何管理

当前仓库使用 Git 管理。常用命令：

```bash
# 查看当前改动
git status

# 查看最近提交
git log --oneline -5

# 添加文档或代码
git add docs/问知社区AskWise技术说明与答辩手册.md

# 提交改动
git commit -m "docs: add defense technical handbook"
```

当前仓库中还存在桌面端打包相关说明和文档，`docs/current_status.md` 提到 GitHub Actions 可用于 Windows 桌面端安装包构建。

### 11.7 数据库迁移如何执行

项目提供 PowerShell 脚本：

```powershell
# 加载主 schema
.\scripts\load-oracle-schema.ps1

# 加载演示数据
.\scripts\load-seed-data.ps1

# 校验数据库结构
.\scripts\validate-oracle-schema.ps1
```

旧环境补跑迁移时：

```powershell
.\scripts\load-oracle-schema.ps1 -SqlFiles `
  sql/migrations/20260405_add_answers_user_id.sql `
  sql/migrations/20260405_add_answer_comments.sql `
  sql/migrations/20260422_add_media_assets.sql
```

命令解释：

- `load-oracle-schema.ps1`：把 SQL 文件执行到 Oracle。
- `load-seed-data.ps1`：导入固定演示数据。
- `validate-oracle-schema.ps1`：检查表、约束、视图、过程是否存在。

### 11.8 生产环境如何部署

当前项目已经有部署文档：

- `docs/aliyun_ecs_deployment.md`
- `docs/oracle_cloud_free_deployment.md`

生产环境基本思路：

1. 在服务器上准备 Oracle 数据库。
2. 配置 `.env`，使用强随机 `JWT_SECRET_KEY` 和真实 `DEEPSEEK_API_KEY`。
3. 安装 Python 依赖。
4. 用 `uvicorn` 或进程管理工具启动 FastAPI。
5. 使用 Nginx 反向代理到 FastAPI。
6. 配置 HTTPS。
7. 定期备份数据库。

答辩时可以这样说：

> 本地开发时我用 uvicorn 直接运行，数据库通过 Docker 启动。生产环境建议用 Nginx 反向代理 FastAPI，并配置 HTTPS 和强密钥。Oracle 数据库需要单独部署和备份，环境变量不应提交到 Git。

# 十二、项目亮点、不足与改进方向

### 12.1 项目亮点

1. 前后端数据库闭环完整  
   用户从页面操作到数据库写入再返回页面展示，链路完整。

2. 数据库设计较完整  
   包含主键、外键、唯一约束、检查约束、索引、视图、触发器和存储过程。

3. 引入 AI 首答和 AI 自动标签  
   通过 DeepSeek 和 OpenAI 兼容 SDK 实现。

4. 推荐系统不是假数据  
   使用 `user_tag_profile`、`recommendations` 和 PL/SQL 过程生成推荐。

5. 权限控制较清晰  
   普通用户和管理员分开，受保护接口由后端校验。

6. 图片上传真实落库  
   使用 Oracle BLOB 存储头像、问题图和回答图。

7. 管理后台可演示  
   用户治理、分类管理、标签治理、内容治理和日志查看都具备基础能力。

8. 有桌面端形态  
   `desktop/` 使用 Tauri 作为轻量客户端壳。

### 12.2 项目不足

1. 当前项目未实现好友或关注系统。
2. 当前项目未实现通知、站内信、消息提醒。
3. 当前项目未实现评论图片。
4. 当前项目未实现媒体审核后台。
5. 当前项目未实现推荐规则人工干预。
6. 当前项目未实现标签合并和批量审核。
7. 当前仓库未发现正式 pytest 单元测试目录。
8. JWT 缺少刷新和主动失效机制。
9. 前端是原生 HTML，公共 JS 复用和工程化程度有限。
10. 部分详情数据存在潜在 N+1 查询优化空间。

### 12.3 后续改进方向

- 增加好友系统或关注系统。
- 增加通知、站内信和消息提醒。
- 增加评论图片。
- 增加媒体审核状态和后台审核入口。
- 增加推荐规则人工干预。
- 增加标签合并、批量审核和标签质量治理。
- 增加 pytest 自动化测试。
- 增加生产级 Dockerfile 和 CI/CD。
- 优化图片存储，把 BLOB 改为对象存储。
- 将前端拆分成模块化 JS 或迁移到 Vue/React。

答辩时可以这样说：

> 项目当前是可演示的 MVP，重点是把社区核心链路、AI 问答、推荐和数据库设计跑通。后续如果继续做成生产级系统，我会优先补通知、关注、媒体审核、自动化测试和部署工程化。

# 十三、答辩问答准备

Q1：为什么你的项目叫全栈项目？  
A1：因为它覆盖了前端页面、后端接口、数据库设计和部署运行。用户在前端操作，后端处理业务逻辑，Oracle 数据库存储数据，三层之间有完整的数据流。

Q2：前端和后端是如何通信的？  
A2：前端使用浏览器原生 `fetch` 调用 FastAPI 提供的 HTTP 接口。普通读接口返回 JSON，图片接口返回二进制内容，登录后需要在请求头中携带 `Authorization: Bearer <token>`。

Q3：你的前端用了什么技术？  
A3：主要是原生 HTML、CSS、JavaScript。页面在 `app/web/` 下，FastAPI 负责返回 HTML 文件，页面内部再用 JavaScript 请求后端 API。

Q4：你的项目是不是 React 项目？  
A4：不是。当前项目没有使用 React，所以没有真正的 props、state、hooks。它使用原生 JavaScript 的函数和状态对象组织页面逻辑。

Q5：前端路由怎么实现？  
A5：页面路由由 FastAPI 提供，比如 `/home` 返回 `home.html`，`/questions/{question_id}` 返回 `detail.html`。页面内部用 URL 参数控制筛选、推荐、热榜等状态。

Q6：后端为什么选择 FastAPI？  
A6：FastAPI 适合快速构建 REST API，支持依赖注入、Pydantic 参数校验和自动文档。项目中的路由、鉴权依赖和响应模型都能很好地配合。

Q7：后端代码怎么分层？  
A7：路由层在 `app/api/routes/`，业务层在 `app/services/`，数据库访问层在 `app/repositories/`。这样可以让 HTTP 处理、业务规则和 SQL 解耦。

Q8：数据库用的是什么？  
A8：使用 Oracle AI Database 26ai Free，数据库脚本在 `sql/` 目录，包括建表、过程、触发器、视图、种子数据和迁移脚本。

Q9：你的用户表有哪些关键字段？  
A9：`users` 表包含 `user_id`、`username`、`password_hash`、`nickname`、`role`、`status`、`register_time`、`last_login_time`、`avatar_media_id`。

Q10：密码是明文存储吗？  
A10：不是。注册时使用 bcrypt 哈希后存入 `password_hash`，登录时用 bcrypt verify 校验用户输入和哈希是否匹配。

Q11：登录认证用 session 还是 JWT？  
A11：使用 JWT。后端登录成功后签发 token，前端保存 token，之后请求受保护接口时放到 Authorization 请求头中。

Q12：后端怎么知道当前用户是谁？  
A12：后端在 `auth_deps.py` 中解析 JWT，读取 `sub` 字段得到用户 ID，然后查询 `users` 表，并检查用户状态是否为 `ACTIVE`。

Q13：为什么不能只在前端判断登录？  
A13：因为前端代码可以被用户修改，也可以绕过页面直接调用接口。真正的权限必须在后端校验。

Q14：管理员权限怎么控制？  
A14：管理员接口依赖 `get_admin_user`，它会先校验 JWT，再检查当前用户 `role` 是否为 `ADMIN`。不是管理员会返回 403。

Q15：问题和标签是什么关系？  
A15：多对多关系。一个问题可以有多个标签，一个标签也能属于多个问题，通过中间表 `question_tags` 实现。

Q16：评论楼中楼怎么设计？  
A16：评论表 `answer_comments` 使用自引用字段 `parent_comment_id` 和 `root_comment_id`，一级评论没有父评论，回复评论会指向父评论和根评论。

Q17：点赞功能怎么实现？  
A17：当前点赞是对回答进行反馈，写入 `answer_feedback` 表。触发器会自动刷新 `answers` 表中的 `like_count`、`dislike_count` 和 `avg_rating`。

Q18：收藏怎么实现？  
A18：收藏记录存在 `favorites` 表，`user_id` 和 `question_id` 有唯一约束，防止同一个用户重复收藏同一个问题。

Q19：项目如何实现推荐？  
A19：系统先根据用户提问、回答、收藏、浏览、反馈、评论和搜索历史生成 `user_tag_profile`，再通过 `qa_app_pkg.generate_recommendations` 生成 `recommendations`。

Q20：AI 首答怎么实现？  
A20：用户调用 `/api/questions/ask` 后，后端先创建问题，再通过 `AIAnswerService` 调用 DeepSeek，生成回答并写入 `answers` 表，同时把 prompt 和响应写入 `ai_prompt_log`。

Q21：AI 自动标签怎么实现？  
A21：如果用户没有选择标签且开启 `auto_tag`，`AITaggingService` 会把问题标题、内容和已有标签发给 DeepSeek，让模型返回 JSON 标签候选，再绑定到 `question_tags`。

Q22：文件上传怎么实现？  
A22：前端用 multipart 上传，后端用 FastAPI `UploadFile` 读取，`MediaService` 校验类型和大小，然后写入 `media_assets` 表的 BLOB 字段。

Q23：图片为什么不存磁盘？  
A23：当前项目选择存入 Oracle BLOB，便于课程设计中展示数据库对多媒体数据的管理。生产环境可以改成对象存储，数据库只存 URL 和元数据。

Q24：项目如何防止 SQL 注入？  
A24：SQL 查询使用绑定变量，例如 `:question_id`、`:user_id`，不是把用户输入直接拼进 SQL。

Q25：项目如何防止 XSS？  
A25：项目配置了 CSP，前端也有 HTML 转义和 Markdown 清洗逻辑。但当前仍允许内联脚本，生产环境应进一步拆分 JS 并收紧 CSP。

Q26：为什么要分页？  
A26：分页可以避免一次返回大量数据，减少数据库压力、网络传输和前端渲染压力。项目列表接口普遍支持 `page` 和 `page_size`。

Q27：索引有什么作用？  
A27：索引可以提高查询速度。比如问题列表经常按状态、分类和时间查询，所以在 `questions` 表上建立了相关索引。

Q28：触发器有什么作用？  
A28：触发器用于自动维护统计字段。例如回答新增或软删除后会重算 `questions.answer_count`，收藏和浏览变化后会调用过程同步收藏数、浏览数。

Q29：存储过程有什么作用？  
A29：项目把统计同步、用户画像重建、推荐生成等靠近数据的逻辑放在 PL/SQL 包 `qa_app_pkg` 中执行，减少后端重复计算。

Q30：项目如何部署？  
A30：本地用 Docker 启动 Oracle，用 uvicorn 启动 FastAPI。Web 页面由 FastAPI 提供。生产环境建议用 Nginx 反向代理 FastAPI，并配置 HTTPS、强密钥和数据库备份。

Q31：当前项目有没有好友功能？  
A31：没有。当前项目未实现好友或关注系统，也没有对应数据表和接口。后续可以增加 `follows` 表实现关注关系。

Q32：当前项目有什么不足？  
A32：主要不足包括没有好友/关注、没有通知、没有评论图片、没有媒体审核、没有正式 pytest 测试、JWT 缺少刷新和主动失效机制。

Q33：你最满意的设计是什么？  
A33：我比较满意数据库和业务闭环设计。它不是只做 CRUD，还包括触发器统计、用户画像、推荐结果、AI 日志和管理员审计，比较适合数据库课程答辩。

Q34：如果老师让你现场演示，你会演示什么？  
A34：我会演示注册登录、发布问题、AI 首答、人工回答、评论、收藏、点赞、用户中心推荐和管理员后台治理，这些能覆盖前端、后端和数据库。

Q35：如果 DeepSeek API 不可用怎么办？  
A35：普通社区发帖仍然可以使用；AI 首答、AI 自动标签和 AI 追问会受到影响。答辩时可以说明这是外部服务依赖，后续可以增加 mock 或异步重试机制。

# 十四、核心代码注释辅助理解

### 14.1 前端核心组件：管理员后台模块切换

文件路径：`app/web/admin.html`

关键代码片段：

```javascript
function switchSection(section) {
    state.currentSection = section; // 保存当前后台模块，比如 users、tags、logs

    document.querySelectorAll('.nav-button').forEach(button => {
        button.classList.toggle('active', button.dataset.section === section);
    });

    document.querySelectorAll('.section').forEach(panel => {
        panel.classList.toggle('active', panel.id === `${section}-section`);
    });

    const [title, desc] = sectionMeta[section] || sectionMeta.overview;
    document.getElementById('section-title').textContent = title;
    document.getElementById('section-desc').textContent = desc;

    loadSection(section); // 切换后加载对应模块的数据
}
```

为什么这样写：

- 当前项目没有 React/Vue，所以通过 DOM class 切换实现模块显示隐藏。
- `state.currentSection` 相当于页面状态。
- `loadSection` 按需请求后端接口，避免一次加载所有后台数据。

老师可能追问：

- 这是不是组件化？  
  可以回答：不是框架级组件化，而是用函数封装模块切换和渲染逻辑，是原生 JS 的轻量组件化思想。

### 14.2 API 请求代码：管理员请求统一携带 token

文件路径：`app/web/admin.html`

关键代码片段：

```javascript
async function adminFetch(path, options = {}) {
    const token = getAccessToken();
    if (!token) {
        redirectToLogin('请先登录管理员账号。');
        throw new Error('Missing token');
    }

    const headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`, // 管理员接口必须带 JWT
    };

    const response = await fetch(buildApiUrl(path, params), {
        ...options,
        headers,
    });

    if (!response.ok) {
        throw new Error('请求失败');
    }

    return response.json();
}
```

为什么这样写：

- 管理员后台所有接口都需要鉴权。
- 封装 `adminFetch` 可以避免每个请求重复写 token 逻辑。
- 如果 token 缺失或失效，前端可以统一跳转登录。

老师可能追问：

- 只在前端加 token 是否安全？  
  回答：不够。真正安全依赖后端 `get_admin_user` 校验 token 和角色。

### 14.3 后端路由代码：发布 AI 首答问题

文件路径：`app/api/routes/questions.py`

关键代码片段：

```python
@router.post(
    "/ask",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_question(
    payload: AskQuestionRequest,
    current_user_id: int = Depends(get_current_user_id), # 必须登录
    service: QuestionService = Depends(get_question_service),
) -> QuestionDetailResponse:
    try:
        normalized_payload = payload.model_copy(
            update={
                "user_id": resolve_authenticated_user_id(
                    current_user_id=current_user_id,
                    requested_user_id=payload.user_id,
                )
            }
        )
        return service.ask_question(normalized_payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
```

为什么这样写：

- `Depends(get_current_user_id)` 保护接口，未登录不能 AI 提问。
- `resolve_authenticated_user_id` 防止用户伪造 `user_id`。
- 路由层只负责参数和鉴权，真正业务交给 `QuestionService`。

老师可能追问：

- 为什么 payload 里还有 `user_id`？  
  回答：这是为了兼容旧接口，但后端会强制它必须和当前 JWT 用户一致，不能随便冒用。

### 14.4 登录认证代码：JWT 签发

文件路径：`app/services/auth_service.py`

关键代码片段：

```python
if not pwd_context.verify(payload.password, user["password_hash"]):
    self._record_failed_login(rate_limit_key)
    self._log_login_attempt(
        connection=connection,
        user_id=user["user_id"],
        ip_address=ip_address,
        result="FAILURE",
    )
    connection.commit()
    raise ValidationError("用户名或密码错误")

expire = datetime.utcnow() + timedelta(minutes=access_token_expire_minutes)
to_encode = {"sub": str(user["user_id"]), "exp": expire}
encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
```

中文注释：

- `pwd_context.verify`：验证用户输入密码和数据库哈希是否匹配。
- `_record_failed_login`：记录内存中的失败次数，用于限流。
- `exp`：JWT 过期时间。
- `sub`：JWT 主体，这里保存用户 ID。

为什么这样写：

- 密码不明文比较，而是通过 bcrypt 校验。
- JWT 中只放必要信息，后端每次再从数据库加载用户。
- 登录失败写日志并限流，降低暴力破解风险。

老师可能追问：

- JWT 里为什么不直接放角色？  
  回答：可以放，但本项目每次会从数据库重新加载用户，这样用户被禁用或角色变更后能更快生效。

### 14.5 JWT 校验代码：加载当前用户

文件路径：`app/api/auth_deps.py`

关键代码片段：

```python
payload = jwt.decode(
    credentials.credentials,
    secret_key,
    algorithms=[algorithm],
)
subject = payload.get("sub")
if subject is None:
    raise ValueError("Missing sub claim.")
return int(subject)
```

```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    user_id = _decode_current_user_id(credentials, required=True)
    assert user_id is not None
    return _ensure_current_user_is_active(_load_current_user(user_id))
```

为什么这样写：

- 先解码 JWT，得到用户 ID。
- 再查数据库加载用户。
- 再检查用户状态是否 `ACTIVE`。
- 如果 token 无效、过期或用户状态异常，就拒绝请求。

老师可能追问：

- 用户锁定后旧 token 还能用吗？  
  回答：不能继续访问受保护接口，因为后端每次会查数据库并检查用户状态。

### 14.6 数据库连接代码：Oracle 连接池

文件路径：`app/db/connection.py`

关键代码片段：

```python
_pool: oracledb.ConnectionPool | None = None
_pool_lock = Lock()

def _get_pool() -> oracledb.ConnectionPool:
    global _pool
    settings = get_settings()

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = oracledb.create_pool(
                    user=settings.app_user,
                    password=settings.app_user_password,
                    dsn=settings.oracle_dsn,
                    min=settings.oracle_pool_min,
                    max=settings.oracle_pool_max,
                    increment=settings.oracle_pool_increment,
                )
    return _pool
```

```python
@contextmanager
def get_connection() -> Iterator[oracledb.Connection]:
    connection = _get_pool().acquire()
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
```

为什么这样写：

- 连接池复用数据库连接，减少频繁创建连接成本。
- `Lock` 保证多线程下只初始化一次连接池。
- 上下文管理器保证异常时 rollback，结束时关闭连接。

老师可能追问：

- `connection.close()` 是不是关闭数据库连接？  
  回答：在连接池模式下通常是把连接归还给连接池，而不是销毁物理连接。

### 14.7 核心 SQL：问题表和回答表关系

文件路径：`sql/create_tables.sql`

关键代码片段：

```sql
CREATE TABLE questions (
    question_id      NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY,
    user_id          NUMBER             NOT NULL,
    category_id      NUMBER             NOT NULL,
    title            VARCHAR2(200 CHAR) NOT NULL,
    content          CLOB               NOT NULL,
    status           VARCHAR2(20 CHAR)  DEFAULT 'OPEN' NOT NULL,
    accepted_answer_id NUMBER,
    view_count       NUMBER             DEFAULT 0       NOT NULL,
    favorite_count   NUMBER             DEFAULT 0       NOT NULL,
    answer_count     NUMBER             DEFAULT 0       NOT NULL,
    CONSTRAINT pk_questions PRIMARY KEY (question_id),
    CONSTRAINT fk_questions_user
        FOREIGN KEY (user_id) REFERENCES users (user_id),
    CONSTRAINT fk_questions_category
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
);
```

```sql
CREATE TABLE answers (
    answer_id          NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY,
    question_id        NUMBER             NOT NULL,
    user_id            NUMBER,
    answer_type        VARCHAR2(20 CHAR)  NOT NULL,
    content            CLOB               NOT NULL,
    like_count         NUMBER             DEFAULT 0       NOT NULL,
    dislike_count      NUMBER             DEFAULT 0       NOT NULL,
    CONSTRAINT pk_answers PRIMARY KEY (answer_id),
    CONSTRAINT fk_answers_question
        FOREIGN KEY (question_id) REFERENCES questions (question_id),
    CONSTRAINT ck_answers_type CHECK (answer_type IN ('AI', 'MANUAL', 'SYSTEM'))
);
```

为什么这样写：

- 一个问题可以有多个回答，所以 `answers.question_id` 外键指向 `questions.question_id`。
- `answer_type` 区分 AI 回答、人工回答和系统回答。
- `content` 使用 CLOB，适合较长文本。
- 统计字段保存在 `questions` 和 `answers` 中，方便列表展示。

老师可能追问：

- 为什么回答表中 `user_id` 可以为空？  
  回答：因为 AI 回答和系统回答不是普通用户发布的，只有人工回答要求 `user_id` 不为空。

### 14.8 核心 SQL：触发器同步统计

文件路径：`sql/triggers.sql`

关键代码片段：

```sql
CREATE OR REPLACE TRIGGER trg_answer_feedback_refresh_stats
FOR INSERT OR UPDATE OF answer_id, is_like, rating OR DELETE ON answer_feedback
COMPOUND TRIGGER
    AFTER STATEMENT IS
    BEGIN
        FOR i IN 1 .. g_count LOOP
            qa_app_pkg.refresh_answer_feedback_stats(g_answer_ids(i));
        END LOOP;
    END AFTER STATEMENT;
END trg_answer_feedback_refresh_stats;
/
```

为什么这样写：

- 当 `answer_feedback` 改变时，自动重新统计回答点赞数、点踩数和平均评分。
- 使用 compound trigger 可以避免逐行触发时重复执行大量统计。
- 统计逻辑放在 `qa_app_pkg.refresh_answer_feedback_stats` 中，便于复用。

老师可能追问：

- 为什么不用后端每次手动更新？  
  回答：放在数据库触发器中可以保证无论哪个入口修改反馈表，统计字段都会保持一致。

### 14.9 核心 SQL：推荐生成过程

文件路径：`sql/procedures.sql`

关键代码片段：

```sql
PROCEDURE rebuild_user_tag_profile(
    p_user_id IN users.user_id%TYPE
) IS
BEGIN
    DELETE FROM user_tag_profile
     WHERE user_id = p_user_id;

    INSERT INTO user_tag_profile (
        user_id,
        tag_id,
        weight,
        update_time
    )
    SELECT p_user_id,
           src.tag_id,
           LEAST(ROUND(SUM(src.weight), 2), 99.99),
           SYSDATE
      FROM (
          -- 提问、回答、收藏、浏览、反馈、评论、搜索都会贡献标签权重
      ) src
     GROUP BY src.tag_id
    HAVING SUM(src.weight) > 0;
END rebuild_user_tag_profile;
```

为什么这样写：

- 用户画像不是手写标签，而是根据行为计算。
- 行为包括提问、回答、收藏、浏览、反馈、评论、搜索。
- 权重越高表示用户越可能对该标签感兴趣。

老师可能追问：

- 推荐是不是机器学习？  
  回答：当前不是复杂机器学习模型，而是基于行为权重和标签匹配的规则型混合推荐。它可解释、适合课程设计，也方便在数据库中实现。

# 十五、最后答辩重点总结

### 15.1 最需要重点背熟的 10 个问题

1. 为什么这是一个全栈项目？
2. 前端、后端、数据库分别负责什么？
3. 登录认证为什么用 JWT？
4. 密码为什么不能明文保存，bcrypt 怎么起作用？
5. 后端如何防止用户伪造 `user_id`？
6. 问题、回答、评论、标签之间是什么表关系？
7. 收藏和点赞分别存在哪些表？
8. 推荐系统是怎么根据用户行为生成的？
9. 图片上传为什么存到 `media_assets` 表？
10. 当前项目有哪些未实现功能和改进方向？

### 15.2 老师最可能追问的 10 个技术细节

1. `Authorization: Bearer token` 的具体流程。
2. `get_current_user` 和 `get_admin_user` 的区别。
3. `questions` 和 `answers` 为什么是一对多。
4. `question_tags` 为什么是中间表。
5. `answer_comments` 如何实现楼中楼。
6. 触发器如何同步统计字段。
7. `qa_app_pkg` 为什么放在数据库里。
8. 分页 SQL 为什么能提升性能。
9. SQL 绑定变量如何防止注入。
10. BLOB 存图片的优缺点。

### 15.3 项目目前最容易被问到的不足

1. 当前项目未实现好友或关注系统。
2. 当前项目未实现通知和站内信。
3. 当前项目未实现评论图片。
4. 当前项目未实现媒体审核后台。
5. 当前项目未实现推荐规则人工干预。
6. 当前项目未实现标签合并和批量审核。
7. 当前项目未发现正式 pytest 单元测试套件。
8. JWT 缺少刷新和主动失效机制。
9. 前端没有使用框架，工程化和复用性有限。
10. 回答图片挂载存在潜在 N+1 查询优化空间。
