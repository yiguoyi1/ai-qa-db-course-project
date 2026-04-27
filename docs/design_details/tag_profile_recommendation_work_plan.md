# 问题标签、用户画像与问题推荐增强工作计划

## 1. 背景

当前项目已经具备基础标签、用户画像和推荐能力：

- `TAGS` 保存标签。
- `QUESTION_TAGS` 保存问题与标签的多对多关系。
- `USER_TAG_PROFILE` 保存用户对标签的兴趣权重。
- `RECOMMENDATIONS` 保存推荐结果。
- `qa_app_pkg.rebuild_user_tag_profile` 已经能根据提问、回答、收藏、浏览、反馈、评论和搜索等行为重建画像。
- `qa_app_pkg.generate_recommendations` 已经能基于 `HYBRID + USER_TAG_PROFILE + POPULARITY` 生成推荐。

本轮增强不是重做推荐系统，而是在现有结构上补强三件事：

1. 让问题标签来源更清楚。
2. 让用户画像权重更稳定。
3. 让推荐从单一标签匹配逐步升级为可解释的混合推荐。

## 2. 总体目标

### 2.1 业务目标

- 用户发布问题时可以选择已有标签。
- 用户可以输入自定义标签。
- 用户不选择标签时，系统可以调用 AI 自动分析问题并补标签。
- AI 优先匹配已有标签，匹配不到时再创建新标签。
- 用户画像根据用户行为持续沉淀兴趣权重。
- 推荐结果能够解释为什么推荐某个问题。

### 2.2 技术目标

- 保留当前 Oracle 表结构主线，做向后兼容扩展。
- 标签、画像、推荐都要能被 SQL 和文档解释清楚。
- AI 标签能力只作为增强层，不破坏用户主动选择标签的主流程。
- 推荐第一阶段继续使用可解释规则，不急于上复杂聚类。

## 3. 阶段一：标签体系补强

### 3.1 数据库扩展

建议扩展 `TAGS`：

```sql
source          VARCHAR2(20 CHAR) DEFAULT 'SYSTEM' NOT NULL,
status          VARCHAR2(20 CHAR) DEFAULT 'ACTIVE' NOT NULL,
description     VARCHAR2(200 CHAR),
create_user_id  NUMBER,
create_time     DATE DEFAULT SYSDATE NOT NULL
```

建议枚举：

- `source`: `SYSTEM`, `USER`, `AI`, `ADMIN`
- `status`: `ACTIVE`, `PENDING`, `DISABLED`

建议扩展 `QUESTION_TAGS`：

```sql
source            VARCHAR2(30 CHAR) DEFAULT 'USER_SELECTED' NOT NULL,
confidence_score  NUMBER(5,2),
create_time        DATE DEFAULT SYSDATE NOT NULL
```

建议枚举：

- `USER_SELECTED`: 用户选择已有标签
- `USER_CREATED`: 用户输入并创建新标签
- `AI_MATCHED`: AI 从已有标签中匹配
- `AI_CREATED`: AI 创建新标签
- `ADMIN_ADJUSTED`: 管理员调整

### 3.2 约束建议

- `TAGS.TAG_NAME` 继续唯一。
- 标签名统一做 trim 和长度限制。
- AI 生成的新标签建议限制为 1 到 3 个。
- `QUESTION_TAGS.CONFIDENCE_SCORE` 范围建议为 `0` 到 `100`。
- 同一个问题不能重复绑定同一个标签，继续保留 `uq_question_tags_pair`。

### 3.3 迁移要求

需要新增迁移脚本，例如：

```text
sql/migrations/20260427_extend_tag_metadata.sql
```

迁移需要处理旧数据：

- 现有 `TAGS` 默认 `source = 'SYSTEM'`
- 现有 `TAGS` 默认 `status = 'ACTIVE'`
- 现有 `QUESTION_TAGS` 默认 `source = 'USER_SELECTED'`
- 现有 `QUESTION_TAGS.CONFIDENCE_SCORE` 可以为空

## 4. 阶段二：用户选标签与自定义标签

### 4.1 发帖请求模型

当前 `QuestionCreateRequest` 已有 `tag_ids`。建议扩展：

```python
tag_ids: list[int] = []
custom_tags: list[str] = []
auto_tag: bool = True
```

业务含义：

- `tag_ids`: 用户选择已有标签。
- `custom_tags`: 用户输入的新标签。
- `auto_tag`: 当用户没有提供标签时，是否启用 AI 自动打标签。

### 4.2 服务层流程

发布问题时建议流程：

