# Facebook 全栈项目开发答辩问答速记版

> 背诵口径：项目名称叫《Facebook 全栈项目开发》，当前真实实现是一个带 AI 首答、问答社区、用户行为、推荐和后台治理的全栈社区系统。不要说成完整 Facebook 克隆，也不要编造好友、关注、通知等当前未实现功能。

## 一、项目整体架构

Q1：为什么你的项目叫全栈项目？  
A1：因为它不是单独的静态页面，也不是只有后端接口。用户在前端页面操作，前端通过 `fetch` 调用 FastAPI 接口，后端处理登录、发帖、评论、推荐等业务，再访问 Oracle 数据库存取数据，最后把结果返回给前端展示。所以它覆盖了前端、后端、数据库和部署运行，是完整的全栈闭环。

Q2：你的项目整体是做什么的？  
A2：这个项目是一个社区问答平台，可以理解为类似社区动态流的系统。用户可以注册登录、发布问题、触发 AI 首答、回答、评论、收藏、点赞或点踩，还可以上传头像和图片。系统会记录浏览、搜索、收藏等行为，再生成用户画像和推荐。管理员还能管理用户、分类、标签、内容和日志。

Q3：项目采用什么架构？  
A3：项目采用 B/S 架构，也就是浏览器访问服务器。前端页面由 FastAPI 返回，页面里的 JavaScript 再请求后端 API。后端内部又分成路由层、业务层和数据访问层：`routes` 接收请求，`services` 处理业务，`repositories` 执行 SQL，最后访问 Oracle 数据库。

Q4：前端、后端、数据库分别负责什么？  
A4：前端负责展示页面、收集用户输入、发请求和渲染结果；后端负责鉴权、参数校验、业务规则、AI 调用和事务控制；数据库负责持久化用户、问题、回答、评论、收藏、推荐、日志等数据，并通过主外键、索引、触发器和存储过程保证数据一致性和查询效率。

Q5：用户访问一个页面时数据是怎么出来的？  
A5：比如用户访问 `/home`，FastAPI 先返回 `app/web/home.html`。页面加载后，JavaScript 调用 `/api/questions` 或 `/api/search/questions`。后端从 Oracle 查询问题、作者、标签、收藏状态等数据，封装成 JSON 返回。前端拿到 JSON 后再渲染成问题卡片。

## 二、前端

Q6：你的前端用了什么技术？  
A6：前端主要使用原生 HTML、CSS 和 JavaScript，没有使用 React 或 Vue。页面文件都在 `app/web/` 下，比如 `home.html` 是首页，`detail.html` 是详情页，`profile.html` 是用户中心，`admin.html` 是管理后台。这样写的好处是结构直观，适合课程答辩讲清楚页面、请求和状态管理原理。

Q7：为什么没有用 React 或 Vue？  
A7：这个项目重点是课程设计和全栈闭环，所以我选择原生前端实现，更容易展示底层逻辑。虽然没有框架组件，但我用 JavaScript 函数、状态对象和 DOM 操作组织页面逻辑，例如后台模块切换、问题列表渲染、评论树渲染，本质上也体现了组件化思想。

Q8：项目里有没有 props、state、hooks？  
A8：没有真正的 React `props`、`state`、`hooks`，因为这不是 React 项目。当前项目用函数参数类似 props，用普通对象或全局变量保存页面状态，页面初始化函数类似生命周期。答辩时我会明确说明：这是原生 JS 的状态管理，不是框架 hooks。

Q9：前端路由怎么实现？  
A9：前端不是单页应用路由，而是由 FastAPI 提供页面路由。比如 `/` 返回 `index.html`，`/login` 返回登录页，`/home` 返回社区首页，`/questions/{question_id}` 返回详情页，`/me` 返回用户中心，`/admin` 返回后台页面。页面内部再用 URL 参数控制搜索、热榜、推荐等状态。

Q10：前端怎么调用后端接口？  
A10：前端使用浏览器原生 `fetch` 调接口。普通接口比如 `/api/questions` 可以游客访问；需要登录的接口，比如发帖、评论、收藏、上传图片，会从 `sessionStorage` 取出 `access_token`，放到请求头 `Authorization: Bearer <token>` 里，后端再验证身份。

