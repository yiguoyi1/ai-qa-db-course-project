# 当前项目现状

这份文档用于说明仓库在当前代码状态下已经完成了什么、哪些能力已经能演示、以及下一步最值得优先收口的地方。

如果你刚接手项目，建议阅读顺序：

1. [README.md](../README.md)
2. [docs/current_status.md](current_status.md)
3. [docs/README.md](README.md)
4. [docs/onboarding_checklist.md](onboarding_checklist.md)

## 1. 当前项目定位

当前项目已经不是单纯的数据库课程设计稿，而是一个可以本地运行的问答社区 MVP：

- 后端：`FastAPI`
- 数据库：`Oracle AI Database 26ai Free`
- AI 提供商：`DeepSeek`，通过 OpenAI 兼容 SDK 调用
- 网页前端：`app/web/` 下的静态 HTML 页面
- 测试前端：`frontend_cli/` 下的独立 CLI

项目主线是：

- 用户注册、登录
- 用户发布问题
- 可选触发 AI 首答
- 用户继续发布人工回答
- 用户搜索、浏览、收藏、点赞/点踩
- 系统根据行为生成推荐

## 2. 当前已完成功能

### 2.1 数据库与基础设施

- Oracle 26ai Docker 本地运行方案
- 完整业务 schema、主外键、唯一约束、检查约束、索引
- 统计同步触发器
- 推荐相关包与过程 `qa_app_pkg`
- 种子数据导入与结构校验脚本

### 2.2 后端 API

- `GET /health`
- 用户注册：`POST /api/auth/register`
- 用户登录：`POST /api/auth/login`
- AI 首答提问：`POST /api/questions/ask`
- 纯社区式发帖：`POST /api/questions`
- 问题列表与详情：`GET /api/questions`、`GET /api/questions/{question_id}`
- 人工回答：`POST /api/questions/{question_id}/answers`
- 采纳答案：`POST /api/questions/{question_id}/accept-answer`
- 分类、标签、搜索：`GET /api/categories`、`GET /api/tags`、`GET /api/search/questions`
- 搜索历史：`GET /api/search/history`
- 浏览、收藏：`POST /api/questions/{question_id}/browse`、`POST /api/questions/{question_id}/favorite`、`DELETE /api/questions/{question_id}/favorite`
- 回答反馈与状态回显：`POST /api/answers/{answer_id}/feedback`、`GET /api/questions/{question_id}/feedbacks`
- 评论与楼中楼：`POST /api/answers/{answer_id}/comments`、`GET /api/answers/{answer_id}/comments`、`DELETE /api/comments/{comment_id}`
- 用户中心：`GET /api/users/{user_id}/profile`、`GET /api/users/{user_id}/questions`、`GET /api/users/{user_id}/answers`、`GET /api/users/{user_id}/favorites`
- 用户历史：`GET /api/users/{user_id}/browse-history`、`GET /api/users/{user_id}/search-history`
- 用户画像与推荐：`POST /api/users/{user_id}/profile/rebuild`、`POST /api/users/{user_id}/recommendations/generate`、`GET /api/users/{user_id}/recommendations`
- 头像与内容图片：`POST /api/users/me/avatar`、`GET /api/users/me/avatar`、`DELETE /api/users/me/avatar`
- 问题配图：`POST /api/questions/{question_id}/images`、`GET /api/questions/{question_id}/images`、`DELETE /api/questions/{question_id}/images/{media_id}`
- 回答配图：`POST /api/answers/{answer_id}/images`、`GET /api/answers/{answer_id}/images`、`DELETE /api/answers/{answer_id}/images/{media_id}`

### 2.3 网页前端

当前仓库已经包含由 FastAPI 统一交付的网页前端，页面源码位于 `app/web/`：

- [app/web/login.html](../app/web/login.html)
  - 登录
  - 注册
  - 登录成功后将 `access_token`、`user_id`、`username`、`user_role` 保存到 `sessionStorage`，不同标签页之间互不干扰
- [app/web/home.html](../app/web/home.html)
  - 首页问题流
  - 搜索问题
  - 搜索历史下拉
  - 首页问题流中的收藏 / 取消收藏
  - 收藏数量回显
  - 发帖弹窗
  - 纯社区发帖与 AI 发帖都要求填写正文
  - 可切换“纯社区发帖”与“发帖并触发 AI 首答”
  - 热门标签动态加载
  - 登录态展示与退出登录
