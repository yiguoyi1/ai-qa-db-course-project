# 项目文档总览

这份文档是给协作者的快速入口，帮助大家在最短时间内理解：

- 这个项目现在做到哪一步了
- 当前网页前端和 CLI 各自负责什么
- 代码主要分层和文件入口在哪里
- 哪些能力已经完成，哪些地方最值得优先收口

## 1. 先看哪几份文档

如果你刚接手这个仓库，建议按这个顺序看：

1. [README.md](../README.md)
2. [current_status.md](current_status.md)
3. [onboarding_checklist.md](onboarding_checklist.md)
4. [community_platform_design.md](design_details/community_platform_design.md)
5. [business_code_architecture.md](design_details/business_code_architecture.md)

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
- 分类、标签、搜索、搜索历史
- 浏览、收藏、回答反馈
- 评论与楼中楼回复
- 用户画像重建与推荐生成
- 静态网页登录页、首页、详情页
- 独立 CLI 业务测试入口

### 3.2 当前仍未完全收口

- 采纳答案
- 用户中心
- 网页端评论、收藏、推荐的完整闭环
- 网页前端通过 FastAPI 统一托管
- JWT 鉴权与显式 `user_id` 两套调用方式的统一
- 多轮对话正式业务链

## 4. 当前最值得优先改的点

### 4.1 统一接口契约与鉴权

当前项目正处于从“显式 `user_id` 调试模式”向“JWT 登录态模式”过渡的阶段，已经出现：

- 新旧接口并存
- 路由职责混杂
- 同一种业务存在两套反馈入口

这部分是最值得先收口的工程问题。

### 4.2 把网页前端纳入统一交付

当前 `app/web/` 页面已经能演示，但还没有通过 FastAPI 静态托管，且 API 地址直接写死为 `http://127.0.0.1:8000`。这会影响后续演示、部署和多人协作。

### 4.3 修正发帖体验与后端校验错位

首页弹窗把详细描述显示为可选，但 AI 发帖接口仍要求 `content` 非空，容易让用户在默认开关下直接撞到校验错误。

### 4.4 继续补齐社区主链路

最适合继续推进的仍然是：

1. 采纳答案
2. 用户中心
3. 网页端更多互动功能
4. 多轮对话正式业务链

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

当前网页前端的作用是：

- 演示登录、首页流和详情页交互
- 直接通过 HTTP 调后端接口
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
- `POST /api/questions/answers/{answer_id}/feedback`
- `GET /api/questions/{question_id}/feedbacks`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`

### 6.5 推荐

- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`

## 7. 当前关键业务规则

这几条是协作者最容易误解的地方，最好先统一口径：

- `POST /api/questions/ask` 不是“纯提问”，它会触发 AI 首答
- `POST /api/questions` 是纯社区发帖入口
- 当前网页前端已经开始使用 JWT 登录态
- 当前后端仍有一部分接口保留显式 `user_id`
- `MANUAL` 回答代表社区用户回答，必须带真实 `user_id`
- `AI` / `SYSTEM` 回答不带 `user_id`
- 评论挂在回答下，不直接挂在问题下
- 评论允许自回复
- 评论不支持编辑
- 评论删除采用软删除，不级联子回复
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

启动 API 后，直接打开：

- `app/web/login.html`
- `app/web/home.html`
- `app/web/detail.html`

当前注意事项：

- 页面默认请求 `http://127.0.0.1:8000`
- 页面还没有通过 FastAPI 统一托管

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
- [onboarding_checklist.md](onboarding_checklist.md)

### 10.2 产品与业务设计

- [data_design.md](design_details/data_design.md)
- [community_platform_design.md](design_details/community_platform_design.md)
- [threaded_comment_design.md](design_details/threaded_comment_design.md)

### 10.3 数据设计

- [data_tables.md](design_details/data_tables.md)
- [data_flow.md](design_details/data_flow.md)
- [constraints_and_rules.md](design_details/constraints_and_rules.md)
- [data_design_full.md](design_details/data_design_full.md)

### 10.4 工程协作

- [business_code_architecture.md](design_details/business_code_architecture.md)
- [code_and_file_standards.md](design_details/code_and_file_standards.md)
- [oracle-26ai-docker.md](setup/oracle-26ai-docker.md)
