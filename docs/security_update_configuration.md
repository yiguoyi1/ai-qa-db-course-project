# 安全更新后的配置指南

最后更新：2026-04-28

本文面向刚接手项目或刚拉取安全更新的同事，说明这次安全加固之后应该如何配置 `.env`、数据库迁移和客户端相关项。

## 1. 先说结论

不要重新生成或覆盖现有 `.env`。如果本地或服务器已经能正常运行，只需要把本次新增的配置项补进去，并保留原来的数据库密码、JWT 密钥和 DeepSeek API Key。

本次安全更新主要涉及：

- CORS 从任意来源改为白名单。
- 后端增加安全响应头和 CSP。
- 登录失败增加限流配置。
- 数据库访问改为连接池。
- DeepSeek 调用增加超时配置。
- 搜索增加可选 Oracle Text 全文索引。
- 桌面客户端 Tauri CSP 从 `null` 改为显式策略。

## 2. `.env` 需要新增的配置

把下面这些配置补到现有 `.env` 中即可：

```env
ORACLE_POOL_MIN=1
ORACLE_POOL_MAX=5
ORACLE_POOL_INCREMENT=1

AUTH_LOGIN_MAX_FAILURES=5
AUTH_LOGIN_WINDOW_SECONDS=300

CORS_ALLOW_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,http://tauri.localhost,https://tauri.localhost,tauri://localhost
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' http: https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'

SEARCH_USE_ORACLE_TEXT=false

DEEPSEEK_TIMEOUT_SECONDS=30
```

保留这些已有配置，不要改回示例值：

```env
APP_USER=AI_QA_APP
APP_USER_PASSWORD=<你的数据库应用用户密码>
JWT_SECRET_KEY=<当前环境专用强随机密钥>
DEEPSEEK_API_KEY=<你的 DeepSeek API Key>
```

`JWT_SECRET_KEY` 不能使用 `please-set-a-strong-random-secret-per-env`，长度至少 32 个字符。

## 3. 配置项说明

| 配置项 | 推荐值 | 作用 | 什么时候需要改 |
| --- | --- | --- | --- |
| `ORACLE_POOL_MIN` | `1` | 数据库连接池最小连接数 | 本地开发通常不用改 |
| `ORACLE_POOL_MAX` | `5` | 数据库连接池最大连接数 | 并发更高时可调大 |
| `ORACLE_POOL_INCREMENT` | `1` | 连接池扩容步长 | 通常不用改 |
| `AUTH_LOGIN_MAX_FAILURES` | `5` | 同一 IP + 用户名窗口期内允许失败次数 | 演示环境可保持默认 |
| `AUTH_LOGIN_WINDOW_SECONDS` | `300` | 登录失败统计窗口，单位秒 | 想放宽限流时可调大/调小 |
| `CORS_ALLOW_ORIGINS` | 见上方示例 | 允许跨域访问 API 的来源白名单 | 部署到线上域名时必须加入线上域名 |
| `CONTENT_SECURITY_POLICY` | 见上方示例 | 后端响应的内容安全策略 | 引入新 CDN、图片域名或 API 域名时需要调整 |
| `SEARCH_USE_ORACLE_TEXT` | `false` | 是否启用 Oracle Text 全文搜索 | 导入全文索引迁移后再改为 `true` |
| `DEEPSEEK_TIMEOUT_SECONDS` | `30` | DeepSeek API 调用超时时间 | 网络慢或模型响应慢时可适当调大 |

## 4. 本地开发配置

本地开发推荐保持：

```env
CORS_ALLOW_ORIGINS=http://127.0.0.1:8000,http://localhost:8000,http://tauri.localhost,https://tauri.localhost,tauri://localhost
SEARCH_USE_ORACLE_TEXT=false
```

原因：

- 网页前端由 FastAPI 同源提供，`127.0.0.1:8000` 和 `localhost:8000` 覆盖浏览器访问。
- Tauri 客户端会通过本地窗口加载页面，需要保留 `tauri.localhost` 和 `tauri://localhost`。
- Oracle Text 索引是可选优化，没导入迁移前保持 `false` 更稳。

## 5. 线上或局域网部署配置

如果后端部署到真实域名，例如：

```text
https://qa.example.com
```

需要把这个域名加入 `CORS_ALLOW_ORIGINS`：

```env
CORS_ALLOW_ORIGINS=https://qa.example.com,http://127.0.0.1:8000,http://localhost:8000,http://tauri.localhost,https://tauri.localhost,tauri://localhost
```

如果前端页面、API 和静态资源都由同一个 FastAPI 服务提供，通常不需要额外放开很多来源。

如果新增了外部图片 CDN、对象存储或 API 域名，需要同步调整 `CONTENT_SECURITY_POLICY` 中对应字段：

