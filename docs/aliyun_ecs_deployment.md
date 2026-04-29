# 阿里云 ECS 公网部署指南

最后更新：2026-04-29

本文记录 AI QA 社区在阿里云 ECS 上完成公网部署的推荐流程，覆盖 Ubuntu 初始化、Docker、Oracle 镜像中转、数据库初始化、FastAPI systemd、Nginx 反向代理和常见问题。

## 1. 已验证的服务器配置

本次验证环境：

```text
云厂商：阿里云 ECS
地域：华东1（杭州）
系统：Ubuntu 22.04 64位
规格：4 vCPU / 8 GiB
公网 IP：按实际服务器为准
系统盘：40 GiB ESSD Entry
```

这套配置可以跑：

```text
Nginx + FastAPI + Oracle 26ai Docker + DeepSeek API
```

注意：40 GiB 磁盘偏紧，Oracle 镜像、数据卷和系统依赖会占用不少空间。正式长期使用建议 80 GiB 以上。

## 2. 安全组

入方向只开放：

```text
22/tcp   SSH
80/tcp   HTTP
443/tcp  HTTPS
```

不要开放：

```text
8000/tcp  FastAPI
1521/tcp  Oracle
3306/tcp
6379/tcp
```

推荐访问路径：

```text
公网 80/443 -> Nginx -> 127.0.0.1:8000 -> FastAPI -> localhost:1521 -> Oracle 容器
```

部署初期可以让 SSH 来源是 `0.0.0.0/0`，上线后建议改成自己的公网 IP `/32`。

## 3. 系统初始化

登录 ECS：

```bash
ssh root@<服务器公网 IP>
```

更新系统并安装基础工具：

```bash
apt update
apt upgrade -y
apt install -y git curl unzip nginx python3 python3-venv python3-pip ca-certificates gnupg lsb-release
timedatectl set-timezone Asia/Shanghai
```

检查：

```bash
date
python3 --version
nginx -v
df -h
free -h
```

## 4. 安装 Docker Compose v2

不要使用 Ubuntu 自带的旧 `docker-compose` v1，它不支持当前 `compose.yaml` 中的 `name:` 字段。

安装 Docker 官方源：

```bash
apt remove -y docker-compose docker.io containerd runc
apt update
apt install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl daemon-reload
systemctl enable docker
systemctl start docker
```

检查：

```bash
docker --version
docker compose version
systemctl status docker --no-pager
```

## 5. 拉取项目代码

```bash
cd /opt
git clone <你的 GitHub 仓库地址> ai-qa-community
cd /opt/ai-qa-community
```

如果仓库是私有仓库，先配置 GitHub PAT 或 SSH Key。

## 6. 配置 `.env`

```bash
cd /opt/ai-qa-community
cp .env.example .env
nano .env
```

公网 IP 首次部署示例：

```env
APP_ENV=prod
APP_HOST=127.0.0.1
APP_PORT=8000

ORACLE_DB_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1
ORACLE_POOL_MIN=1
ORACLE_POOL_MAX=5
ORACLE_POOL_INCREMENT=1

APP_USER=AI_QA_APP
APP_USER_PASSWORD=<生产环境强密码>

JWT_SECRET_KEY=<至少32位强随机字符串>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

CORS_ALLOW_ORIGINS=http://<服务器公网 IP>
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' http://<服务器公网 IP>; object-src 'none'; base-uri 'self'; frame-ancestors 'none'

SEARCH_USE_ORACLE_TEXT=false

DEEPSEEK_API_KEY=<你的 DeepSeek API Key>
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=30
```

生成 JWT 密钥：

```bash
openssl rand -hex 32
```

保存 `nano`：

```text
Ctrl + O
Enter
Ctrl + X
```

不要在截图或聊天中暴露 `DEEPSEEK_API_KEY` 和 `JWT_SECRET_KEY`。

## 7. 使用阿里云 ACR 中转 Oracle 镜像

Oracle 官方镜像仓库在国内可能非常慢。推荐把镜像先推到阿里云容器镜像服务 ACR，再由 ECS 从同地域 ACR 拉取。

### 7.1 ACR 控制台配置

在阿里云容器镜像服务个人版中：

```text
地域：与 ECS 一致，例如华东1（杭州）
命名空间：例如 aiqa
仓库名称：oracle-free
仓库类型：私有
代码源：本地仓库
```

在“访问凭证”中设置固定密码。登录地址以页面实际提示为准，个人版实例通常类似：

```text
crpi-xxxx.cn-hangzhou.personal.cr.aliyuncs.com
```

ECS 同 VPC 拉取时可以优先使用：

```text
crpi-xxxx-vpc.cn-hangzhou.personal.cr.aliyuncs.com
```

### 7.2 Apple Silicon Mac 推送 amd64 镜像

如果本地 Mac 是 Apple Silicon，直接 `docker pull` 默认可能得到 `arm64` 镜像，ECS 是 `amd64`，会出现：

```text
linux/arm64 does not match linux/amd64
```

推荐使用 `skopeo` 指定架构复制，不影响本地正在运行的 Oracle 容器。

安装：

```bash
brew install skopeo
```

登录 ACR：

```bash
skopeo login --username <ACR 登录名> <ACR 个人版实例地址>
```

复制 amd64 镜像：

```bash
skopeo copy \
  --retry-times 10 \
  --override-os linux \
  --override-arch amd64 \
  docker://container-registry.oracle.com/database/free:23.26.1.0 \
  docker://<ACR 个人版实例地址>/aiqa/oracle-free:23.26.1.0-amd64
```

