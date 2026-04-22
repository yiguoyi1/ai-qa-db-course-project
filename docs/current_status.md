# 当前项目现状

这份文档用于说明仓库在当前代码状态下已经完成了什么、哪些能力已经能演示、以及下一步最值得优先收口的地方。

如果你刚接手项目，建议阅读顺序：

1. [README.md](../README.md)
2. [docs/current_status.md](current_status.md)
3. [docs/README.md](README.md)
4. [docs/onboarding_checklist.md](onboarding_checklist.md)

## 1. 当前项目定位

当前项目已经不是单纯的数据库课程设计稿，而是一个可以本地运行的问答社区 MVP：

- 后端：`FastAPI`
- 数据库：`Oracle AI Database 26ai Free`
- AI 提供商：`DeepSeek`，通过 OpenAI 兼容 SDK 调用
- 网页前端：`app/web/` 下的静态 HTML 页面
- 测试前端：`frontend_cli/` 下的独立 CLI

项目主线是：

- 用户注册、登录
- 用户发布问题
- 可选触发 AI 首答
- 用户继续发布人工回答
- 用户搜索、浏览、收藏、点赞/点踩
- 系统根据行为生成推荐

## 2. 当前已完成功能

### 2.1 数据库与基础设施

- Oracle 26ai Docker 本地运行方案
- 完整业务 schema、主外键、唯一约束、检查约束、索引
- 统计同步触发器
- 推荐相关包与过程 `qa_app_pkg`
- 种子数据导入与结构校验脚本

### 2.2 后端 API

- `GET /health`
- 用户注册：`POST /api/auth/register`
- 用户登录：`POST /api/auth/login`
- AI 首答提问：`POST /api/questions/ask`
- 纯社区式发帖：`POST /api/questions`
- 问题列表与详情：`GET /api/questions`、`GET /api/questions/{question_id}`
- 人工回答：`POST /api/questions/{question_id}/answers`
- 分类、标签、搜索：`GET /api/categories`、`GET /api/tags`、`GET /api/search/questions`
- 搜索历史：`GET /api/search/history`
- 浏览、收藏：`POST /api/questions/{question_id}/browse`、`POST /api/questions/{question_id}/favorite`、`DELETE /api/questions/{question_id}/favorite`
- 回答反馈与状态回显：`POST /api/answers/{answer_id}/feedback`、`POST /api/questions/answers/{answer_id}/feedback`、`GET /api/questions/{question_id}/feedbacks`
- 评论与楼中楼：`POST /api/answers/{answer_id}/comments`、`GET /api/answers/{answer_id}/comments`、`DELETE /api/comments/{comment_id}`
- 用户画像与推荐：`POST /api/users/{user_id}/profile/rebuild`、`POST /api/users/{user_id}/recommendations/generate`、`GET /api/users/{user_id}/recommendations`

### 2.3 网页前端

当前仓库已经包含可直接打开的静态网页前端，位于 `app/web/`：

- [app/web/login.html](../app/web/login.html)
  - 登录
  - 注册
  - 登录成功后将 `access_token`、`user_id`、`username` 保存到 `localStorage`
- [app/web/home.html](../app/web/home.html)
  - 首页问题流
  - 搜索问题
  - 搜索历史下拉
  - 发帖弹窗
  - 可切换“纯社区发帖”与“发帖并触发 AI 首答”
  - 登录态展示与退出登录
- [app/web/detail.html](../app/web/detail.html)
  - 问题详情
  - 回答列表
  - Markdown 渲染与代码高亮
  - 发布人工回答
  - 点赞 / 点踩
  - 当前用户反馈状态回显

### 2.4 CLI 测试前端

- `frontend_cli/` 仍然保留，适合验证接口和回归测试
- `scripts/start_business_test.py` 可以自动检查 `/health` 并拉起 CLI 菜单

## 3. 当前最值得先改的地方

### 3.1 第一优先级：统一接口契约与鉴权方式

当前后端已经开始接入 JWT 登录态，但仍处于“新旧接口并存”阶段，主要表现为：

- `POST /api/answers/{answer_id}/feedback` 与 `POST /api/questions/answers/{answer_id}/feedback` 同时存在
- 部分接口通过 JWT 取 `user_id`
- 部分接口仍显式传 `user_id`
- `get_current_user_id` 放在 `questions.py` 中，并被其他路由反向 import

这会带来三个问题：

- 前端和 CLI 很难形成统一调用规范
- 路由职责变得混杂
- 后续继续扩展用户中心和权限控制时会更难收口

建议优先动作：

1. 把登录鉴权依赖抽到独立的 `deps/auth.py` 或类似位置
2. 明确哪些接口必须走 JWT，哪些接口保留显式 `user_id`
3. 统一回答反馈入口，只保留一套主路由
4. 清理 `questions.py` 中混入的非问题资源逻辑

### 3.2 第二优先级：把网页前端纳入统一交付方式

当前网页前端已经可以演示，但还没有和 FastAPI 统一托管，存在这些问题：

- `app/web/` 页面默认直接写死请求 `http://127.0.0.1:8000`
- 页面不是通过 FastAPI 静态文件或模板路由提供
- 热门标签仍是写死的展示数据

建议优先动作：

1. 用 FastAPI 静态文件或模板方式托管 `app/web/`
2. 把 API base URL 抽成统一配置
3. 用真实标签接口替换首页右侧硬编码热门标签

### 3.3 第三优先级：修正“发帖体验”和后端约束之间的错位

当前首页发帖弹窗已经很好用了，但仍有一个明显错位：

- UI 上“详细描述”显示为可选
- AI 开关默认开启
- 但 `POST /api/questions/ask` 的 `content` 仍要求非空

这意味着：

- 用户如果直接用默认开关发帖且不填正文，会收到校验错误

建议优先动作：

1. 要么把 AI 发帖时的正文改为必填并给出前端提示
2. 要么放宽 `AskQuestionRequest.content` 的校验
3. 同时补上分类、标签选择，而不是前端固定写死 `category_id = 1`、`tag_ids = []`

### 3.4 第四优先级：收口安全与配置

当前登录功能已可演示，但还有明显的工程化缺口：

- `SECRET_KEY` 仍硬编码在 `auth_service.py`
- JWT 相关配置未进入 `.env`
- 登录、注册成功后的审计链路还没有完全和 `LOGIN_LOG` 打通

建议优先动作：

1. 把 JWT 密钥、算法、有效期挪到配置层
2. 在登录流程里补齐审计记录
3. 明确用户停用、锁定等状态的处理口径

### 3.5 第五优先级：补齐社区核心能力

当前最适合继续做的业务能力仍然是：

1. 采纳答案
2. 用户中心
3. 收藏、评论、推荐等功能的网页端入口
4. 多轮对话正式业务链

## 4. 当前仍未完成或未完全收口的能力

- 采纳答案
- 用户中心
- 网页端的评论、收藏、推荐等完整闭环
- 网页前端与后端的统一托管和统一配置
- 登录审计与权限边界收口
- 多轮对话正式业务链

## 5. 当前最稳妥的协作口径

现在最准确的项目描述应该是：

- 这是一个“带 AI 首答、行为记录、推荐能力、基础网页登录和静态网页前端”的问答社区 MVP
- CLI 和网页前端同时存在
- API 已经开始从“显式 `user_id` 测试模式”过渡到“JWT 登录态模式”，但还没有完全统一

如果后续继续开发，建议优先顺序为：

1. 统一路由与鉴权
2. 统一网页前端交付方式
3. 修正发帖与反馈的接口契约
4. 再补用户中心和采纳答案
