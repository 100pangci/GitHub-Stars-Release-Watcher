# GitHub Stars Release Watcher

一款自托管应用，用于监控你 GitHub 星标仓库的新发布版本和标签。每周邮件汇总所有星标项目的新版本。

[English](./README.md)

## 功能特性

- **GitHub 星标同步**：自动同步你星标的仓库
- **发布/标签监控**：检查每个仓库的新 GitHub Release 和标签
- **每周邮件汇总**：每周收到包含所有更新的综合邮件
- **Web 界面**：易于使用的配置和监控界面
- **无外部依赖**：使用 SQLite 数据库，无需 Redis/Postgres/Celery
- **单容器部署**：所有组件运行在一个 Podman/Docker 容器中

## 快速开始

### 使用 Podman

```bash
# 构建镜像
podman build -t github-stars-release-watcher:latest .

# 创建数据目录
mkdir -p data

# 运行容器
podman run -d --name github-stars-release-watcher \
  -p 8000:8000 \
  -v ./data:/data:z \
  -e APP_PASSWORD='your-secure-password' \
  -e SESSION_SECRET='your-random-secret-here' \
  --restart=always \
  github-stars-release-watcher:latest
```

然后打开 http://localhost:8000 并使用密码登录。

### 使用 Docker

```bash
# 构建镜像
docker build -t github-stars-release-watcher:latest -f Containerfile .

# 运行容器
docker run -d --name github-stars-release-watcher \
  -p 8000:8000 \
  -v ./data:/data \
  -e APP_PASSWORD='your-secure-password' \
  -e SESSION_SECRET='your-random-secret-here' \
  --restart=always \
  github-stars-release-watcher:latest
```

### 使用 Docker Compose

```bash
# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 更新后重新构建并启动
docker compose up -d --build
```

项目包含 `compose.yaml` 配置文件：

```yaml
version: "3.8"
services:
  watcher:
    build:
      context: .
      dockerfile: Containerfile
    container_name: github-stars-release-watcher
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    environment:
      - APP_PASSWORD=your-secure-password
      - SESSION_SECRET=your-random-secret-here
      - APP_COOKIE_SECURE=false
      - CHECK_SCHEDULE=weekly
      - CHECK_WEEKDAY=mon
      - CHECK_TIME=09:00
    restart: unless-stopped
```

你也可以用 `.env` 文件管理环境变量：

```bash
# .env（放在 compose.yaml 旁边）
APP_PASSWORD=your-secure-password
SESSION_SECRET=your-random-secret-here
```

然后 `docker compose up -d` 将自动使用这些值。

## 环境变量

| 变量 | 是否必需 | 默认值 | 说明 |
|---|---|---|---|
| `APP_PASSWORD` | 否* | 自动生成 | Web UI 登录密码 |
| `SESSION_SECRET` | 否* | 自动生成 | 会话 cookie 密钥 |
| `APP_COOKIE_SECURE` | 否 | `false` | 使用 HTTPS 时设为 `true` |
| `DATABASE_URL` | 否 | `sqlite:////data/app.db` | 数据库路径 |
| `GITHUB_USERNAME` | 否 | - | GitHub 用户名（可在 Web UI 中设置） |
| `GITHUB_TOKEN` | 否 | - | GitHub 个人访问令牌（可在 Web UI 中设置） |
| `CHECK_SCHEDULE` | 否 | `weekly` | 检查频率：`hourly`、`daily`、`weekly` |
| `CHECK_WEEKDAY` | 否 | `mon` | 每周检查的日期 |
| `CHECK_TIME` | 否 | `09:00` | 定时检查的时间 |
| `MONITOR_PRERELEASES` | 否 | `false` | 是否包含预发布版本 |

*\* 如果未设置，首次启动时自动生成随机密码并打印到容器日志。*

## 配置步骤

### 1. GitHub 个人访问令牌

1. 进入 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 创建新令牌，至少需要 `repo` 范围（用于私有仓库），公开仓库无需范围
3. 复制令牌并在 Web UI 设置页面中输入

### 2. 配置应用

