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
- 桌面客户端：`desktop/` 下的 Tauri 轻量客户端壳
- 测试前端：`frontend_cli/` 下的独立 CLI

项目主线是：

- 对外产品首页展示与引导注册
- 用户注册、登录
- 用户发布问题
- 用户按推荐、热榜、分类、状态和标签浏览问题
- 可选触发 AI 首答
- 用户继续发布人工回答
- 用户围绕 AI 首答继续多轮追问
- 用户搜索、浏览、收藏、点赞/点踩
- 用户上传头像、问题配图和回答配图
- 管理员治理用户、分类、标签、内容和审计日志
- 系统根据行为生成推荐
- 桌面端通过 Tauri 独立窗口访问现有 FastAPI Web 前端

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
- 发帖标签增强：`tag_ids` 绑定已有标签，`custom_tags` 创建或复用自定义标签，`auto_tag` 支持无标签时 AI 自动补标签
- 问题列表与详情：`GET /api/questions`、`GET /api/questions/{question_id}`
- 人工回答：`POST /api/questions/{question_id}/answers`
- 采纳答案：`POST /api/questions/{question_id}/accept-answer`
- 分类、标签、搜索：`GET /api/categories`、`GET /api/tags`、`GET /api/tags/suggestions`、`GET /api/search/questions`
- 搜索历史：`GET /api/search/history`
- 浏览、收藏：`POST /api/questions/{question_id}/browse`、`POST /api/questions/{question_id}/favorite`、`DELETE /api/questions/{question_id}/favorite`
- 回答反馈与状态回显：`POST /api/answers/{answer_id}/feedback`、`GET /api/questions/{question_id}/feedbacks`
- 评论与楼中楼：`POST /api/answers/{answer_id}/comments`、`GET /api/answers/{answer_id}/comments`、`DELETE /api/comments/{comment_id}`
- AI 多轮追问：`POST /api/questions/{question_id}/answers/{answer_id}/follow-up`、`GET /api/questions/{question_id}/answers/{answer_id}/follow-up-sessions`、`GET /api/chat/sessions/{session_id}`
- 用户中心：`GET /api/users/me/profile`、`PATCH /api/users/me/profile`、`GET /api/users/{user_id}/profile`、`GET /api/users/{user_id}/questions`、`GET /api/users/{user_id}/answers`、`GET /api/users/{user_id}/favorites`
- 用户历史：`GET /api/users/{user_id}/browse-history`、`GET /api/users/{user_id}/search-history`
- 用户画像与推荐：`POST /api/users/{user_id}/profile/rebuild`、`POST /api/users/{user_id}/recommendations/generate`、`GET /api/users/{user_id}/recommendations`
- 管理员标签治理：`GET /api/admin/tags`、`PATCH /api/admin/tags/{tag_id}`
- 管理员基础治理：用户、分类、问题状态、评论状态、登录日志和操作日志相关接口
- 头像与内容图片：`POST /api/users/me/avatar`、`GET /api/users/me/avatar`、`DELETE /api/users/me/avatar`
- 问题配图：`POST /api/questions/{question_id}/images`、`GET /api/questions/{question_id}/images`、`DELETE /api/questions/{question_id}/images/{media_id}`
- 回答配图：`POST /api/answers/{answer_id}/images`、`GET /api/answers/{answer_id}/images`、`DELETE /api/answers/{answer_id}/images/{media_id}`
- 媒体读取：`GET /api/media/files/{file_name}`

### 2.3 网页前端

当前仓库已经包含由 FastAPI 统一交付的网页前端，页面源码位于 `app/web/`：

- [app/web/index.html](../app/web/index.html)
  - 对外产品介绍首页
  - 产品优势、核心功能、使用场景、热门标签、FAQ 和立即体验入口
- [app/web/login.html](../app/web/login.html)
  - 登录
  - 注册
  - 根据用户名/密码错误和服务异常显示不同的用户友好提示
  - 登录成功后将 `access_token`、`user_id`、`username`、`user_role` 保存到 `sessionStorage`，不同标签页之间互不干扰
- [app/web/home.html](../app/web/home.html)
  - 推荐 / 热榜问题流
  - 分类、状态、标签筛选
  - 搜索问题
  - 搜索历史下拉，和其他页面搜索框保持一致
  - 首页问题流中的收藏 / 取消收藏
  - 收藏数量回显
  - 发帖弹窗
  - 纯社区发帖与 AI 发帖都要求填写正文
  - 可切换“纯社区发帖”与“发帖并触发 AI 首答”
  - 支持选择已有标签、输入自定义标签、查看标签建议和无标签时自动识别
  - 支持选择问题配图并随问题发布
  - 热门标签动态加载
  - 顶部导航与头像下拉菜单
  - 登录态展示与退出登录
