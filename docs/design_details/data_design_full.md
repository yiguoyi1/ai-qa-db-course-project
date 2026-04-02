# 3 数据设计

## 3.1 数据设计目标

本系统的数据设计围绕智能问答平台的核心业务展开，目标如下：

1. 实现用户、问题、回答、分类、标签等基础数据的规范化存储。
2. 实现浏览、收藏、反馈、搜索等行为数据的统一管理。
3. 支持 AI 回答过程的数据记录，提高系统的智能化特征与可追溯性。
4. 支持单轮问答与多轮对话两种业务场景。
5. 通过主键、外键、唯一约束及检查约束保证数据完整性与一致性。
6. 满足数据库课程设计要求，当前版本已覆盖表、主键、外键、索引、触发器、存储过程、函数及大对象等内容，并为视图与更多推荐扩展预留空间。

---

## 3.2 数据设计原则

1. **结构清晰**：实体关系明确
2. **规范化设计**：减少冗余
3. **面向业务流程**：围绕问答与推荐
4. **可扩展性**：支持 AI 与推荐扩展

---

## 3.3 数据表总体结构

系统数据表分为五类：

### 基础数据表

* USERS
* CATEGORIES
* QUESTIONS
* ANSWERS
* TAGS
* QUESTION_TAGS

### 用户行为表

* ANSWER_FEEDBACK
* FAVORITES
* BROWSE_HISTORY
* SEARCH_HISTORY

### 推荐相关表

* RECOMMENDATIONS
* USER_TAG_PROFILE

### AI扩展表

* CHAT_SESSION
* CHAT_MESSAGE
* AI_PROMPT_LOG

### 系统管理表

* LOGIN_LOG
* OPERATION_LOG

---

## 3.4 数据表详细设计

### 3.4.1 USERS 用户表

用于存储用户基本信息。

| 字段名 | 类型 | 说明 |
| --------------- | ------------- | ------------ |
| USER_ID | NUMBER | 主键 |
| USERNAME | VARCHAR2(50) | 登录名 |
| PASSWORD_HASH | VARCHAR2(100) | 密码摘要 |
| NICKNAME | VARCHAR2(50) | 昵称 |
| EMAIL | VARCHAR2(100) | 邮箱 |
| PHONE | VARCHAR2(20) | 电话 |
| ROLE | VARCHAR2(20) | USER / ADMIN |
| STATUS | VARCHAR2(20) | 状态 |
| REGISTER_TIME | DATE | 注册时间 |
| LAST_LOGIN_TIME | DATE | 最近登录时间 |

**主键：** USER_ID

**唯一约束：** USERNAME

---

### 3.4.2 CATEGORIES 分类表

| 字段名 | 类型 |
| ------------- | ------------- |
| CATEGORY_ID | NUMBER |
| CATEGORY_NAME | VARCHAR2(50) |
| DESCRIPTION | VARCHAR2(200) |
| STATUS | VARCHAR2(20) |

**主键：** CATEGORY_ID

**唯一约束：** CATEGORY_NAME

---

### 3.4.3 QUESTIONS 问题表

| 字段名 | 类型 |
| -------------- | ------------- |
| QUESTION_ID | NUMBER |
| USER_ID | NUMBER |
| CATEGORY_ID | NUMBER |
| TITLE | VARCHAR2(200) |
| CONTENT | CLOB |
| ASK_TIME | DATE |
| STATUS | VARCHAR2(20) |
| VIEW_COUNT | NUMBER |
| FAVORITE_COUNT | NUMBER |
| ANSWER_COUNT | NUMBER |

**主键：** QUESTION_ID

**外键：**
* USER_ID → USERS
* CATEGORY_ID → CATEGORIES

---

### 3.4.4 ANSWERS 回答表

| 字段名 | 类型 |
| ---------------- | ------------ |
| ANSWER_ID | NUMBER |
| QUESTION_ID | NUMBER |
| ANSWER_TYPE | VARCHAR2(20) |
| PROVIDER_NAME | VARCHAR2(50) |
| CONTENT | CLOB |
| GENERATE_TIME | DATE |
| MODEL_NAME | VARCHAR2(50) |
| CONFIDENCE_SCORE | NUMBER(5,2) |
| LIKE_COUNT | NUMBER |
| DISLIKE_COUNT | NUMBER |
| AVG_RATING | NUMBER(3,2) |

