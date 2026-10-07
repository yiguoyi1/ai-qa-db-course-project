# 问知社区 AskWise Community

问知社区是一个融合 AI 首答、用户互助、行为画像与个性化推荐的智能问答社区平台。

本仓库原工程名为 `ai-qa-db-course-project`，当前正式项目名统一为 **问知社区 AskWise Community**。

本项目自有源码采用 [MIT 许可证](LICENSE)。Oracle 容器镜像、DeepSeek API 和第三方依赖适用各自的许可或服务条款。

## 项目简介

本项目是一个面向数据库课程设计的智能问答社区 MVP，围绕“问答 + AI 辅助 + 用户行为 + 个性化推荐”构建完整的数据闭环。

当前仓库已经不只是数据库设计稿，而是同时包含：

- Oracle 26ai 数据库脚本与校验脚本
- FastAPI 后端
- 网页前端源码与页面入口
- Tauri 桌面客户端入口
- 独立 CLI 测试前端

如果你是新的协作者，建议先看：

- [docs/current_status.md](docs/current_status.md)
- [docs/README.md](docs/README.md)
- [docs/testing_guide.md](docs/testing_guide.md)
- [docs/security_update_configuration.md](docs/security_update_configuration.md)
- [docs/oracle_cloud_free_deployment.md](docs/oracle_cloud_free_deployment.md)
- [docs/aliyun_ecs_deployment.md](docs/aliyun_ecs_deployment.md)
- [docs/onboarding_checklist.md](docs/onboarding_checklist.md)
- [docs/chat_followup_api_guide.md](docs/chat_followup_api_guide.md)

## 当前已完成能力

### 1. 数据库与推荐闭环

- `sql/create_tables.sql`：建表、主外键、唯一约束、检查约束、索引
- `sql/procedures.sql`：统计同步、画像重建、推荐生成
- `sql/triggers.sql`：自动维护统计字段与登录时间
- `sql/views.sql`：问题概览、热门问题、回答质量、用户画像、推荐明细、标签明细、用户行为、媒体和 AI 追问汇总视图
- `sql/seed_data.sql`：固定演示数据
- `scripts/validate-oracle-schema.ps1`：结构和业务规则校验

### 2. FastAPI 后端

- 健康检查：`GET /health`
- 注册 / 登录：`POST /api/auth/register`、`POST /api/auth/login`
- AI 首答提问：`POST /api/questions/ask`
- 纯社区发帖：`POST /api/questions`
- 问题列表 / 详情：`GET /api/questions`、`GET /api/questions/{question_id}`
- 人工回答：`POST /api/questions/{question_id}/answers`
- 删除回答：`DELETE /api/answers/{answer_id}`
- 采纳答案：`POST /api/questions/{question_id}/accept-answer`
- 用户中心：`GET /api/users/me/profile`、`PATCH /api/users/me/profile`、`GET /api/users/{user_id}/profile`、`GET /api/users/{user_id}/questions`、`GET /api/users/{user_id}/answers`、`GET /api/users/{user_id}/favorites`
- 用户历史：`GET /api/users/{user_id}/browse-history`、`GET /api/users/{user_id}/search-history`
- 分类、标签、标签建议、搜索、搜索历史
- 浏览、收藏、反馈、评论
- 基于 AI 首答的多轮追问会话
- 用户画像重建与推荐生成
- 用户头像、问题配图、回答配图和 Oracle BLOB 媒体读取
- 管理员用户、分类、标签、内容和审计日志治理

### 3. 网页前端

当前仓库已经包含由 FastAPI 统一交付的网页前端，页面源码位于 `app/web/`：

- [app/web/index.html](app/web/index.html)
- [app/web/login.html](app/web/login.html)
- [app/web/home.html](app/web/home.html)
- [app/web/detail.html](app/web/detail.html)
- [app/web/profile.html](app/web/profile.html)
- [app/web/admin.html](app/web/admin.html)

当前推荐访问入口：

- `/`
- `/login`
- `/home`
- `/home?section=recommend`
- `/home?section=hot`
- `/me`
- `/admin`
- `/questions/{question_id}`

当前网页端已经实现：

