# 业务代码架构设计

## 1. 设计目标

本设计用于承接当前已经完成的 Oracle 26ai 数据库部分，把“文档 + SQL + 触发器 + 存储过程”继续往上延伸到真正可运行的业务代码层。

本阶段的目标不是一上来做完整前后端，而是先落地一条最小可演示业务闭环：

1. 用户提交问题
2. 系统调用 AI 生成回答
3. 问题、回答、Prompt 日志写入 Oracle
4. 用户查看问题详情并进行收藏、反馈
5. 系统生成推荐结果并供用户查询

## 2. 推荐架构方案

### 2.1 总体方案

建议采用“单体后端应用 + Oracle 数据库 + 外部 AI 提供商”的结构。

推荐技术路线：

- 后端框架：`FastAPI`
- 数据库访问：`python-oracledb`
- AI 接入：`OpenAI SDK` 或兼容 OpenAI API 的模型服务
- 配置管理：`.env`
- 测试：`pytest`

选择这个方案的原因：

- 结构简单，适合课程设计阶段快速落地
- Python 接入 AI 模型和 Oracle 都比较直接
- 当前已经同时落地网页端入口和独立 CLI，后续继续扩展也方便
- 即使以后换成 Java / Node.js，这套模块边界仍然成立

## 3. 建议目录结构

推荐在仓库根目录新增应用层代码目录 `app/`，整体结构如下：

```text
app/
  main.py
  api/
    router.py
    deps.py
    routes/
      auth.py
      answers.py
      browse.py
      comments.py
      favorites.py
      feedback.py
      meta.py
      questions.py
      recommendations.py
      search.py
  core/
    errors.py
    settings.py
  db/
    connection.py
  schemas/
    answer.py
    auth.py
    browse.py
    comment.py
    favorite.py
    feedback.py
    meta.py
    question.py
    recommendation.py
  services/
    ai_answer_service.py
    answer_service.py
    auth_service.py
    browse_service.py
    comment_service.py
    favorite_service.py
    feedback_service.py
    meta_service.py
    question_service.py
    recommendation_service.py
    search_service.py
  repositories/
    answer_repository.py
    browse_repository.py
    comment_repository.py
    favorite_repository.py
    feedback_repository.py
    log_repository.py
    meta_repository.py
    question_repository.py
    recommendation_repository.py
    search_repository.py
    user_repository.py
  integrations/
    llm/
      openai_client.py
  prompts/
    question_answer_prompt.py
  web/
    login.html
    home.html
    detail.html

frontend_cli/
  api_client.py
  config.py
  main.py
  render.py

scripts/
  start_business_test.py

tests/
  unit/
  integration/
  api/
```

## 4. 分层职责说明

### 4.1 `api/`

这一层只负责 HTTP 接口，不写核心业务逻辑。

职责：

- 接收请求
- 参数校验
- 调用 service
- 返回统一响应

不应该做的事：

- 直接写 SQL
- 直接调用 OpenAI
- 在路由函数里拼装复杂业务流程

### 4.2 `schemas/`

这一层负责请求体、响应体和内部 DTO 定义。

职责：

- 定义接口输入输出格式
- 保证字段类型清晰
- 统一错误返回结构

例如：

- `AskQuestionRequest`
- `QuestionDetailResponse`
- `SaveAnswerFeedbackRequest`
- `RecommendationItem`

### 4.3 `services/`

这是业务核心层，也是后面最重要的一层。

职责：

- 编排多个 repository 和外部服务
- 实现单轮问答、多轮对话、推荐生成等业务流程
- 决定事务边界

你可以把它理解成：

- route 决定“入口”
- service 决定“业务怎么跑”
- repository 决定“数据怎么存”

### 4.4 `repositories/`

这一层专门负责数据库读写，建议使用 `python-oracledb` 直接访问 Oracle，而不是当前阶段就上 ORM。

职责：

- 执行 SQL
- 调用存储过程
- 做表级别的数据查询与写入

这样设计的好处是：

- 和你现有的 Oracle DDL、过程、触发器天然一致
- 避免 ORM 在 Oracle 特性支持上的额外复杂度
- 更利于直接调用 `qa_app_pkg`

### 4.5 `integrations/llm/`

这一层只负责接 AI 提供商，不和数据库逻辑混在一起。

职责：

- 构造模型调用请求
- 发送 prompt
- 获取返回文本
- 记录 token 使用量、模型名等元信息

后续即使从 OpenAI 换到其他模型服务，也只需要改这一层。

### 4.6 `prompts/`

这一层保存提示词模板。

职责：

- 单轮问答 prompt 模板
- 多轮会话 prompt 模板
- 系统角色说明

这样做的原因是：

- prompt 不应该硬编码在 service 里
- 后续调 prompt 时更容易比较版本

