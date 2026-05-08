# 桌面客户端环境配置与安装包获取指南

最后更新：2026-04-27

本文面向刚接手项目的同事，目标是让你完成 AI QA 社区桌面客户端相关环境配置、开发运行、打包，以及安装包下载。

桌面客户端位于：

```text
desktop/
```

当前客户端是 Tauri 轻量桌面壳，不内置 Oracle、DeepSeek 或 FastAPI。安装包启动后会先检测服务器 `http://120.55.74.107/health`，后端可用后进入服务器 `/home` 社区首页；未登录用户可以先浏览内容，右上角登录后再进行发帖、收藏、回答等操作。本地开发时仍可在启动页手动改为 `http://127.0.0.1:8000`。

官方参考：

- [Tauri v2 Prerequisites](https://v2.tauri.app/start/prerequisites/)
- [Tauri Windows Installer](https://v2.tauri.app/distribute/windows-installer/)
- [Node.js Download](https://nodejs.org/en/download)
- [Rust Install](https://www.rust-lang.org/tools/install)

## 1. 你需要先判断自己要做什么

如果只是体验客户端：

1. 确认服务器 `http://120.55.74.107/health` 可访问。
2. 获取 `.dmg`、`.app`、`-setup.exe` 或 `.msi` 安装包。
3. 安装并打开客户端。

如果要开发或打包客户端：

1. 配置 Node/npm。
2. 配置 Rust/Cargo。
3. 安装平台依赖。
4. 在 `desktop/` 下执行 `npm install`。
5. 运行或打包 Tauri 客户端。

## 2. 通用前置条件

请先确认仓库已经拉到本地，并进入项目根目录：

```bash
cd /Users/corld/Desktop/软件系统开发/Facebook
```

Windows PowerShell 示例：

```powershell
cd <你的仓库路径>\Facebook
```

如果要本地开发，确认本机后端可以启动：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器打开本机健康检查：

```text
http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

## 3. macOS 环境配置

### 3.1 安装系统依赖

安装 Xcode Command Line Tools：

```bash
xcode-select --install
```

确认 Homebrew 可用：

```bash
brew --version
```

如果没有 Homebrew，请先到 [brew.sh](https://brew.sh/) 按官方说明安装。

### 3.2 安装 Node/npm 与 Rust/Cargo

```bash
brew install node rust
```

验证：

```bash
node -v
npm -v
rustc --version
cargo --version
```

### 3.3 安装客户端依赖

```bash
cd desktop
npm install
```

### 3.4 开发运行

如果后端已经手动启动：

```bash
npm run dev
```

如果希望脚本尝试自动拉起 FastAPI 后端：

```bash
npm run dev:full
```

### 3.5 macOS 打包

```bash
npm run build
```

产物位置：

```text
desktop/src-tauri/target/release/bundle/macos/
desktop/src-tauri/target/release/bundle/dmg/
```

当前项目已经验证可以生成：

```text
AI QA Community.app
AI QA Community_0.1.0_aarch64.dmg
```

## 4. Windows 环境配置

Windows 建议使用 Windows 10 或 Windows 11。

### 4.1 安装 Microsoft C++ Build Tools

1. 打开 [Tauri v2 Prerequisites](https://v2.tauri.app/start/prerequisites/)。
2. 按 Windows 部分下载 Microsoft C++ Build Tools。
3. 安装时勾选 `Desktop development with C++`。
4. 安装完成后重启终端或重启系统。

如果后续出现 `link.exe`、`cl.exe`、MSVC 或 Windows SDK 相关报错，通常是这一步没有装完整。

### 4.2 安装 WebView2 Runtime

Tauri 在 Windows 上使用 Microsoft Edge WebView2 渲染页面。Windows 10 1803 及以后版本通常已自带 WebView2。

如果客户端无法打开窗口或提示 WebView2 缺失，请安装 Microsoft Edge WebView2 Runtime 的 Evergreen Bootstrapper。

### 4.3 检查 VBSCRIPT

如果你需要构建 `.msi`，Windows 需要启用 VBSCRIPT 可选功能。大多数系统默认启用。

如果构建 `.msi` 时出现 `failed to run light.exe` 一类错误：

1. 打开 Settings。
2. 进入 Apps。
3. 进入 Optional features。
4. 打开 More Windows features。
5. 找到并勾选 VBSCRIPT。
6. 按提示重启系统。

### 4.4 安装 Node/npm 与 Rust/Cargo

推荐安装 Node.js LTS。可通过官网下载，也可以使用 winget：

```powershell
winget install OpenJS.NodeJS.LTS
```

推荐通过 rustup 安装 Rust：

```powershell
winget install Rustlang.Rustup
```

安装后重新打开 PowerShell，验证：

```powershell
node -v
npm -v
rustc --version
cargo --version
```

如 `rustc` 或 `cargo` 找不到，先重新打开 PowerShell；仍然找不到时检查 Rust 是否加入了用户 PATH。

### 4.5 安装客户端依赖

```powershell
cd desktop
npm install
```

### 4.6 Windows 开发运行

如果后端已经手动启动：

```powershell
npm run dev
```

如果希望脚本尝试自动拉起 FastAPI 后端：

```powershell
npm run dev:full:windows
```

如需指定后端地址：

```powershell
$env:AI_QA_BACKEND_URL="http://127.0.0.1:8000"
npm run dev:full:windows
```

### 4.7 Windows 打包

构建 NSIS `-setup.exe` 和 WiX `.msi`：

```powershell
npm run build:windows
```

只构建 NSIS：

```powershell
npm run build:windows:nsis
```

只构建 MSI：

```powershell
npm run build:windows:msi
```

产物位置：

```text
desktop/src-tauri/target/release/bundle/nsis/
desktop/src-tauri/target/release/bundle/msi/
```

说明：

- NSIS 产物通常是 `AI QA Community_*_x64-setup.exe` 一类文件。
- MSI 产物通常是 `AI QA Community_*.msi`。
- Tauri 官方说明 `.msi` 只能在 Windows 上构建。

## 5. 通过 GitHub Actions 下载 Windows 安装包

仓库工作流：

```text
.github/workflows/build-desktop-windows.yml
```

如果你有 GitHub 仓库权限，可以这样下载 Windows 客户端：

1. 打开 GitHub 仓库页面。
2. 进入 Actions。
3. 选择 `Build Windows Desktop Client`。
4. 点击 `Run workflow` 手动触发，或等待 `main` 分支推送后自动触发。
5. 等待 workflow 运行完成。
6. 打开对应 run。
7. 在 Artifacts 区域下载 `ai-qa-community-windows`。
8. 解压 artifact，里面应包含 NSIS `-setup.exe` 和 WiX `.msi`。

注意：修改或新增 `.github/workflows/*.yml` 时，推送使用的 GitHub Personal Access Token 需要具备 `workflow` 权限。

## 6. 安装包分发建议

开发演示阶段：

- macOS：优先发 `.dmg`。
- Windows：优先发 NSIS `-setup.exe`。
- 如需企业内网部署或软件分发系统，可使用 `.msi`。

正式分发阶段建议补充：

- macOS 代码签名与公证。
- Windows 代码签名证书。
- 自动更新策略。
- 后端地址配置策略。

## 7. 验证客户端是否可用

无论 macOS 还是 Windows，打开客户端后按下面顺序验证：

1. 打开 `http://120.55.74.107/health`，确认返回 `{"status":"ok"}`。
2. 如需本地开发，再启动本机 FastAPI 并把启动页地址改为 `http://127.0.0.1:8000`。
3. 打开桌面客户端。
4. 启动页显示后端已连接。
5. 客户端自动进入 `/home`。
6. 未登录状态查看热榜、搜索或打开问题详情。
7. 点击右上角登录按钮，登录普通用户。
8. 打开一个问题详情。
9. 进入用户中心或管理员后台，确认页面跳转正常。

## 8. 常见问题

### 8.1 `npm` 找不到

说明 Node.js 没有安装完整，或 PATH 没刷新。

处理：

1. 重新安装 Node.js LTS。
2. 关闭并重新打开终端。
3. 再执行 `node -v` 和 `npm -v`。

### 8.2 `cargo` 或 `rustc` 找不到

说明 Rust 没装好，或 PATH 没刷新。

处理：

1. Windows 推荐使用 rustup。
2. macOS 可使用 `brew install rust`。
3. 重新打开终端。
4. 执行 `rustc --version` 和 `cargo --version`。

### 8.3 Windows 构建时报 MSVC 或 linker 错误

通常是 Microsoft C++ Build Tools 没装完整。

处理：

1. 重新打开 Visual Studio Installer。
2. 修改 Build Tools 安装项。
3. 勾选 `Desktop development with C++`。
4. 确认 Windows SDK 已安装。

### 8.4 Windows 客户端提示 WebView2 缺失

安装 Microsoft Edge WebView2 Runtime Evergreen Bootstrapper。

### 8.5 `.msi` 构建失败并提到 `light.exe`

检查 Windows VBSCRIPT 可选功能是否启用。

### 8.6 启动页一直显示无法连接后端

先确认服务器健康检查可用：

```text
http://120.55.74.107/health
```

如果要连接本地开发后端，再确认本机 FastAPI 已启动：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

再打开：

```text
http://127.0.0.1:8000/health
```

如果本地端口不是 `8000`，在启动页里手动修改后端地址，或设置：

```powershell
$env:AI_QA_BACKEND_URL="http://127.0.0.1:<你的端口>"
```

### 8.7 macOS 打开 `.app` 被系统拦截

开发阶段产物通常没有签名和公证。可右键打开，或在系统设置里允许打开。正式分发前需要补代码签名与公证。

## 9. 不要提交这些内容

这些目录和文件是构建产物或本机依赖，不应该提交：

```text
desktop/node_modules/
desktop/src-tauri/target/
desktop/src-tauri/gen/
```

当前 `.gitignore` 已经忽略它们。

## 10. 快速命令备忘

macOS：

```bash
brew install node rust
cd desktop
npm install
npm run dev:full
npm run build
```

Windows：

```powershell
cd desktop
npm install
npm run dev:full:windows
npm run build:windows
```