1. 校验分类、用户、问题标题和正文。
2. 创建 `QUESTIONS`。
3. 如果 `tag_ids` 不为空，绑定为 `USER_SELECTED`。
4. 如果 `custom_tags` 不为空，创建或复用标签，再绑定为 `USER_CREATED`。
5. 如果两者都为空且 `auto_tag = true`，调用 AI 标签服务。
6. AI 匹配已有标签时，绑定为 `AI_MATCHED`。
7. AI 创建新标签时，写入 `TAGS` 并绑定为 `AI_CREATED`。
8. 返回问题详情时带回最终标签列表。

### 4.3 新增后端组件

建议新增：

```text
app/repositories/tag_repository.py
app/services/tag_service.py
app/services/ai_tagging_service.py
app/prompts/question_tag_prompt.py
app/schemas/tag.py
```

也可以先不拆太细，把 `tag_repository` 和 `ai_tagging_service` 作为第一阶段新增，后续再整理。

## 5. 阶段三：AI 自动打标签

### 5.1 AI 输入

AI 标签分析需要输入：

- 问题标题
- 问题正文
- 当前已有标签列表
- 标签数量上限

### 5.2 AI 输出契约

建议要求 AI 只返回 JSON：

```json
{
  "matched_tags": [
    {
      "tag_id": 1,
      "tag_name": "oracle",
      "confidence_score": 92
    }
  ],
  "new_tags": [
    {
      "tag_name": "oracle-listener",
      "confidence_score": 86
    }
  ],
  "reason": "问题主要讨论 Oracle 监听端口和容器连接排查。"
}
```

### 5.3 结果处理规则

- 优先使用 `matched_tags`。
- 只有没有足够匹配标签时，才使用 `new_tags`。
- `confidence_score < 60` 的标签不自动绑定。
- 标签名必须经过规范化后再入库。
- AI 返回异常时不阻断发帖，可以让问题无标签发布，并记录日志。

### 5.4 日志建议

可以复用 `AI_PROMPT_LOG`，也可以后续新增专门日志表。

第一阶段建议复用 `AI_PROMPT_LOG`：

- `question_id`: 当前问题 ID
- `prompt_text`: 标签分析 prompt
- `response_text`: AI 原始 JSON
- `model_name`: DeepSeek 模型名
- `token_usage`: token 使用量

## 6. 阶段四：用户画像增强

### 6.1 当前画像基础

当前 `USER_TAG_PROFILE` 可以继续保留，作为用户兴趣向量：

```text
user_id + tag_id + weight
```

### 6.2 已落地权重来源

`rebuild_user_tag_profile` 当前按以下行为累计用户标签兴趣：

| 行为 | 当前权重或规则 |
| --- | --- |
| 用户提问带标签 | 5 |
| 用户回答某问题 | 4 |
| 用户收藏某问题 | 3 |
| 用户浏览某问题 | 基础 1，叠加停留时长和点击深度，上限受控 |
| 用户反馈某回答 | 点赞、点踩和评分组合换算 |
| 用户评论某回答 | 1.5 |
| 用户搜索关键词命中标签 | 1 |

### 6.3 衰减机制

后续可以加入时间衰减：

```text
最终权重 = 行为权重 * 时间衰减系数
```

第一阶段可以不做时间衰减，避免存储过程过早复杂化。

## 7. 阶段五：问题推荐增强

### 7.1 当前 HYBRID 推荐策略

当前使用可解释的混合规则：

```text
推荐分 = 标签匹配分 + 热度分 + 新鲜度分
```

当前拆分：

- 标签匹配分：来自 `USER_TAG_PROFILE.weight`
- 热度分：浏览数、收藏数、回答数
- 新鲜度分：近期问题加权
- 过滤规则：不推荐自己的问题、不推荐已收藏问题、不推荐关闭或归档问题

### 7.2 推荐类型

当前已有枚举：

- `TAG_BASED`
- `POPULARITY`
- `HYBRID`
- `MANUAL`

当前 `generate_recommendations` 生成的主要推荐类型为 `HYBRID`。当候选问题命中用户画像标签时，`REC_SOURCE` 记录为 `USER_TAG_PROFILE`；没有画像标签命中但仍具备热度或新鲜度价值时，`REC_SOURCE` 记录为 `POPULARITY`。

### 7.3 聚类和开源算法

聚类可行，但建议放在后续阶段。原因是：

- 当前数据量可能不够大。
- 聚类推荐解释成本更高。
- 数据库课程设计更适合先展示可解释推荐。

后续可选方案：

