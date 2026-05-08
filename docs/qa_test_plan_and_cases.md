# AI QA Community 测试计划与测试用例

生成日期：2026-05-01  
适用项目：`ai-qa-db-course-project` / 智能问答记录与推荐管理系统  
测试阶段：开发基本完成后的系统测试、接口测试、回归测试和上线前验收

## 1. 项目理解

### 1.1 信息来源

本测试文档基于当前仓库实际代码与文档梳理，重点读取了：

- 后端入口与路由：`app/main.py`、`app/web_routes.py`、`app/api/routes/*`
- 鉴权逻辑：`app/api/auth_deps.py`、`app/services/auth_service.py`
- 请求和响应模型：`app/schemas/*`
- 业务服务：`app/services/*`
- 数据库脚本：`sql/create_tables.sql`、`sql/procedures.sql`、`sql/triggers.sql`、`sql/views.sql`、`sql/migrations/*`
- 前端页面：`app/web/index.html`、`login.html`、`home.html`、`detail.html`、`profile.html`、`admin.html`
- 桌面端：`desktop/package.json`、`desktop/src-tauri/tauri.conf.json`
- 现有说明：`README.md`、`docs/current_status.md`、`docs/testing_guide.md`

### 1.2 项目类型与技术栈

项目类型：全栈 AI 问答社区 MVP，包含 Web 前端、FastAPI 后端、Oracle 数据库、AI 首答和 Tauri 桌面客户端入口。  
技术栈：FastAPI、python-oracledb、Oracle AI Database 26ai Free、DeepSeek(OpenAI SDK 兼容调用)、原生 HTML/CSS/JavaScript、Tauri 2、Python CLI。  
认证方式：`POST /api/auth/login` 返回 JWT，前端保存到 `sessionStorage`，受保护接口通过 `Authorization: Bearer <token>` 调用。  
数据存储：Oracle 业务表覆盖用户、分类、标签、问题、回答、反馈、评论、收藏、浏览历史、搜索历史、推荐、画像、AI 会话、媒体、登录日志和操作日志。

### 1.3 核心功能模块

- 产品首页：`/`，展示产品介绍、功能、热门标签、FAQ、桌面客户端下载入口。
- 登录注册：`/login`，支持注册、登录、失败提示、JWT 登录态保存、退出登录。
- 游客浏览：未登录可访问 `/home`、`/questions/{question_id}`、搜索、筛选、查看公开回答/评论/图片。
- 问题流：推荐、热榜、分类、状态、标签筛选、分页、收藏状态回显。
- 发帖：纯社区发帖 `POST /api/questions`，AI 首答发帖 `POST /api/questions/ask`，支持已有标签、自定义标签、AI 自动标签、问题配图。
- 问题详情：问题内容、标签、图片、回答列表、Markdown 渲染、回答配图、收藏、浏览记录。
- 回答与采纳：人工回答、AI 回答、提问者或管理员采纳答案、已采纳高亮。
- 社区互动：回答点赞/点踩/评分、评论、楼中楼回复、软删除评论、收藏/取消收藏。
- AI 多轮追问：围绕 AI 回答创建/续写会话，查看本人会话和消息。
- 用户中心：个人资料、头像上传/删除、我的问题、我的回答、我的收藏、最近浏览、最近搜索、画像重建和推荐生成。
- 管理后台：用户治理、分类管理、标签治理、问题/评论状态治理、登录日志和操作日志查询。
- 媒体：用户头像、问题配图、回答配图、Oracle BLOB 读取，支持 JPEG/PNG/WebP，单文件最大 50MB。
- 桌面客户端：Tauri 壳检测后端 `/health`，可进入服务器 `/home`。
- CLI：`frontend_cli` 作为 HTTP 调用型测试前端，可用于接口演示和回归。

### 1.4 关键用户流程

1. 游客打开 `/`，进入 `/home`，搜索/筛选问题，打开详情页，查看回答、图片和评论。
2. 用户注册账号，登录成功后进入 `/home`，右上角显示用户信息。
3. 登录用户发布纯社区问题，选择分类/标签/图片，进入详情页查看问题。
4. 登录用户发布 AI 首答问题，系统创建问题、调用 DeepSeek 生成 AI 回答、记录 prompt 日志。
5. 其他用户在详情页发布人工回答，提问者或管理员采纳答案。
6. 用户收藏问题、取消收藏、点赞/点踩回答、发表评论和楼中楼回复。
7. 用户围绕 AI 回答发起追问，后续进入已有会话继续追问。
8. 用户进入 `/me` 修改资料、上传头像、查看我的问题/回答/收藏/历史、重建画像并刷新推荐。
9. 管理员进入 `/admin` 治理用户、分类、标签、内容状态，并查看登录/操作日志。
10. 桌面客户端启动后检测公网或本地后端，成功后进入现有 Web 社区。

### 1.5 明确假设与已知缺口

