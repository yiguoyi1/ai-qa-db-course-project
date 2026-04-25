# AI 多轮追问后端说明

## 1. 功能定位

当前多轮追问能力的业务语义是：

- 用户先通过 `POST /api/questions/ask` 获得一条 `AI` 类型首答
- 用户围绕这条 AI 首答继续追问
- 系统把这段连续交流保存为一条独立会话

这不是一个脱离问题详情的通用聊天窗口，而是“基于某道题、某条 AI 回答”的追问会话。

## 2. 数据锚点

会话主表：`CHAT_SESSION`

当前正式锚定字段：

- `USER_ID`
- `QUESTION_ID`
- `SEED_ANSWER_ID`
- `STATUS`
- `START_TIME`
- `END_TIME`

消息表：`CHAT_MESSAGE`

- `SESSION_ID`
- `SENDER_TYPE`
- `CONTENT`
- `SEND_TIME`
- `MODEL_NAME`

因此，一条追问会话的归属关系是：

- 属于某个用户
- 围绕某个问题
- 基于某条 AI 首答

## 3. 当前接口

### 3.1 创建或续写追问

`POST /api/questions/{question_id}/answers/{answer_id}/follow-up`

用途：

- 当 `session_id` 为空时，创建新会话并写入“用户追问 + AI 回复”
- 当 `session_id` 存在时，向已有会话继续追加一轮“用户追问 + AI 回复”

请求体：

```json
{
  "session_id": 12,
  "content": "如果容器已经启动，但数据库一直连不上，我应该先查什么？"
}
```

说明：

- `session_id` 可选
- `content` 必填

成功响应：

```json
{
  "session": {
    "session_id": 12,
    "user_id": 21,
    "question_id": 62,
    "seed_answer_id": 82,
    "status": "OPEN",
    "start_time": "2026-04-25T21:26:31+08:00",
    "end_time": null,
    "message_count": 4,
    "last_message_time": "2026-04-25T21:26:31+08:00"
  },
  "messages": [
    {
      "message_id": 5,
      "session_id": 12,
      "sender_type": "USER",
      "content": "如果容器已经启动，但数据库一直连不上，我应该先查什么？",
      "send_time": "2026-04-25T21:26:31+08:00",
      "model_name": null
    },
    {
      "message_id": 6,
      "session_id": 12,
      "sender_type": "AI",
      "content": "建议先检查容器健康状态、监听端口和初始化日志。",
      "send_time": "2026-04-25T21:26:31+08:00",
      "model_name": "deepseek-chat"
    }
  ]
}
```

### 3.2 查看某条 AI 首答下的追问会话列表

`GET /api/questions/{question_id}/answers/{answer_id}/follow-up-sessions`

用途：

- 查看围绕这条 AI 首答已经产生过哪些追问会话

成功响应：

```json
{
  "question_id": 62,
  "seed_answer_id": 82,
  "item_count": 1,
  "items": [
    {
      "session_id": 12,
      "user_id": 21,
      "question_id": 62,
      "seed_answer_id": 82,
      "status": "OPEN",
      "start_time": "2026-04-25T21:26:31+08:00",
      "end_time": null,
      "message_count": 4,
      "last_message_time": "2026-04-25T21:26:31+08:00"
    }
  ]
}
```

### 3.3 查看会话详情

`GET /api/chat/sessions/{session_id}`

用途：

- 拉取某条追问会话详情
- 用于会话回放

成功响应：

- 返回结构与 `POST follow-up` 的响应一致

## 4. 当前业务规则

当前后端已经落实的约束如下：

1. 只有 `AI` 类型回答可以发起多轮追问
2. `answer_id` 必须属于当前 `question_id`
3. 任何已登录用户都可以查看会话列表和会话详情，但只有会话创建者可以续写
4. 续写时 `session_id` 必须和当前 `question_id + answer_id` 对齐
5. 只有 `OPEN` 状态的会话可以继续追问
6. 每次追问都会写入两条消息：
   - 一条 `USER`
   - 一条 `AI`
7. Prompt 会带入：
   - 原问题标题
   - 原问题内容
   - 首条 AI 回答
   - 当前会话历史消息
8. 每次 AI 回复都会额外写入 `AI_PROMPT_LOG`

## 5. 当前未做的部分

当前已经完成的是后端主链路，尚未完成的是：

- 网页前端入口
- CLI 专用入口
- 会话关闭接口
- 会话删除 / 归档接口
- 多轮追问专属页面展示

## 6. 自检脚本

仓库已补充业务约束自检脚本：

```powershell
python -B .\scripts\validate_chat_followup.py
```

该脚本不会调用真实 DeepSeek，而是使用 fake LLM 响应完成本地校验。

当前会覆盖这些约束：

- AI 首答可以成功开启追问会话
- 同一会话可以成功续写第二轮
- 会话列表与详情可正常读取
- 其他用户可以查看别人的会话列表与会话详情
- 非 AI 回答不能发起追问
- `question_id` 与 `answer_id` 不匹配时会被拒绝
- 其他用户不能续写别人的会话
- `session_id` 与当前问题 / 回答锚点不匹配时会被拒绝
- `CLOSED` 会话不能继续追问

## 7. 迁移说明

如果当前数据库不是全新初始化，而是旧版本继续升级，需要补跑：

```sql
@sql/migrations/20260425_extend_chat_session_for_follow_up.sql
```

这条迁移会为 `CHAT_SESSION` 增加：

- `QUESTION_ID`
- `SEED_ANSWER_ID`
- 对应外键和索引