- 外部脚本：加到 `script-src`。
- 外部样式：加到 `style-src`。
- 外部图片：加到 `img-src`。
- 外部 API：加到 `connect-src`。

不要为了省事把 CSP 改成全量通配。尤其不要随意设置：

```env
CONTENT_SECURITY_POLICY=
```

也不要默认使用：

```text
default-src *
```

## 6. Oracle Text 搜索迁移

本次新增迁移脚本：

```text
sql/migrations/20260428_add_question_oracle_text_indexes.sql
```

它会创建两个可选全文索引：

- `IDX_QUESTIONS_TITLE_TEXT`：加速 `questions.title` 搜索。
- `IDX_QUESTIONS_CONTENT_TEXT`：加速 `questions.content` 搜索。

导入方式示例：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load-oracle-schema.ps1 -SqlFiles `
  sql/migrations/20260428_add_question_oracle_text_indexes.sql
```

macOS 或 PowerShell 7：

```powershell
pwsh -File ./scripts/load-oracle-schema.ps1 -SqlFiles sql/migrations/20260428_add_question_oracle_text_indexes.sql
```

迁移导入成功后，再把 `.env` 改为：

```env
SEARCH_USE_ORACLE_TEXT=true
```

然后重启后端。

如果迁移未导入，保持：

```env
SEARCH_USE_ORACLE_TEXT=false
```

## 7. Tauri 桌面客户端配置

桌面端安全策略已经写在：

```text
desktop/src-tauri/tauri.conf.json
```

当前 CSP 允许：

- Tauri IPC。
- 本地脚本和样式。
- 图片 `self`、`data:`、`blob:`。
- 连接本地和 HTTP/HTTPS API。

一般不需要手动改 Tauri CSP。

如果后续客户端需要访问固定线上 API，优先把后端域名配置到网页端和后端 CORS，而不是把 Tauri CSP 放开成无限制策略。

## 8. 修改后需要重启什么

修改 `.env` 后必须重启 FastAPI：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

如果使用桌面客户端开发模式，也建议重启 Tauri：

```bash
cd desktop
npm run dev
```

Windows：

```powershell
cd desktop
npm run dev:full:windows
```

## 9. 验证清单

配置完成后按顺序验证：

1. 打开健康检查：

```text
http://127.0.0.1:8000/health
```

预期：

```json
{"status":"ok"}
```

2. 打开首页：

```text
http://127.0.0.1:8000/home
```

预期：未登录也能浏览内容，右上角显示登录入口。

3. 打开问题详情：

```text
http://127.0.0.1:8000/questions/<question_id>
```

预期：游客可以看问题、回答、图片和公开评论。

4. 尝试发帖、收藏、评论或 AI 追问。

预期：未登录时引导登录，登录后才能操作。

5. 连续输错登录密码超过 5 次。

预期：接口返回限流提示，过一段时间后可以继续尝试。

6. 上传超过限制的头像、问题图片或回答图片。

预期：后端拒绝，不应等到完整大文件读入内存后才处理。

7. 如果启用了 `SEARCH_USE_ORACLE_TEXT=true`，搜索已有关键词。

预期：搜索结果正常；如果数据库没有 Oracle Text 索引，先改回 `false` 再排查迁移。

## 10. 常见问题

### 10.1 改完 `.env` 为什么没生效

后端启动时会读取 `.env`，修改后需要重启 FastAPI。

### 10.2 游客打开首页还是被踢到登录页

先清空浏览器 `sessionStorage` 或退出登录，再刷新页面。安全更新后，公共浏览接口遇到失效 token 会降级为游客模式。

### 10.3 搜索启用 Oracle Text 后报错

先确认是否已经导入：

```text
sql/migrations/20260428_add_question_oracle_text_indexes.sql
```

如果不确定，先把：

```env
SEARCH_USE_ORACLE_TEXT=false
```

重启后端，恢复旧搜索路径。

### 10.4 跨域请求失败

检查浏览器实际访问来源是否在 `CORS_ALLOW_ORIGINS` 里。来源必须包含协议、域名和端口，例如：

```text
http://localhost:8000
```

和：

```text
http://127.0.0.1:8000
```

是两个不同来源。

### 10.5 新增 CDN 后页面资源加载失败

检查 `CONTENT_SECURITY_POLICY`。新增脚本域名要加入 `script-src`，新增样式域名要加入 `style-src`，新增图片域名要加入 `img-src`。

## 11. 推荐提交前检查

提交安全配置相关改动前，建议至少执行：

```bash
python3 -m compileall -f app frontend_cli scripts
git diff --check
```

如果本机已安装项目依赖，再补充：

```bash
python -c "from app.main import app; print(app.title)"
```

如果要验证桌面端配置：

```bash
npm --prefix desktop run info
```
