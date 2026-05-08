# 数据库视图补跑说明

这份说明用于协作者在同步代码后判断是否需要补跑 `sql/views.sql` 或视图迁移脚本。

## 1. 什么时候需要跑视图脚本

需要跑的情况：

- 旧数据库之前只跑过建表、过程、触发器或业务迁移，但没有跑过 `sql/views.sql`。
- 数据库里没有 `V_QUESTION_OVERVIEW`、`V_HOT_QUESTIONS` 等视图。
- 已经跑过旧版视图，但需要同步当前仓库新增的报表视图。
- 答辩或交接前，需要确认数据库对象覆盖表、约束、索引、触发器、过程、函数和视图。

不需要单独跑的情况：

- 全新初始化数据库时已经执行过默认的 `scripts/load-oracle-schema.ps1`。
- 因为默认 schema 加载顺序已经包含 `sql/views.sql`。

默认加载内容包括：

```text
sql/create_tables.sql
sql/procedures.sql
sql/triggers.sql
sql/views.sql
```

## 2. 推荐执行方式

如果不确定当前数据库有没有完整视图，直接跑完整视图脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load-oracle-schema.ps1 -SqlFiles sql/views.sql
```

`sql/views.sql` 使用 `CREATE OR REPLACE VIEW`，重复执行是安全的。

如果数据库已经有旧版视图，只想补这次新增和刷新的报表视图，也可以跑视图迁移：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load-oracle-schema.ps1 -SqlFiles sql/migrations/20260503_refresh_reporting_views.sql
```

推荐优先级：

1. 不确定有没有完整视图：跑 `sql/views.sql`。
2. 确认旧视图已经存在，只差本次更新：跑 `20260503_refresh_reporting_views.sql`。
3. 全新库：正常跑默认 schema 加载，不需要单独跑视图脚本。

## 3. 当前应存在的视图

当前仓库落地的视图包括：

| 视图名 | 用途 |
| --- | --- |
| `V_QUESTION_OVERVIEW` | 问题概览，整合作者、分类、统计字段、标签数、图片数和活跃度分 |
| `V_HOT_QUESTIONS` | 热门问题候选列表 |
| `V_ANSWER_QUALITY_SUMMARY` | 回答质量概览，整合反馈、评论和采纳状态 |
| `V_USER_TAG_PROFILE_DETAIL` | 用户画像明细，展示标签权重和排名 |
| `V_ACTIVE_RECOMMENDATION_DETAIL` | 当前有效推荐明细 |
| `V_QUESTION_TAG_DETAIL` | 问题标签明细，展示标签来源、绑定来源和置信度 |
| `V_USER_ACTIVITY_SUMMARY` | 用户行为汇总，统计提问、回答、评论、收藏、浏览、搜索、画像和推荐 |
| `V_MEDIA_ASSET_DETAIL` | 媒体资源明细，整合上传者、归属对象、文件类型、大小和访问地址 |
| `V_CHAT_FOLLOWUP_SUMMARY` | AI 追问会话汇总，统计消息数和最后消息时间 |

## 4. 验证方式

跑完视图脚本后，可以执行完整 schema 校验：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
```

也可以进入数据库后检查视图状态：

```sql
SELECT object_name, status
  FROM user_objects
 WHERE object_type = 'VIEW'
 ORDER BY object_name;
```

所有业务视图应为 `VALID`。如果 `USER_ERRORS` 里出现视图错误，优先确认是否已经先跑过对应的表结构和迁移脚本。

## 5. Windows PowerShell 注意事项

如果一次要跑多个 SQL 文件，建议使用数组传参：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

$files = @(
  "sql/views.sql",
  "sql/migrations/20260503_refresh_reporting_views.sql"
)

.\scripts\load-oracle-schema.ps1 -SqlFiles $files
```

不要在 Windows PowerShell 里直接把多个文件平铺传给 `-SqlFiles` 后再换行追加其它参数，否则第二个文件可能被误解析成其它位置参数。