Q11：登录状态保存在什么地方？  
A11：登录成功后，前端保存后端返回的 `access_token`、`user_id`、`username`、`user_role`。根据项目当前实现和文档说明，主要保存在 `sessionStorage`，这样同一个浏览器标签页内可以保持登录，关闭标签页后登录态会消失，安全性比长期保存在本地稍好。

Q12：前端如何处理错误和跳转？  
A12：前端请求接口后会判断响应状态。如果登录失败，会显示用户名密码错误或服务异常提示；如果 token 失效或未登录访问写操作，会提示登录并跳转 `/login`。操作成功后，比如发布问题、收藏、评论，会刷新列表或详情区域，把后端返回的新数据展示出来。

## 三、后端

Q13：后端使用什么技术？  
A13：后端使用 FastAPI，入口是 `app/main.py`。它注册了网页路由、认证路由、`/api` 聚合路由，还配置了 CORS 和安全响应头。数据库访问使用 `python-oracledb`，请求响应模型用 Pydantic，密码哈希用 bcrypt，JWT 用 `python-jose`，AI 调用使用 OpenAI 兼容 SDK 接入 DeepSeek。

Q14：后端代码怎么分层？  
A14：后端分为三层。`app/api/routes/` 是路由层，负责接收 HTTP 请求和鉴权；`app/services/` 是业务层，负责参数校验、事务、业务流程，比如发帖和 AI 首答；`app/repositories/` 是数据访问层，专门写 SQL 操作 Oracle。这样职责清楚，后期维护比较方便。

Q15：后端入口文件做了什么？  
A15：`app/main.py` 创建 FastAPI 应用，注册 `web_router` 返回前端 HTML，注册 `/api/auth` 和 `/api` 路由，配置 CORS，增加安全响应头中间件，还提供 `/health` 健康检查接口。简单说，它是整个后端服务启动和路由组织的总入口。

Q16：后端怎么连接数据库？  
A16：数据库连接在 `app/db/connection.py`。项目不是每次请求都新建连接，而是用 `oracledb.create_pool` 创建 Oracle 连接池。业务代码通过 `get_connection()` 获取连接，正常执行后 commit，异常时 rollback，最后把连接归还给连接池。这样性能更好，也更安全。

Q17：后端如何做参数校验？  
A17：项目有两层校验。第一层是 Pydantic schema，比如标题长度、正文长度、ID 必须大于 0。第二层是 service 业务校验，比如问题状态是否允许回答、用户是否有权限、标签是否可用。数据库层还有检查约束，三层一起保证数据合法。

Q18：后端异常怎么处理？  
A18：项目定义了 `AppError`、`ValidationError`、`NotFoundError` 等异常。路由层捕获这些异常并转换成 HTTP 错误响应。数据库异常也会在 service 层翻译，比如外键错误、唯一约束冲突、检查约束失败，会返回更容易理解的错误信息。

## 四、数据库

Q19：数据库使用什么？  
A19：项目使用 Oracle AI Database 26ai Free。数据库脚本在 `sql/` 目录，`create_tables.sql` 负责建表和索引，`procedures.sql` 负责存储过程和推荐逻辑，`triggers.sql` 负责触发器，`views.sql` 负责视图，`seed_data.sql` 负责演示数据。

Q20：核心表有哪些？  
A20：核心表包括 `users` 用户表、`questions` 问题表、`answers` 回答表、`answer_comments` 评论表、`favorites` 收藏表、`answer_feedback` 点赞点踩表、`tags` 标签表、`question_tags` 问题标签关联表、`media_assets` 图片表、`recommendations` 推荐表和 `login_log`、`operation_log` 日志表。

Q21：问题和标签是什么关系？  
A21：问题和标签是多对多关系。一个问题可以有多个标签，一个标签也可以对应多个问题，所以项目用中间表 `question_tags` 实现。`question_tags.question_id` 指向 `questions`，`question_tags.tag_id` 指向 `tags`，这样关系清晰，也方便按标签筛选问题。

