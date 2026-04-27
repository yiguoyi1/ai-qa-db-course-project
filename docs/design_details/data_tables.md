# 数据表与业务映射说明

## 1. 说明

本文件用于说明每张数据表在产品中的业务角色，重点回答两个问题：

- 这张表是为哪个模块服务的
- 这张表在具体业务流程中承担什么作用

## 2. 基础数据表

| 表名 | 所属模块 | 业务作用 | 核心字段 | 说明 |
| --- | --- | --- | --- | --- |
| `USERS` | 用户与权限 | 保存账号身份、角色、用户状态和当前头像引用 | `USERNAME`, `ROLE`, `STATUS`, `LAST_LOGIN_TIME`, `AVATAR_MEDIA_ID` | 是登录、提问、收藏、推荐等全部业务的主体表 |
| `CATEGORIES` | 问题分类 | 管理问题所属分类 | `CATEGORY_NAME`, `STATUS` | 用于问题归类和后台分类运营 |
| `TAGS` | 标签管理 | 存储可复用标签及其来源状态 | `TAG_NAME`, `SOURCE`, `STATUS`, `CREATE_USER_ID` | 是画像与推荐计算的基础标签集合，可区分系统、用户、AI、管理员来源 |
| `MEDIA_ASSETS` | 媒体资源 | 统一保存头像、问题配图、回答配图的元数据和 BLOB 内容 | `OWNER_TYPE`, `OWNER_ID`, `PUBLIC_URL`, `FILE_CONTENT`, `STATUS` | 图片二进制保存在 Oracle `BLOB`，`PUBLIC_URL` 由后端读取 BLOB 返回 |
| `QUESTIONS` | 问题管理 | 存储用户提出的问题和当前采纳答案 | `USER_ID`, `CATEGORY_ID`, `TITLE`, `STATUS`, `ACCEPTED_ANSWER_ID` | 是问答系统的核心主表 |
| `ANSWERS` | 回答管理 | 存储 AI、人工或系统回答 | `QUESTION_ID`, `ANSWER_TYPE`, `CONTENT`, `AVG_RATING` | 承载回答内容及其质量统计，并通过 `(QUESTION_ID, ANSWER_ID)` 支撑采纳答案约束 |
| `QUESTION_TAGS` | 标签关联 | 建立问题与标签的多对多关系并记录绑定来源 | `QUESTION_ID`, `TAG_ID`, `SOURCE`, `CONFIDENCE_SCORE` | 为推荐、画像和标签展示提供连接关系，可追踪用户选择、自定义标签和 AI 自动标签 |

## 3. 用户行为表

| 表名 | 所属模块 | 业务作用 | 核心字段 | 说明 |
| --- | --- | --- | --- | --- |
| `ANSWER_FEEDBACK` | 回答反馈 | 记录用户对回答的点赞、点踩、评分 | `ANSWER_ID`, `USER_ID`, `IS_LIKE`, `RATING` | 一人对同一回答只保留一条当前反馈 |
| `ANSWER_COMMENTS` | 评论与回复 | 记录回答下的社区评论、回复与楼中楼结构 | `ANSWER_ID`, `USER_ID`, `PARENT_COMMENT_ID`, `ROOT_COMMENT_ID`, `STATUS` | 采用软删除，删除后保留评论树结构 |
| `FAVORITES` | 收藏管理 | 记录用户收藏的问题 | `USER_ID`, `QUESTION_ID`, `FAVORITE_TIME` | 用于收藏列表、热度统计和推荐过滤 |
| `BROWSE_HISTORY` | 浏览行为 | 记录用户浏览的问题及停留情况 | `USER_ID`, `QUESTION_ID`, `DURATION`, `CLICK_DEPTH` | 用于浏览统计和兴趣画像建模 |
| `SEARCH_HISTORY` | 搜索行为 | 记录用户搜索关键词 | `USER_ID`, `KEYWORD`, `SEARCH_TIME` | 用于分析搜索偏好和潜在热点 |

## 4. 推荐相关表

| 表名 | 所属模块 | 业务作用 | 核心字段 | 说明 |
| --- | --- | --- | --- | --- |
| `USER_TAG_PROFILE` | 用户画像 | 沉淀用户在不同标签上的兴趣权重 | `USER_ID`, `TAG_ID`, `WEIGHT` | 由行为数据重建，不建议手工直接维护 |
| `RECOMMENDATIONS` | 推荐结果 | 保存生成后的推荐列表 | `USER_ID`, `QUESTION_ID`, `REC_TYPE`, `REC_SCORE`, `STATUS` | 当前主要承载标签推荐结果 |