## 5. 业务模块设计

### 5.1 问题、AI 首答与人工回答模块

建议文件：

- `api/routes/questions.py`
- `api/routes/answers.py`
- `services/question_service.py`
- `services/ai_answer_service.py`
- `services/answer_service.py`
- `repositories/question_repository.py`
- `repositories/answer_repository.py`
- `repositories/log_repository.py`
- `integrations/llm/openai_client.py`
- `prompts/question_answer_prompt.py`

当前能力：

- 提问并生成 AI 首答
- 问题列表与问题详情查询
- 用户人工回答问题
- Prompt 日志落库

### 5.2 分类、标签与搜索模块

建议文件：

- `api/routes/meta.py`
- `api/routes/search.py`
- `services/meta_service.py`
- `services/search_service.py`
- `repositories/meta_repository.py`
- `repositories/search_repository.py`

当前能力：

- 查询分类与标签元数据
- 按关键词、分类、标签搜索问题
- 可选写入 `SEARCH_HISTORY`

### 5.3 浏览、收藏、反馈与评论模块

建议文件：

- `api/routes/browse.py`
- `api/routes/favorites.py`
- `api/routes/feedback.py`
- `api/routes/comments.py`
- `services/browse_service.py`
- `services/favorite_service.py`
- `services/feedback_service.py`
- `services/comment_service.py`
- `repositories/browse_repository.py`
- `repositories/favorite_repository.py`
- `repositories/feedback_repository.py`
- `repositories/comment_repository.py`

当前能力：

- 记录浏览行为
- 收藏问题
- 取消收藏
- 提交回答反馈
- 对同一回答更新已有反馈
- 发表评论、回复评论与软删除评论

### 5.4 推荐模块

建议文件：

- `api/routes/recommendations.py`
- `services/recommendation_service.py`
- `repositories/recommendation_repository.py`

推荐 service 的职责：

- 调用 `qa_app_pkg.rebuild_user_tag_profile`
- 调用 `qa_app_pkg.generate_recommendations`
- 查询 `RECOMMENDATIONS` 返回结果

这一层尽量复用数据库里已经写好的过程，不要在应用层重复实现同一套推荐逻辑。

### 5.5 网页前端与 CLI 测试前端

建议文件：

- `app/web/login.html`
- `app/web/home.html`
- `app/web/detail.html`
- `frontend_cli/main.py`
- `frontend_cli/api_client.py`
- `frontend_cli/render.py`
- `scripts/start_business_test.py`

当前能力：

- 网页端已具备登录、首页列表、搜索、发帖、详情、回答、点赞/点踩等主链路
- 网页端页面源码位于 `app/web/`，当前已经通过 FastAPI 提供统一访问入口
- 通过 HTTP 调后端接口，不直接依赖 service/repository
- 覆盖问题、回答、收藏、反馈、评论、推荐等核心测试入口
- 一键拉起 API 并进入菜单模式

## 6. 单轮 AI 问答主流程

这是最应该优先落地的一条链路。

建议实现流程如下：

1. 前端或调用方发送“提问”请求
2. `questions` 路由接收参数
3. `question_service` 先写入 `QUESTIONS`
4. 根据分类或输入标签写入 `QUESTION_TAGS`
5. `ai_answer_service` 读取问题信息并组装 prompt
6. `openai_client` 调用模型
7. 将模型输出写入 `ANSWERS`
8. 将 prompt、response、model、token_usage 写入 `AI_PROMPT_LOG`
9. 返回问题详情与回答内容

对应数据表：

- `QUESTIONS`
- `QUESTION_TAGS`
- `ANSWERS`
- `AI_PROMPT_LOG`

## 7. 建议的首批接口

建议先做以下接口，而不是一次性铺满所有能力：

### 7.1 认证

- `POST /api/auth/register`
- `POST /api/auth/login`

### 7.2 问题与回答

- `POST /api/questions/ask`
- `GET /api/questions/{question_id}`
- `GET /api/questions`
- `POST /api/questions/{question_id}/answers`

### 7.3 元数据与搜索

- `GET /api/categories`
- `GET /api/tags`
- `GET /api/search/questions`

### 7.4 社区行为

- `POST /api/questions/{question_id}/browse`
- `POST /api/questions/{question_id}/favorite`
- `DELETE /api/questions/{question_id}/favorite`
- `POST /api/answers/{answer_id}/feedback`
- `POST /api/answers/{answer_id}/comments`
- `GET /api/answers/{answer_id}/comments`
- `DELETE /api/comments/{comment_id}`

### 7.5 推荐

- `POST /api/users/{user_id}/profile/rebuild`
- `POST /api/users/{user_id}/recommendations/generate`
- `GET /api/users/{user_id}/recommendations`

