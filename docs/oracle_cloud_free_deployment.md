# Oracle Cloud 免费部署方案

最后更新：2026-04-28

本文面向想把 AI QA 社区部署到公网访问的同事，目标是在尽量不花钱的前提下，用 Oracle Cloud Free Tier 完成一套可访问的线上环境。

## 1. 推荐架构

最推荐的免费部署架构：

```text
用户浏览器
  -> 域名 HTTPS
  -> Oracle Cloud 免费 VM
  -> Nginx
  -> FastAPI
  -> Oracle Autonomous Database Always Free
  -> DeepSeek API
```

推荐这样拆分：

- Oracle Cloud 免费 VM：运行 FastAPI、Nginx、项目代码。
- Oracle Autonomous Database Always Free：运行数据库。
- DeepSeek：继续使用外部 API Key。
- 域名：可选，但强烈建议配置，方便 HTTPS 和公网访问。

不建议在免费 VM 上继续跑当前 `docker compose` 里的 Oracle 数据库容器。原因是 Oracle Cloud 免费 VM 常见选择是 Arm A1，而 Oracle 数据库容器镜像和资源要求更容易踩坑。数据库用 Oracle 自家的 Always Free Autonomous Database 更稳。

## 2. 免费资源选择

### 2.1 计算资源

在 Oracle Cloud 控制台创建 Compute Instance。

推荐：

```text
Shape: VM.Standard.A1.Flex
OCPU: 1 到 2
Memory: 6GB 到 12GB
系统: Ubuntu 22.04 或 24.04
```

如果账号资源紧张，A1 实例可能创建失败，可以换可用区或稍后重试。

### 2.2 数据库资源

创建 Autonomous Database：

```text
Workload type: Transaction Processing
Deployment type: Serverless
Always Free: Enabled
Database name: AIQA
```

记住管理员密码，并下载 Wallet。后面 Python 连接 Autonomous Database 需要 Wallet。

## 3. 云服务器初始化

SSH 登录服务器：

```bash
ssh ubuntu@<你的服务器公网 IP>
```

更新系统：

```bash
sudo apt update
sudo apt upgrade -y
```

安装基础工具：

```bash
sudo apt install -y git curl unzip nginx python3 python3-venv python3-pip
```

如果还需要在服务器上构建桌面客户端，再装 Node 和 Rust；只部署网页服务则不需要。

## 4. 拉取项目代码

```bash
cd /opt
sudo git clone <你的仓库地址> ai-qa-community
sudo chown -R $USER:$USER ai-qa-community
cd ai-qa-community
```

创建 Python 虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. 配置 Autonomous Database Wallet

在 Oracle Cloud 控制台下载数据库 Wallet，例如 `Wallet_AIQA.zip`。

上传到服务器：

```bash
scp Wallet_AIQA.zip ubuntu@<服务器公网 IP>:/opt/ai-qa-community/wallet/
```

服务器上解压：

```bash
cd /opt/ai-qa-community
mkdir -p wallet
unzip wallet/Wallet_AIQA.zip -d wallet
```

后续 `.env` 里的 `ORACLE_DB_HOST` 不再写 `localhost`，而是使用 Wallet 中 `tnsnames.ora` 里的服务名。常见服务名类似：

```text
aiqa_low
aiqa_medium
aiqa_high
```

建议线上用：

```text
aiqa_low
```

## 6. 生产 `.env` 示例

复制示例：

```bash
cp .env.example .env
```

然后编辑：

```bash
nano .env
```

推荐配置：

```env
APP_NAME=AI QA API
APP_ENV=prod
APP_HOST=127.0.0.1
APP_PORT=8000

ORACLE_DB_HOST=
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=aiqa_low
ORACLE_POOL_MIN=1
ORACLE_POOL_MAX=5
ORACLE_POOL_INCREMENT=1

APP_USER=AI_QA_APP
APP_USER_PASSWORD=<生产环境强密码>

JWT_SECRET_KEY=<至少32位强随机字符串>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

AUTH_LOGIN_MAX_FAILURES=5
AUTH_LOGIN_WINDOW_SECONDS=300

CORS_ALLOW_ORIGINS=https://<你的域名>
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https://<你的域名>; object-src 'none'; base-uri 'self'; frame-ancestors 'none'

SEARCH_USE_ORACLE_TEXT=false

DEEPSEEK_API_KEY=<你的 DeepSeek API Key>
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=30
```

注意：

- `JWT_SECRET_KEY` 必须换成生产专用强随机字符串。
- `APP_USER_PASSWORD` 不要使用示例密码。
- 如果暂时没有域名，用 `http://<服务器公网 IP>` 填 `CORS_ALLOW_ORIGINS`，但正式访问建议尽快上 HTTPS 域名。

