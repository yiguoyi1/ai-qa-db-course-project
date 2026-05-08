# 功能模块图说明

这份文档用于说明“问知社区 AskWise Community”的功能模块图。它适合放在课程答辩、项目展示或协作者交接材料中，用来快速说明系统有哪些功能域。

## 1. 文件位置

Mermaid 源文件：

```text
docs/diagrams/askwise_function_modules.mmd
```

VS Code Markdown 预览入口：

```text
docs/diagrams/askwise_function_modules_preview.md
```

已导出的 PNG：

```text
docs/diagrams/askwise_function_modules.png
```

已导出的 SVG：

```text
docs/diagrams/askwise_function_modules.svg
```

## 2. 图的定位

功能模块图回答的是“系统包含哪些功能模块”。

它和其他图的分工如下：

- 功能模块图：说明系统功能域和功能清单。
- 业务关系图：说明用户、问题、回答、AI、推荐、媒体和管理员治理之间的业务关系。
- ER 图：说明数据库表、字段、主键、外键和约束。

## 3. 当前功能模块

图中把系统拆成 7 个主要模块：

- 访问入口：产品首页、网页端、Tauri 桌面端、CLI 测试前端。
- 用户端功能：注册登录、游客浏览、发布问题、人工回答、评论、收藏反馈、采纳答案、用户中心。
- AI 辅助能力：AI 首答、AI 多轮追问、AI 自动分类、AI 自动标签、AI 调用日志。
- 画像与推荐：行为采集、用户标签画像、HYBRID 推荐、首页与用户中心推荐。
- 媒体能力：头像、问题配图、回答配图、Oracle BLOB 存储、统一媒体读取。
- 管理员后台：用户治理、分类治理、标签治理、内容治理、审计日志。
- 数据与运行支撑：Oracle schema、触发器、存储过程、视图、种子数据、Docker / WSL、部署与打包。

## 4. 查看与导出

推荐在 VS Code 打开：

```text
docs/diagrams/askwise_function_modules_preview.md
```

然后按 `Ctrl+Shift+V` 预览。

如果本地安装 Mermaid CLI，可以重新导出图片：

```powershell
mmdc -i docs/diagrams/askwise_function_modules.mmd -o docs/diagrams/askwise_function_modules.svg -b white
mmdc -i docs/diagrams/askwise_function_modules.mmd -o docs/diagrams/askwise_function_modules.png -b white -s 4
```

## 5. 维护规则

当以下内容发生变化时，需要同步维护这张图：

1. 新增用户端主功能。
2. 新增管理员后台模块。
3. 新增 AI 能力，例如审核、总结、相似问题推荐。
4. 新增媒体能力，例如评论图片或媒体审核。
5. 新增客户端入口，例如移动端。
6. 改变推荐、画像、行为采集的核心边界。
