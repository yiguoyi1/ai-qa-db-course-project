# 3 数据设计

## 3.1 数据设计目标

本系统的数据设计围绕智能问答平台的核心业务展开，目标如下：

1. 实现用户、问题、回答、分类、标签等基础数据的规范化存储。
2. 实现浏览、收藏、反馈、搜索等行为数据的统一管理。
3. 支持 AI 回答过程的数据记录，提高系统的智能化特征与可追溯性。
4. 支持单轮问答与多轮对话两种业务场景。
5. 通过主键、外键、唯一约束及检查约束保证数据完整性与一致性。
6. 满足数据库课程设计要求，覆盖表、主键、外键、索引、视图、序列、触发器、存储过程、函数及大对象等内容。

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

（用户→问题→回答→行为→推荐完整链路）

---

## 3.6 数据设计优化说明

（AI日志 + 会话 + 用户画像 + 推荐增强）

---

## 3.7 索引设计

对用户、问题、推荐等关键字段建立索引，提高查询效率。

---

## 3.8 视图设计

包括热门问题视图、推荐视图、用户兴趣视图等。

---

## 3.9 触发器设计

自动维护浏览量、收藏数、评分等统计信息。

---

## 3.10 存储过程与函数设计

实现推荐生成、兴趣更新等逻辑。

---

## 3.11 序列设计

各主表使用序列生成主键。

---

## 3.12 关键字段说明

定义状态与类型字段取值范围。

---

## 3.13 数据合法性说明

通过非空、范围、枚举约束保证数据正确性。

---

## 3.14 数据流逻辑说明

用户行为 → 兴趣画像 → 推荐生成。

---

## 3.15 数据设计总结

本系统在传统问答结构基础上，引入 AI 与推荐机制，实现结构完整、扩展性强的数据设计。
