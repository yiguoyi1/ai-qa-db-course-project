# ai-qa-db-course-project
AI QA system with recommendation and database design.
# 🤖 智能问答记录与推荐管理系统

## 📌 项目简介

本项目为数据库课程设计，实现一个面向智能问答场景的管理系统。  
系统支持用户提问、AI回答记录、用户行为分析以及个性化推荐功能。

本系统在传统问答管理结构基础上，引入：

- 🤖 AI生成日志记录
- 💬 多轮会话管理
- 📊 用户兴趣画像建模
- 🎯 多策略推荐机制

实现“问答 + 行为 + 推荐”的完整数据闭环。

---

## 🏗️ 系统架构

本系统采用 **C/S + B/S 混合模式**：

- 🌐 前端：B/S（Web访问）
- 🖥️ 后台管理：C/S（数据维护与分析）
- 🗄️ 数据层：Oracle 11g 数据库

---

## 🧱 数据库设计概览

系统数据表分为五大模块：

### 1️⃣ 基础数据

- USERS（用户）
- QUESTIONS（问题）
- ANSWERS（回答）
- CATEGORIES（分类）
- TAGS（标签）

---

### 2️⃣ 用户行为

- BROWSE_HISTORY（浏览记录）
- FAVORITES（收藏）
- ANSWER_FEEDBACK（反馈）
- SEARCH_HISTORY（搜索）

---

### 3️⃣ 推荐系统

- RECOMMENDATIONS（推荐记录）
- USER_TAG_PROFILE（用户兴趣画像）

---

### 4️⃣ AI扩展

- CHAT_SESSION（会话）
- CHAT_MESSAGE（消息）
- AI_PROMPT_LOG（AI日志）

---

### 5️⃣ 系统管理

- LOGIN_LOG（登录日志）
- OPERATION_LOG（操作日志）

---

## 🔗 核心数据流程

```text
用户行为 → 标签权重计算 → 用户画像 → 推荐生成