- 产品介绍首页和立即体验入口
- 登录与注册
- 区分用户名 / 密码错误和服务异常的登录提示
- 登录审计写入 `LOGIN_LOG`
- 用户状态校验：只有 `ACTIVE` 用户可以登录并继续访问受保护接口
- 游客未登录可浏览首页、搜索、筛选、问题详情、回答、图片和公开评论
- 游客右上角固定显示登录按钮，发帖、收藏、回答、评论、反馈、AI 追问等操作要求登录
- 首页推荐 / 热榜问题流
- 分类、状态、标签筛选
- 全站搜索与搜索历史下拉
- 发布问题，支持手动分类或 AI 自动分类、已有标签、自定义标签、标签建议、AI 自动标签和问题配图
- 首页发帖正文统一必填
- 切换“纯社区发帖”与“AI 首答发帖”
- 首页热门标签动态加载
- 问题详情查看
- 问题配图和回答配图展示，当前用户可删除自己的图片
- Markdown 回答渲染与代码高亮
- 发布人工回答，支持回答配图
- 采纳答案与已采纳答案高亮
- 点赞 / 点踩、取消反馈与当前用户反馈状态回显
- 首页与详情页收藏 / 取消收藏
- 收藏状态与收藏数量回显
- 评论、楼中楼回复、默认折叠子回复和软删除占位
- AI 首答多轮追问会话入口、会话列表和消息展示
- 用户中心总览页
- 个人资料展示和修改、头像上传和删除
- 我的问题 / 我的回答 / 我的收藏 / 我的推荐，列表支持继续加载
- 最近浏览 / 最近搜索
- 兴趣画像重建与推荐刷新入口
- 管理员后台：总览、用户治理、分类管理、标签治理、内容治理、登录日志、操作日志
- 管理员后台中文化展示：角色、状态、日志类型在页面上显示为中文友好文案，提交给后端的枚举值保持不变
- 管理员内容 ID 查询：在内容治理页查看最近问题、回答 ID、评论 ID，并一键填入治理表单
- 管理员入口：管理员账号会在首页、详情页、用户中心看到“管理后台”入口
- 顶部导航、头像下拉菜单、卡片、按钮、标签、表单和弹窗已做企业级 UI/UX 统一优化
- 登录态展示与退出登录，退出后回到游客浏览模式

### 4. CLI 测试前端

仓库仍保留独立 CLI：

- `frontend_cli/main.py`
- `frontend_cli/api_client.py`
- `frontend_cli/config.py`
- `frontend_cli/render.py`

CLI 不直接依赖 `service` / `repository`，而是只通过 HTTP 调用 FastAPI，适合做接口回归和业务演示。

### 5. Tauri 桌面客户端

仓库新增桌面客户端工程：

- `desktop/`

桌面端是轻量客户端壳，不重写现有社区页面。安装包默认检测 `http://120.55.74.107/health`，后端可用后进入服务器 `/home` 社区首页；本地开发时可在启动页切回 `http://127.0.0.1:8000`。

常用命令：

```bash
cd desktop
npm install
npm run dev
```

如需让脚本尝试同时拉起 FastAPI 后端：

```bash
cd desktop
npm run dev:full
```

打包：

```bash
cd desktop
npm run build
```

macOS 构建产物位于 `desktop/src-tauri/target/release/bundle/`。

Windows 本地打包请在 Windows PowerShell 下执行：

```powershell
cd desktop
npm install
npm run build:windows
```

Windows 版会生成 NSIS `-setup.exe` 和 WiX `.msi`，产物位于 `desktop/src-tauri/target/release/bundle/`。

也可以通过 GitHub Actions 出 Windows 安装包：进入仓库的 `Actions` 页面，选择 `Build Windows Desktop Client`，手动运行后下载 Windows 桌面客户端安装包。

## 当前最值得先改的地方

基于当前代码现状，前几轮核心收口已经完成到可用状态：

- 受保护写接口已经以 JWT 登录态为主
- 少量 `user_id` 字段只保留过渡兼容与一致性校验
- CLI 已补充登录与 `Bearer Token` 透传能力
- 网页前端已经由 FastAPI 统一提供入口
- 页面请求已经改为同源 API，不再写死 `127.0.0.1:8000`
- 首页热门标签已经改为真实标签接口数据

这一轮已经继续收口了接口边界：

- 回答反馈写入口只保留 `POST /api/answers/{answer_id}/feedback`
- `questions.py` 已只保留问题资源本身
- 搜索读接口不再接受历史 `user_id` 查询参数
- 采纳答案已经完成前后端闭环

接下来最值得继续推进的是：

1. 补齐评论图片、通知联动和更细的社区互动细节。
2. 完善媒体审核、推荐规则干预、日志导出等后台治理深度能力。
3. 继续压缩 CLI 和少量写接口里的 `user_id` 过渡参数。

详细说明见：

- [docs/current_status.md](docs/current_status.md)

## 当前技术栈