- `scikit-learn + TF-IDF + KMeans`: 适合课程项目，轻量可解释。
- `sentence-transformers`: 效果更好，适合文本相似推荐。
- `HDBSCAN`: 可自动发现主题簇，但依赖较重。
- `LightFM` 或 `implicit`: 适合行为数据足够多之后做协同过滤。

建议路线：

1. 保持当前 `HYBRID` 规则推荐作为主链路。
2. 再做 TF-IDF 文本相似推荐。
3. 最后再考虑聚类生成主题频道。

## 8. 接口规划

### 8.1 标签接口

当前已有：

- `GET /api/tags`
- `GET /api/tags/suggestions`

建议新增：

- `POST /api/tags`
- `POST /api/questions/{question_id}/tags/analyze`

### 8.2 发帖接口扩展

当前已有：

- `POST /api/questions`
- `POST /api/questions/ask`

建议扩展请求体：

```json
{
  "user_id": 1,
  "category_id": 2,
  "title": "Oracle 容器启动后连接不上怎么办？",
  "content": "数据库容器显示 healthy，但应用连接失败。",
  "tag_ids": [1, 2],
  "custom_tags": ["oracle-listener"],
  "auto_tag": true
}
```

## 9. 测试计划

### 9.1 数据库测试

- 新标签字段存在。
- 老数据迁移后默认值正确。
- 标签状态和来源枚举约束生效。
- `QUESTION_TAGS.CONFIDENCE_SCORE` 范围约束生效。

### 9.2 后端测试

- 用户选择已有标签时正常绑定。
- 用户输入自定义标签时正常创建和绑定。
- 用户不传标签时触发 AI 自动标签。
- AI 匹配已有标签时不重复创建。
- AI 创建新标签时能正常写入。
- AI 失败时发帖不被阻断。

### 9.3 推荐测试

- 重建画像后 `USER_TAG_PROFILE` 权重变化符合预期。
- 生成推荐后高匹配标签问题排序更靠前。
- 自己的问题不会被推荐。
- 已收藏问题不会被推荐。
- 关闭、归档问题不会被推荐。

## 10. 第一轮建议实现范围

第一轮建议只做这些：

1. 扩展 `TAGS` 和 `QUESTION_TAGS` 元数据字段。
2. 补迁移脚本。
3. 支持用户自定义标签。
4. 支持用户不选标签时 AI 自动打标签。
5. 文档同步。
6. 一轮基础测试。

暂时不做：

- 聚类推荐。
- embedding 推荐。
- 标签审核后台。
- 复杂时间衰减。
- 标签合并治理。

## 11. 验收标准

第一轮完成后，应满足：

- 用户发布问题时可以没有手动标签。
- 无手动标签时，系统能自动补出 1 到 3 个标签。
- 自动标签能够优先复用已有标签。
- 新标签来源可以被追踪为 `AI_CREATED`。
- 问题标签绑定来源可以区分用户和 AI。
- 用户画像和推荐仍能兼容旧逻辑。
- 文档能解释标签、画像、推荐三者之间的关系。

## 12. 第一轮实现状态

已落地：

- `TAGS` 增加 `source`、`status`、`description`、`create_user_id`、`create_time`。
- `QUESTION_TAGS` 增加 `source`、`confidence_score`、`create_time`。
- 新增迁移脚本 `sql/migrations/20260427_extend_tag_metadata.sql`。
- `POST /api/questions` 和 `POST /api/questions/ask` 支持 `tag_ids`、`custom_tags`、`auto_tag`。
- 用户选择已有标签时记录为 `USER_SELECTED`。
- 用户输入自定义标签时创建或复用标签，并记录为 `USER_CREATED`。
- 用户未提供任何标签且 `auto_tag=true` 时，调用 DeepSeek 分析问题标签。
- AI 优先匹配已有标签，记录为 `AI_MATCHED`；无法匹配时创建新标签，记录为 `AI_CREATED`。
- `GET /api/tags` 仅返回 `ACTIVE` 标签。
- 新增管理员基础标签治理接口：`GET /api/admin/tags`、`PATCH /api/admin/tags/{tag_id}`。
- 新增公开标签建议接口：`GET /api/tags/suggestions`，用于发帖时按关键词提示已有 `ACTIVE` 标签。
- `rebuild_user_tag_profile` 已扩展回答、评论、搜索等行为权重，画像来源更完整。
- `generate_recommendations` 已升级为 `HYBRID` 推荐，推荐理由会说明画像分、热度分和新鲜度分。

仍待后续阶段处理：

- 标签创建、标签合并和批量审核。
- 基于文本相似度或聚类的推荐补充。