- [app/web/detail.html](../app/web/detail.html)
  - 问题详情
  - 回答列表
  - Markdown 渲染与代码高亮
  - 发布人工回答
  - 收藏 / 取消收藏
  - 收藏状态与收藏数量回显
  - 采纳答案与已采纳答案高亮
  - 点赞 / 点踩
  - 当前用户反馈状态回显
- [app/web/profile.html](../app/web/profile.html)
  - 用户中心总览
  - 我的问题 / 我的回答 / 我的收藏
  - 我的推荐、最近浏览、最近搜索
  - 兴趣画像重建与推荐刷新
  - 收藏列表里直接取消收藏
- [app/web/admin.html](../app/web/admin.html)
  - 管理员后台总览
  - 用户治理：筛选用户，修改角色和状态
  - 分类管理：创建分类，修改名称、描述和启用状态
  - 内容治理：查看最近问题，展开回答和评论 ID，并一键填入状态治理表单
  - 审计日志：查询登录日志和操作日志
  - 中文友好展示角色、状态和日志类型，后端枚举值保持不变

当前推荐访问入口：

- `/login`
- `/home`
- `/me`
- `/admin`
- `/questions/{question_id}`

### 2.4 CLI 测试前端

- `frontend_cli/` 仍然保留，适合验证接口和回归测试
- `scripts/start_business_test.py` 可以自动检查 `/health` 并拉起 CLI 菜单

## 3. 当前最值得先改的地方

### 3.1 已完成阶段：统一接口契约与鉴权方式（第一阶段）

这一阶段已经完成到“可继续开发”的状态，主要包括：

- 把登录鉴权依赖抽到了独立模块
- 受保护写接口已经以 JWT 登录态为主
- 少量显式 `user_id` 字段仅保留过渡兼容，并要求与当前登录用户一致
- CLI 已补充登录接口和 `Bearer Token` 透传能力

当前仍然保留的收尾项有：

- 部分写接口仍保留显式 `user_id` 兼容字段
- CLI 里仍有少量旧交互习惯待继续收口

### 3.2 已完成阶段：统一网页前端交付方式（第二阶段）

这一阶段已经完成到“可直接演示与交接”的状态，主要包括：

- FastAPI 已提供统一网页入口 `/login`、`/home`、`/questions/{question_id}`
- 页面请求已经改为同源 `/api/...` 调用，不再写死 `127.0.0.1:8000`
- 首页热门标签已经改为通过真实标签接口动态加载
- 页面跳转已经改为应用路由，不再依赖直接打开本地 `html` 文件

当前仍建议保持的协作口径：

- 页面源码仍然保存在 `app/web/`
- 运行和演示时，应优先通过 FastAPI 页面入口访问，而不是直接双击本地文件

### 3.3 已完成阶段：发帖正文规则统一（第三阶段）

这一阶段已经完成到“前后端口径一致”的状态，主要包括：

- 首页发帖弹窗已将“详细描述”明确为必填
- `POST /api/questions` 与 `POST /api/questions/ask` 现在都统一要求 `content` 非空
- 网页端提交前会先做必填校验，避免用户点击后才收到后端报错

当前仍建议后续补的点有：

- 分类、标签选择仍是简化实现，前端还没有完整暴露出来
- 社区发帖成功后的返回结构仍比较简化，后续可以继续统一

### 3.4 已完成阶段：登录安全基础收口（第四阶段）

这一阶段已经完成到“基础规则已生效”的状态，主要包括：

- JWT 密钥、算法、有效期已经进入 `.env`
- 登录成功、密码错误、锁定账号登录都会写入 `LOGIN_LOG`
- 账号状态口径已经明确：
  - `ACTIVE`：允许登录，也允许继续访问受保护接口
  - `INACTIVE`：拒绝登录，也拒绝访问受保护接口
  - `LOCKED`：拒绝登录，也拒绝访问受保护接口；登录审计结果记为 `LOCKED`
  - `DISABLED`：拒绝登录，也拒绝访问受保护接口
- 受保护接口在 JWT 解码后会再次检查用户当前状态，避免旧 token 绕过停用/锁定
- `JWT_SECRET_KEY` 必须是当前环境单独设置的强随机密钥，示例占位值不可直接用于真实环境

当前仍建议后续补的点有：

