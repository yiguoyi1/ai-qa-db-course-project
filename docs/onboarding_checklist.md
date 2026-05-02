# 新协作者交接清单

这份清单面向第一次接手本仓库的协作者。目标不是介绍全部设计细节，而是让你在第一天内完成：

- 确认项目现状
- 跑起本地环境
- 验证核心业务链路
- 知道改动时该看哪些文件
- 避免提交明显不合规的内容

## 1. 先用 10 分钟了解项目

先看这 4 份文档：

1. [README.md](../README.md)
2. [handoff.md](handoff.md)
3. [current_status.md](current_status.md)
4. [docs/README.md](README.md)
5. [desktop_client_setup.md](desktop_client_setup.md)
6. [community_platform_design.md](design_details/community_platform_design.md)
7. [admin_governance_guide.md](admin_governance_guide.md)

读完后你应该能回答这几个问题：

- 这是“问答社区”，不是纯 AI 问答机器人
- 当前数据库和后端已经可运行
- 当前同时有网页端入口和独立 CLI
- 当前受保护写接口已经以 JWT 登录态为主，但仍有少量兼容字段和过渡路由待继续清理

## 2. 准备本地环境

### 2.1 必备条件

- Windows + PowerShell
- Docker Desktop
- Oracle 26ai 容器能正常启动
- Python 环境可用

### 2.2 初始化配置

```powershell
Copy-Item .env.example .env
```

至少确认这些配置可用：

- `ORACLE_PWD`
- `APP_USER`
- `APP_USER_PASSWORD`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL`

## 3. 跑起数据库

按顺序执行：

```powershell
.\scripts\start-oracle26ai.ps1
.\scripts\load-oracle-schema.ps1
.\scripts\load-seed-data.ps1
```

如果你接到的不是全新数据库，而是之前已经跑过的老库，需要按缺失情况补跑迁移脚本。当前仓库已有迁移包括：

```powershell
$migrations = @(
  "sql/migrations/20260405_add_answers_user_id.sql",
  "sql/migrations/20260405_add_answer_comments.sql",
  "sql/migrations/20260422_add_media_assets.sql",
  "sql/migrations/20260422_add_question_acceptance.sql",
  "sql/migrations/20260425_extend_chat_session_for_follow_up.sql",
  "sql/migrations/20260427_extend_tag_metadata.sql",
  "sql/migrations/20260428_add_question_oracle_text_indexes.sql",
  "sql/migrations/20260429_add_deleted_question_status.sql",
  "sql/migrations/20260429_limit_media_asset_file_size.sql",
  "sql/migrations/20260502_improve_recommendation_scoring.sql",
  "sql/migrations/20260503_refresh_reporting_views.sql"
)
.\scripts\load-oracle-schema.ps1 -SqlFiles $migrations
```

传多个 SQL 文件时建议先放进数组再传给 `-SqlFiles`；如果只缺某一次迁移，也可以只传单个 `.sql` 文件。

`20260428_add_question_oracle_text_indexes.sql` 是搜索性能优化迁移。导入后可把 `.env` 里的 `SEARCH_USE_ORACLE_TEXT` 改成 `true`，未导入时保持默认 `false`。

如果是第一次接手，建议再执行一次结构验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
```

到这一步你应该确认：

- Oracle 容器是 `healthy`
- schema 能导入
- 种子数据能导入
- 校验脚本不报编译错误

## 4. 跑起后端

安装依赖：

```powershell
pip install -r requirements.txt
```

启动 API：

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

打开这些地址检查：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## 5. 用网页前端或 CLI 验证主链路

### 5.1 网页前端验证

API 正常后，建议直接访问：

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/home`
- `http://127.0.0.1:8000/me`
- `http://127.0.0.1:8000/admin`
- `http://127.0.0.1:8000/questions/62`

建议最少手动验证这几步：

1. 注册一个新账号
2. 登录并跳转到首页
3. 首页搜索已有问题
4. 通过发帖弹窗发布一个纯社区问题
5. 再发布一个带 AI 首答的问题
6. 打开详情页并尝试发布人工回答
7. 对已有回答执行点赞或点踩
8. 上传问题配图或回答配图，确认详情页正文下方可显示图片

### 5.2 CLI 验证

最推荐的入口：

```powershell
python .\scripts\start_business_test.py
```

如果 API 已经手动开好了：

```powershell
python .\scripts\start_business_test.py --skip-api-start
```

你也可以单独跑这些命令确认业务逻辑：

```powershell
python -m frontend_cli.main auth login --username your_name --password your_password
python -m frontend_cli.main categories
python -m frontend_cli.main tags
python -m frontend_cli.main questions list
python -m frontend_cli.main questions detail --question-id 62
python -m frontend_cli.main recommendations list --user-id 22
```

如果要验证社区行为，再补测：

```powershell
python -m frontend_cli.main --access-token your_token questions answer --question-id 62 --user-id 22 --content "这是一个人工回答示例"
python -m frontend_cli.main --access-token your_token comments add --answer-id 82 --user-id 22 --content "这是一条评论"
python -m frontend_cli.main comments list --answer-id 82
```

### 5.3 桌面客户端验证

如果你需要接手客户端开发或下载安装包，请先看：

- [desktop_client_setup.md](desktop_client_setup.md)

macOS 常用命令：

```bash
cd desktop
npm install
npm run dev:full
```

Windows PowerShell 常用命令：

```powershell
cd desktop
npm install
npm run dev:full:windows
npm run build:windows
```

### 5.4 管理员链路验证