- [app/web/detail.html](../app/web/detail.html)
  - 问题详情
  - 回答列表
  - 问题配图和回答配图展示
  - 当前用户可删除自己发布的问题配图和回答配图
  - Markdown 渲染与代码高亮
  - 发布人工回答
  - 发布回答时支持选择回答配图
  - 收藏 / 取消收藏
  - 收藏状态与收藏数量回显
  - 采纳答案与已采纳答案高亮
  - 点赞 / 点踩
  - 点赞 / 点踩可切换和取消
  - 当前用户反馈状态回显
  - 评论、楼中楼回复和默认折叠的子回复
  - 围绕 AI 首答发起和查看多轮追问会话
- [app/web/profile.html](../app/web/profile.html)
  - 用户中心总览
  - 个人资料展示和修改
  - 头像上传、查看和删除
  - 我的问题 / 我的回答 / 我的收藏
  - 我的推荐、最近浏览、最近搜索
  - 兴趣画像重建与推荐刷新
  - 收藏列表里直接取消收藏
  - 列表模块支持继续加载
- [app/web/admin.html](../app/web/admin.html)
  - 管理员后台总览
  - 用户治理：筛选用户，修改角色和状态
  - 分类管理：创建分类，修改名称、描述和启用状态
  - 标签治理：查看标签元数据，修改标签状态和描述
  - 内容治理：查看最近问题，展开回答和评论 ID，并一键填入状态治理表单
  - 审计日志：查询登录日志和操作日志
  - 中文友好展示角色、状态和日志类型，后端枚举值保持不变

当前推荐访问入口：

- `/`
- `/login`
- `/home`
- `/home?section=recommend`
- `/home?section=hot`
- `/me`
- `/admin`
- `/questions/{question_id}`

### 2.4 CLI 测试前端

- `frontend_cli/` 仍然保留，适合验证接口和回归测试
- `scripts/start_business_test.py` 可以自动检查 `/health` 并拉起 CLI 菜单

### 2.5 桌面客户端

当前仓库已经新增 Tauri 桌面客户端，源码位于 `desktop/`：

- [desktop/src/index.html](../desktop/src/index.html)
  - 本地启动页
  - 自动检测 `http://127.0.0.1:8000/health`
  - 后端可用后进入现有 `/login` 页面
  - 后端不可用时展示启动命令和重新检测入口
- [desktop/src-tauri/](../desktop/src-tauri)
  - Tauri 2 桌面壳配置
  - macOS / Windows / Linux 图标资源
  - Windows 专用打包配置 `tauri.windows.conf.json`
  - Rust 入口代码
- [desktop/scripts/dev-with-backend.sh](../desktop/scripts/dev-with-backend.sh)
  - macOS 开发辅助脚本
  - 可以检测并拉起本地 FastAPI 后端，再启动 Tauri 开发窗口
- [desktop/scripts/dev-with-backend.ps1](../desktop/scripts/dev-with-backend.ps1)
  - Windows PowerShell 开发辅助脚本
- [desktop/scripts/build-windows.ps1](../desktop/scripts/build-windows.ps1)
  - Windows 本机打包脚本
- [.github/workflows/build-desktop-windows.yml](../.github/workflows/build-desktop-windows.yml)
  - GitHub Actions Windows 出包工作流

当前已经验证：

1. 本机已安装 Node/npm、Rust/Cargo 和 Xcode Command Line Tools
2. `npm install` 可安装桌面端依赖
3. `npm run build` 可生成 macOS `.app` 和 `.dmg`
4. 构建产物位于 `desktop/src-tauri/target/release/bundle/`
5. Windows 构建入口已补齐，需在 Windows 或 GitHub Actions `windows-latest` 环境生成 `.msi` / `-setup.exe`

桌面端当前只作为客户端入口，不内置 Oracle、DeepSeek 或 FastAPI 服务，以保持原有 B/S 架构清晰。

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

- FastAPI 已提供统一网页入口 `/`、`/login`、`/home`、`/questions/{question_id}`、`/me`、`/admin`
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

- 发帖成功后的跳转、刷新和推荐重算提示还可以继续做得更产品化
- 标签合并、批量审核仍需要管理员侧进一步增强

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
5. 后台支持总览、用户治理、分类管理、标签治理、内容治理和审计日志查询
6. 内容治理页支持查询最近问题，查看回答 ID 和评论 ID，并一键填入状态调整表单

### 3.10 已完成阶段：网页端评论与楼中楼互动

这一阶段已经完成到“网页端首版互动闭环”的状态，主要包括：

1. 问题详情页回答卡片支持展开和收起评论区
2. 用户可发布一级评论，并可回复评论形成楼中楼
3. 子回复支持默认折叠、展开与收起
4. 用户可删除自己的评论，删除后保留楼层结构并显示占位状态
5. 页面通过现有评论接口完成评论加载、发布与删除交互

