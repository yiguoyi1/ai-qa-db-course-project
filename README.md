# ai-qa-db-course-project

AI QA community MVP backed by Oracle 26ai, FastAPI, and DeepSeek.

# 智能问答记录与推荐管理系统

## 项目简介

本项目是一个面向数据库课程设计的问答社区 MVP，围绕“问答 + 行为 + 推荐”构建完整的数据闭环。

当前仓库已经不只是数据库设计稿，而是同时包含：

- Oracle 26ai 数据库脚本与校验脚本
- FastAPI 后端
- 网页前端源码与页面入口
- 独立 CLI 测试前端

如果你是新的协作者，建议先看：

- [docs/current_status.md](docs/current_status.md)
- [docs/README.md](docs/README.md)
- [docs/onboarding_checklist.md](docs/onboarding_checklist.md)

## 当前已完成能力

### 1. 数据库与推荐闭环

- `sql/create_tables.sql`：建表、主外键、唯一约束、检查约束、索引
- `sql/procedures.sql`：统计同步、画像重建、推荐生成
- `sql/triggers.sql`：自动维护统计字段与登录时间
- `sql/seed_data.sql`：固定演示数据
- `scripts/validate-oracle-schema.ps1`：结构和业务规则校验

### 2. FastAPI 后端

- 健康检查：`GET /health`
- 注册 / 登录：`POST /api/auth/register`、`POST /api/auth/login`
- AI 首答提问：`POST /api/questions/ask`
- 纯社区发帖：`POST /api/questions`
- 问题列表 / 详情：`GET /api/questions`、`GET /api/questions/{question_id}`
- 人工回答：`POST /api/questions/{question_id}/answers`
- 分类、标签、搜索、搜索历史
- 浏览、收藏、反馈、评论
- 用户画像重建与推荐生成

### 3. 网页前端

当前仓库已经包含由 FastAPI 统一交付的网页前端，页面源码位于 `app/web/`：

- [app/web/login.html](app/web/login.html)
- [app/web/home.html](app/web/home.html)
- [app/web/detail.html](app/web/detail.html)

当前推荐访问入口：

- `/login`
- `/home`
- `/questions/{question_id}`

当前网页端已经实现：

- 登录与注册
- 首页问题流
- 搜索与搜索历史下拉
- 发布问题
- 首页发帖正文统一必填
- 切换“纯社区发帖”与“AI 首答发帖”
- 首页热门标签动态加载
- 问题详情查看
- Markdown 回答渲染与代码高亮
- 发布人工回答
- 点赞 / 点踩与当前用户反馈状态回显
- 登录态展示与退出登录

### 4. CLI 测试前端

仓库仍保留独立 CLI：

- `frontend_cli/main.py`
- `frontend_cli/api_client.py`
- `frontend_cli/config.py`
- `frontend_cli/render.py`

CLI 不直接依赖 `service` / `repository`，而是只通过 HTTP 调用 FastAPI，适合做接口回归和业务演示。

## 当前最值得先改的地方

基于当前代码现状，前三阶段已经完成到可用状态：

- 受保护写接口已经以 JWT 登录态为主
- 少量 `user_id` 字段只保留过渡兼容与一致性校验
- CLI 已补充登录与 `Bearer Token` 透传能力
- 网页前端已经由 FastAPI 统一提供入口
- 页面请求已经改为同源 API，不再写死 `127.0.0.1:8000`
- 首页热门标签已经改为真实标签接口数据

接下来最值得继续收口的是：

1. 收口安全配置
   JWT 参数已经进入 `.env`，下一步重点是登录审计、用户状态和生产环境密钥管理。
2. 继续清理鉴权过渡接口
   回答反馈仍保留兼容入口，`questions.py` 内也还有历史遗留路由需要进一步拆分。
3. 补齐社区核心能力
   采纳答案、用户中心、网页端评论 / 收藏 / 推荐入口仍待完善。

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
- 执行 `create_tables.sql`、`procedures.sql`、`triggers.sql`
- 检查无效对象与编译错误
- 运行正向与逆向测试
- 验证触发器、统计字段、推荐逻辑
- 最后自动清理临时用户

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

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/home`
- `http://127.0.0.1:8000/questions/62`

注意：

- 页面源码仍位于 `app/web/`
- 页面请求现在走同源 `/api/...`，不再写死本地地址
- 登录成功后，JWT 和用户信息会写入 `localStorage`
- 首页右侧热门标签现在来自 `GET /api/tags`

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
- CLI 里的 `user_id` 参数目前只作为过渡兼容字段，服务端会校验它必须和当前登录用户一致

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

### 搜索与行为

- `GET /api/categories`
- `GET /api/tags`
- `GET /api/search/questions`
- `GET /api/search/history`
- `POST /api/questions/{question_id}/browse`
- `POST /api/questions/{question_id}/favorite`
- `DELETE /api/questions/{question_id}/favorite`
- `POST /api/answers/{answer_id}/feedback`
- `POST /api/questions/answers/{answer_id}/feedback`
- `GET /api/questions/{question_id}/feedbacks`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`

### 推荐

- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`

## 当前仍未完全完成或未收口的能力

- 采纳答案
- 用户中心
- 网页前端评论 / 收藏 / 推荐完整闭环
- 登录审计收口
- 多轮对话正式业务链

## 文档地图

- [docs/current_status.md](docs/current_status.md)
  当前代码状态、已完成能力、优先改进项
- [docs/README.md](docs/README.md)
  协作者快速入口
- [docs/onboarding_checklist.md](docs/onboarding_checklist.md)
  新协作者交接清单
- [docs/design_details/business_code_architecture.md](docs/design_details/business_code_architecture.md)
  业务代码架构说明
- [docs/design_details/community_platform_design.md](docs/design_details/community_platform_design.md)
  社区产品与接口设计
- [docs/setup/oracle-26ai-docker.md](docs/setup/oracle-26ai-docker.md)
  Oracle 26ai 部署说明
