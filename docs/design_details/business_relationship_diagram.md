# 业务关系图说明

本项目已经包含一张完整 ER 图，用于讲数据库表、主键、外键和关键字段。为了方便协作者快速理解业务链路，额外补充一张业务关系图。

## 1. 文件位置

Mermaid 源文件：

```text
docs/diagrams/ai_qa_business_relationship.mmd
```

VS Code Markdown 预览入口：

```text
docs/diagrams/ai_qa_business_relationship_preview.md
```

## 2. 图的定位

这张图用于回答“系统里各业务模块之间是什么关系”：

- 访问入口：游客、登录用户、管理员、网页前端、CLI / Tauri
- 后端服务：认证、问题、回答、评论、分类、标签、媒体、AI、行为、画像、推荐、治理
- 基础设施：Oracle 26ai 数据库、DeepSeek API

它不替代 ER 图。涉及表字段、主键、外键和约束时，仍以 [er_diagram.md](er_diagram.md) 和 `sql/create_tables.sql` 为准。

## 3. 核心业务关系

- 用户注册登录后，围绕问题进行提问、回答、评论、收藏、浏览、搜索和反馈。
- 问题属于一个启用分类，可以绑定多个标签，可以带问题配图。
- 回答属于一个问题，可以被问题作者或管理员采纳，可以带回答配图。
- 评论挂在回答下，楼中楼通过评论自引用表达。
- AI 首答由问题触发，后续追问绑定到“问题 + AI 首答”。
- 行为数据进入用户画像，用户画像和行为共同参与 HYBRID 推荐。
- 管理员通过治理入口管理用户、分类、标签、问题、评论和审计日志。

## 4. 查看方式

推荐在 VS Code 中打开：

```text
docs/diagrams/ai_qa_business_relationship_preview.md
```

然后按 `Ctrl+Shift+V` 预览 Mermaid 图。

如果本地安装了 Mermaid CLI，可以导出图片：

```powershell
mmdc -i docs/diagrams/ai_qa_business_relationship.mmd -o docs/diagrams/ai_qa_business_relationship.svg -b white
mmdc -i docs/diagrams/ai_qa_business_relationship.mmd -o docs/diagrams/ai_qa_business_relationship.png -b white -s 4
```

## 5. 维护规则

当以下内容发生变化时，需要同步检查这张图：

1. 新增主要业务模块。
2. 删除或合并主要业务模块。
3. 修改 AI 首答、AI 追问、推荐、媒体、评论等主链路。
4. 调整管理员治理范围。
5. 修改访问入口，例如新增独立前端或移动端。