如果你本次接手需要改后台治理相关能力，建议额外做一遍管理员验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\grant-admin.ps1 -Username <your_username>
powershell -ExecutionPolicy Bypass -File .\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password> -WriteSmoke
```

建议先看：

- [admin_governance_guide.md](admin_governance_guide.md)

如果要验证管理员网页后台，重新登录管理员账号后访问 `/admin`，至少确认：

1. 总览、用户治理、分类管理、内容治理、审计日志五个模块可以切换
2. 用户治理可以筛选用户，并看到中文角色/状态文案
3. 内容治理可以加载最近问题，展开回答并查看评论 ID
4. “填入问题 ID / 填入评论 ID”按钮能把 ID 写入下方状态调整表单

## 6. 协作者最应该先知道的业务规则

这些不是“可选理解”，而是当前实现已经固定下来的口径：

- `POST /api/questions/ask` 会自动触发 AI 首答，不是纯提问
- `POST /api/questions` 是纯社区发帖入口
- 当前网页前端和受保护写接口已经使用 JWT 登录态
- 登录时会写 `LOGIN_LOG`，成功记 `SUCCESS`，失败记 `FAILURE`，锁定账号记 `LOCKED`
- `USERS.STATUS` 当前口径是：`ACTIVE` 允许登录和继续访问，`INACTIVE` / `DISABLED` 拒绝登录和继续访问，`LOCKED` 拒绝登录和继续访问并单独记锁定审计
- 少量 `user_id` 字段仍保留作兼容，但服务端会校验它必须与当前登录用户一致
- `MANUAL` 回答必须带真实 `user_id`
- `AI` / `SYSTEM` 回答不带 `user_id`
- 评论挂在回答下，不直接挂在问题下
- 评论允许自回复
- 评论不支持编辑
- 评论删除采用软删除
- 删除评论不会级联删除子回复
- 推荐逻辑优先复用数据库过程，不在 Python 里重写
- 当前推荐 API 保持不变，画像权重和推荐评分增强集中在 `qa_app_pkg`

## 7. 改代码前先看哪些文件

### 7.1 如果要改登录、发帖、详情页联动

- [login.html](../app/web/login.html)
- [home.html](../app/web/home.html)
- [detail.html](../app/web/detail.html)
- [auth.py](../app/api/routes/auth.py)
- [auth_service.py](../app/services/auth_service.py)
- [questions.py](../app/api/routes/questions.py)

### 7.2 如果要改问题、回答、评论

- [answers.py](../app/api/routes/answers.py)
- [comments.py](../app/api/routes/comments.py)
- [question_service.py](../app/services/question_service.py)
- [answer_service.py](../app/services/answer_service.py)
- [comment_service.py](../app/services/comment_service.py)
- [question_repository.py](../app/repositories/question_repository.py)
- [answer_repository.py](../app/repositories/answer_repository.py)
- [comment_repository.py](../app/repositories/comment_repository.py)

### 7.3 如果要改推荐

- [recommendations.py](../app/api/routes/recommendations.py)
- [recommendation_service.py](../app/services/recommendation_service.py)
- [recommendation_repository.py](../app/repositories/recommendation_repository.py)
- [procedures.sql](../sql/procedures.sql)

### 7.4 如果要改数据库结构

- [create_tables.sql](../sql/create_tables.sql)
- [procedures.sql](../sql/procedures.sql)
- [triggers.sql](../sql/triggers.sql)
- [views.sql](../sql/views.sql)
- [constraints_and_rules.md](design_details/constraints_and_rules.md)
- `sql/migrations/`

## 8. 协作时不要做的事

- 不要提交真实 `.env`
- 不要把本机绝对路径、真实密码、日志垃圾提交进仓库
- 不要在 Python 里手动维护统计字段
- 不要在应用层复制一套推荐算法
- 不要忽略网页前端和后端之间的接口错位
- 不要只改代码不改文档
- 不要把未实现能力写成“已完成”

## 9. 每次改动后的最小自检

改完后至少做这几步：

1. 能否启动 API
2. `/health` 是否正常
3. 网页前端是否还能完成登录、列表、详情、发帖、回答、点赞主链路
4. 对应 CLI 命令是否还能跑通
5. 如果改了数据库结构，校验脚本是否还能过
6. 是否同步更新了相关文档
7. `git status` 里是否出现了不该提交的 `.env`、日志、缓存文件

## 10. 当前最推荐继续做的事

如果你是新加入的协作者，最适合接着推进的是：

1. 评论图片与媒体审核、清理后台
2. 推荐规则人工干预入口
3. 采纳答案取消、采纳历史和更细的答案治理
4. 标签合并、批量审核和标签质量治理
5. 少量写接口兼容字段的继续清理

如果你只想先熟悉系统，不建议一上来就碰：

- 多轮对话
- 推荐算法重构
- 大规模重写数据库逻辑

## 11. 交接完成标准

如果你已经完成下面这些，就说明你已经具备继续协作的基础：

- 能独立跑起 Oracle 容器
- 能独立启动 FastAPI
- 能至少用网页前端或 CLI 跑通一条业务链
- 知道当前受保护写接口已经以 JWT 为主，兼容 `user_id` 仅用于过渡校验
- 知道评论和推荐的关键规则
- 知道多轮追问后端已经可用，并且能独立运行 `python -B .\\scripts\\validate_chat_followup.py`
- 知道改数据库要同步改文档
- 知道当前下一阶段优先级是什么

做到这一步，再开始写代码会顺很多。
