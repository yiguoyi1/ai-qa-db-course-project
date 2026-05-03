# ER 图说明

本项目的 ER 图源文件位于：

```text
docs/diagrams/ai_qa_er_diagram.mmd
```

VS Code Markdown 预览入口位于：

```text
docs/diagrams/ai_qa_er_diagram_preview.md
```

已导出的高清 PNG 位于：

```text
docs/diagrams/ai_qa_er_diagram.png
```

已导出的 SVG 位于：

```text
docs/diagrams/ai_qa_er_diagram.svg
```

该图根据 `sql/create_tables.sql` 中的表、主键、外键和关键业务字段整理，用于课程答辩、协作者交接和数据库结构讲解。

## 1. 查看方式

推荐方式：

- 在 VS Code 打开 `docs/diagrams/ai_qa_er_diagram_preview.md`，按 `Ctrl+Shift+V` 直接预览。
- 在支持 Mermaid 的 Markdown 预览器中打开。
- 使用 VS Code Mermaid 插件预览。
- 复制 `docs/diagrams/ai_qa_er_diagram.mmd` 内容到 Mermaid Live Editor。
- GitHub 支持 Mermaid 代码块渲染，但 `.mmd` 文件本身是否自动渲染取决于页面入口。

如果本地安装了 Mermaid CLI，可以导出 SVG，SVG 适合放大查看和插入文档：

```powershell
mmdc -i docs/diagrams/ai_qa_er_diagram.mmd -o docs/diagrams/ai_qa_er_diagram.svg -b white
```

当前环境已安装 Node.js LTS 和 Mermaid CLI。导出高清 PNG 的命令为：

```powershell
mmdc -i docs/diagrams/ai_qa_er_diagram.mmd -o docs/diagrams/ai_qa_er_diagram.png -b white -s 6
```

## 2. 图中覆盖的核心模块

ER 图覆盖以下业务模块：

- 用户、角色与登录审计：`USERS`, `LOGIN_LOG`, `OPERATION_LOG`
- 分类与标签：`CATEGORIES`, `TAGS`, `QUESTION_TAGS`
- 问题与回答：`QUESTIONS`, `ANSWERS`
- 回答反馈与楼中楼评论：`ANSWER_FEEDBACK`, `ANSWER_COMMENTS`
- 收藏、浏览、搜索行为：`FAVORITES`, `BROWSE_HISTORY`, `SEARCH_HISTORY`
- 用户画像与推荐：`USER_TAG_PROFILE`, `RECOMMENDATIONS`
- AI 首答与追问：`AI_PROMPT_LOG`, `CHAT_SESSION`, `CHAT_MESSAGE`
- 媒体资源：`MEDIA_ASSETS`

## 3. 需要特别说明的关系

`MEDIA_ASSETS.owner_type + owner_id` 是业务多态归属字段，可以表示头像、问题配图和回答配图。

数据库层面当前只显式约束：

- `MEDIA_ASSETS.uploader_user_id -> USERS.user_id`
- `USERS.avatar_media_id -> MEDIA_ASSETS.media_id`

`owner_id` 根据 `owner_type` 指向 `USERS`、`QUESTIONS` 或 `ANSWERS` 的业务含义由服务层保证，不是传统单一外键。

`QUESTIONS.accepted_answer_id` 通过复合外键约束到 `ANSWERS(question_id, answer_id)`，用于保证一个问题只能采纳属于自己的回答。

`ANSWER_COMMENTS` 使用自引用外键表达楼中楼结构：

- `parent_comment_id` 表示直接父评论
- `root_comment_id` 表示所属根评论
- `reply_to_user_id` 表示回复目标用户

## 4. 后续维护规则

修改 `sql/create_tables.sql` 后，应同步检查：

1. 是否新增或删除表。
2. 是否新增、删除或调整外键。
3. 是否新增关键业务字段。
4. 是否需要更新 `docs/diagrams/ai_qa_er_diagram.mmd`。
5. 如已导出 SVG/PNG，也要重新生成图片。

ER 图以 `sql/create_tables.sql` 为准，设计文档中的描述不能反过来覆盖数据库真实结构。