- 不存在 `user_id` 的登录失败尝试仍无法写入 `LOGIN_LOG`
- 审计日志后续可继续补导出、时间范围筛选和更复杂的检索条件

### 3.5 已完成阶段：继续清理鉴权过渡接口

这一轮已经完成的收口包括：

1. 回答反馈写入口统一为 `POST /api/answers/{answer_id}/feedback`
2. `questions.py` 中移除了反馈相关的混入路由
3. 搜索读接口不再接受历史 `user_id` 查询参数，搜索历史改为仅依据当前 JWT 登录态记录
4. CLI 与文档已同步到新的接口口径

### 3.6 已完成阶段：采纳答案主链路（第五阶段）

这一阶段已经完成到“前后端闭环可演示”的状态，主要包括：

1. 数据库已支持 `accepted_answer_id`
2. 后端已提供 `POST /api/questions/{question_id}/accept-answer`
3. 只有提问者或管理员可以采纳答案
4. 采纳后问题状态自动变为 `RESOLVED`
5. 问题详情页会高亮已采纳答案，并禁止继续发布新回答
6. 首页和搜索页默认会继续展示 `RESOLVED` 问题，不会在采纳后从列表里“消失”

### 3.7 已完成阶段：用户中心主链路（第六阶段）

这一阶段已经完成到“前后端可直接演示”的状态，主要包括：

1. 后端已提供用户中心聚合接口：个人概览、我的问题、我的回答、我的收藏、最近浏览、最近搜索
2. 网页端新增 `/me` 页面，并从首页、详情页统一进入
3. 用户中心已接入推荐列表、兴趣画像重建和推荐刷新动作
4. 收藏列表支持直接取消收藏
5. 详情页已补记浏览历史，最近浏览链路在网页端可闭环

### 3.8 已完成阶段：头像、问题配图与回答配图 MVP

当前媒体能力已经从设计推进到前后端可用状态：

1. `MEDIA_ASSETS` 统一记录头像、问题配图和回答配图元数据，并用 `FILE_CONTENT BLOB` 保存图片二进制
2. 用户头像支持上传、查看、删除
3. 问题配图支持上传、列表、删除，并在问题详情 `images` 中返回
4. 回答配图支持上传、列表、删除，并在问题详情的回答对象 `images` 中返回
5. CLI 已补充问题配图和回答配图的上传、列表、删除命令
6. 网页端发帖弹窗支持选择问题配图，回答框支持选择回答配图，并在详情页显示在正文下方

当前仍保留为后续增强的媒体能力：

- 评论图片
- 图片审核、隐藏与清理后台

### 3.9 已完成阶段：管理员网页后台与治理交互

这一阶段已经完成到“可演示治理闭环”的状态，主要包括：

1. FastAPI 已提供 `/admin` 和 `/admin.html` 页面入口
2. 普通社区页面会对管理员展示“管理后台”入口
3. 管理后台与社区页面统一为蓝色主色、白色卡片和浅灰背景
4. 管理后台下拉选项和状态徽标使用中文友好文案
5. 后台支持总览、用户治理、分类管理、内容治理和审计日志查询
6. 内容治理页支持查询最近问题，查看回答 ID 和评论 ID，并一键填入状态调整表单

### 3.10 当前第一优先级：补齐社区核心能力

当前最适合继续做的业务能力仍然是：

1. 网页端评论与楼中楼入口
2. 媒体审核与清理后台
3. 多轮对话正式业务链

## 4. 当前仍未完成或未完全收口的能力

- 网页端评论、楼中楼回复的完整展示与交互入口
- 多轮对话正式业务链
- 评论图片与图片审核后台
- 推荐规则人工干预入口

## 5. 当前最稳妥的协作口径

现在最准确的项目描述应该是：

- 这是一个“带 AI 首答、行为记录、推荐能力、网页端社区页面和基础管理员后台”的问答社区 MVP
- CLI 和网页前端同时存在
- 写接口现在已经以 JWT 登录态为主，旧 `user_id` 字段只保留过渡兼容与一致性校验
- 读接口已经收口到 JWT / 路径参数主导，剩余清理点主要集中在少量写接口兼容字段

如果后续继续开发，建议优先顺序为：

1. 先补网页端评论、回复完整闭环
2. 再补媒体审核与清理后台
3. 补多轮对话正式业务链