## 5. AI 扩展表

| 表名 | 所属模块 | 业务作用 | 核心字段 | 说明 |
| --- | --- | --- | --- | --- |
| `CHAT_SESSION` | 多轮会话 | 记录一次完整会话的开始、结束和状态 | `USER_ID`, `START_TIME`, `END_TIME`, `STATUS` | 支撑连续追问场景 |
| `CHAT_MESSAGE` | 会话消息 | 记录会话中的每条用户或 AI 消息 | `SESSION_ID`, `SENDER_TYPE`, `CONTENT` | 与 `CHAT_SESSION` 组成主从关系 |
| `AI_PROMPT_LOG` | AI 调用日志 | 记录提示词、返回内容和 token 消耗 | `QUESTION_ID`, `PROMPT_TEXT`, `RESPONSE_TEXT`, `TOKEN_USAGE` | 适合做追溯、成本分析和模型比较 |

## 6. 系统管理表

| 表名 | 所属模块 | 业务作用 | 核心字段 | 说明 |
| --- | --- | --- | --- | --- |
| `LOGIN_LOG` | 登录审计 | 记录每次登录尝试的时间、IP 和结果 | `USER_ID`, `LOGIN_TIME`, `IP_ADDRESS`, `RESULT` | 成功登录后会联动更新 `USERS.LAST_LOGIN_TIME` |
| `OPERATION_LOG` | 操作审计 | 记录关键操作行为 | `USER_ID`, `OP_TYPE`, `OP_CONTENT`, `OP_TIME` | 适合后台审计和问题追踪 |

## 7. 统计字段与自动维护关系

以下表包含“由业务行为自动维护”的统计字段：

| 目标表 | 统计字段 | 来源表 | 维护方式 |
| --- | --- | --- | --- |
| `QUESTIONS` | `VIEW_COUNT` | `BROWSE_HISTORY` | 触发器调用过程重算 |
| `QUESTIONS` | `FAVORITE_COUNT` | `FAVORITES` | 触发器调用过程重算 |
| `QUESTIONS` | `ANSWER_COUNT` | `ANSWERS` | 触发器调用过程重算 |
| `ANSWERS` | `LIKE_COUNT` | `ANSWER_FEEDBACK` | 触发器调用过程重算 |
| `ANSWERS` | `DISLIKE_COUNT` | `ANSWER_FEEDBACK` | 触发器调用过程重算 |
| `ANSWERS` | `AVG_RATING` | `ANSWER_FEEDBACK` | 触发器调用过程重算 |
| `USERS` | `LAST_LOGIN_TIME` | `LOGIN_LOG` | 成功登录后触发器同步 |

## 8. 产品模块到数据表的映射

| 产品模块 | 主要数据表 |
| --- | --- |
| 登录与权限 | `USERS`, `LOGIN_LOG` |
| 提问与回答 | `QUESTIONS`, `ANSWERS`, `CATEGORIES` |
| 标签体系 | `TAGS`, `QUESTION_TAGS` |
| 收藏与浏览 | `FAVORITES`, `BROWSE_HISTORY` |
| 搜索记录 | `SEARCH_HISTORY` |
| 回答反馈 | `ANSWER_FEEDBACK` |
| 评论与回复 | `ANSWER_COMMENTS` |
| 画像与推荐 | `USER_TAG_PROFILE`, `RECOMMENDATIONS` |
| AI 会话与调用日志 | `CHAT_SESSION`, `CHAT_MESSAGE`, `AI_PROMPT_LOG` |
| 后台审计 | `OPERATION_LOG`, `LOGIN_LOG` |
| 头像与内容图片 | `MEDIA_ASSETS`, `USERS` |
| 采纳答案 | `QUESTIONS`, `ANSWERS` |

## 9. 当前版本的表设计特点

- 主链路完整：从用户、问题、回答到推荐都已经具备对应表结构
- 行为与主数据分离：便于统计、审计和后续扩展
- 社区互动结构更完整：回答反馈与评论回复分层建模，避免混用
- 采纳答案约束更稳：通过 `QUESTIONS (QUESTION_ID, ACCEPTED_ANSWER_ID)` 复合外键保证不能跨问题采纳回答
- 媒体资源统一：头像、问题配图和回答配图全部落入 `MEDIA_ASSETS`，图片内容保存在 `FILE_CONTENT BLOB`
- 画像与推荐解耦：画像负责沉淀兴趣，推荐负责产出结果
- 日志能力完整：登录日志、操作日志、Prompt 日志、会话日志分层清晰
- 设计偏向课程答辩友好：每个模块都能明确说明“业务目的”和“数据库落点”