### 3.11 已完成阶段：AI 多轮追问前后端闭环

这一阶段已经完成到“前后端可演示、后端可自检”的状态，主要包括：

1. 会话正式锚定到 `QUESTION_ID + SEED_ANSWER_ID`
2. 支持创建新追问会话
3. 支持向已有会话继续追加一轮追问
4. 支持读取围绕某条 AI 首答的会话列表
5. 支持读取某条会话的完整消息历史
6. 每轮追问都会写入 `CHAT_MESSAGE`
7. 每轮 AI 回复都会写入 `AI_PROMPT_LOG`
8. 已提供本地自检脚本 `python -B .\\scripts\\validate_chat_followup.py`
9. 问题详情页已经提供“继续追问这条 AI 回答”的会话入口
10. 会话列表优先显示昵称，没有昵称时回退到用户名，并能正确区分本人和其他用户
11. AI 回复在追问窗口里已做段落、列表和代码块等基础格式化

### 3.12 已完成阶段：用户画像与 HYBRID 推荐增强

这一阶段已经完成到“数据库过程、后端读取和文档口径一致”的状态，主要包括：

1. 用户标签画像已纳入提问、回答、收藏、浏览、反馈、评论和搜索行为
2. 推荐生成已从单一标签推荐升级为 `HYBRID` 推荐
3. 推荐分数由画像分、热度分和新鲜度分组成
4. 推荐结果会通过 `REC_SOURCE` 区分画像命中和热度补充来源
5. 后端推荐查询仅返回 `ACTIVE` 标签，避免禁用标签继续出现在画像和推荐解释中
6. Oracle schema 校验脚本已覆盖 `HYBRID` 推荐类型和推荐分数预期

### 3.13 已完成阶段：网页端产品化与企业级 UI/UX 优化

这一阶段已经完成到“演示观感明显提升、主交互不被破坏”的状态，主要包括：

1. 新增对外产品介绍首页，形成从官网介绍到社区登录的完整入口
2. 顶部导航统一为品牌 Logo、推荐 / 热榜分区、搜索框和头像下拉菜单
3. 全站搜索框统一支持搜索历史下拉
4. 用户展示统一优先使用昵称，没有昵称时回退到用户名
5. 首页、详情页、用户中心、管理员后台统一蓝白浅灰的企业级视觉语言
6. 卡片、按钮、标签、表单、弹窗和空状态样式已经做过统一优化
7. 发帖弹窗滚动已限制在弹窗内部，避免滚轮穿透到底层页面

### 3.14 已完成阶段：Tauri 桌面客户端 MVP

这一阶段已经完成到“可打包桌面入口”的状态，主要包括：

1. 新增 `desktop/` Tauri 2 工程
2. 桌面端启动页可检测 FastAPI 后端健康状态
3. 后端可用后进入现有 Web 登录页，完整复用原有社区功能
4. 提供 `npm run dev`、`npm run dev:full` 和 `npm run build`
5. 已生成桌面端图标资源
6. macOS 构建已通过，产出 `.app` 与 `.dmg`
7. Windows 本地构建脚本和 CI 工作流已补齐，可生成 NSIS `-setup.exe` 与 WiX `.msi`

当前仍建议后续补的点有：

- 应用签名与公证，方便 macOS 正式分发
- 自动更新
- 托盘菜单和系统通知
- 可配置线上后端地址

### 3.15 当前第一优先级：治理与高级能力

当前最适合继续做的业务能力仍然是：

1. 评论图片与媒体审核、清理后台
2. 推荐规则人工干预入口
3. 采纳答案取消、采纳历史和更完整的答案治理
4. 标签合并、批量审核和标签质量治理

## 4. 当前仍未完成或未完全收口的能力

- 评论图片与图片审核后台
- 标签合并、批量审核和标签质量治理
- 推荐规则人工干预入口
- 采纳答案取消、采纳历史和更细的答案治理
- 通知、消息提醒和站内信

## 5. 当前最稳妥的协作口径

现在最准确的项目描述应该是：

- 这是一个“带 AI 首答、行为记录、推荐能力、网页端社区页面和基础管理员后台”的问答社区 MVP
- CLI 和网页前端同时存在
- 写接口现在已经以 JWT 登录态为主，旧 `user_id` 字段只保留过渡兼容与一致性校验
- 读接口已经收口到 JWT / 路径参数主导，剩余清理点主要集中在少量写接口兼容字段

如果后续继续开发，建议优先顺序为：

1. 先补评论图片与媒体审核、清理后台，避免图片能力只覆盖问题和回答
2. 补推荐规则人工干预入口，让管理员能解释和调控推荐结果
3. 补采纳答案取消、采纳历史和更细的答案治理
4. 补标签合并、批量审核和标签质量治理，避免 AI 或用户自定义标签长期失控