**主键：** ANSWER_ID

**外键：** QUESTION_ID → QUESTIONS

---

### 3.4.5 TAGS 标签表

| 字段名 | 类型 |
| -------- | ------------ |
| TAG_ID | NUMBER |
| TAG_NAME | VARCHAR2(50) |

**主键：** TAG_ID

**唯一约束：** TAG_NAME

---

### 3.4.6 QUESTION_TAGS

| 字段名 | 类型 |
| ----------- | ------ |
| QT_ID | NUMBER |
| QUESTION_ID | NUMBER |
| TAG_ID | NUMBER |

**主键：** QT_ID

**外键：**
* QUESTION_ID → QUESTIONS
* TAG_ID → TAGS

**唯一约束：** (QUESTION_ID, TAG_ID)

---

### 3.4.7 ANSWER_FEEDBACK

| 字段名 | 类型 |
| ------------- | ------------- |
| FEEDBACK_ID | NUMBER |
| ANSWER_ID | NUMBER |
| USER_ID | NUMBER |
| IS_LIKE | VARCHAR2(10) |
| RATING | NUMBER(2,1) |
| COMMENT_TEXT | VARCHAR2(500) |
| FEEDBACK_TIME | DATE |

**主键：** FEEDBACK_ID

**外键：**
* ANSWER_ID → ANSWERS
* USER_ID → USERS

---

### 3.4.8 FAVORITES

| 字段名 | 类型 |
| ------------- | ------ |
| FAVORITE_ID | NUMBER |
| USER_ID | NUMBER |
| QUESTION_ID | NUMBER |
| FAVORITE_TIME | DATE |

**主键：** FAVORITE_ID

**外键：**
* USER_ID → USERS
* QUESTION_ID → QUESTIONS

**唯一约束：** (USER_ID, QUESTION_ID)

---

### 3.4.9 BROWSE_HISTORY

| 字段名 | 类型 |
| ----------- | ------ |
| HISTORY_ID | NUMBER |
| USER_ID | NUMBER |
| QUESTION_ID | NUMBER |
| BROWSE_TIME | DATE |
| DURATION | NUMBER |
| CLICK_DEPTH | NUMBER |

**主键：** HISTORY_ID

**外键：**
* USER_ID → USERS
* QUESTION_ID → QUESTIONS

---

### 3.4.10 SEARCH_HISTORY

| 字段名 | 类型 |
| ----------- | ------------- |
| SEARCH_ID | NUMBER |
| USER_ID | NUMBER |
| KEYWORD | VARCHAR2(100) |
| SEARCH_TIME | DATE |

**主键：** SEARCH_ID

**外键：** USER_ID → USERS

---

### 3.4.11 RECOMMENDATIONS

| 字段名 | 类型 |
| ----------- | ------------- |
| REC_ID | NUMBER |
| USER_ID | NUMBER |
| QUESTION_ID | NUMBER |
| REC_TYPE | VARCHAR2(50) |
| REC_SOURCE | VARCHAR2(50) |
| REC_REASON | VARCHAR2(200) |
| REC_SCORE | NUMBER(6,2) |
| REC_TIME | DATE |
| STATUS | VARCHAR2(20) |

**主键：** REC_ID

**外键：**
* USER_ID → USERS
* QUESTION_ID → QUESTIONS

---

### 3.4.12 USER_TAG_PROFILE

| 字段名 | 类型 |
| ----------- | ----------- |
| PROFILE_ID | NUMBER |
| USER_ID | NUMBER |
| TAG_ID | NUMBER |
| WEIGHT | NUMBER(6,2) |
| UPDATE_TIME | DATE |

**主键：** PROFILE_ID

**外键：**
* USER_ID → USERS
* TAG_ID → TAGS

---

### 3.4.13 CHAT_SESSION

| 字段名 | 类型 |
| ---------- | ------------ |
| SESSION_ID | NUMBER |
| USER_ID | NUMBER |
| START_TIME | DATE |
| END_TIME | DATE |
| STATUS | VARCHAR2(20) |

**主键：** SESSION_ID

**外键：** USER_ID → USERS

---

### 3.4.14 CHAT_MESSAGE