Q22：评论楼中楼怎么设计？  
A22：评论存在 `answer_comments` 表中，并且评论是挂在回答下面的。楼中楼通过自引用字段实现：`parent_comment_id` 表示父评论，`root_comment_id` 表示根评论，`reply_to_user_id` 表示回复谁。删除评论时不是直接物理删除，而是改状态并显示占位文案。

Q23：为什么要用索引？  
A23：索引用来提高查询性能。项目里问题列表经常按状态、分类、时间查，所以有 `idx_questions_status`、`idx_questions_category_id`、`idx_questions_ask_time`。用户中心、收藏、推荐、搜索历史也都有对应索引。没有索引时数据多了可能全表扫描，查询会慢。

Q24：触发器有什么作用？  
A24：触发器用来自动维护统计数据。例如新增回答、收藏、浏览记录后，触发器会调用 `qa_app_pkg.sync_question_statistics` 更新问题的回答数、收藏数、浏览数。回答点赞变化后，也会自动更新回答的点赞数、点踩数和平均评分，保证统计字段一致。

Q25：推荐系统是怎么做的？  
A25：推荐不是假数据，而是根据用户行为生成。系统会根据用户提问、回答、收藏、浏览、反馈、评论、搜索等行为计算标签权重，写入 `user_tag_profile`。然后 `qa_app_pkg.generate_recommendations` 根据标签匹配、热度、新鲜度和惩罚项生成推荐结果。

## 五、登录认证和权限

Q26：登录流程是什么？  
A26：用户在登录页输入账号密码，前端调用 `POST /api/auth/login`。后端查询 `users` 表，用 bcrypt 校验密码。如果成功，就生成 JWT，并写入 `login_log`。前端保存 token，后续访问发帖、评论、收藏等接口时携带 token。

Q27：JWT 里保存了什么？  
A27：项目的 JWT 主要保存 `sub` 和 `exp`。`sub` 是用户 ID，`exp` 是过期时间。后端不会完全依赖 token 里的角色，而是每次解析出用户 ID 后再查数据库，确认用户存在、状态是 `ACTIVE`，这样用户被锁定或停用后可以及时生效。

Q28：管理员权限怎么判断？  
A28：管理员接口使用 `get_admin_user` 依赖。它先通过 JWT 获取当前用户，再检查用户 `role` 是否为 `ADMIN`。如果不是管理员，就返回 403。前端隐藏后台入口只是体验优化，真正的权限控制在后端。

Q29：为什么不能只靠前端隐藏按钮？  
A29：因为前端代码运行在浏览器，用户可以修改页面、伪造请求，甚至不用页面直接调用接口。如果只靠前端判断，普通用户可以绕过按钮直接请求后台接口。所以所有关键权限都必须在后端校验。

Q30：用户被锁定后还能用旧 token 吗？  
A30：不能继续访问受保护接口。因为后端每次解析 JWT 后，还会从数据库重新加载用户，并检查 `status` 是否为 `ACTIVE`。如果用户状态是 `LOCKED`、`DISABLED` 或 `INACTIVE`，后端会拒绝请求。

## 六、接口和核心功能

Q31：发布问题调用哪个接口？  
A31：普通发帖调用 `POST /api/questions`，AI 首答发帖调用 `POST /api/questions/ask`。后端会创建 `questions` 记录，绑定标签。如果是 AI 模式，还会调用 DeepSeek 生成首答，把回答写入 `answers`，同时把 prompt 和结果写入 `ai_prompt_log`。

Q32：查询问题列表调用哪个接口？  
A32：普通列表调用 `GET /api/questions`，搜索列表调用 `GET /api/search/questions`。接口支持分页、分类、标签、状态等参数。后端查询 Oracle 后返回 `QuestionListResponse`，前端把返回的 `items` 渲染成问题卡片。

