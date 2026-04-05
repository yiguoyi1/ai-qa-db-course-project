# 新协作者交接清单

这份清单面向第一次接手本仓库的协作者。目标不是介绍全部设计细节，而是让你在第一天内完成：

- 确认项目现状
- 跑起本地环境
- 验证核心业务链路
- 知道改动时该看哪些文件
- 避免提交明显不合规的内容

## 1. 先用 10 分钟了解项目

先看这 4 份文档：

1. [README.md](/F:/ai-qa-db-course-project/README.md)
2. [docs/README.md](/F:/ai-qa-db-course-project/docs/README.md)
3. [community_platform_design.md](/F:/ai-qa-db-course-project/docs/design_details/community_platform_design.md)
4. [business_code_architecture.md](/F:/ai-qa-db-course-project/docs/design_details/business_code_architecture.md)

读完后你应该能回答这几个问题：

- 这是“问答社区”，不是纯 AI 问答机器人
- 当前数据库和后端已经可运行
- 当前测试入口是独立 CLI，而不是网页前端
- 当前仍以显式 `user_id` 测业务，不是完整登录态

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

打开这个地址检查：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## 5. 用独立 CLI 验证主链路

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
python -m frontend_cli.main categories
python -m frontend_cli.main tags
python -m frontend_cli.main questions list
python -m frontend_cli.main questions detail --question-id 62
python -m frontend_cli.main recommendations list --user-id 22
```

如果要验证社区行为，再补测：

```powershell
python -m frontend_cli.main questions answer --question-id 62 --user-id 22 --content "这是一个人工回答示例"
python -m frontend_cli.main comments add --answer-id 82 --user-id 22 --content "这是一条评论"
python -m frontend_cli.main comments list --answer-id 82
```

## 6. 协作者最应该先知道的业务规则

这些不是“可选理解”，而是当前实现已经固定下来的口径：

- `POST /api/questions/ask` 会自动触发 AI 首答，不是纯提问
- `MANUAL` 回答必须带真实 `user_id`
- `AI` / `SYSTEM` 回答不带 `user_id`
- 评论挂在回答下，不直接挂在问题下
- 评论允许自回复
- 评论不支持编辑
- 评论删除采用软删除
- 删除评论不会级联删除子回复
- 已删除顶层评论显示“原评论已删除”
- 已删除回复显示“原回复已删除”
- 推荐逻辑优先复用数据库过程，不在 Python 里重写

## 7. 改代码前先看哪些文件

### 7.1 如果要改问题、回答、评论

- [questions.py](/F:/ai-qa-db-course-project/app/api/routes/questions.py)
- [answers.py](/F:/ai-qa-db-course-project/app/api/routes/answers.py)
- [comments.py](/F:/ai-qa-db-course-project/app/api/routes/comments.py)
- [question_service.py](/F:/ai-qa-db-course-project/app/services/question_service.py)
- [answer_service.py](/F:/ai-qa-db-course-project/app/services/answer_service.py)
- [comment_service.py](/F:/ai-qa-db-course-project/app/services/comment_service.py)
- [question_repository.py](/F:/ai-qa-db-course-project/app/repositories/question_repository.py)
- [answer_repository.py](/F:/ai-qa-db-course-project/app/repositories/answer_repository.py)
- [comment_repository.py](/F:/ai-qa-db-course-project/app/repositories/comment_repository.py)

### 7.2 如果要改推荐

- [recommendations.py](/F:/ai-qa-db-course-project/app/api/routes/recommendations.py)
- [recommendation_service.py](/F:/ai-qa-db-course-project/app/services/recommendation_service.py)
- [recommendation_repository.py](/F:/ai-qa-db-course-project/app/repositories/recommendation_repository.py)
- [procedures.sql](/F:/ai-qa-db-course-project/sql/procedures.sql)

### 7.3 如果要改数据库结构

- [create_tables.sql](/F:/ai-qa-db-course-project/sql/create_tables.sql)
- [procedures.sql](/F:/ai-qa-db-course-project/sql/procedures.sql)
- [triggers.sql](/F:/ai-qa-db-course-project/sql/triggers.sql)
- [constraints_and_rules.md](/F:/ai-qa-db-course-project/docs/design_details/constraints_and_rules.md)
- `sql/migrations/`

## 8. 协作时不要做的事

- 不要提交真实 `.env`
- 不要把本机绝对路径、真实密码、日志垃圾提交进仓库
- 不要在 Python 里手动维护统计字段
- 不要在应用层复制一套推荐算法
- 不要只改代码不改文档
- 不要把未实现能力写成“已完成”

## 9. 每次改动后的最小自检

改完后至少做这几步：

1. 能否启动 API
2. `/health` 是否正常
3. 对应 CLI 命令是否还能跑通
4. 如果改了数据库结构，校验脚本是否还能过
5. 是否同步更新了相关文档
6. `git status` 里是否出现了不该提交的 `.env`、日志、缓存文件

## 10. 当前最推荐继续做的事

如果你是新加入的协作者，最适合接着推进的是：

1. 纯社区式提问接口 `POST /api/questions`
2. 采纳答案
3. 用户中心
4. 登录与鉴权

如果你只想先熟悉系统，不建议一上来就碰：

- 多轮对话
- 复杂前端页面
- 推荐算法重构

## 11. 交接完成标准

如果你已经完成下面这些，就说明你已经具备继续协作的基础：

- 能独立跑起 Oracle 容器
- 能独立启动 FastAPI
- 能用 CLI 跑通至少一条业务链
- 知道评论和推荐的关键规则
- 知道改数据库要同步改文档
- 知道当前下一阶段优先级是什么

做到这一步，再开始写代码会顺很多。