| 字段名 | 类型 |
| ----------- | ------------ |
| MESSAGE_ID | NUMBER |
| SESSION_ID | NUMBER |
| SENDER_TYPE | VARCHAR2(20) |
| CONTENT | CLOB |
| SEND_TIME | DATE |
| MODEL_NAME | VARCHAR2(50) |

**主键：** MESSAGE_ID

**外键：** SESSION_ID → CHAT_SESSION

---

### 3.4.15 AI_PROMPT_LOG

| 字段名 | 类型 |
| ------------- | ------------ |
| PROMPT_ID | NUMBER |
| QUESTION_ID | NUMBER |
| PROMPT_TEXT | CLOB |
| RESPONSE_TEXT | CLOB |
| TOKEN_USAGE | NUMBER |
| MODEL_NAME | VARCHAR2(50) |
| GENERATE_TIME | DATE |

**主键：** PROMPT_ID

**外键：** QUESTION_ID → QUESTIONS

---

### 3.4.16 LOGIN_LOG

| 字段名 | 类型 |
| ---------- | ------------ |
| LOG_ID | NUMBER |
| USER_ID | NUMBER |
| LOGIN_TIME | DATE |
| IP_ADDRESS | VARCHAR2(50) |
| RESULT | VARCHAR2(20) |

**主键：** LOG_ID

**外键：** USER_ID → USERS

---

### 3.4.17 OPERATION_LOG

| 字段名 | 类型 |
| ---------- | ------------- |
| OP_ID | NUMBER |
| USER_ID | NUMBER |
| OP_TYPE | VARCHAR2(50) |
| OP_CONTENT | VARCHAR2(200) |
| OP_TIME | DATE |

**主键：** OP_ID

**外键：** USER_ID → USERS

---

## 3.5 数据关系说明

本系统的数据关系以 `USERS` 为业务主体，以 `QUESTIONS` 和 `ANSWERS` 为主链路核心，并通过行为表、画像表和推荐表形成完整闭环。

主要关系如下：

1. 一个用户可以提出多个问题，`QUESTIONS.USER_ID -> USERS.USER_ID`
2. 一个问题属于一个分类，`QUESTIONS.CATEGORY_ID -> CATEGORIES.CATEGORY_ID`
3. 一个问题可以对应多个回答，`ANSWERS.QUESTION_ID -> QUESTIONS.QUESTION_ID`
4. 一个问题可以挂载多个标签，通过 `QUESTION_TAGS` 与 `TAGS` 建立多对多关系
5. 用户可对问题进行浏览、收藏、搜索，对回答进行反馈，这些行为分别落入独立行为表
6. 系统根据行为数据重建 `USER_TAG_PROFILE`，再生成 `RECOMMENDATIONS`
7. 登录、操作、Prompt 与会话信息独立存储，保证业务数据与审计数据解耦

整体关系链路可概括为：

`用户 -> 问题 -> 回答 -> 行为 -> 画像 -> 推荐`

---

## 3.6 数据设计优化说明

当前版本在传统问答结构基础上做了以下优化：

1. 引入 `AI_PROMPT_LOG`，用于记录提示词、响应内容、模型名和 token 消耗，提升可追溯性
2. 引入 `CHAT_SESSION` 与 `CHAT_MESSAGE`，支持多轮对话场景
3. 引入 `USER_TAG_PROFILE`，将用户行为沉淀为标签权重，避免推荐只依赖单次行为
4. 引入 `RECOMMENDATIONS`，将推荐结果落表，便于查询、排序和状态管理
5. 通过触发器和存储过程自动回写问题和回答统计字段，避免应用层重复维护统计逻辑

---

## 3.7 索引设计

对用户、问题、推荐等关键字段建立索引，提高查询效率。

---

## 3.8 视图设计

当前仓库尚未落地独立视图脚本。

从产品与课程设计角度，后续可补充以下视图：

1. 热门问题视图：聚合浏览量、收藏数、回答数，用于首页热点展示
2. 用户推荐视图：按用户查看当前有效推荐结果
3. 用户兴趣视图：按用户查看标签权重分布

当前版本已通过基础表、索引、过程和触发器支撑这些视图后续扩展。

---

## 3.9 触发器设计

当前已实现的触发器包括：