- 假设测试环境已完成 Oracle schema、迁移脚本和种子数据导入，至少有普通用户 A、普通用户 B、管理员用户。
- AI 首答和追问依赖 DeepSeek API Key 与网络可用性；若外部服务不可用，AI 链路需单独记录为环境阻塞或使用可控 mock。
- 当前仓库未发现正式单元测试目录或 pytest 测试套件；只有脚本级校验和冒烟工具，例如 `scripts/test-admin-api.ps1`、`scripts/validate-oracle-schema.ps1`。
- 评论图片、媒体审核、日志导出、推荐规则人工干预、标签合并/批量审核、通知类能力在当前代码和文档中属于未覆盖或后续增强。
- 已发现明显前端问题：`app/web/detail.html` 删除帖子成功后跳转到 `/profile`，但 `app/web_routes.py` 只注册了 `/me`，应作为上线前高风险项验证并修复。
- 登录审计存在已知限制：不存在的用户名登录失败没有 `user_id`，当前无法写入 `LOGIN_LOG`。
- 用户资料的 `email`、`phone` 当前仅做长度限制，未发现邮箱/手机号格式校验。

## 2. Test Plan

### A. 测试目标

- 验证核心业务流程在前端、后端、数据库之间闭环正确：注册登录、发帖、AI 首答、回答、采纳、收藏、反馈、评论、用户中心、推荐、后台治理。
- 验证认证、权限和用户状态控制可靠：未登录拦截、普通用户越权拦截、管理员权限、停用/锁定账号旧 token 失效。
- 验证接口输入校验、错误处理和数据库约束符合预期：空值、越界、非法 ID、重复数据、错误枚举、无效媒体。
- 验证 UI 可用性和一致性：游客态/登录态导航、表单校验、弹窗、列表分页、移动端响应式、错误提示。
- 验证基础安全能力：JWT 配置强制要求、CORS/CSP/安全响应头、路径穿越防护、媒体 MIME/大小限制、权限绕过防护。
- 验证上线前稳定性：健康检查、数据库连接池、AI 超时处理、桌面端启动检测、关键回归路径无阻塞缺陷。

### B. 测试范围

#### In Scope

- Web 页面：`/`、`/login`、`/home`、`/home?section=recommend`、`/home?section=hot`、`/questions/{question_id}`、`/me`、`/admin`。
- 后端 API：`/health`、`/api/auth/*`、`/api/questions*`、`/api/answers*`、`/api/comments*`、`/api/search*`、`/api/categories`、`/api/tags*`、`/api/users*`、`/api/admin*`、`/api/media/files/*`。
- 数据库：表约束、主外键、唯一约束、状态枚举、触发器统计字段、推荐/画像过程、登录和操作日志。
- 认证与权限：JWT、用户状态、管理员角色、本人资源访问、作者权限、游客限制。
- 媒体：头像、问题配图、回答配图上传/展示/删除，BLOB 读取。
- AI：AI 首答、AI 自动标签、多轮追问、AI prompt 日志。
- 桌面端：Tauri 启动页、后端检测、进入 Web 社区、打包产物基础验证。
- CLI/脚本：结构校验脚本、管理员 API 冒烟脚本、CLI 登录和接口调用。

#### Out of Scope

- 评论图片上传和展示。
- 图片审核、媒体隐藏、媒体清理后台。
- 推荐规则人工干预后台。
- 日志导出、复杂审计检索。
- 邮件、短信、站内信通知。
- 大规模压测和容量规划。
- 第三方 AI 模型质量评测，不评价答案事实正确性，只验证调用链路、失败处理和数据落库。
- 浏览器兼容矩阵的旧版本浏览器，优先 Chrome、Edge、Safari 最新稳定版。

### C. 测试策略

- 功能测试：按用户流程执行端到端测试，优先覆盖 P0 主链路。
- 接口测试：使用 curl/Postman/HTTP client/CLI 直接调用 API，验证状态码、响应结构、鉴权、错误信息和数据库副作用。
- UI 测试：覆盖页面入口、导航、表单校验、弹窗、列表、筛选、移动端布局、游客态和登录态差异。
- 回归测试：围绕登录、发帖、详情、回答、收藏、评论、管理员治理执行固定用例集。
- 边界测试：字段长度、空白字符串、非法 ID、非法枚举、分页边界、标签上限、媒体大小/类型上限。
- 安全测试（基础）：未授权访问、越权访问、旧 token 状态复查、管理员接口权限、媒体路径穿越、CSP/CORS/安全头、登录失败限流。
- 数据库测试：检查约束报错、级联影响、统计字段更新、唯一约束、推荐和画像过程结果。
- AI 依赖测试：区分 AI 服务可用、超时、Key 缺失、返回异常场景。

### D. 测试环境

