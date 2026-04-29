# 项目交接说明

这份文档面向刚接手本项目的协作者，用来快速说明当前代码状态、已验证内容、启动方式、关键业务规则和下一步优先事项。

## 1. 当前推荐分支

当前推荐基于 `main` 分支继续协作：

```text
main
```

当前文档整理前的本地基线提交：

```text
55bec04
```

现在的 `main` 已经整合了采纳答案、收藏、用户中心、管理员、媒体、头像、问题配图、回答配图、标签增强、AI 多轮追问前端和推荐画像相关能力。

保留但不建议直接合并的安全备份分支：

```text
integrate-collab-updates
backup-local-before-collab-integration
```

它们用于追溯整合过程和本地备份，不是当前推荐交付分支。

## 2. 已验证状态

历史本地验证曾覆盖：

- Docker Desktop 已启动
- `oracle26ai` 容器状态为 `healthy`
- `scripts/validate-oracle-schema.ps1` 已完整通过
- Oracle 对象无编译错误
- 触发器统计校验通过
- 推荐过程幂等性校验通过
- 采纳答案跨问题引用已被数据库约束拒绝
- Python 源码编译检查通过
- `app.main` 和 `frontend_cli.main` 导入通过
- CLI `questions` 命令已包含 `accept` 和图片相关命令

推荐重新验证命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
python -B -c "import app.main; import frontend_cli.main; print('imports ok')"
python -B -m frontend_cli.main questions --help
```

## 3. 环境启动顺序

第一次接手建议按顺序执行：

```powershell
Copy-Item .env.example .env
.\scripts\start-oracle26ai.ps1
.\scripts\load-oracle-schema.ps1
.\scripts\load-seed-data.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 启动后检查：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/home`
- `http://127.0.0.1:8000/home?section=recommend`
- `http://127.0.0.1:8000/home?section=hot`
- `http://127.0.0.1:8000/me`
- `http://127.0.0.1:8000/admin`

## 4. 当前核心能力

已经具备的主链路：

- 用户注册和登录
- JWT 鉴权
- 产品介绍首页
- 纯社区发帖
- AI 首答提问
- 发帖分类、已有标签、自定义标签、标签建议和 AI 自动标签
- 人工回答
- 采纳答案
- 问题收藏
- 回答点赞、点踩和评分
- 回答评论和楼中楼回复
- AI 首答多轮追问网页交互
- 搜索和搜索历史
- 推荐 / 热榜首页分区
- 浏览历史
- 用户中心
- 用户画像和推荐
- 管理员用户、分类、标签、问题、评论和日志治理接口
- 用户头像
- 问题配图
- 回答配图

当前网页入口：

- `/`
- `/login`
- `/home`
- `/home?section=recommend`
- `/home?section=hot`
- `/questions/{question_id}`
- `/me`
- `/admin`

当前 CLI 入口：

```powershell
python .\scripts\start_business_test.py
python -m frontend_cli.main menu
```

## 5. 关键业务规则

协作者改代码前必须统一以下口径：

- `POST /api/questions/ask` 会触发 AI 首答。
- `POST /api/questions` 是纯社区发帖，不触发 AI。
- 受保护写接口以 JWT 登录态为主。
- 仍保留的 `user_id` 字段属于过渡兼容字段，必须与当前登录用户一致。
- `MANUAL` 回答必须有真实用户。
- `AI` 和 `SYSTEM` 回答不绑定普通用户。
- 采纳答案只能由提问者或管理员执行。
- 采纳答案后问题状态变为 `RESOLVED`。
- 数据库复合外键保证被采纳回答必须属于当前问题。
- 已采纳问题当前不再接受新人工回答。
- 评论挂在回答下，不直接挂在问题下。
- 评论允许自回复。
- 评论不支持编辑。
- 评论删除是软删除，不级联删除子回复。
- 图片元数据统一保存在 `MEDIA_ASSETS`。
- 统计字段优先由数据库触发器维护，不应在 Python 里重复加减。
- 推荐逻辑优先调用数据库包 `qa_app_pkg`。

## 6. 数据库交接重点

主 DDL：

```text
sql/create_tables.sql
sql/procedures.sql
sql/triggers.sql
sql/views.sql
sql/seed_data.sql
```

本次整合新增或重点调整：

```text
sql/migrations/20260405_add_answers_user_id.sql
sql/migrations/20260405_add_answer_comments.sql
sql/migrations/20260422_add_media_assets.sql
sql/migrations/20260422_add_question_acceptance.sql
sql/migrations/20260425_extend_chat_session_for_follow_up.sql
sql/migrations/20260427_extend_tag_metadata.sql
sql/migrations/20260429_add_deleted_question_status.sql
sql/migrations/20260429_limit_media_asset_file_size.sql
```

采纳答案相关约束要点：

- `questions.accepted_answer_id` 保存当前被采纳回答。
- `answers` 上有 `UNIQUE (question_id, answer_id)`。
- `questions(question_id, accepted_answer_id)` 复合外键引用 `answers(question_id, answer_id)`。
- 这样可以避免“问题 A 采纳问题 B 的答案”。

媒体相关表：

- `MEDIA_ASSETS` 统一保存头像、问题配图、回答配图元数据。
- 图片二进制保存在 `MEDIA_ASSETS.FILE_CONTENT BLOB`。
- `PUBLIC_URL` 指向 `/api/media/files/{file_name}`，由后端从 Oracle BLOB 读取返回。

## 7. 代码入口地图

后端路由：

```text
app/api/routes/
```

业务服务：

```text
app/services/
```

数据库访问：

```text
app/repositories/
```

请求响应模型：

```text
app/schemas/
```

网页前端：

```text
app/web/
```

CLI 测试前端：

```text
frontend_cli/
```

## 8. 当前仍需补齐

建议下一阶段优先级：

1. 评论图片和图片审核后台。
2. 推荐规则人工干预入口。
3. 取消采纳或采纳历史。
4. 标签合并、批量审核和标签质量治理。
5. 写接口兼容字段的继续清理。

已经补齐的前端交互：

- 网页端问题配图和回答配图上传入口已接入，并在详情页正文下方展示。
- 网页端 AI 首答多轮追问入口已接入详情页，支持会话列表、消息展示和创建 / 续写追问。
- 管理员网页后台已接入 `/admin`，覆盖总览、用户治理、分类管理、标签治理、内容治理、登录日志和操作日志。
- 管理员后台已统一为社区蓝色视觉风格，角色、状态和日志类型显示为中文友好文案。
- 内容治理页已经支持从最近问题定位问题 ID、展开回答查看评论 ID，并一键填入治理表单。

## 9. 提交前检查

每次提交前至少做：

```powershell
git status --short
python -B -c "import pathlib; files=list(pathlib.Path('app').rglob('*.py'))+list(pathlib.Path('frontend_cli').rglob('*.py')); [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in files]; print(f'compiled {len(files)} files without pycache')"
python -B -c "import app.main; import frontend_cli.main; print('imports ok')"
git diff --check
```

如果改了数据库结构，必须额外执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
```

不要提交：

- `.env`
- 历史本地 `uploads/` 目录如果存在，只作为旧运行残留，不再是媒体主存储。
- `*.log`
- `__pycache__/`
- 临时测试图片
- 本机绝对路径
- 真实 API Key 或密码