Q33：评论调用哪个接口？  
A33：发表评论或回复调用 `POST /api/answers/{answer_id}/comments`，查看评论树调用 `GET /api/answers/{answer_id}/comments`，删除自己的评论调用 `DELETE /api/comments/{comment_id}`。评论是挂在回答下面的，不是直接挂在问题下面。

Q34：点赞和收藏有什么区别？  
A34：收藏是对问题的收藏，数据存在 `favorites` 表；点赞或点踩是对回答的反馈，数据存在 `answer_feedback` 表。收藏会影响问题的收藏数，点赞点踩会影响回答的 `like_count`、`dislike_count` 和评分统计。

Q35：图片上传怎么实现？  
A35：头像、问题图片、回答图片都支持上传。前端用 multipart 表单上传文件，后端用 `UploadFile` 读取，`MediaService` 校验图片类型和大小，然后写入 `media_assets` 表，其中 `file_content` 是 BLOB。前端通过 `/api/media/files/{file_name}` 读取图片。

## 七、安全

Q36：项目如何防止 SQL 注入？  
A36：项目 SQL 基本使用绑定变量，比如 `:question_id`、`:user_id`，而不是把用户输入直接拼接进 SQL。这样数据库会把用户输入当作参数值处理，而不是当作 SQL 语句执行，可以有效防止 SQL 注入。

Q37：项目如何防止 XSS？  
A37：项目配置了 CSP 安全策略，前端也有 `escapeHtml` 这类转义函数。详情页 Markdown 渲染后还有清洗逻辑，避免直接执行危险 HTML。不过当前为了兼容内联脚本，CSP 里仍有 `unsafe-inline`，生产环境还需要继续收紧。

Q38：环境变量怎么保护？  
A38：项目用 `.env` 保存敏感配置，比如数据库密码、JWT 密钥、DeepSeek API Key。仓库里提供的是 `.env.example` 示例文件。真正运行时应该自己创建 `.env`，并设置强随机 `JWT_SECRET_KEY`，不能把真实密钥提交到 Git。

Q39：文件上传有什么安全限制？  
A39：后端限制上传文件不能为空，大小不能超过限制，MIME 类型只能是 `image/jpeg`、`image/png`、`image/webp`。并且问题图片只能问题作者管理，回答图片只能人工回答作者管理，避免用户上传或删除别人的图片。

Q40：当前安全上还有什么不足？  
A40：主要不足是 JWT 没有刷新和主动失效机制，CSP 仍允许内联脚本，媒体上传没有审核后台，邮箱和手机号格式校验还不够严格，也没有完整自动化安全测试。这些可以作为后续生产级改进方向。

## 八、部署运行

Q41：本地怎么运行项目？  
A41：先复制 `.env.example` 为 `.env`，配置数据库、JWT 和 DeepSeek Key。然后用 Docker 或脚本启动 Oracle，再执行数据库 schema 和 seed 脚本。最后安装 Python 依赖，运行 `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`，浏览器访问 `/home`。

Q42：前端需要单独启动吗？  
A42：Web 前端不需要单独启动。FastAPI 同时提供 HTML 页面和 API。比如访问 `/home` 时，后端直接返回 `app/web/home.html`；页面再请求 `/api/...` 获取数据。桌面端如果要运行，则进入 `desktop/` 执行 `npm run dev`。

Q43：Docker 在项目中做什么？  
A43：Docker 主要用于运行 Oracle 数据库。`compose.yaml` 定义了 `oracle26ai` 服务，包括镜像、端口、环境变量、数据卷和初始化脚本。FastAPI 当前主要通过本机 Python 环境启动，没有单独 Dockerfile。

Q44：数据库迁移脚本有什么用？  
A44：`sql/migrations/` 用来保存数据库结构的增量变化。新环境可以直接执行主 schema，旧环境不能随便删库重建，所以要靠迁移脚本新增字段、表、索引或约束。这样不同环境的数据库结构可以保持一致。

Q45：生产环境怎么部署更合理？  
A45：生产环境建议 Oracle 单独部署并定期备份，FastAPI 用进程管理工具运行，前面加 Nginx 反向代理和 HTTPS。`.env` 用强密钥和真实 API Key，不能提交仓库。图片如果规模变大，可以改为对象存储，数据库只保存元数据。