## 7. 连接 Autonomous Database 的代码配置

当前项目的 `app/db/connection.py` 使用 `oracle_dsn` 连接。连接 Autonomous Database 时通常还需要配置 Wallet 路径。

推荐下一步在项目中增加这些环境变量：

```env
ORACLE_WALLET_DIR=/opt/ai-qa-community/wallet
ORACLE_WALLET_PASSWORD=<Wallet 密码，如创建时设置>
```

然后让 `oracledb.create_pool(...)` 使用 `config_dir` 和 `wallet_location`。

如果暂时不改代码，也可以先继续使用一台 x86 云服务器跑 Oracle 容器，但这就不一定是 Always Free 方案。

## 8. 初始化数据库 schema

Autonomous Database 上建议使用 SQLcl、SQL Developer 或 Python 脚本导入 SQL。

需要导入：

```text
sql/create_tables.sql
sql/procedures.sql
sql/triggers.sql
sql/seed_data.sql
sql/migrations/*.sql
```

推荐顺序：

```text
1. create_tables.sql
2. procedures.sql
3. triggers.sql
4. seed_data.sql
5. migrations 按日期顺序执行
```

如果导入了：

```text
sql/migrations/20260428_add_question_oracle_text_indexes.sql
```

再把 `.env` 改为：

```env
SEARCH_USE_ORACLE_TEXT=true
```

否则保持：

```env
SEARCH_USE_ORACLE_TEXT=false
```

## 9. systemd 管理 FastAPI

创建服务文件：

```bash
sudo nano /etc/systemd/system/ai-qa.service
```

写入：

```ini
[Unit]
Description=AI QA FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/ai-qa-community
Environment="PATH=/opt/ai-qa-community/.venv/bin"
ExecStart=/opt/ai-qa-community/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-qa
sudo systemctl start ai-qa
sudo systemctl status ai-qa
```

查看日志：

```bash
journalctl -u ai-qa -f
```

## 10. Nginx 反向代理

创建配置：

```bash
sudo nano /etc/nginx/sites-available/ai-qa
```

写入：

```nginx
server {
    listen 80;
    server_name <你的域名>;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/ai-qa /etc/nginx/sites-enabled/ai-qa
sudo nginx -t
sudo systemctl reload nginx
```

## 11. HTTPS

安装 certbot：

```bash
sudo apt install -y certbot python3-certbot-nginx
```

申请证书：

```bash
sudo certbot --nginx -d <你的域名>
```

完成后检查：

```text
https://<你的域名>/health
```

## 12. 云安全组和防火墙

Oracle Cloud 安全列表或 Network Security Group 开放：

```text
22/tcp
80/tcp
443/tcp
```

不要开放：

```text
1521/tcp
8000/tcp
```

FastAPI 只监听 `127.0.0.1:8000`，公网只通过 Nginx 访问。

## 13. 部署后验证

按顺序访问：

```text
https://<你的域名>/health
https://<你的域名>/
https://<你的域名>/home
https://<你的域名>/login
```

然后验证：

1. 游客可以浏览首页。
2. 游客可以进入问题详情。
3. 游客不能发帖、收藏、评论、反馈和 AI 追问。
4. 注册和登录正常。
5. 登录后可以发布问题。
6. AI 首答能正常调用 DeepSeek。
7. 图片上传和展示正常。
8. 管理员账号可以进入 `/admin`。

## 14. 常见问题

### 14.1 A1 免费机器创建失败

Oracle 免费资源经常紧张。可以：

- 换可用区。
- 降低 OCPU 和内存。
- 过一段时间再试。

### 14.2 HTTPS 正常但登录或接口失败

检查 `.env`：

```env
CORS_ALLOW_ORIGINS=https://<你的域名>
CONTENT_SECURITY_POLICY=...
```

改完后重启：

```bash
sudo systemctl restart ai-qa
```

### 14.3 数据库连不上

重点检查：

- Wallet 是否上传并解压。
- `ORACLE_SERVICE_NAME` 是否和 `tnsnames.ora` 中一致。
- 数据库用户和密码是否正确。
- 项目是否已支持 Wallet 连接参数。

### 14.4 图片上传失败

检查 Nginx：

```nginx
client_max_body_size 10m;
```

同时确认后端上传限制。当前头像、问题配图、回答配图都有大小限制。

## 15. 后续建议

为了让 Oracle Cloud 部署真正顺滑，建议继续做两件事：

1. 在 `app/db/connection.py` 中正式支持 Autonomous Database Wallet 环境变量。
2. 增加一份 `systemd` 和 `nginx` 示例文件到 `deploy/` 目录，减少手工复制错误。