如果网络中断报 `unexpected EOF`，重复执行同一条命令即可，已存在的层会显示 `skipped: already exists`。

检查架构：

```bash
skopeo inspect docker://<ACR 个人版实例地址>/aiqa/oracle-free:23.26.1.0-amd64 | grep -E '"Architecture"|"Os"'
```

期望：

```text
"Architecture": "amd64"
"Os": "linux"
```

### 7.3 ECS 使用 ACR 镜像

ECS 上登录 ACR：

```bash
docker login --username=<ACR 登录名> <ACR VPC 实例地址>
```

如果 VPC 地址失败，改用公网实例地址。

修改 `compose.yaml`：

```bash
cd /opt/ai-qa-community
nano compose.yaml
```

把 Oracle 镜像改成：

```yaml
image: <ACR VPC 实例地址>/aiqa/oracle-free:23.26.1.0-amd64
```

如果 VPC 地址不能用，使用：

```yaml
image: <ACR 个人版实例地址>/aiqa/oracle-free:23.26.1.0-amd64
```

启动 Oracle：

```bash
docker compose pull
docker compose up -d
docker ps
```

等待状态变为：

```text
Up ... (healthy)
```

查看日志：

```bash
docker logs -f oracle26ai
```

## 8. 初始化数据库

确认 `AI_QA_APP` 用户可登录：

```bash
docker exec -it oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1" <<EOF
SELECT USER FROM dual;
EXIT;
EOF'
```

导入 schema：

```bash
docker exec -i oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1"' < sql/create_tables.sql
docker exec -i oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1"' < sql/procedures.sql
docker exec -i oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1"' < sql/triggers.sql
docker exec -i oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1"' < sql/views.sql
docker exec -i oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1"' < sql/seed_data.sql
```

导入迁移：

```bash
for f in sql/migrations/*.sql; do
  echo "Running $f"
  docker exec -i oracle26ai bash -lc 'sqlplus -L "$APP_USER/$APP_USER_PASSWORD@localhost:1521/FREEPDB1"' < "$f"
done
```

如果 Oracle Text 迁移成功，可以改：

```env
SEARCH_USE_ORACLE_TEXT=true
```

否则保持默认：

```env
SEARCH_USE_ORACLE_TEXT=false
```

## 9. 安装 Python 依赖

```bash
cd /opt/ai-qa-community
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` 已固定：

```text
bcrypt>=4.0.1,<4.1.0
```

这是为了避免 `passlib==1.7.x` 与新版 `bcrypt` 不兼容，注册时报：

```text
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
```

如果旧环境已经遇到该问题，执行：

```bash
source /opt/ai-qa-community/.venv/bin/activate
pip uninstall -y bcrypt
pip install "bcrypt==4.0.1"
```

验证：

```bash
python - <<'PY'
from passlib.context import CryptContext
ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = ctx.hash("test123456")
print(ctx.verify("test123456", hashed))
PY
```

期望输出：

```text
True
```

## 10. systemd 管理 FastAPI

创建服务：

```bash
cat > /etc/systemd/system/ai-qa.service <<'EOF'
[Unit]
Description=AI QA FastAPI Service
After=network.target docker.service
Requires=docker.service

[Service]
User=root
WorkingDirectory=/opt/ai-qa-community
Environment="PATH=/opt/ai-qa-community/.venv/bin"
ExecStart=/opt/ai-qa-community/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-qa
systemctl restart ai-qa
systemctl status ai-qa --no-pager
```

如果日志出现：

```text
[Errno 98] address already in use
```

说明之前手动启动的 `uvicorn` 还占着 8000 端口。处理：

```bash
ss -ltnp | grep ':8000'
kill <pid>
systemctl restart ai-qa
```

查看日志：

```bash
journalctl -u ai-qa -f
```

## 11. Nginx 反向代理

```bash
cat > /etc/nginx/sites-available/ai-qa <<'EOF'
server {
    listen 80;
    server_name <服务器公网 IP>;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ai-qa /etc/nginx/sites-enabled/ai-qa
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

验证：

```bash
curl http://127.0.0.1:8000/health
curl http://<服务器公网 IP>/health
```

期望：

```json
{"status":"ok"}
```

## 12. 浏览器回归清单

访问：

```text
http://<服务器公网 IP>/
http://<服务器公网 IP>/home
http://<服务器公网 IP>/login
http://<服务器公网 IP>/health
```

至少验证：

1. 游客可以打开首页和社区首页。
2. 注册新账号成功。
3. 登录成功。
4. 发一个纯社区问题。
5. 打开详情页。
6. 发布回答或评论。
7. Nginx、公网、FastAPI、Oracle 主链路都正常。

## 13. 上线后安全收尾

完成公网部署后建议：

- 将安全组 SSH `22` 来源从 `0.0.0.0/0` 改为自己的公网 IP `/32`。
- 绑定域名。
- 配置 HTTPS。
- 将 `.env` 的 `CORS_ALLOW_ORIGINS` 和 `CONTENT_SECURITY_POLICY` 从公网 IP 改为域名。
- 定期备份 Oracle 数据卷。
- 不要暴露 `1521` 和 `8000` 到公网。

## 14. 常用运维命令

```bash
systemctl status ai-qa --no-pager
journalctl -u ai-qa -f
systemctl restart ai-qa

docker ps
docker logs -f oracle26ai
docker compose down
docker compose up -d

nginx -t
systemctl reload nginx
```
