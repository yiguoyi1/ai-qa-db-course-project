# 项目文档总览

这份文档是给协作者的快速入口，帮助大家在最短时间内理解：

- 这个项目现在做到哪一步了
- 当前网页前端和 CLI 各自负责什么
- 代码主要分层和文件入口在哪里
- 哪些能力已经完成，哪些地方最值得优先收口

## 1. 先看哪几份文档

如果你刚接手这个仓库，建议按这个顺序看：

1. [README.md](../README.md)
2. [handoff.md](handoff.md)
3. [current_status.md](current_status.md)
4. [testing_guide.md](testing_guide.md)
5. [onboarding_checklist.md](onboarding_checklist.md)
6. [admin_governance_guide.md](admin_governance_guide.md)
7. [community_platform_design.md](design_details/community_platform_design.md)
8. [business_code_architecture.md](design_details/business_code_architecture.md)
9. [media_and_avatar_design.md](design_details/media_and_avatar_design.md)

## 2. 项目当前定位

当前项目已经不是纯数据库设计稿，而是一个可以本地运行的问答社区 MVP：

- 后端：`FastAPI`
- 数据库：`Oracle AI Database 26ai Free`
- AI 提供商：`DeepSeek`
- 网页前端：`app/web/` 下的静态页面
- 测试前端：`frontend_cli/` 下的独立 CLI

业务定位上，它是“问答社区 + AI 首答 + 行为记录 + 推荐”。

也就是说：

- 用户可以注册、登录
- 用户可以提问
- 系统可以生成 AI 首答
- 用户之间可以继续人工回答
- 用户可以搜索、浏览、收藏、点赞、点踩
- 系统可以根据行为数据生成推荐

## 3. 当前实现状态

### 3.1 已实现

- Oracle 26ai Docker 本地环境
- 建表、约束、索引、触发器、存储过程
- 固定业务 schema：`AI_QA_APP`
- 固定演示数据导入
- 注册 / 登录与 JWT 房卡发放
- 问题列表与问题详情
- AI 首答
- 纯社区发帖
- 用户人工回答
- 采纳答案
- 分类、标签、搜索、搜索历史
- 浏览、收藏、回答反馈
- 评论与楼中楼回复
- 用户画像重建与推荐生成
- 用户中心聚合接口与最近浏览 / 搜索历史
- 用户头像、问题配图、回答配图
- Oracle BLOB 媒体存储与 `/api/media/files/{file_name}` 读取入口
- 基于 AI 首答的多轮追问后端接口与自检脚本
- 由 FastAPI 提供入口的网页登录页、首页、详情页、用户中心页、管理员后台页
- 独立 CLI 业务测试入口

### 3.2 当前仍未完全收口

- 评论图片与媒体治理后台
- 鉴权过渡接口与历史兼容参数的进一步清理
- 多轮对话前端入口与页面交互

## 4. 当前最值得优先改的点

### 4.1 继续清理鉴权过渡接口

这一轮已经收掉双反馈入口和问题路由混杂逻辑，鉴权过渡层现在主要只剩少量写接口兼容字段。

### 4.2 继续增强社区与治理能力

最适合继续推进的仍然是：

1. 评论图片与媒体审核、治理后台
2. 多轮对话前端入口与页面交互
3. 鉴权过渡接口与历史兼容参数的进一步清理

### 4.3 完善后台管理与审计查询

当前登录审计已经能写入 `LOGIN_LOG`，用户状态口径也已经生效，管理员网页后台已经覆盖用户治理、分类管理、内容治理和审计日志查询。后续更值得继续补的是媒体审核、日志导出和推荐规则人工干预。

详细说明见：

- [current_status.md](current_status.md)

## 5. 仓库结构速览

### 5.1 数据库与部署

- `compose.yaml`：Oracle 26ai 容器定义
- `docker/oracle/startup/`：容器首次启动时执行的初始化脚本
- `sql/`：DDL、过程、触发器、演示数据、迁移脚本
- `scripts/`：启动容器、导入 schema、导入种子数据、业务测试入口

### 5.2 后端应用

- `app/api/routes/`：HTTP 路由层
- `app/services/`：业务编排层
- `app/repositories/`：数据库访问层
- `app/schemas/`：请求与响应模型
- `app/integrations/llm/`：AI 提供商接入
- `app/prompts/`：提示词模板

### 5.3 网页前端

- `app/web/login.html`
- `app/web/home.html`
- `app/web/detail.html`
- `app/web/profile.html`
- `app/web/admin.html`
- [chat_followup_api_guide.md](chat_followup_api_guide.md)

当前网页前端的作用是：

- 演示登录、首页流、详情页、用户中心和管理员后台交互
- 覆盖首页、详情页、用户中心的收藏主链路，以及管理员侧用户、分类、内容和日志治理
- 支持问题配图和回答配图上传，并在详情页正文下方展示
- 管理员后台提供中文友好的角色、状态和日志类型展示
- 管理员后台内容治理页可查询问题 ID、回答 ID、评论 ID，并一键填入治理表单
- 通过 FastAPI 统一页面入口访问，并用同源 HTTP 调后端接口
- 验证 JWT 登录态与页面交互是否能跑通

### 5.4 CLI 测试前端

- `frontend_cli/`：独立命令行前端

它的作用不是做正式 UI，而是：

- 验证业务逻辑能否跑通
- 作为独立调用方测试接口
- 避免直接在 Python 里绕过 API 调 service

## 6. 当前 API 主链路

### 6.1 认证

- `POST /api/auth/register`
- `POST /api/auth/login`

### 6.2 问题与回答

