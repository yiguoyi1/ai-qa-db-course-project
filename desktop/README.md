# AI QA 桌面客户端

这个目录是 AI QA 社区的 Tauri 桌面客户端。它不重写现有前端，而是提供一个轻量桌面壳：

- 启动后先检测 `http://127.0.0.1:8000/health`。
- 后端可用时自动进入现有 `/login` 页面。
- 登录、首页、详情页、用户中心、管理员后台等能力继续复用 FastAPI 交付的 Web 前端。

## 环境

当前开发环境需要：

- Node.js 与 npm
- Rust 与 Cargo

macOS 还需要：

- Xcode Command Line Tools

Windows 还需要：

- Microsoft C++ Build Tools，并勾选 `Desktop development with C++`
- Microsoft Edge WebView2 Runtime
- 如需生成 `.msi`，确保 Windows Optional Features 中的 VBSCRIPT 可用

本机已通过 Homebrew 安装：

```bash
brew install node rust
```

## 安装依赖

```bash
cd desktop
npm install
```

## 运行

macOS / Linux 下，如果后端已经启动：

```bash
cd desktop
npm run dev
```

macOS / Linux 下，如果想让脚本顺手启动 FastAPI 后端：

```bash
cd desktop
npm run dev:full
```

Windows PowerShell 下，如果想让脚本顺手启动 FastAPI 后端：

```powershell
cd desktop
npm run dev:full:windows
```

后端默认地址是 `http://127.0.0.1:8000`。如需改地址：

```bash
AI_QA_BACKEND_URL=http://127.0.0.1:8000 npm run dev:full
```

Windows PowerShell 下：

```powershell
$env:AI_QA_BACKEND_URL="http://127.0.0.1:8000"
npm run dev:full:windows
```

## 打包

```bash
cd desktop
npm run build
```

macOS 构建产物通常位于：

```text
desktop/src-tauri/target/release/bundle/
```

## Windows 打包

在 Windows PowerShell 下：

```powershell
cd desktop
npm install
npm run build:windows
```

默认会生成 NSIS `-setup.exe` 和 WiX `.msi` 两种安装包。也可以单独构建：

```powershell
npm run build:windows:nsis
npm run build:windows:msi
```

Windows 构建产物通常位于：

```text
desktop/src-tauri/target/release/bundle/nsis/
desktop/src-tauri/target/release/bundle/msi/
```

Windows 专用配置位于：

```text
desktop/src-tauri/tauri.windows.conf.json
```

其中 NSIS 安装器默认使用当前用户安装模式，不要求管理员权限；`.msi` 必须在 Windows 上构建。

## GitHub Actions 出 Windows 包

仓库包含 Windows 桌面端出包工作流：

```text
.github/workflows/build-desktop-windows.yml
```

进入 GitHub 仓库的 `Actions` 页面，选择 `Build Windows Desktop Client`，手动运行后可下载 `ai-qa-community-windows` artifact。里面包含 NSIS `-setup.exe` 和 WiX `.msi`。

## 设计边界

桌面端当前只负责客户端外壳与入口体验，不内置 Oracle、DeepSeek 或 FastAPI 服务。这样可以保持原有 B/S 架构清晰，后续也能平滑切到线上 API 地址。
