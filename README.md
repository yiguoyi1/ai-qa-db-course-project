# ai-qa-db-course-project

AI QA system with recommendation and database design.

# 智能问答记录与推荐管理系统

## 项目简介

本项目是一个面向数据库课程设计的智能问答系统，围绕“问答 + 行为 + 推荐”构建完整的数据闭环。

如果是新的协作者，建议先看：

- [docs/README.md](/F:/ai-qa-db-course-project/docs/README.md)
- [docs/onboarding_checklist.md](/F:/ai-qa-db-course-project/docs/onboarding_checklist.md)

系统支持：

- 用户提问与 AI 回答记录
- 浏览、收藏、反馈、搜索等行为数据管理
- 用户兴趣画像建模
- 多策略推荐生成
- AI Prompt 与多轮会话日志记录

## 当前技术栈

- 数据库：Oracle AI Database 26ai Free
- 本地运行方式：Docker Desktop + Oracle 官方容器镜像
- SQL 脚本：Oracle 26ai 兼容 DDL / Package / Trigger
- 适用环境：Windows + PowerShell + WSL 2

## 数据库设计概览

系统数据表分为五大模块：

### 1. 基础数据

- `USERS`
- `CATEGORIES`
- `QUESTIONS`
- `ANSWERS`
- `TAGS`
- `QUESTION_TAGS`

### 2. 用户行为

- `ANSWER_FEEDBACK`
- `FAVORITES`
- `BROWSE_HISTORY`
- `SEARCH_HISTORY`

### 3. 推荐相关

- `RECOMMENDATIONS`
- `USER_TAG_PROFILE`

### 4. AI 扩展

- `CHAT_SESSION`
- `CHAT_MESSAGE`
- `AI_PROMPT_LOG`

### 5. 系统管理

- `LOGIN_LOG`
- `OPERATION_LOG`

## 核心数据流程

```text
用户行为 -> 标签权重计算 -> 用户画像 -> 推荐生成
```

## 仓库中的关键 SQL

- `sql/create_tables.sql`：建表、主外键、唯一约束、检查约束、索引
- `sql/procedures.sql`：统计同步、画像重建、推荐生成等业务过程
- `sql/triggers.sql`：自动维护统计字段与登录时间

## 本地启动 Oracle 26ai

### 前置条件

1. 安装 Docker Desktop，并启用 WSL 2 后端
2. 登录 Oracle Container Registry 并接受 `database/free` 仓库条款
3. 执行：

```powershell
docker login container-registry.oracle.com
```

Oracle 仓库页面：

`https://container-registry.oracle.com/ords/ocr/ba/database/free`

### 初始化步骤

1. 复制环境变量文件：

```powershell
Copy-Item .env.example .env
```

2. 修改 `.env` 中至少这两个值：

- `ORACLE_PWD`
- `APP_USER_PASSWORD`

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

当前已验证通过的要点包括：

- 全部表与索引可成功创建
- `qa_app_pkg` 包和触发器可成功编译
- 浏览量、收藏数、回答数、点赞数、评分均可自动同步
- 重复用户名、重复收藏、重复反馈、非法评分、非法外键会被正确拒绝

## 最小 API 骨架

仓库现在已经包含“单轮 AI 问答最小闭环”的 FastAPI 代码骨架，核心目录如下：

- `app/main.py`
- `app/api/routes/questions.py`
- `app/services/question_service.py`
- `app/services/ai_answer_service.py`
- `app/repositories/`
- `app/integrations/llm/openai_client.py`
- `app/prompts/question_answer_prompt.py`

### 运行前补充配置

在 `.env` 中补充或确认以下值：

- `APP_USER`
- `APP_USER_PASSWORD`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL`

### 安装依赖

```powershell
pip install -r requirements.txt
```

### 启动 API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 当前已提供的接口

- `GET /health`
- `POST /api/questions/ask`
- `GET /api/questions/{question_id}`

当前还已补充：

- `GET /api/questions`
- `POST /api/questions/{question_id}/answers`
- `GET /api/categories`
- `GET /api/tags`
- `POST /api/questions/{question_id}/browse`
- `POST /api/questions/{question_id}/favorite`
- `DELETE /api/questions/{question_id}/favorite`
- `POST /api/answers/{answer_id}/feedback`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`
- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`
- `GET /api/search/questions`

## 独立 CLI 前端

仓库现在包含一个单独的命令行前端：

- `frontend_cli/main.py`
- `frontend_cli/api_client.py`
- `frontend_cli/config.py`
- `frontend_cli/render.py`

这个 CLI 前端不会直接 import `app/services` 或 `app/repositories`，而是只通过 HTTP 调用 FastAPI 接口，因此和业务逻辑代码保持解耦。

### CLI 配置

可在 `.env` 中配置：

- `CLI_API_BASE_URL`
- `CLI_API_TIMEOUT`

默认值分别是：

- `http://127.0.0.1:8000`
- `30`

### CLI 示例

先启动 API：

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

再在另一个终端执行：

```powershell
python -m frontend_cli.main health
python -m frontend_cli.main menu
python -m frontend_cli.main categories
python -m frontend_cli.main tags
python -m frontend_cli.main questions list
python -m frontend_cli.main questions detail --question-id <question_id>
python -m frontend_cli.main questions answer --question-id <question_id> --user-id <user_id> --content "这是一个人工回答示例"
python -m frontend_cli.main comments add --answer-id <answer_id> --user-id <user_id> --content "这是一条评论"
python -m frontend_cli.main comments list --answer-id <answer_id>
python -m frontend_cli.main comments delete --comment-id <comment_id> --user-id <user_id>
python -m frontend_cli.main search questions --q DeepSeek
python -m frontend_cli.main recommendations list --user-id <user_id>
```

### 一键业务测试入口

如果你当前主要是验证业务逻辑，可以直接使用这个脚本：

优先推荐 Python 入口：

```powershell
python .\scripts\start_business_test.py
```

它会：

- 检查 `http://127.0.0.1:8000/health`
- 如果 API 还没启动，就自动启动 `uvicorn`
- 等待后端可用
- 直接进入 CLI 菜单模式
- 退出菜单后，如果 API 是脚本临时拉起的，就自动关闭

如果你已经手动启动了 API，也可以这样复用现有服务：

```powershell
python .\scripts\start_business_test.py --skip-api-start
```

如果你更习惯 PowerShell，也可以继续使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-business-test.ps1
```

对应的 PowerShell 复用方式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-business-test.ps1 -SkipApiStart
```

## 连接信息

- Host: `localhost`
- Port: `1521`
- Service Name: `FREEPDB1`
- 管理员密码：`.env` 中的 `ORACLE_PWD`
- 应用用户：`.env` 中的 `APP_USER`
- 应用密码：`.env` 中的 `APP_USER_PASSWORD`

## 常用命令

```powershell
docker compose up -d
docker compose logs -f oracle26ai
docker compose down
docker exec -it oracle26ai sqlplus system/<password>@//localhost:1521/FREEPDB1
```

## 相关文档

- [docs/README.md](/F:/ai-qa-db-course-project/docs/README.md)
- [docs/onboarding_checklist.md](/F:/ai-qa-db-course-project/docs/onboarding_checklist.md)
- `docs/setup/oracle-26ai-docker.md`
- `docs/design_details/data_design_full.md`
- `docs/design_details/business_code_architecture.md`
- `docs/design_details/community_platform_design.md`
- `docs/design_details/threaded_comment_design.md`