1. 回答变更后同步问题回答数
2. 收藏变更后同步问题收藏数
3. 浏览记录变更后同步问题浏览数
4. 回答反馈变更后同步点赞数、点踩数和平均评分
5. 登录成功后同步更新用户最近登录时间

这些触发器的设计目标是让统计字段在数据库层自动保持一致。

---

## 3.10 存储过程与函数设计

当前已实现的核心过程与函数包括：

1. `sync_question_statistics`：重算问题浏览数、收藏数、回答数
2. `refresh_answer_feedback_stats`：重算回答点赞数、点踩数、平均评分
3. `rebuild_user_tag_profile`：根据提问、收藏、浏览、反馈行为重建用户标签画像
4. `get_recommendation_score`：计算单个问题对指定用户的推荐分数
5. `generate_recommendations`：为指定用户生成推荐结果并更新推荐状态

当前实际落地的推荐逻辑以 `TAG_BASED + USER_TAG_PROFILE` 为主。

---

## 3.11 主键生成设计

当前版本主表主键统一使用 Oracle 的 `IDENTITY` 能力生成，而不是单独维护序列对象。

采用该方案的原因是：

1. Oracle 26ai 原生支持 `IDENTITY`
2. 脚本更简洁，便于课程设计演示和一键建库
3. 能满足当前版本对主键自动生成的需求

如果后续课程要求必须单独展示序列对象，可再补充 `SEQUENCE + TRIGGER/DEFAULT` 方案。

---

## 3.12 关键字段说明

当前已在数据库约束中明确以下关键字段取值范围：

1. `USERS.ROLE`: `USER`, `ADMIN`
2. `USERS.STATUS`: `ACTIVE`, `INACTIVE`, `LOCKED`, `DISABLED`
3. `CATEGORIES.STATUS`: `ACTIVE`, `INACTIVE`
4. `QUESTIONS.STATUS`: `OPEN`, `RESOLVED`, `CLOSED`, `ARCHIVED`
5. `ANSWERS.ANSWER_TYPE`: `AI`, `MANUAL`, `SYSTEM`
6. `ANSWER_FEEDBACK.IS_LIKE`: `Y`, `N`
7. `RECOMMENDATIONS.REC_TYPE`: `TAG_BASED`, `POPULARITY`, `HYBRID`, `MANUAL`
8. `RECOMMENDATIONS.REC_SOURCE`: `USER_TAG_PROFILE`, `POPULARITY`, `USER_ACTION`, `ADMIN_RULE`, `MANUAL`
9. `RECOMMENDATIONS.STATUS`: `ACTIVE`, `EXPIRED`, `DISMISSED`
10. `CHAT_SESSION.STATUS`: `OPEN`, `CLOSED`, `ARCHIVED`
11. `CHAT_MESSAGE.SENDER_TYPE`: `USER`, `AI`, `SYSTEM`
12. `LOGIN_LOG.RESULT`: `SUCCESS`, `FAILURE`, `LOCKED`

---

## 3.13 数据合法性说明

系统主要通过以下方式保证数据合法性：

1. 非空约束：保证关键主字段不能为空
2. 主键与唯一约束：避免重复数据
3. 外键约束：保证主从关系和引用完整性
4. 检查约束：限制状态、类型、评分、统计值范围
5. 触发器与过程：自动维护聚合统计，避免业务数据与统计字段不一致

例如：

- 用户名必须唯一
- 同一用户不能重复收藏同一问题
- 同一用户对同一回答只能保留一条反馈
- 评分必须在 `0` 到 `5` 之间
- 浏览数、收藏数、回答数、点赞数等统计值不能为负数

---

## 3.14 数据流逻辑说明

当前数据流逻辑如下：

1. 用户登录并进入系统
2. 用户执行提问、浏览、收藏、搜索、反馈等动作
3. 行为数据写入对应业务表
4. 触发器和过程自动更新问题与回答的统计字段
5. 存储过程根据行为重建用户标签画像
6. 推荐过程根据画像和问题热度生成推荐结果

因此，本系统的推荐不是孤立模块，而是依赖完整行为链路驱动的。

---

## 3.15 数据设计总结

本系统在传统问答结构基础上，引入 AI 与推荐机制，实现结构完整、扩展性强的数据设计。