- 前端环境：FastAPI 同源静态页面 `app/web/`，推荐访问 `http://127.0.0.1:8000`。
- 后端环境：Python 3.x，FastAPI + Uvicorn，启动命令 `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`。
- 数据库：Oracle AI Database 26ai Free，本地 Docker 或远程 Oracle，需导入 `sql/create_tables.sql`、迁移脚本、过程、触发器、视图和种子数据。
- AI 服务：DeepSeek API，环境变量 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_TIMEOUT_SECONDS`。
- 认证配置：`JWT_SECRET_KEY` 必须为当前环境强随机值且长度至少 32 字符，不能使用 `.env.example` 占位值。
- 桌面端：Node/npm、Rust/Cargo、Tauri 2；macOS 需 Xcode Command Line Tools，Windows 需 WebView2 Runtime 和 Microsoft C++ Build Tools。
- 浏览器：Chrome、Edge、Safari 最新稳定版；移动端使用浏览器开发者工具模拟 390x844、768x1024、1440x900。

### E. 测试类型说明

- Unit Test：当前仓库未发现正式单元测试目录或 pytest 自动化套件，建议后续补 AuthService、QuestionService、MediaService、AdminService 的单元测试。
- Integration Test：通过 FastAPI + Oracle + DeepSeek 的接口级测试执行，重点验证服务层、仓储层和数据库约束联动。
- System Test：通过真实浏览器执行完整 Web 流程，覆盖游客、普通用户、管理员三类角色。
- UAT：由业务/验收人员按主流程确认演示可用性、页面文案、操作路径和核心数据闭环。

### F. 风险分析

- 登录系统风险：JWT 密钥配置错误会导致所有受保护接口 500；登录失败限流是内存级，服务重启后会清空；不存在用户名失败不写登录日志。
- 权限绕过风险：用户中心和推荐接口依赖 path `user_id` 与当前用户一致；管理员接口依赖 `get_admin_user`，需重点做越权测试。
- 用户状态风险：锁定/停用用户已有 token 必须在每次受保护接口调用时被重新拦截。
- 数据一致性风险：收藏数、回答数、点赞/点踩数、采纳状态、评论回复数依赖触发器或业务更新，需验证前端展示和数据库一致。
- AI 链路风险：DeepSeek Key、网络、超时、返回格式异常可能导致 AI 发帖或追问失败，需验证失败回滚和错误提示。
- 媒体风险：BLOB 文件较大可能带来上传超时、响应慢和存储增长；需验证 MIME、大小、数量、作者权限和路径穿越。
- 搜索风险：`SEARCH_USE_ORACLE_TEXT` 依赖迁移脚本和 Oracle Text 索引，开启/关闭模式应分别验证。
- 管理后台风险：用户状态、角色、内容状态修改属于高影响操作，需校验操作日志和页面中文展示。
- 前端路由风险：已发现删除帖子成功后跳转 `/profile`，当前后端未注册该路由，预期应跳转 `/me`。
- 测试覆盖风险：当前缺少自动化单元测试，回归主要依赖手工和脚本，后续修改容易产生行为回退。

## 3. Test Cases

测试数据准备：

- 普通用户 A：用于注册、登录、发帖、上传图片、评论、追问。
- 普通用户 B：用于跨用户查看、回答、收藏、越权验证。
- 管理员用户：用于 `/admin` 和 `/api/admin/*`。
- 分类/标签：至少 2 个 ACTIVE 分类、5 个 ACTIVE 标签、1 个 DISABLED 或 PENDING 标签。
- 媒体文件：合法 JPEG、PNG、WebP；非法 TXT/PDF；空文件；大于 50MB 的图片文件。
- 问题数据：至少 1 个 OPEN 问题、1 个有 AI 回答的问题、1 个有人工回答的问题、1 个 CLOSED/ARCHIVED/DELETED 状态问题。

| ID | 模块 | 测试点 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-ENV-001 | 环境 | 健康检查 | 后端已启动 | GET `/health` | 返回 200，响应为 `{"status":"ok"}` | P0 |
| TC-ENV-002 | 环境 | JWT 密钥占位值拦截 | `.env` 使用示例占位 `JWT_SECRET_KEY` | 调用登录或受保护接口 | 返回 500，提示 JWT 密钥必须配置强随机值；不得签发 token | P0 |
| TC-ENV-003 | 环境 | Oracle 连接池配置 | `.env` 配置数据库账号密码 | 打开 `/home` 并 GET `/api/categories` | 不出现连接配置错误；分类数据正常返回 | P0 |
| TC-ENV-004 | 环境 | 安全响应头 | 后端已启动 | 访问 `/home`，检查响应头 | 包含 CSP、`X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy` | P1 |
| TC-AUTH-001 | 登录注册 | 注册成功 | 用户名未存在 | 打开 `/login`；输入用户名、密码、昵称；提交注册 | 返回注册成功；数据库新增 ACTIVE USER；页面给出成功提示 | P0 |
| TC-AUTH-002 | 登录注册 | 注册字段校验 | 无 | 用户名少于 3 位；密码少于 6 位；昵称超过 50 字；分别提交 | 前端或 API 拒绝提交；API 返回 422 或业务错误；不得创建用户 | P0 |
| TC-AUTH-003 | 登录注册 | 重复用户名 | 已存在用户 A | 使用相同 username 注册 | 返回业务错误“用户名已被注册”；不得覆盖原用户 | P0 |
| TC-AUTH-004 | 登录注册 | 登录成功 | 用户 A ACTIVE | 输入正确用户名密码登录 | 返回 access_token、user_id、username、role；前端进入 `/home`；`sessionStorage` 保存登录态 | P0 |
| TC-AUTH-005 | 登录注册 | 登录错误提示 | 用户 A 存在 | 输入错误密码登录 | 返回“用户名或密码错误”；不返回 token；写入 FAILURE 登录日志 | P0 |
| TC-AUTH-006 | 登录注册 | 不存在用户登录 | 用户名不存在 | 输入不存在用户名登录 | 返回“用户名或密码错误”；不泄露用户是否存在；记录当前已知限制：无 user_id 时不写 LOGIN_LOG | P1 |
| TC-AUTH-007 | 登录注册 | 登录失败限流 | `AUTH_LOGIN_MAX_FAILURES=5` | 同一用户名/IP 连续输错密码 5 次后再次登录 | 返回 429 和重试时间；成功登录后失败计数清理 | P1 |
| TC-AUTH-008 | 登录注册 | 锁定/停用账号拒绝登录 | 管理员将用户状态设为 LOCKED/DISABLED/INACTIVE | 使用该用户登录 | LOCKED 返回 423；DISABLED/INACTIVE 返回 403；页面显示账号不可用 | P0 |
| TC-AUTH-009 | 鉴权 | 无 token 访问受保护接口 | 未登录 | GET `/api/users/me/profile`；POST `/api/questions` | 返回 401；页面跳转登录或显示登录要求 | P0 |
| TC-AUTH-010 | 鉴权 | 无效/过期 token | 使用伪造 token | GET `/api/users/me/profile` | 返回 401，提示令牌无效或过期 | P0 |
| TC-AUTH-011 | 鉴权 | 旧 token 状态复查 | 用户 A 已登录，管理员将 A 改为 LOCKED | A 使用旧 token 调用 POST `/api/questions` | 返回 423；旧 token 不能继续写操作 | P0 |
| TC-HOME-001 | 首页 | 产品首页入口 | 后端已启动 | 打开 `/`；点击立即体验 | 产品首页正常展示；跳转 `/home`，无本地文件路径或 404 | P1 |
| TC-HOME-002 | 首页 | 游客访问社区首页 | 清空 sessionStorage | 打开 `/home` | 问题流、搜索、筛选、热门标签展示；右上角显示登录按钮 | P0 |
| TC-HOME-003 | 首页 | 首页推荐/热榜入口 | 有问题数据 | 打开 `/home?section=recommend` 和 `/home?section=hot` | 列表正常加载；URL section 与页面状态一致；空数据有友好空态 | P1 |
| TC-HOME-004 | 首页 | 分类/状态/标签筛选 | 有分类标签和不同状态问题 | 选择分类、状态、标签筛选 | GET `/api/questions` 带参数；列表只显示匹配结果；分页总数正确 | P1 |
| TC-HOME-005 | 首页 | 游客写操作拦截 | 未登录 | 点击提问、收藏、回答入口 | 不发送无鉴权写请求或返回 401；页面提示先登录 | P0 |
| TC-HOME-006 | 首页 | 顶部导航登录态 | 用户 A 已登录 | 打开 `/home`；展开头像菜单；退出登录 | 显示昵称/用户名；普通用户不显示管理员入口；退出后恢复游客态 | P1 |
| TC-SEARCH-001 | 搜索 | 游客搜索 | 未登录且有问题数据 | 在首页搜索框输入关键词 | GET `/api/search/questions?q=...` 返回结果；游客可查看结果和详情 | P0 |
| TC-SEARCH-002 | 搜索 | 搜索历史 | 用户 A 已登录 | 搜索 2 个关键词；刷新页面；打开搜索历史下拉 | `/api/search/history` 返回本人历史；不同用户之间历史隔离 | P1 |
| TC-SEARCH-003 | 搜索 | 搜索参数边界 | 无 | q 为空、超过 100 字、page=0、page_size=51 | API 返回 422 或业务校验错误；服务不崩溃 | P1 |
| TC-Q-001 | 问题 | 纯社区发帖成功 | 用户 A 登录；至少一个 ACTIVE 分类 | 打开提问弹窗；可手动选择分类或使用 AI 自动分类；填写标题、正文、标签；提交纯社区发帖 | POST `/api/questions` 成功；生成 question_id；详情页可查看问题 | P0 |
| TC-Q-002 | 问题 | AI 首答发帖成功 | 用户 A 登录；DeepSeek 可用 | 选择 AI 首答发帖；填写标题正文；可不手动选择分类；提交 | POST `/api/questions/ask` 返回 201；问题创建；至少生成 1 条 AI 回答；写入 prompt 日志 | P0 |
| TC-Q-003 | 问题 | 发帖必填校验 | 用户 A 登录 | 标题为空、正文为空、category_id 非法分别提交 | 前端阻止或 API 返回 422/400；数据库不得新增问题 | P0 |
| TC-Q-004 | 问题 | AI 自动分类与兜底 | 用户 A 登录；存在 ACTIVE 分类 | POST `/api/questions` 不传 category_id 且 auto_category=true；再模拟 AI 分类失败 | 成功时使用 AI 选择的 ACTIVE 分类；失败时回落到 `其他问题` | P1 |
| TC-Q-005 | 问题 | 标签上限 | 用户 A 登录 | 提交超过 10 个 tag_ids/custom_tags | API 返回错误“A question can have at most 10 tags”；不得部分绑定异常标签 | P1 |
| TC-Q-006 | 问题 | 非 ACTIVE 标签 | 存在 DISABLED/PENDING 标签 | 发帖时选择该标签 ID | API 返回不可用标签错误；问题和标签绑定回滚 | P1 |
| TC-Q-007 | 问题 | 自定义标签规范化 | 用户 A 登录 | 输入 `#  Data   Science  ` 等自定义标签 | 标签转为小写、空格转连字符、去重；重复标签不重复绑定 | P2 |
| TC-Q-008 | 问题 | AI 自动标签降级 | DeepSeek 标签服务异常 | 不选标签且 auto_tag=true 发帖 | 发帖本身不失败；无标签或保留已有标签；记录 AI 标签失败不阻塞主流程 | P1 |
| TC-Q-009 | 问题详情 | 游客查看详情 | 有公开问题 | 未登录打开 `/questions/{id}` | 展示标题、正文、标签、回答、图片、评论；写操作入口提示登录 | P0 |
| TC-Q-010 | 问题详情 | 不存在问题 | 无此 ID | 打开 `/questions/999999` 或 GET `/api/questions/999999` | 页面友好提示或 API 404；不出现空白页 | P1 |
| TC-Q-011 | 问题详情 | DELETED 问题可见性 | 问题被软删除 | 作者访问详情；其他用户/游客访问详情 | 作者可按设计查看或提示已删除；非作者返回 404 | P0 |
| TC-Q-012 | 问题 | 作者删除帖子 | 用户 A 是问题作者 | A 在详情页点击删除帖子并确认 | API 返回 DELETED；问题从普通列表隐藏；操作日志写入 | P1 |
| TC-Q-013 | 问题 | 删除后前端跳转 | 用户 A 是问题作者 | 删除帖子成功后观察页面跳转 | 当前代码预期暴露缺陷：跳到 `/profile` 可能 404；应修复为 `/me` 后再通过 | P1 |
| TC-Q-014 | 问题 | 非作者删除帖子 | 用户 B 登录，尝试删除 A 的问题 | DELETE `/api/questions/{id}` | 返回 403；问题状态不变 | P0 |
| TC-ANS-001 | 回答 | 人工回答成功 | 用户 B 登录；存在 OPEN 问题 | 在详情页填写回答并提交 | POST `/api/questions/{id}/answers` 返回 201；回答列表刷新；answer_count 增加 | P0 |
| TC-ANS-009 | 回答 | 作者删除自己的回答 | 用户 B 登录；存在 B 发布且未被采纳的人工回答 | DELETE `/api/answers/{answer_id}` | 返回 DELETED；回答从详情列表隐藏；问题 answer_count 减少；操作日志写入 | P0 |
| TC-ANS-010 | 回答 | 非作者删除回答失败 | 用户 C 登录；存在用户 B 的人工回答 | DELETE `/api/answers/{answer_id}` | 返回 403；回答仍正常展示 | P0 |
| TC-ANS-011 | 回答 | 已采纳回答禁止删除 | 问题已采纳某回答 | 作者或管理员删除该回答 | 返回业务错误；`accepted_answer_id` 不被破坏 | P0 |
| TC-ANS-002 | 回答 | 回答内容校验 | 用户 B 登录 | 回答内容为空、超过 10000 字 | 前端或 API 拒绝；不得新增回答 | P0 |
| TC-ANS-003 | 回答 | user_id 兼容字段一致性 | 用户 B 登录 | payload 中传 user_id=A | 返回 403 `user_id 与当前登录用户不一致` | P0 |
| TC-ANS-004 | 采纳 | 提问者采纳人工回答 | 用户 A 是提问者；问题有回答 | A 点击采纳 B 的回答 | 问题状态/accepted_answer_id 更新；已采纳答案高亮；列表展示 RESOLVED 或采纳状态 | P0 |
| TC-ANS-005 | 采纳 | 管理员采纳 | 管理员登录；问题有回答 | 管理员调用采纳接口 | 采纳成功；操作结果在详情页可见 | P1 |
| TC-ANS-006 | 采纳 | 非提问者采纳 | 用户 B 非提问者 | B 采纳任意回答 | 返回 403；accepted_answer_id 不变 | P0 |
| TC-ANS-007 | 采纳 | 采纳错误回答 ID | 问题 A 和问题 B 各有回答 | 在问题 A 中传问题 B 的 answer_id | 返回错误“answer_id 不属于当前问题”；状态不变 | P0 |
| TC-ANS-008 | 采纳 | CLOSED/ARCHIVED/DELETED 问题采纳 | 问题状态为 CLOSED/ARCHIVED/DELETED | 调用采纳接口 | 返回业务错误；不能采纳 | P1 |
| TC-FAV-001 | 收藏 | 收藏成功 | 用户 A 登录；存在问题 | 点击收藏 | POST `/api/questions/{id}/favorite` 返回 201；按钮变已收藏；favorite_count +1 | P0 |
| TC-FAV-002 | 收藏 | 重复收藏幂等 | 用户 A 已收藏 | 再次点击收藏或重复 POST | 不产生重复收藏记录；favorite_count 不重复增加 | P1 |
| TC-FAV-003 | 收藏 | 取消收藏 | 用户 A 已收藏 | 点击取消收藏 | DELETE 成功；按钮恢复；favorite_count -1；用户中心收藏列表移除 | P0 |
| TC-FAV-004 | 收藏 | 越权 user_id | 用户 A 登录 | 删除收藏时 query `user_id=B` | 返回 403；A/B 收藏状态不被误改 | P0 |
| TC-FB-001 | 反馈 | 点赞回答 | 用户 A 登录；存在回答 | 点击点赞 | POST `/api/answers/{answer_id}/feedback` with `is_like=Y`；like_count 更新；本人状态回显 | P0 |
| TC-FB-002 | 反馈 | 点踩与切换 | 用户 A 已点赞 | 点击点踩 | 原点赞切换为点踩；like_count -1；dislike_count +1 | P0 |
| TC-FB-003 | 反馈 | 取消反馈 | 用户 A 已点赞或点踩 | 再次点击相同反馈 | operation 为 DELETED；计数恢复；本人状态清空 | P1 |
| TC-FB-004 | 反馈 | 评分边界 | 用户 A 登录 | rating=-1、rating=6、comment_text 超 500 | API 返回 422；不得写入无效反馈 | P1 |
| TC-CMT-001 | 评论 | 一级评论成功 | 用户 A 登录；存在回答 | 输入评论并提交 | POST `/api/answers/{id}/comments` 返回 201；评论树展示新增评论 | P0 |
| TC-CMT-002 | 评论 | 楼中楼回复 | 已有一级评论 | 点击回复，输入内容提交 | parent/root/reply_to 信息正确；子回复默认折叠或按设计展示；reply_count 更新 | P1 |
| TC-CMT-003 | 评论 | 评论内容校验 | 用户 A 登录 | 空评论、超过 2000 字评论 | 前端或 API 拒绝；不得新增评论 | P0 |
| TC-CMT-004 | 评论 | 删除自己的评论 | 用户 A 有评论 | A 删除自己的评论 | DELETE `/api/comments/{id}` 成功；评论软删除占位；子回复结构不破坏 | P1 |
| TC-CMT-005 | 评论 | 删除他人评论越权 | 用户 B 尝试删除 A 评论 | 调用删除接口 | 返回 403 或业务错误；评论仍为 ACTIVE | P0 |
| TC-CHAT-001 | AI 追问 | 基于 AI 回答发起追问 | 用户 A 登录；问题有 AI 回答；DeepSeek 可用 | 输入追问并提交 | 创建 chat_session；写入用户消息和 AI 消息；返回会话详情 | P0 |
| TC-CHAT-002 | AI 追问 | 基于人工回答追问 | 用户 A 登录；选择人工回答 | 调用 follow-up 接口 | 返回错误“仅支持基于 AI 回答发起” | P1 |
| TC-CHAT-003 | AI 追问 | 续写本人会话 | 用户 A 已有 OPEN 会话 | 带 session_id 再次追问 | 会话复用；消息数增加；历史上下文参与生成 | P1 |
| TC-CHAT-004 | AI 追问 | 查看他人会话越权 | 用户 B 获取 A 的 session_id | GET `/api/chat/sessions/{session_id}` | 返回 403；不能查看他人消息 | P0 |
| TC-CHAT-005 | AI 追问 | session 与问题/回答不匹配 | 用户 A 登录 | 使用不匹配 question_id/answer_id/session_id | 返回校验错误；不新增消息 | P1 |
| TC-MEDIA-001 | 媒体 | 上传头像成功 | 用户 A 登录；准备 jpg/png/webp | 在 `/me` 上传头像 | POST `/api/users/me/avatar` 成功；头像展示；旧头像替换后标记删除 | P1 |
| TC-MEDIA-002 | 媒体 | 删除头像 | 用户 A 有头像 | 点击删除头像 | DELETE 成功；用户资料不再显示头像；再次 GET avatar 返回 404 | P1 |
| TC-MEDIA-003 | 媒体 | 问题配图上传 | 用户 A 是问题作者 | 上传 1 张合法图片到问题 | POST `/api/questions/{id}/images` 成功；详情页展示图片；public_url 可读取 | P1 |
| TC-MEDIA-004 | 媒体 | 回答配图上传 | 用户 B 是人工回答作者 | 上传合法图片到回答 | POST `/api/answers/{id}/images` 成功；详情页回答下展示图片 | P1 |
| TC-MEDIA-005 | 媒体 | 媒体类型限制 | 用户 A 登录；准备 txt/pdf | 上传到头像/问题/回答 | 返回错误“Image MIME type must be image/jpeg, image/png, or image/webp” | P0 |
| TC-MEDIA-006 | 媒体 | 媒体大小和空文件 | 用户 A 登录；准备空文件和 >50MB 图片 | 分别上传 | 返回大小/空文件错误；不得落库 | P0 |
| TC-MEDIA-007 | 媒体 | 图片数量上限 | 问题已有 9 张图；回答已有 6 张图 | 再上传 1 张 | 问题返回最多 9 张；回答返回最多 6 张；不新增第 10/7 张 | P1 |
| TC-MEDIA-008 | 媒体 | 非作者管理图片 | 用户 B 登录；A 的问题/回答图片存在 | B 删除 A 的图片 | 返回 403；图片仍可展示 | P0 |
| TC-MEDIA-009 | 媒体 | 媒体路径穿越 | 有任意媒体 | GET `/api/media/files/../x` 或包含反斜杠文件名 | 返回 400/404；不得读取非媒体文件 | P0 |
| TC-USER-001 | 用户中心 | 访问个人中心 | 用户 A 登录 | 打开 `/me` | 展示资料、统计、我的问题/回答/收藏/推荐/历史模块 | P0 |
| TC-USER-002 | 用户中心 | 游客访问个人中心 | 未登录 | 打开 `/me` | 跳转 `/login` 或提示登录；不得展示任何用户数据 | P0 |
| TC-USER-003 | 用户中心 | 修改资料 | 用户 A 登录 | 修改 nickname、email、phone 并保存 | PATCH 成功；页面和 sessionStorage 昵称刷新；数据库更新 | P1 |
| TC-USER-004 | 用户中心 | 资料字段边界 | 用户 A 登录 | nickname>50、email>100、phone>20 | API 返回 422；当前缺少 email/phone 格式校验需记录风险 | P2 |
| TC-USER-005 | 用户中心 | 本人资源访问 | 用户 A 登录 | GET `/api/users/{A}/questions`、answers、favorites、browse-history、search-history | 返回 A 本人数据；分页和 limit 生效 | P0 |
| TC-USER-006 | 用户中心 | 跨用户访问拦截 | 用户 A 登录 | GET `/api/users/{B}/favorites` 等路径 | 返回 403“只能访问当前登录用户自己的资源” | P0 |
| TC-REC-001 | 推荐 | 重建兴趣画像 | 用户 A 有浏览、收藏、搜索、反馈行为 | POST `/api/users/{A}/profile/rebuild` | 返回 item_count 和标签权重；`user_tag_profile` 更新 | P1 |
| TC-REC-002 | 推荐 | 生成推荐 | 用户 A 有画像 | POST `/api/users/{A}/recommendations/generate?limit=10` | 返回 active_count；推荐列表可在 `/me` 和 `/home?section=recommend` 展示 | P1 |
| TC-REC-003 | 推荐 | 推荐越权 | 用户 A 登录 | POST `/api/users/{B}/recommendations/generate` | 返回 403；不得生成 B 的推荐 | P0 |
| TC-ADMIN-001 | 管理后台 | 管理员访问后台 | 管理员登录 | 打开 `/admin` | 后台总览正常；用户/分类/标签/内容/日志模块可切换 | P0 |
| TC-ADMIN-002 | 管理后台 | 普通用户访问后台 | 用户 A 登录 | 打开 `/admin` 或 GET `/api/admin/users` | 页面重定向或 API 403；不得泄露后台数据 | P0 |
| TC-ADMIN-003 | 用户治理 | 修改用户状态 | 管理员登录；用户 A ACTIVE | 将 A 改为 LOCKED/DISABLED/INACTIVE | API 成功；A 登录或旧 token 调用受保护接口被拒绝；写操作日志 | P0 |
| TC-ADMIN-004 | 用户治理 | 修改用户角色 | 管理员登录；用户 A USER | 将 A 改为 ADMIN，再改回 USER | 角色变化生效；管理员入口展示随角色变化；操作日志记录 | P1 |
| TC-ADMIN-005 | 用户治理 | 非法角色/状态 | 管理员登录 | 提交 role=ROOT 或 status=UNKNOWN | 返回业务错误；数据库不变 | P0 |
| TC-ADMIN-006 | 分类管理 | 新建分类 | 管理员登录 | 输入分类名称、描述、ACTIVE 创建 | 分类列表新增；前台发帖分类可选；操作日志记录 | P1 |
| TC-ADMIN-007 | 分类管理 | 重名分类 | 已有分类名 | 创建或改名为重复名称 | 返回“Category name already exists”；不产生重复数据 | P1 |
| TC-ADMIN-008 | 标签治理 | 查询和修改标签 | 管理员登录；存在标签 | 按 keyword/source/status 筛选；修改描述和状态 | 列表结果正确；状态变更后发帖选择可用性同步变化 | P1 |
| TC-ADMIN-009 | 内容治理 | 修改问题状态 | 管理员登录；存在问题 | 改为 CLOSED/ARCHIVED/DELETED，再查看前台列表 | 状态更新；普通列表按状态过滤正确；DELETED 对非作者不可见 | P0 |
| TC-ADMIN-010 | 内容治理 | 删除问题 | 管理员登录 | DELETE `/api/admin/questions/{id}?reason=...` | 问题状态 DELETED；操作日志包含原因 | P1 |
| TC-ADMIN-011 | 内容治理 | 修改评论状态 | 管理员登录；存在评论 | PATCH `/api/admin/comments/{id}/status` 为 HIDDEN/ACTIVE | 详情页评论展示按状态变化；操作日志记录 | P1 |
| TC-ADMIN-012 | 审计日志 | 登录和操作日志查询 | 管理员登录 | 查询 `/api/admin/logs/login` 和 `/api/admin/logs/operations`，带 page/result/op_type/user_id | 分页、筛选和中文展示正确；普通用户不可访问 | P1 |
| TC-API-001 | API | 分页边界 | 有列表数据 | page=0、page_size=0、page_size 超上限调用 questions/admin/users | 返回 422 或业务错误；服务不崩溃 | P1 |
| TC-API-002 | API | 非法枚举 | 有 token | questions status=INVALID；admin role/status/source 非法 | 返回 400/422；数据不变 | P0 |
| TC-API-003 | API | 404 和错误结构 | 无效 question_id/answer_id/comment_id/media_id | 调用详情、回答图片、评论删除等接口 | 返回 404 或明确业务错误；响应包含 detail | P1 |
| TC-API-004 | API | 数据库约束 | 构造非法外键 category_id/tag_id/answer_id | 调用对应写接口 | 返回校验错误；事务回滚，无半成品数据 | P0 |
| TC-API-005 | API | CORS 基础 | 使用允许和不允许 Origin | 调用 `/api/questions` OPTIONS/GET | 允许域正常；未允许域不应获得可用跨域授权 | P2 |
| TC-UI-001 | UI | 响应式布局 | 有数据 | 在 390x844、768x1024、1440x900 打开首页、详情、用户中心、后台 | 无横向滚动；按钮、卡片、表单文字不重叠；弹窗可滚动 | P1 |
| TC-UI-002 | UI | 表单错误提示 | 打开发帖、登录、资料、后台表单 | 提交空值/非法值 | 用户能看到明确错误；按钮 loading 后恢复；不重复提交 | P1 |
| TC-UI-003 | UI | Markdown 和代码高亮 | 回答包含 Markdown、代码块、链接 | 打开详情页 | Markdown 正常渲染；代码块样式正常；页面无 XSS 可执行脚本 | P1 |
| TC-UI-004 | UI | 多标签页登录隔离 | 同一浏览器两个标签页 | 标签页 1 登录 A，标签页 2 登录 B | 因使用 sessionStorage，两个标签页登录态不互相覆盖 | P1 |
| TC-DESK-001 | 桌面端 | 后端不可用启动页 | 桌面端依赖已安装；后端不可用 | 在 `desktop` 执行 `npm run dev` | 启动页提示无法连接；提供公网地址和本地开发地址切换/重试 | P2 |
| TC-DESK-002 | 桌面端 | 后端可用进入社区 | `/health` 可访问 | 启动桌面端或点击重新检测 | Tauri 窗口进入 `/home`；游客浏览和登录逻辑与浏览器一致 | P1 |
| TC-DESK-003 | 桌面端 | 打包产物 | macOS/Windows 构建环境就绪 | 执行 `npm run build` 或 Windows 构建脚本 | 生成对应 `.app`/`.dmg`/`.msi`/`.exe`；启动后可检测后端 | P2 |
| TC-CLI-001 | CLI | CLI 登录和接口回归 | 后端已启动；CLI 配置 API 地址 | 使用 CLI 登录并调用问题列表/详情/发帖 | CLI 通过 HTTP 调用 FastAPI；Bearer Token 透传成功 | P2 |
| TC-REG-001 | 回归 | 主链路回归 | 环境和账号准备完成 | A 注册登录 -> 发 AI 问题 -> B 回答 -> A 采纳 -> A 收藏/反馈/评论 -> A 查看用户中心 -> Admin 治理 | 全链路无阻塞；关键数据在前端、API、数据库一致 | P0 |
| TC-REG-002 | 回归 | 游客到登录转换 | 游客在详情页尝试收藏/评论/回答 | 点击操作后登录 A，再返回详情页 | 登录后可继续操作；不会丢失或误用游客状态 | P1 |

## 4. Go-Live Checklist

### Blocking - 必须通过

- `/health`、数据库连接、核心页面入口全部可用。
- `.env` 使用强随机 `JWT_SECRET_KEY`，不能使用 `.env.example` 占位值。
- 注册、登录、退出、无 token、无效 token、锁定/停用账号拦截全部通过。
- 游客可浏览但不能执行发帖、回答、收藏、评论、反馈、追问等写操作。
- 普通用户不能访问 `/admin` 和 `/api/admin/*`。
- 用户 A 不能访问或修改用户 B 的用户中心、推荐、收藏、会话、图片、评论删除等本人资源。
- 发帖、AI 首答、回答、采纳、收藏、反馈、评论、媒体上传、用户中心、管理员治理主链路通过。
- 数据库统计字段和前端数量展示一致：answer_count、favorite_count、like_count、dislike_count、reply_count。
- 媒体 MIME、大小、数量、作者权限和路径穿越测试通过。
- AI 服务不可用时，系统能给出明确错误，不产生半创建数据或事务残留。
- 已知 `/profile` 删除后跳转问题修复或有明确临时处理方案。
- 管理员修改用户状态后，旧 token 无法继续访问受保护接口。

### 高风险项

- DeepSeek 服务超时、Key 缺失、返回异常。
- Oracle Text 开关与迁移脚本不一致导致搜索异常。
- 大文件上传导致请求超时或数据库空间增长。
- 管理后台误操作导致用户、内容、分类、标签状态异常。
- 缺少自动化单元测试，回归依赖人工执行。
- 登录失败限流为进程内存实现，多实例部署下策略不一致。
- email/phone 格式未校验，可能进入脏数据。

### 建议优化项

- 补充 pytest 单元测试和 FastAPI TestClient 集成测试。
- 为登录、发帖、收藏、评论、管理员接口增加自动化回归脚本。
- 为 AI 调用增加 mock 模式和可重复测试数据。
- 增加日志导出、审计时间范围筛选和媒体审核后台。
- 修复 `/profile` 路由跳转，统一用户中心入口为 `/me`。
- 增加邮箱/手机号格式校验。
- 增加生产环境上传限流、文件清理策略和监控告警。

## 5. Bug Report Template

```markdown
## Bug 标题
[模块] 简短描述问题，例如：详情页删除帖子成功后跳转到未注册路由 /profile

## 环境
- 测试环境：
- 浏览器/客户端：
- 后端版本/分支：
- 数据库环境：
- 测试账号/角色：

## 前置条件
说明账号、数据、配置、页面入口等。

## 复现步骤
1. 
2. 
3. 

## 实际结果
描述实际看到的页面、接口响应、数据库状态或日志。

## 预期结果
描述按需求或代码契约应该发生的结果。

## 严重程度
- Blocker：阻塞上线或主链路不可用
- Critical：核心功能错误、数据损坏、权限绕过、安全问题
- Major：重要功能不可用但有替代路径
- Minor：体验、文案、样式或低风险边界问题

## 优先级
P0 / P1 / P2

## 附件
- 截图或录屏：
- Network 请求/响应：
- Console 日志：
- 后端日志：
- 相关数据 ID：user_id、question_id、answer_id、comment_id、media_id

## 备注
是否可稳定复现、是否只在某浏览器/某账号/某状态下出现。
```