- `POST /api/questions/ask`
- `POST /api/questions`
- `GET /api/questions`
- `GET /api/questions/{question_id}`
- `POST /api/questions/{question_id}/answers`
- `POST /api/questions/{question_id}/accept-answer`

### 6.3 元数据与搜索

- `GET /api/categories`
- `GET /api/tags`
- `GET /api/search/questions`
- `GET /api/search/history`

### 6.4 社区行为

- `POST /api/questions/{question_id}/browse`
- `POST /api/questions/{question_id}/favorite`
- `DELETE /api/questions/{question_id}/favorite`
- `POST /api/answers/{answer_id}/feedback`
- `GET /api/questions/{question_id}/feedbacks`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`

### 6.5 推荐

- `GET /api/users/me/profile`
- `PATCH /api/users/me/profile`
- `GET /api/users/{user_id}/profile`
- `GET /api/users/{user_id}/questions`
- `GET /api/users/{user_id}/answers`
- `GET /api/users/{user_id}/favorites`
- `GET /api/users/{user_id}/browse-history`
- `GET /api/users/{user_id}/search-history`
- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`

### 6.6 头像与内容图片

- `POST /api/users/me/avatar`
- `GET /api/users/me/avatar`
- `DELETE /api/users/me/avatar`
- `POST /api/questions/{question_id}/images`
- `GET /api/questions/{question_id}/images`
- `DELETE /api/questions/{question_id}/images/{media_id}`
- `POST /api/answers/{answer_id}/images`
- `GET /api/answers/{answer_id}/images`
- `DELETE /api/answers/{answer_id}/images/{media_id}`
- `GET /api/media/files/{file_name}`

## 7. 当前关键业务规则

这几条是协作者最容易误解的地方，最好先统一口径：

- `POST /api/questions/ask` 不是“纯提问”，它会触发 AI 首答
- `POST /api/questions` 是纯社区发帖入口
- `POST /api/questions/{question_id}/accept-answer` 只允许提问者或管理员执行，并会把问题状态改成 `RESOLVED`
- 这两类发帖当前都要求正文 `content` 必填
- 当前网页前端和受保护写接口已经以 JWT 登录态为主
- 登录时会写 `LOGIN_LOG`，成功记 `SUCCESS`，密码错误/停用/未激活记 `FAILURE`，锁定账号记 `LOCKED`
- `USERS.STATUS` 当前口径是：`ACTIVE` 允许登录与继续访问，`INACTIVE` / `DISABLED` 拒绝登录与访问，`LOCKED` 拒绝登录与访问且单独记锁定审计
- 部分请求模型里仍保留 `user_id` 兼容字段，但服务端会校验它必须与当前登录用户一致
- `MANUAL` 回答代表社区用户回答，必须带真实 `user_id`
- `AI` / `SYSTEM` 回答不带 `user_id`
- 评论挂在回答下，不直接挂在问题下
- 评论允许自回复
- 评论不支持编辑
- 评论删除采用软删除，不级联子回复
- 头像、问题配图和回答配图统一写入 `MEDIA_ASSETS.FILE_CONTENT BLOB`
- 媒体访问统一通过 `/api/media/files/{file_name}` 读取 Oracle BLOB
- 推荐逻辑优先复用数据库里的 `qa_app_pkg`

## 8. 本地协作最常用的启动方式

### 8.1 启动数据库

```powershell
Copy-Item .env.example .env
.\scripts\start-oracle26ai.ps1
.\scripts\load-oracle-schema.ps1
.\scripts\load-seed-data.ps1
```

### 8.2 启动 API

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.3 体验网页前端

启动 API 后，直接访问：

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/home`
- `http://127.0.0.1:8000/me`
- `http://127.0.0.1:8000/admin`
- `http://127.0.0.1:8000/questions/62`

当前注意事项：

- 页面源码仍位于 `app/web/`
- 页面请求现在走同源 `/api/...`

### 8.4 一键进入 CLI 业务测试

```powershell
python .\scripts\start_business_test.py
```

## 9. 协作时最容易踩坑的点

- 不要把 `.env` 提交进 Git
- 不要在 Python 里手动维护浏览量、收藏数、回答数、点赞数、平均分，数据库已经有触发器
- 不要在应用层重复实现推荐算法，优先调用数据库过程
- 不要忽略网页前端和后端之间的接口错位
- 如果改了数据库约束，记得同步：
  - `sql/create_tables.sql`
  - `docs/design_details/constraints_and_rules.md`
  - 对应迁移脚本或验证脚本
- 如果改了业务接口，记得同步：
  - `README.md`
  - 本文档
  - `docs/current_status.md`
  - 相关设计文档

## 10. 文档地图

### 10.1 当前状态与协作入口

- [current_status.md](current_status.md)
- [handoff.md](handoff.md)
- [onboarding_checklist.md](onboarding_checklist.md)
- [admin_governance_guide.md](admin_governance_guide.md)

### 10.2 产品与业务设计

- [data_design.md](design_details/data_design.md)
- [community_platform_design.md](design_details/community_platform_design.md)
- [threaded_comment_design.md](design_details/threaded_comment_design.md)
- [media_and_avatar_design.md](design_details/media_and_avatar_design.md)

### 10.3 数据设计

- [data_tables.md](design_details/data_tables.md)
- [data_flow.md](design_details/data_flow.md)
- [constraints_and_rules.md](design_details/constraints_and_rules.md)
- [data_design_full.md](design_details/data_design_full.md)

### 10.4 工程协作

- [business_code_architecture.md](design_details/business_code_architecture.md)
- [code_and_file_standards.md](design_details/code_and_file_standards.md)
- [oracle-26ai-docker.md](setup/oracle-26ai-docker.md)