- 后端：`FastAPI`
- 数据库：`Oracle AI Database 26ai Free`
- 数据库访问：`python-oracledb`
- AI 提供商：`DeepSeek`
- AI SDK：`OpenAI SDK`
- 配置管理：`.env`
- 网页前端：原生 HTML + CSS + JavaScript
- 测试前端：Python CLI

## 仓库结构速览

- `app/`
  - `api/`：HTTP 路由与依赖
  - `services/`：业务编排层
  - `repositories/`：数据库访问层
  - `schemas/`：请求与响应模型
  - `integrations/llm/`：AI 提供商接入
  - `prompts/`：提示词模板
  - `web/`：网页前端源码
- `frontend_cli/`
  独立命令行前端
- `sql/`
  DDL、过程、触发器、迁移、种子数据
- `scripts/`
  启动容器、导入 schema、导入种子数据、业务测试入口
- `docker/`
  Oracle 启动相关文件
- `docs/`
  协作文档、设计文档、部署文档

## 本地启动 Oracle 26ai

### 前置条件

1. 安装 Docker Desktop，并启用 WSL 2 后端
2. 登录 Oracle Container Registry 并接受 `database/free` 仓库条款
3. 执行：

```powershell
docker login container-registry.oracle.com
```

Oracle 仓库页面：

