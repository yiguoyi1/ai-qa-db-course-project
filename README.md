# ai-qa-db-course-project

AI QA system with recommendation and database design.

# 智能问答记录与推荐管理系统

## 项目简介

本项目是一个面向数据库课程设计的智能问答系统，围绕“问答 + 行为 + 推荐”构建完整的数据闭环。

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

- `docs/setup/oracle-26ai-docker.md`
- `docs/design_details/data_design_full.md`
