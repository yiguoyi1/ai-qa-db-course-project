# 项目文档总览

这份文档是给协作者的快速入口，帮助大家在最短时间内理解：

- 这个项目现在做到哪一步了
- 本地应该怎么启动
- 代码主要分层和文件入口在哪里
- 当前哪些功能已经实现，哪些还没有
- 继续开发时应该优先看哪些文档

## 1. 项目当前定位

当前项目已经不是纯数据库设计稿，而是一个可以本地运行的问答社区 MVP：

- 后端：`FastAPI`
- 数据库：`Oracle AI Database 26ai Free`
- AI 提供商：`DeepSeek`
- 测试前端：独立 CLI，通过 HTTP 调后端，不直接依赖业务层代码

业务定位上，它是“问答社区 + AI 首答 + 行为记录 + 推荐”。

也就是说：

- 用户可以提问
- 系统可以生成 AI 首答
- 用户之间可以继续人工回答
- 用户可以浏览、收藏、反馈、评论和回复
- 系统可以根据行为数据生成推荐

## 2. 当前实现状态

### 2.1 已实现

- Oracle 26ai Docker 本地环境
- 建表、约束、索引、触发器、存储过程
- 固定业务 schema：`AI_QA_APP`
- 固定演示数据导入
- 问题列表与问题详情
- AI 首答
- 用户人工回答
- 分类、标签、搜索
- 浏览、收藏、回答反馈
- 评论与楼中楼回复
- 用户画像重建与推荐生成
- 独立 CLI 业务测试入口

### 2.2 暂未实现

- 真实登录 / 鉴权
- 纯社区式提问接口 `POST /api/questions`
- 采纳答案
- 用户中心
- 多轮对话正式业务链

## 3. 协作者建议阅读顺序

如果是第一次接手这个仓库，建议按这个顺序看：

1. [README.md](/F:/ai-qa-db-course-project/README.md)
2. [onboarding_checklist.md](/F:/ai-qa-db-course-project/docs/onboarding_checklist.md)
3. [community_platform_design.md](/F:/ai-qa-db-course-project/docs/design_details/community_platform_design.md)
4. [business_code_architecture.md](/F:/ai-qa-db-course-project/docs/design_details/business_code_architecture.md)
5. [data_tables.md](/F:/ai-qa-db-course-project/docs/design_details/data_tables.md)
6. [constraints_and_rules.md](/F:/ai-qa-db-course-project/docs/design_details/constraints_and_rules.md)
7. [code_and_file_standards.md](/F:/ai-qa-db-course-project/docs/design_details/code_and_file_standards.md)

如果是要接着做数据库层，优先看：

- [create_tables.sql](/F:/ai-qa-db-course-project/sql/create_tables.sql)
- [procedures.sql](/F:/ai-qa-db-course-project/sql/procedures.sql)
- [triggers.sql](/F:/ai-qa-db-course-project/sql/triggers.sql)
- [oracle-26ai-docker.md](/F:/ai-qa-db-course-project/docs/setup/oracle-26ai-docker.md)

如果是要接着做业务代码，优先看：

- [main.py](/F:/ai-qa-db-course-project/app/main.py)
- [router.py](/F:/ai-qa-db-course-project/app/api/router.py)
- [question_service.py](/F:/ai-qa-db-course-project/app/services/question_service.py)
- [answer_service.py](/F:/ai-qa-db-course-project/app/services/answer_service.py)
- [comment_service.py](/F:/ai-qa-db-course-project/app/services/comment_service.py)
- [recommendation_service.py](/F:/ai-qa-db-course-project/app/services/recommendation_service.py)
- [main.py](/F:/ai-qa-db-course-project/frontend_cli/main.py)

## 4. 仓库结构速览

### 4.1 数据库与部署

- `compose.yaml`：Oracle 26ai 容器定义
- `docker/oracle/startup/`：容器首次启动时执行的初始化脚本
- `sql/`：DDL、过程、触发器、演示数据、迁移脚本
- `scripts/`：启动容器、导入 schema、导入种子数据、业务测试入口

### 4.2 后端应用

- `app/api/routes/`：HTTP 路由层
- `app/services/`：业务编排层
- `app/repositories/`：数据库访问层
- `app/schemas/`：请求与响应模型
- `app/integrations/llm/`：AI 提供商接入
- `app/prompts/`：提示词模板

### 4.3 测试前端

- `frontend_cli/`：独立命令行前端

