# 问知社区 AskWise · 源码发行包

AskWise 是基于 Oracle 26ai、FastAPI 与 DeepSeek 的 AI 辅助问答社区课程项目，支持人工问答、评论、采纳、收藏、AI 首答与追问、自动分类与标签、用户画像和推荐。

这是可用于本地部署、学习和二次开发的**源码包**，不是双击运行的安装程序。不内置 Python 依赖、Oracle 镜像、数据库用户数据或桌面安装包。

- 项目仓库：<https://github.com/yiguoyi1/ai-qa-db-course-project>
- 官方发行页：<https://github.com/yiguoyi1/ai-qa-db-course-project/releases>
- 版本与源代码提交：见包内 `SOURCE_MANIFEST.json`。
- 许可证：MIT，见 `LICENSE`；第三方依赖与服务适用各自条款。

## 1. 环境准备

以下步骤面向 **Windows PowerShell**，所有命令均在解压后的项目根目录执行，无需 Git。

准备 Python 3.10+、启用 Linux 容器的 Docker Desktop，以及 Oracle Container Registry 镜像访问权限。首次安装需要联网下载依赖与镜像；网页中的部分资源使用外部 CDN。AI 功能需要自己的 DeepSeek API Key 和可用额度。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

仅在尚未创建 `.env` 时执行最后一行，不要覆盖已有配置。编辑 `.env`：

| 配置 | 要求 |
| --- | --- |
| `ORACLE_PWD` | 设置独立的 Oracle 管理密码，不使用示例值 |
| `APP_USER_PASSWORD` | 设置应用数据库用户密码，不使用示例值 |
| `JWT_SECRET_KEY` | 使用下方命令生成随机密钥，填写输出值 |
| `DEEPSEEK_API_KEY` | 填入自己的 Key；不用 AI 时留空，并关闭提问时的 AI 首答选项 |
| 数据库连接 | 本地默认 `localhost:1521/FREEPDB1`；调整端口或用户名后同步修改配置 |

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

不得把 `.env`、真实密码或 API Key 上传到公共仓库。

## 2. 初始化全新数据库

先启动 Docker Desktop，再执行：

```powershell
docker login container-registry.oracle.com
powershell -ExecutionPolicy Bypass -File .\scripts\start-oracle26ai.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\load-oracle-schema.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\load-seed-data.ps1
```

`docker login` 使用 Oracle 账号和该镜像仓库要求的登录凭据，不是 Docker Hub 账号。启动脚本会等待容器就绪；首次下载与初始化可能需要较长时间。

Schema 脚本依次加载表、过程包、触发器和视图。种子脚本加载基础分类及少量固定演示记录，不是公网批量造数。之后请在页面注册自己的账号，不依赖演示账号登录。

**已有数据库不要重新执行全新建库流程。** 先备份，再核对 `sql/migrations/` 中尚未执行的迁移及其前置条件，按顺序应用；不要盲目重跑全部迁移。已有 Docker 数据卷不会因修改 `.env` 自动更换数据库管理员密码。

## 3. 启动网页与后端

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

| 入口 | 本地地址 |
| --- | --- |
| 产品介绍 | <http://127.0.0.1:8000/> |
| 注册与登录 | <http://127.0.0.1:8000/login> |
| 社区首页 | <http://127.0.0.1:8000/home> |
| API 文档 | <http://127.0.0.1:8000/docs> |
| 进程健康检查 | <http://127.0.0.1:8000/health> |

`/health` 仅说明 Web 进程可响应，不证明 Oracle 已连接或 AI Key 可用。进一步检查数据库：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
```

建议验证注册、登录、发布不带 AI 的问题、人工回答与删除，再使用自己的 Key 测试 AI 首答和追问。真实 AI 调用会产生费用。

需要管理员时，先注册自己的账号，再以有数据库操作权限的身份执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\grant-admin.ps1 -Username your_username
```

## 4. 可选客户端

CLI 业务测试入口：

```powershell
.\.venv\Scripts\python.exe .\scripts\start_business_test.py
```

`desktop/` 包含 Tauri 桌面端源码，不是独立后端。Windows 构建另需 Node.js、Rust、Microsoft C++ Build Tools 和 WebView2：

```powershell
cd desktop
npm ci
npm run dev
```

在桌面启动页手动填写自己的后端地址，本地为 `http://127.0.0.1:8000`。源码中的历史演示服务器地址不作为公共服务提供，也不保证可用；每次启动请检查连接地址。构建安装包可运行 `npm run build:windows:nsis`，本发行版不提供预编译安装程序，网页内的桌面下载入口也需自行部署安装文件。

## 5. 包内容与校验

包含 `app/`、`frontend_cli/`、`desktop/`、`sql/`、`docker/`、运行和校验所需的 `scripts/`、首页使用的 `promo/` 资源、配置模板和 MIT 许可证。未包含 `.git/`、真实 `.env`、运行日志、用户上传数据、造数输出、课程报告或本地依赖。

发行页提供 `askwise-community-<版本>-source.zip` 及同名 `.sha256`。在解压前执行下列命令，将输出的 Hash 与校验文件内容比较：

```powershell
Get-FileHash .\askwise-community-v0.1.1-source.zip -Algorithm SHA256
```

`SOURCE_MANIFEST.json` 记录来源提交与每个文件的 SHA-256。运行代码直接读取该提交的 Git 对象，不混入维护者未提交的本地修改；包内本说明取代仓库展示 README，避免引用未打包的报告和设计文档。

请下载发行页 Assets 中明确命名的 `askwise-community-*-source.zip`。GitHub 自动生成的 `Source code (zip)` / `Source code (tar.gz)` 是完整仓库快照，不是本精简发行包。