登录 Web UI 后：

1. **GitHub 设置**：输入 GitHub 用户名和个人访问令牌
2. **计划设置**：配置检查发布版本的频率
3. **发布/标签策略**：配置监控偏好
4. **邮件/SMTP 设置**：配置 SMTP 用于每周邮件汇总

### 3. 初始同步

1. 进入仪表盘，点击"立即同步星标"以获取星标仓库
2. 然后点击"立即检查发布版本"以扫描发布版本

首次检查将初始化所有仓库的状态（除非在设置中启用了 `allow_initial_notifications`，否则不会发送通知）。

## Podman Systemd 集成

将容器作为 systemd 服务运行：

```bash
# 生成 systemd 单元文件
podman generate systemd --new --name github-stars-release-watcher > ~/.config/systemd/user/github-stars-release-watcher.service

# 启用并启动服务
systemctl --user enable --now github-stars-release-watcher.service
```

或在 `/etc/systemd/system/github-stars-release-watcher.service` 创建 root systemd 服务：

```ini
[Unit]
Description=GitHub Stars Release Watcher
After=network-online.target

[Service]
Type=simple
ExecStartPre=/usr/bin/podman pull github-stars-release-watcher:latest
ExecStart=/usr/bin/podman run --rm \
  --name github-stars-release-watcher \
  -p 8000:8000 \
  -v /opt/github-stars-release-watcher/data:/data:z \
  -e APP_PASSWORD='your-secure-password' \
  -e SESSION_SECRET='your-random-secret-here' \
  github-stars-release-watcher:latest
ExecStop=/usr/bin/podman stop -t 10 github-stars-release-watcher
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## Web UI 页面

- **仪表盘**：概览统计、速率限制状态和系统健康
- **仓库**：浏览和搜索星标仓库，检查单个仓库
- **事件/更新**：查看检测到的发布/标签事件
- **设置**：配置 GitHub、计划、发布策略和邮件
- **日志**：查看最近的应用日志

## 安全说明

- GitHub 令牌和 SMTP 密码以哈希/加密形式存储在数据库中
- 机密信息永远不会在 Web UI 或日志中显示
- Session cookie 使用 HttpOnly、SameSite=Lax 属性
- 所有配置更改都需要认证
- 所有 POST 请求均有 CSRF 保护
- 不执行来自用户输入的任何 shell 命令

## 开发

### 前提条件

- Python 3.12+
- pip

### 安装

```bash
# 克隆仓库
cd github-stars-release-watcher

# 安装依赖
pip install -e ".[dev]"

# 运行应用
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 运行测试

```bash
pytest
```

## 项目结构

```
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 环境配置
│   ├── database.py          # 数据库初始化
│   ├── models.py            # SQLAlchemy 模型
│   ├── security.py          # 认证与密码管理
│   ├── github_client.py     # GitHub API 客户端
│   ├── services/
│   │   ├── stars.py         # 星标仓库同步服务
│   │   ├── releases.py      # 发布/标签检查服务
│   │   ├── emailer.py       # 邮件发送服务
│   │   ├── scheduler.py     # APScheduler 管理
│   │   ├── settings.py      # 设置 CRUD 操作
│   │   └── logs.py          # 应用日志
│   ├── routers/
│   │   ├── health.py        # 健康检查端点
│   │   ├── auth.py          # 登录/登出路由
│   │   ├── dashboard.py     # 仪表盘路由
│   │   ├── repos.py         # 仓库管理路由
│   │   ├── events.py        # 事件查看路由
│   │   ├── settings.py      # 设置管理路由
│   │   └── tasks.py         # 手动触发任务路由
│   ├── templates/           # Jinja2 HTML 模板
│   └── static/              # CSS 和静态资源
├── tests/
│   ├── test_github_client.py
│   ├── test_release_detection.py
│   └── test_settings_validation.py
├── Containerfile            # Podman/Docker 构建文件
├── compose.yaml             # Docker Compose 配置
├── pyproject.toml           # Python 项目配置
└── README.md
```

## 许可证

MIT
