# Public Demo Data Seeding

本文档说明如何使用 `scripts/seed_public_demo_data.py` 通过公网 HTTP API 生成演示数据，以及为什么原始输出文件不进入 Git 仓库。

## 1. 目标

脚本用于模拟普通问答社区用户的真实使用路径：

- 注册演示用户
- 登录获取访问令牌
- 发布问题
- 触发 AI 首答
- 触发自动标签生成
- 输出账号和问题生成记录

脚本只通过 HTTP API 访问系统，不直接写数据库，因此更接近真实用户行为，也能顺带验证后端接口链路。

## 2. 安全边界

`seed_outputs/` 目录默认不提交到 Git。

原因是原始输出中包含以下敏感或不适合长期公开的信息：

- `accounts_*.csv` 包含演示账号的明文密码
- `questions_*.csv` 包含公网环境生成的问题 ID 和用户 ID
- `*.log` 可能包含运行过程中的错误详情
- `*.pid` 只对本机当次运行有效

如需共享账号，请在团队内部通过临时安全渠道传递，或重新生成一批账号。

## 3. 常用命令

先确认公网服务地址可访问，再运行脚本：

```powershell
python scripts/seed_public_demo_data.py --base-url http://120.55.74.107/ --users 10 --questions-per-user 5
```

仅预览生成内容，不发请求：

```powershell
python scripts/seed_public_demo_data.py --dry-run --users 3 --questions-per-user 2
```

控制并发和请求间隔，避免对公网服务造成突发压力：

```powershell
python scripts/seed_public_demo_data.py --base-url http://120.55.74.107/ --users 20 --questions-per-user 5 --concurrency 3 --min-delay 0.8 --max-delay 2.0
```

## 4. 输出文件

脚本会把输出写入 `seed_outputs/`：

- `accounts_<timestamp>.csv`：账号生成记录
- `questions_<timestamp>.csv`：问题生成记录
- `<run_id>.stdout.log`：后台运行标准输出
- `<run_id>.stderr.log`：后台运行错误输出
- `<run_id>.pid`：后台进程 ID

账号输出字段示例：

```csv
index,username,password,nickname,user_id,interest_domains,profile_summary,scene_hint,profile_source,status,error
1,demoqa_music_001_xxxxx,***,月白调试员01,101,徒步|DIY维修|游戏设备,示例画像,示例场景,deepseek,OK,
```

问题输出字段示例：

```csv
username,user_id,question_no,question_id,category_id,interest_domain,title,status,answer_count,error
demoqa_music_001_xxxxx,101,1,371,2,徒步,第一次接触徒步，新手应该先从哪里开始？,OPEN,1,
```

## 5. 已验证规模

本地已验证过一批公网演示数据生成：

- 100 个演示账号
- 1000 条演示问题
- 每个账号围绕 1-3 个兴趣领域提问
- 问题覆盖生活、旅行、学习、运动、宠物、摄影、数码、职业、理财、手作等多个领域
- 问题发布后可触发 AI 首答和自动标签链路

原始 CSV 未提交，避免把演示账号密码写入 Git 历史。

## 6. 使用建议

- 大批量造数前先用 `--dry-run` 检查内容分布。
- 公网环境建议设置较低并发，并保留请求间隔。
- 如果要重新造数，建议更换 `--username-prefix` 或 `--seed`，避免用户名冲突。
- 如果只想验证链路，优先使用小批量参数。
