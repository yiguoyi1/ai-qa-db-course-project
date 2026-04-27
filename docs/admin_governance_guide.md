# 管理员协作说明

这份文档面向两类人：

- 第一次接手本项目、需要快速理解管理员能力的协作者
- 需要本地验证管理员链路是否可用的开发者

目标不是重复所有设计细节，而是把“管理员是什么、现在做到哪、怎么跑起来、怎么验证、代码在哪”集中到一个入口里。

## 1. 当前管理员模型

当前项目没有单独维护 `ADMINS` 表，而是直接使用：

- `USERS.ROLE = 'ADMIN'`

这表示管理员本质上仍然是平台用户，只是在普通用户能力之外拥有治理权限。

当前角色口径：

- `USER`：普通社区用户
- `ADMIN`：具备后台治理能力的用户

当前用户状态口径：

- `ACTIVE`：允许登录和继续访问
- `INACTIVE`：不允许登录
- `LOCKED`：不允许登录，且登录日志记录为锁定
- `DISABLED`：不允许登录

## 2. 当前已经实现的管理员能力

当前代码已经落地的管理员能力包括：

- 查看分类列表
- 创建分类
- 修改分类名称、描述、状态
- 查看标签列表，按来源、状态、关键词过滤
- 修改标签名称、描述、状态
- 查看用户列表
- 修改用户角色
- 修改用户状态
- 修改问题状态
- 隐藏或恢复评论
- 查询登录日志
- 查询操作日志
- 自动写入管理员操作日志
- 管理员网页后台 `/admin`
- 网页后台中的内容 ID 查询：从最近问题定位问题 ID，展开回答后查看评论 ID，并一键填入治理表单
- 网页后台中文友好展示角色、状态和操作类型，实际接口枚举值保持不变

当前管理员日志能力包括：

- 登录行为写入 `LOGIN_LOG`
- 管理动作写入 `OPERATION_LOG`

## 3. 当前尚未落地的管理员能力

这部分已经在设计中被提到，但当前代码还没有正式补齐：

- 标签创建、标签合并和批量审核
- 推荐规则人工干预
- 媒体资源治理
- 图片 / 头像审核

这意味着当前管理员能力已经够做“治理最小闭环”，并具备可演示的网页后台；但还不是覆盖媒体审核、推荐干预、导出统计的完整后台系统。

## 4. 管理员业务规则

这些规则已经体现在当前代码里，协作时要按这个口径理解：

- 管理员不能移除自己的管理员身份
- 管理员不能把自己改成不可用状态
- 最后一个 `ACTIVE ADMIN` 不能被降级或停用
- 评论治理优先采用 `HIDDEN / ACTIVE` 的显示治理方式，而不是直接强删
- 标签治理优先采用 `ACTIVE / PENDING / DISABLED` 的状态治理方式，禁用标签不会继续进入公开标签列表和新问题绑定
- 评论作者自己的删除链路和管理员治理链路是两条不同链路
- 关键治理动作必须写入 `OPERATION_LOG`

## 5. 本地验证最短路径

如果你要在新环境里快速验证管理员链路，建议按这个顺序做。

### 5.1 启动数据库和应用

```powershell
Copy-Item .env.example .env
.\scripts\start-oracle26ai.ps1
.\scripts\load-oracle-schema.ps1
.\scripts\load-seed-data.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 创建普通用户

先通过以下任一方式创建一个普通账号：

- 网页注册页
- `POST /api/auth/register`

### 5.3 授予管理员角色

```powershell
.\scripts\grant-admin.ps1 -Username <your_username>
```

如果 PowerShell 因执行策略拦截脚本，可以改用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\grant-admin.ps1 -Username <your_username>
```

### 5.4 一键验证管理员接口

```powershell
.\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password>
```

推荐直接测最新代码时使用默认端口 `8001`，因为脚本会在目标端口没有 API 时自动拉起一份临时 FastAPI 进程。

如果你已经手动起好了最新 API，可以这样复用现有端口：

```powershell
.\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password> -Port 8000 -SkipApiStart
```

如果你还要顺便验证“创建分类 / 更新分类 / 写入操作日志”链路：

```powershell
.\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password> -WriteSmoke
```

`-WriteSmoke` 会：

- 创建一条临时分类
- 把该分类更新为 `INACTIVE`
- 在结果摘要里校验 `ADMIN_CREATE_CATEGORY` 和 `ADMIN_UPDATE_CATEGORY` 是否已经写入日志