## 九、项目不足和改进

Q46：项目当前有没有好友或关注？  
A46：当前没有。仓库里没有好友表、关注表，也没有对应接口和页面。答辩时不能说已经实现。后续可以新增 `follows` 表，用 `follower_id` 和 `followee_id` 表示关注关系，再做关注列表和关注信息流。

Q47：项目当前最大的不足是什么？  
A47：当前项目是可演示的 MVP，但还不是完整生产级社区。主要不足包括没有好友/关注、没有通知、没有评论图片、没有媒体审核、没有推荐规则人工干预、没有正式 pytest 单元测试，前端工程化也还可以继续提升。

Q48：如果继续优化，你会先做什么？  
A48：我会先补自动化测试和媒体审核，因为它们关系到系统稳定性和安全性。然后补通知、关注系统和推荐规则后台，让社区互动更完整。最后再做工程化改造，比如拆分前端 JS、增加 Dockerfile、CI/CD 和生产监控。

Q49：项目有什么亮点？  
A49：亮点是全栈闭环比较完整，不只是 CRUD。它有 AI 首答、AI 自动标签、评论楼中楼、图片 BLOB 存储、用户画像、推荐生成、管理员后台和审计日志。数据库层还用了约束、索引、触发器、视图和 PL/SQL 包，适合数据库课程答辩。

Q50：如果老师问“这和 Facebook 有什么关系”，怎么回答？  
A50：我会说项目名称沿用了“Facebook 全栈项目开发”，但当前实现重点是社区平台的通用能力，比如用户、内容流、评论、收藏、图片、推荐和后台治理。它不是完整复刻 Facebook，而是一个课程范围内的社区问答全栈系统。

# 答辩前 30 分钟快速复习清单

## 先背 10 句话

1. 这是一个基于 FastAPI、Oracle 26ai 和原生前端的全栈社区问答系统。
2. 前端在 `app/web/`，后端在 `app/`，数据库脚本在 `sql/`。
3. 前端用 `fetch` 调后端接口，登录后携带 `Authorization: Bearer token`。
4. 后端分为 routes、services、repositories 三层。
5. 数据库使用 Oracle，包含表、约束、索引、触发器、视图和存储过程。
6. 密码使用 bcrypt 哈希存储，不保存明文。
7. 登录使用 JWT，后端每次解析 token 后还会查数据库确认用户状态。
8. 问题和标签是多对多，通过 `question_tags` 中间表实现。
9. 推荐通过用户行为生成标签画像，再生成推荐结果。
10. 当前没有好友、关注、通知、媒体审核和正式单元测试，答辩时要如实说明。

## 重点看 10 个文件

1. `app/main.py`：后端入口。
2. `app/web_routes.py`：页面路由。
3. `app/api/auth_deps.py`：JWT 鉴权。
4. `app/services/auth_service.py`：注册登录。
5. `app/services/question_service.py`：发帖和 AI 首答。
6. `app/services/media_service.py`：图片上传。
7. `app/services/recommendation_service.py`：推荐接口。
8. `sql/create_tables.sql`：表结构。
9. `sql/procedures.sql`：推荐和画像过程。
10. `sql/triggers.sql`：统计同步触发器。

## 最容易被追问的 10 个点

1. 为什么是全栈？
2. 为什么不用 React/Vue？
3. JWT 登录流程是什么？
4. 后端如何防止伪造用户 ID？
5. 密码为什么安全？
6. 问题、回答、评论、标签的表关系。
7. 收藏和点赞分别怎么存。
8. 推荐算法是不是真实实现。
9. 图片为什么存 BLOB。
10. 当前项目没有实现哪些功能。

## 最后 5 分钟提醒

- 不要说实现了好友/关注，当前项目未实现。
- 不要说实现了通知，当前项目未实现。
- 不要说是完整 Facebook 克隆，要说是社区问答全栈项目。
- 不要说密码加密可逆，要说 bcrypt 哈希不可逆。
- 不要说前端能保证权限，要说真正权限在后端。