它的作用不是做正式 UI，而是：

- 验证业务逻辑能否跑通
- 作为独立调用方测试接口
- 避免直接在 Python 里绕过 API 调 service

## 5. 当前 API 主链路

### 5.1 问题与回答

- `POST /api/questions/ask`
- `GET /api/questions`
- `GET /api/questions/{question_id}`
- `POST /api/questions/{question_id}/answers`

### 5.2 元数据与搜索

- `GET /api/categories`
- `GET /api/tags`
- `GET /api/search/questions`

### 5.3 社区行为

- `POST /api/questions/{question_id}/browse`
- `POST /api/questions/{question_id}/favorite`
- `DELETE /api/questions/{question_id}/favorite`
- `POST /api/answers/{answer_id}/feedback`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`

### 5.4 推荐

- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`

## 6. 当前关键业务规则

这几条是协作者最容易误解的地方，最好先统一口径：

- 当前没有真实登录态，业务接口大多显式传 `user_id`
- `POST /api/questions/ask` 不是“纯提问”，它会触发 AI 首答
- `MANUAL` 回答代表社区用户回答，必须带真实 `user_id`
- `AI` / `SYSTEM` 回答不带 `user_id`
- 评论挂在回答下，不直接挂在问题下
- 评论允许自回复
- 评论不支持编辑
- 评论删除采用软删除，不级联子回复
- 已删除顶层评论显示“原评论已删除”
- 已删除回复显示“原回复已删除”
- 推荐逻辑优先复用数据库里的 `qa_app_pkg`

## 7. 本地协作最常用的启动方式

### 7.1 启动数据库

```powershell
Copy-Item .env.example .env
.\scripts\start-oracle26ai.ps1
.\scripts\load-oracle-schema.ps1
.\scripts\load-seed-data.ps1
```

### 7.2 启动 API

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.3 一键进入业务测试

```powershell
python .\scripts\start_business_test.py
```

这个入口会：

- 自动检查 `/health`
- 如有需要自动启动 API
- 进入 CLI 菜单模式

## 8. 协作时最容易踩坑的点

- 不要把 `.env` 提交进 Git
- 不要在 Python 里手动维护浏览量、收藏数、回答数、点赞数、平均分，数据库已经有触发器
- 不要在应用层重复实现推荐算法，优先调用数据库过程
- 如果改了数据库约束，记得同步：
  - `sql/create_tables.sql`
  - `docs/design_details/constraints_and_rules.md`
  - 对应迁移脚本或验证脚本
- 如果改了业务接口，记得同步：
  - `README.md`
  - 本文档
  - 相关设计文档

## 9. 下一阶段最建议做的事

当前最值得继续推进的是：

1. 纯社区式提问接口 `POST /api/questions`
2. 采纳答案
3. 用户中心
4. 登录与鉴权

不建议下一步优先做的事：

- 过早做复杂前端页面
- 过早做多轮对话
- 在应用层重写推荐逻辑

## 10. 文档地图

### 10.1 产品与业务设计

- [data_design.md](/F:/ai-qa-db-course-project/docs/design_details/data_design.md)
- [community_platform_design.md](/F:/ai-qa-db-course-project/docs/design_details/community_platform_design.md)
- [threaded_comment_design.md](/F:/ai-qa-db-course-project/docs/design_details/threaded_comment_design.md)

### 10.2 数据设计

- [data_tables.md](/F:/ai-qa-db-course-project/docs/design_details/data_tables.md)
- [data_flow.md](/F:/ai-qa-db-course-project/docs/design_details/data_flow.md)
- [constraints_and_rules.md](/F:/ai-qa-db-course-project/docs/design_details/constraints_and_rules.md)
- [data_design_full.md](/F:/ai-qa-db-course-project/docs/design_details/data_design_full.md)

### 10.3 工程协作

- [onboarding_checklist.md](/F:/ai-qa-db-course-project/docs/onboarding_checklist.md)
- [business_code_architecture.md](/F:/ai-qa-db-course-project/docs/design_details/business_code_architecture.md)
- [code_and_file_standards.md](/F:/ai-qa-db-course-project/docs/design_details/code_and_file_standards.md)
- [oracle-26ai-docker.md](/F:/ai-qa-db-course-project/docs/setup/oracle-26ai-docker.md)

如果协作者只想快速接手项目，先看这一页和根目录 [README.md](/F:/ai-qa-db-course-project/README.md) 就够了。