### 7.6 多轮对话

- 当前未实现，保留为后续扩展能力

## 8. 各模块与数据库表映射

| 业务模块 | 主要 service | 主要 repository | 关联表 |
| --- | --- | --- | --- |
| 问题与人工回答 | `question_service`, `answer_service` | `question_repository`, `answer_repository` | `QUESTIONS`, `QUESTION_TAGS`, `ANSWERS`, `TAGS` |
| AI 首答 | `ai_answer_service` | `answer_repository`, `log_repository` | `ANSWERS`, `AI_PROMPT_LOG` |
| 元数据 | `meta_service` | `meta_repository` | `CATEGORIES`, `TAGS` |
| 搜索 | `search_service` | `search_repository` | `QUESTIONS`, `QUESTION_TAGS`, `SEARCH_HISTORY` |
| 浏览 | `browse_service` | `browse_repository` | `BROWSE_HISTORY` |
| 收藏 | `favorite_service` | `favorite_repository` | `FAVORITES` |
| 回答反馈 | `feedback_service` | `feedback_repository` | `ANSWER_FEEDBACK` |
| 评论与回复 | `comment_service` | `comment_repository` | `ANSWER_COMMENTS` |
| 推荐 | `recommendation_service` | `recommendation_repository` | `USER_TAG_PROFILE`, `RECOMMENDATIONS` |
| 审计日志 | `log_repository` | `log_repository` | `AI_PROMPT_LOG`, `LOGIN_LOG`, `OPERATION_LOG` |

## 9. 配置文件建议

除了当前已有的 Oracle 配置，建议为应用层新增以下环境变量：

```env
APP_HOST=0.0.0.0
APP_PORT=8000
APP_ENV=dev

APP_USER=AI_QA_APP
APP_USER_PASSWORD=ChangeMeApp123
ORACLE_DB_HOST=localhost
ORACLE_SERVICE_NAME=FREEPDB1

DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

说明：

- 当前代码通过 `.env` 中的 `APP_USER`、`APP_USER_PASSWORD` 连接固定业务 schema
- `DEEPSEEK_BASE_URL` 采用 OpenAI 兼容调用方式，默认即可对接 DeepSeek

## 10. 当前实现进度与下一阶段优先级

当前代码已经完成这些主链路：

- 注册、登录与 JWT 房卡发放
- 问题列表、问题详情、AI 首答
- 纯社区式发帖
- 用户人工回答
- 分类标签、搜索、浏览、收藏、反馈
- 评论与楼中楼回复
- 用户画像与推荐生成
- 网页端主链路
- 独立 CLI 业务测试入口

下一阶段更值得优先补的是：

### 10.1 收口安全配置

- 确保不同环境使用独立且足够强的 JWT 密钥
- 继续补后台用户状态管理与审计查询能力

### 10.2 继续清理鉴权过渡接口

- 合并重复或语义重叠的反馈入口
- 继续拆分 `questions.py` 中混杂的历史遗留逻辑

### 10.3 采纳答案

- 支持提问者采纳某条回答
- 让问题状态与最佳答案形成明确闭环

### 10.4 用户中心

- 我的问题
- 我的回答
- 我的收藏
- 我的搜索与浏览历史

### 10.5 登录与鉴权收口

- 当前登录、注册和 JWT 已基础落地
- 但仍与显式 `user_id` 模式并存，后续应继续收口权限控制与审计

### 10.6 多轮对话

- 当前未实现
- 等社区主链路稳定后再扩展

## 11. 当前核心代码文件

如果你现在要快速理解当前业务实现，优先看这些文件：

```text
app/main.py
app/api/router.py
app/api/routes/questions.py
app/api/routes/answers.py
app/api/routes/comments.py
app/api/routes/recommendations.py
app/services/question_service.py
app/services/ai_answer_service.py
app/services/answer_service.py
app/services/comment_service.py
app/repositories/question_repository.py
app/repositories/answer_repository.py
app/repositories/comment_repository.py
app/repositories/recommendation_repository.py
app/integrations/llm/openai_client.py
app/prompts/question_answer_prompt.py
frontend_cli/main.py
scripts/start_business_test.py
```

看完这批文件，基本就能把当前“问答社区 + AI 首答 + 评论回复 + 推荐”的主链路串起来。

## 12. 结论

你这个项目当前已经不只是“数据库设计”，而是进入了可运行的业务代码阶段。

最稳妥的落地方式是：

- 继续保持单体后端，同时维护网页前端和独立 CLI 两条验证链路
- 继续复用 Oracle 里已经写好的约束、触发器和推荐过程
- 优先收口接口契约、鉴权和网页前端交付方式
- 等采纳答案、用户中心、登录态稳定后，再考虑多轮对话和更复杂推荐策略