如果 PowerShell 拦截脚本，可改用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-admin-api.ps1 -Username <your_username> -Password <your_password>
```

### 5.5 验证管理员网页后台

管理员账号重新登录后，访问：

```text
http://127.0.0.1:8000/admin
```

页面会复用登录后保存的 JWT 调用后台接口。当前网页后台包含：

- 总览：用户数、管理员数、分类数、操作日志数
- 用户治理：按角色和状态筛选用户，修改角色或状态
- 分类管理：创建分类，修改名称、描述和启用状态
- 内容治理：查询最近问题、查看回答 ID 和评论 ID，并一键填入状态调整表单
- 审计日志：查询登录日志和管理员操作日志

管理员页面展示层会显示“普通用户 / 管理员”“正常 / 已锁定 / 已停用”“开放中 / 已解决”等中文文案；传给后端的仍是 `USER / ADMIN`、`ACTIVE / LOCKED / DISABLED`、`OPEN / RESOLVED` 等枚举值。

## 6. 当前管理员接口清单

### 6.1 分类治理

- `GET /api/admin/categories`
- `POST /api/admin/categories`
- `PATCH /api/admin/categories/{category_id}`

### 6.2 标签治理

- `GET /api/admin/tags`
- `PATCH /api/admin/tags/{tag_id}`

### 6.3 用户治理

- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}/status`
- `PATCH /api/admin/users/{user_id}/role`

### 6.4 内容治理

- `PATCH /api/admin/questions/{question_id}/status`
- `PATCH /api/admin/comments/{comment_id}/status`

网页后台为了帮助管理员定位 ID，会复用以下普通读接口：

- `GET /api/questions`
- `GET /api/questions/{question_id}`
- `GET /api/answers/{answer_id}/comments`

### 6.5 日志查询

- `GET /api/admin/logs/login`
- `GET /api/admin/logs/operations`

## 7. 接口与状态口径

为了避免前后端和协作者之间理解不一致，当前管理员接口对应的业务口径如下。

### 7.1 分类状态

- `ACTIVE`
- `INACTIVE`

### 7.2 标签来源

- `SYSTEM`
- `USER`
- `AI`
- `ADMIN`

### 7.3 标签状态

- `ACTIVE`
- `PENDING`
- `DISABLED`

### 7.4 用户角色

- `USER`
- `ADMIN`

### 7.5 用户状态

- `ACTIVE`
- `INACTIVE`
- `LOCKED`
- `DISABLED`

### 7.6 问题状态

- `OPEN`
- `RESOLVED`
- `CLOSED`
- `ARCHIVED`

### 7.7 评论治理状态

- `ACTIVE`
- `HIDDEN`

### 7.8 登录日志结果

- `SUCCESS`
- `FAILURE`
- `LOCKED`

## 8. 代码位置速查

如果你要继续扩展管理员能力，优先看这些文件：

```text
app/api/routes/admin.py
app/api/auth_deps.py
app/api/deps.py
app/services/admin_service.py
app/repositories/admin_repository.py
app/repositories/log_repository.py
app/schemas/admin.py
app/web/admin.html
scripts/grant-admin.ps1
scripts/test-admin-api.ps1
```

各层职责：

- `app/api/routes/admin.py`
  负责管理员接口入口、参数接收、鉴权依赖、错误转换
- `app/services/admin_service.py`
  负责管理员规则，例如最后一个管理员保护、自身保护、状态口径校验
- `app/repositories/admin_repository.py`
  负责管理员相关查询和更新
- `app/repositories/log_repository.py`
  负责登录日志、操作日志写入
- `app/schemas/admin.py`
  负责管理员接口请求和响应模型
- `app/web/admin.html`
  负责管理员网页后台交互，包括总览、用户治理、分类管理、内容治理、审计日志和内容 ID 查询
- `scripts/grant-admin.ps1`
  负责本地环境授予管理员
- `scripts/test-admin-api.ps1`
  负责一键验证管理员链路

## 9. 常见协作提醒

- 不要把 `.env`、真实密钥、真实密码提交进仓库
- 如果你改了管理员状态口径或接口行为，要同步更新 README 和相关设计文档
- 如果你改了数据库结构，要同步更新 `sql/create_tables.sql`、迁移脚本和约束文档
- 如果本机 `8000` 上跑的是旧进程，优先用 `8001` 做管理员烟测
- 不要把“未实现的后台能力”写成“已经完成”

## 10. 推荐的下一步扩展顺序

如果要继续补管理员能力，建议按下面顺序推进：

1. 媒体资源治理
2. 用户头像 / 内容图片审核
3. 推荐规则人工干预入口
4. 更完整的审计筛选条件和导出能力

这样能保持当前“角色鉴权 + 状态治理 + 审计日志”这条主线继续一致扩展。