[container-registry.oracle.com/ords/ocr/ba/database/free](https://container-registry.oracle.com/ords/ocr/ba/database/free)

### 初始化步骤

1. 复制环境变量文件：

```powershell
Copy-Item .env.example .env
```

2. 修改 `.env` 中至少这些值：

- `ORACLE_PWD`
- `APP_USER_PASSWORD`
- `JWT_SECRET_KEY`
- `DEEPSEEK_API_KEY`

3. 启动 Oracle 26ai 容器：

```powershell
.\scripts\start-oracle26ai.ps1
```

如果 PowerShell 拦截脚本执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-oracle26ai.ps1
```

4. 导入 schema：

```powershell
.\scripts\load-oracle-schema.ps1
```

如果你的数据库不是刚初始化的新库，而是基于之前版本继续开发，需要按缺失情况补跑对应迁移：

```powershell
$migrations = @(
  "sql/migrations/20260405_add_answers_user_id.sql",
  "sql/migrations/20260405_add_answer_comments.sql",
  "sql/migrations/20260422_add_media_assets.sql",
  "sql/migrations/20260422_add_question_acceptance.sql",
  "sql/migrations/20260425_extend_chat_session_for_follow_up.sql",
  "sql/migrations/20260427_extend_tag_metadata.sql",
  "sql/migrations/20260429_add_deleted_question_status.sql",
  "sql/migrations/20260429_limit_media_asset_file_size.sql",
  "sql/migrations/20260502_improve_recommendation_scoring.sql",
  "sql/migrations/20260503_refresh_reporting_views.sql",
  "sql/migrations/20260507_standardize_question_categories.sql",
  "sql/migrations/20260508_add_answer_soft_delete.sql"
)
.\scripts\load-oracle-schema.ps1 -SqlFiles $migrations
```

如果你只缺某一次迁移，也可以只传对应的 `.sql` 文件。Windows PowerShell 下传多个文件时建议先放进数组再传给 `-SqlFiles`，避免第二个文件被误解析成其它位置参数。

5. 导入固定演示数据：

```powershell
.\scripts\load-seed-data.ps1
```

## 自动校验

仓库已提供一键验证脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
```

该脚本会：

- 创建临时校验用户
- 执行 `create_tables.sql`、`procedures.sql`、`triggers.sql`、`views.sql`
- 检查无效对象与编译错误
- 运行正向与逆向测试
- 验证触发器、统计字段、推荐逻辑
- 最后自动清理临时用户

## AI 多轮追问

当前仓库已经完成“AI 首答后，用户继续追问”的前后端闭环，并在问题详情页提供会话入口。

这条业务链的语义是：

- 用户先通过 `POST /api/questions/ask` 获得一条 `AI` 类型首答
- 后续追问不是通用聊天，而是绑定在“某个问题 + 某条 AI 首答”上
- 系统会把这段连续交流保存为一条独立会话

当前接口包括：

- `POST /api/questions/{question_id}/answers/{answer_id}/follow-up`
- `GET /api/questions/{question_id}/answers/{answer_id}/follow-up-sessions`
- `GET /api/chat/sessions/{session_id}`

当前已经落实的业务约束包括：

- 只有 `AI` 类型回答可以发起追问
- `answer_id` 必须属于当前 `question_id`
- 任何已登录用户都可以查看会话，但只有会话创建者可以续写
- `session_id` 必须和当前问题、首答锚点一致
- `CLOSED` 状态会话不能继续追问
- 网页端会优先显示用户昵称，没有昵称时显示用户名，并正确区分本人和其他用户

仓库也提供了这条链路的独立自检脚本：

```powershell
python -B .\scripts\validate_chat_followup.py
```

该脚本使用 fake LLM 响应，不依赖真实 DeepSeek 调用，适合本地快速回归。

如果需要看完整接口示例、返回结构和迁移说明，请直接查看：

- [docs/chat_followup_api_guide.md](docs/chat_followup_api_guide.md)

## 启动 API

### 运行前补充配置

在 `.env` 中确认这些值：

- `APP_USER`
- `APP_USER_PASSWORD`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL`

### 安装依赖

```powershell
pip install -r requirements.txt
```

### 启动命令

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后可访问：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## 使用网页前端

API 启动后，推荐直接访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/home`
- `http://127.0.0.1:8000/home?section=recommend`
- `http://127.0.0.1:8000/home?section=hot`
- `http://127.0.0.1:8000/me`
- `http://127.0.0.1:8000/admin`
- `http://127.0.0.1:8000/questions/62`

注意：

- 页面源码仍位于 `app/web/`
- 页面请求现在走同源 `/api/...`，不再写死本地地址
- 登录成功后，JWT 和用户信息会写入 `sessionStorage`，按浏览器标签页隔离，避免多个账号互相覆盖
- 首页右侧热门标签现在来自 `GET /api/tags`
- 全站搜索框都支持搜索历史下拉
- 管理员后台要求当前登录用户为 `ACTIVE ADMIN`；普通用户访问 `/admin` 会被后端鉴权拦截

## 使用 CLI

推荐入口：

```powershell
python .\scripts\start_business_test.py
```

这个入口会：

- 自动检查 `/health`
- 如有需要自动启动 API
- 进入 CLI 菜单模式

也可以单独执行：

```powershell
python -m frontend_cli.main auth login --username <username> --password <password>
python -m frontend_cli.main --access-token <token> menu
python -m frontend_cli.main health
python -m frontend_cli.main menu
python -m frontend_cli.main questions list
python -m frontend_cli.main questions detail --question-id <question_id>
python -m frontend_cli.main --access-token <token> questions answer --question-id <question_id> --user-id <user_id> --content "这是一个人工回答示例"
python -m frontend_cli.main search questions --q DeepSeek
```

CLI 现在支持：

- `auth login` / `auth register`
- 全局参数 `--access-token`
- 环境变量 `CLI_ACCESS_TOKEN`

说明：

- 公开读接口仍可匿名调用
- 受保护写接口现在要求 Bearer Token
- CLI 里仍有少量写接口保留 `user_id` 兼容字段，服务端会校验它必须和当前登录用户一致

## 当前主要接口

说明：

- 公开读接口可匿名访问
- 写接口和用户私有接口需要 Bearer Token

### 认证

- `POST /api/auth/register`
- `POST /api/auth/login`

### 问题与回答

- `POST /api/questions/ask`
- `POST /api/questions`
- `GET /api/questions`
- `GET /api/questions/{question_id}`
- `POST /api/questions/{question_id}/answers`
- `DELETE /api/answers/{answer_id}`
- `POST /api/questions/{question_id}/answers/{answer_id}/follow-up`
- `GET /api/questions/{question_id}/answers/{answer_id}/follow-up-sessions`
- `GET /api/chat/sessions/{session_id}`

多轮追问接口的请求体、响应体和业务规则详见：

- [docs/chat_followup_api_guide.md](docs/chat_followup_api_guide.md)

### 搜索与行为

- `GET /api/categories`
- `GET /api/tags`
- `GET /api/tags/suggestions`
- `GET /api/search/questions`
- `GET /api/search/history`
- `POST /api/questions/{question_id}/browse`
- `POST /api/questions/{question_id}/favorite`
- `DELETE /api/questions/{question_id}/favorite`
- `POST /api/answers/{answer_id}/feedback`
- `GET /api/questions/{question_id}/feedbacks`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`

### 推荐

- `GET /api/users/me/profile`
- `PATCH /api/users/me/profile`
- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`

### 头像与内容图片

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

## 当前仍未完全完成或未收口的能力

- 评论图片
- 媒体审核、隐藏与清理后台
- 推荐规则人工干预入口
- 采纳答案取消、采纳历史和更细的答案治理
- 标签合并、批量审核和标签质量治理

## 多轮追问自检

如果你想验证“AI 首答后继续追问”的后端约束，可以运行：

```powershell
python -B .\scripts\validate_chat_followup.py
```

这个自检不会调用真实 DeepSeek，而是使用 fake LLM 响应完成本地 smoke。

## 文档地图

- [docs/current_status.md](docs/current_status.md)
  当前代码状态、已完成能力、优先改进项
- [docs/README.md](docs/README.md)
  协作者快速入口
- [docs/testing_guide.md](docs/testing_guide.md)
  测试同学按当前功能回归的主文档
- [docs/onboarding_checklist.md](docs/onboarding_checklist.md)
  新协作者交接清单
- [docs/design_details/business_code_architecture.md](docs/design_details/business_code_architecture.md)
  业务代码架构说明
- [docs/design_details/community_platform_design.md](docs/design_details/community_platform_design.md)
  社区产品与接口设计
- [docs/design_details/media_and_avatar_design.md](docs/design_details/media_and_avatar_design.md)
  头像与问题 / 回答图片能力设计
- [docs/setup/oracle-26ai-docker.md](docs/setup/oracle-26ai-docker.md)
  Oracle 26ai 部署说明

## 管理员使用说明

当前项目不单独维护管理员表，而是使用 `USERS.ROLE = 'ADMIN'` 表示管理员身份。

### 1. 授予首个管理员

先通过注册接口或页面创建一个普通用户，然后执行：

```powershell
.\scripts\grant-admin.ps1 -Username <your_username>
```

执行完成后，该账号会被更新为 `ACTIVE ADMIN`。

### 2. 一键验证管理员接口

仓库已提供管理员接口测试入口脚本：

```powershell
.\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password>
```

默认行为：

- 默认使用 `http://127.0.0.1:8001`
- 如果目标端口没有 API，会自动启动一份最新代码的 FastAPI 测试进程
- 自动验证登录、管理员身份、用户列表、分类列表、登录日志、操作日志

如果你已经手动启动了最新 API，也可以这样执行：

```powershell
.\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password> -Port 8000 -SkipApiStart
```

如果你还想顺手验证“创建分类 / 修改分类”这条写入链路，可以加：

```powershell
.\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password> -WriteSmoke
```

注意：

- `-WriteSmoke` 会创建一条临时测试分类，并把它更新为 `INACTIVE`
- 如果你当前 `8000` 已经挂着旧进程，建议改用 `8001` 或其他空闲端口启动最新代码再测

### 3. 使用管理员网页后台

管理员账号重新登录后，可以直接访问：

```text
http://127.0.0.1:8000/admin
```

网页后台当前包含：

- 总览：用户、管理员、分类、操作日志数量概览
- 用户治理：按角色或状态筛选用户，修改用户角色和状态
- 分类管理：创建分类，修改分类名称、描述和启用状态
- 标签治理：查看标签元数据，修改标签状态和描述
- 内容治理：查询最近问题，查看回答 ID 和评论 ID，一键填入治理表单后修改状态
- 审计日志：查询登录日志和管理员操作日志

页面为了演示友好，会把 `ADMIN`、`ACTIVE`、`OPEN` 等枚举显示成中文文案；实际请求仍提交后端要求的枚举值。

### 4. 当前管理员接口

- `GET /api/admin/categories`
- `POST /api/admin/categories`
- `PATCH /api/admin/categories/{category_id}`
- `GET /api/admin/tags`
- `PATCH /api/admin/tags/{tag_id}`
- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}/status`
- `PATCH /api/admin/users/{user_id}/role`
- `PATCH /api/admin/questions/{question_id}/status`
- `DELETE /api/admin/questions/{question_id}`
- `DELETE /api/admin/answers/{answer_id}`
- `PATCH /api/admin/comments/{comment_id}/status`
- `GET /api/admin/logs/login`
- `GET /api/admin/logs/operations`

补充说明：当使用 `.\scripts\test-admin-api.ps1 -WriteSmoke` 时，脚本会在摘要中额外返回写入后的操作日志校验结果，用来确认 `ADMIN_CREATE_CATEGORY` 和 `ADMIN_UPDATE_CATEGORY` 已经成功落日志。

如果 Windows PowerShell 提示“系统上禁止运行脚本”，可以改用：
`powershell -ExecutionPolicy Bypass -File .\scripts\grant-admin.ps1 -Username <your_username>`
或
`powershell -ExecutionPolicy Bypass -File .\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password>`
