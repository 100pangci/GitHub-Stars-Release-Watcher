# GitHub Stars Release Watcher

[English](./README.md)

一款自托管应用，用于监控你 GitHub 星标仓库的新发布版本和标签。每周通过邮件（或任何其他通知渠道）汇总所有星标项目的新版本。

## 功能特性

- **GitHub 星标同步** – 自动同步你星标的仓库
- **发布/标签监控** – 检查每个仓库的新 Release 和标签（支持预发布、标签回退）
- **每周汇总** – 每周收到包含所有更新的综合报告
- **通知框架** – 可扩展的通知系统（内置 SMTP 邮件；可轻松添加 Webhook、Telegram 等）
- **灵活调度** – 支持每小时、每天、每周、每月或自定义间隔
- **Web 界面** – 易于使用的配置和监控界面（Vue 3 + Vuetify 3，Material Design 3）
- **无外部依赖** – 使用 SQLite 数据库，无需 Redis/Postgres/Celery
- **单容器部署** – 所有组件运行在一个 Podman/Docker 容器中
- **多语言界面** – 中文、英文、日文

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
  --restart=always \
  github-stars-release-watcher:latest
```

然后打开 http://localhost:8000 并使用密码登录。

> **注意**：`SESSION_SECRET` 在首次启动时自动生成并持久化到数据库中，除非需要覆盖，否则无需手动设置。

### 使用 Docker

```bash
# 构建镜像
docker build -t github-stars-release-watcher:latest -f Containerfile .

# 运行容器
docker run -d --name github-stars-release-watcher \
  -p 8000:8000 \
  -v ./data:/data \
  -e APP_PASSWORD='your-secure-password' \
  --restart=always \
  github-stars-release-watcher:latest
```

### 使用 Docker Compose

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down

# 更新后重新构建并启动
docker compose up -d --build
```

项目包含 `compose.yaml` 配置文件。你也可以使用 `.env` 文件管理环境变量：

```bash
# .env（放在 compose.yaml 旁边）
APP_PASSWORD=your-secure-password
```

## 环境变量

| 变量 | 是否必需 | 默认值 | 说明 |
|---|---|---|---|
| `APP_PASSWORD` | 否* | 自动生成 | Web UI 登录密码 |
| `SESSION_SECRET` | 否* | 自动生成 | 会话 cookie 和加密密钥 |
| `APP_COOKIE_SECURE` | 否 | `false` | 使用 HTTPS 时设为 `true` |
| `DATABASE_URL` | 否 | `sqlite:////data/app.db` | 数据库路径 |
| `GITHUB_USERNAME` | 否 | – | GitHub 用户名（可在 Web UI 中设置） |
| `GITHUB_TOKEN` | 否 | – | GitHub 个人访问令牌（可在 Web UI 中设置） |
| `CHECK_SCHEDULE` | 否 | `weekly` | 检查频率：`hourly`、`daily`、`weekly`、`monthly`、`custom` |
| `CHECK_WEEKDAY` | 否 | `mon` | 每周检查的日期 |
| `CHECK_TIME` | 否 | `09:00` | 定时检查的时间（UTC） |
| `MONITOR_PRERELEASES` | 否 | `false` | 是否包含预发布版本 |
| `DATA_DIR` | 否 | `/data` | 数据目录 |

*\* 如果 `APP_PASSWORD` 未设置，首次启动时自动生成随机密码并打印到容器日志。`SESSION_SECRET` 首次启动时自动生成并持久化到数据库。*

## 配置步骤

### 1. GitHub 个人访问令牌

1. 进入 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 创建新令牌，至少需要 `repo` 范围（用于私有仓库），公开仓库无需范围
3. 复制令牌并在 Web UI 设置页面中输入

### 2. 配置应用

登录 Web UI 后：

1. **GitHub 设置**：输入 GitHub 用户名和个人访问令牌
2. **计划设置**：配置检查发布版本的频率（每小时/每天/每周/每月/自定义）
3. **发布/标签策略**：配置监控偏好（预发布、标签回退、归档仓库）
4. **通知设置**：配置 SMTP 邮件用于每周汇总

### 3. 初始同步

1. 进入仪表盘，点击**立即同步星标**以获取星标仓库
2. 然后点击**立即检查发布版本**以扫描发布版本

首次检查将初始化所有仓库的状态（除非在设置中启用了 `allow_initial_notifications`，否则不会发送通知）。

## Podman Systemd 集成

```bash
# 生成 systemd 单元文件
podman generate systemd --new --name github-stars-release-watcher > ~/.config/systemd/user/github-stars-release-watcher.service

# 启用并启动
systemctl --user enable --now github-stars-release-watcher.service
```

## Web UI 页面

- **仪表盘** – 概览统计、速率限制状态、系统健康和任务历史
- **仓库** – 浏览和搜索星标仓库，检查单个仓库
- **事件/更新** – 查看检测到的发布/标签事件
- **设置** – 配置 GitHub、计划、发布策略、通知
- **日志** – 查看最近的应用日志

## 添加新的通知渠道

通知框架（`app/services/notifiers/`）让添加自定义渠道变得简单：

1. 创建 `app/services/notifiers/my_channel.py`，类继承 `BaseNotifier`
2. 实现 `name`、`display_name`、`is_configured`、`get_settings`、`save_settings`
3. 在 `app/main.py:lifespan` 中注册：`manager.register(MyNotifier)`
4. 设置 API 和调度器会自动接管新通知器

## 安全说明

- GitHub 令牌和 SMTP 密码使用 Fernet 对称加密存储
- 机密信息永远不会在 Web UI 或日志中显示
- Session cookie 使用 HttpOnly、SameSite=Lax 属性
- 所有配置更改都需要认证
- 所有状态变更请求均有 CSRF 保护（Origin/Referer 检查）
- 登录限流：每 IP 每 15 分钟最多 5 次尝试
- 密码最少 8 个字符
- 所有响应设置了 Content-Security-Policy 头

## 开发

### 前提条件

- Python 3.12+
- Node.js 20+（用于前端开发）
- pip

### 安装

```bash
# 克隆仓库
cd github-stars-release-watcher

# 安装 Python 依赖
pip install -e ".[dev]"

# 安装前端依赖
cd frontend && npm install && cd ..

# 快速启动（在不同窗口中启动前后端开发服务器）
dev.bat          # Windows
# 或
./dev.ps1        # PowerShell
```

也可以手动启动：

```bash
# 终端 1：后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2：前端（Vite 开发服务器，端口 5173）
cd frontend && npm run dev
```

### 运行测试

```bash
pytest                              # 全部测试
pytest tests/test_github_client.py  # 单个文件
```

测试文件覆盖：
- `test_crypto.py` – 加密/解密往返及边界情况
- `test_github_client.py` – GitHub API 客户端初始化、请求头、速率限制
- `test_release_detection.py` – 从 GitHub API 响应解析发布/标签
- `test_settings_encryption.py` – 机密设置的存储加密
- `test_settings_validation.py` – SMTP 端口和 GitHub 用户名验证

## 项目结构

```
├── app/
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 环境配置（pydantic-settings）
│   ├── crypto.py                # Fernet 对称加密/解密
│   ├── database.py              # 数据库引擎与会话（SQLite + WAL）
│   ├── models.py                # SQLAlchemy 模型
│   ├── security.py              # 认证、密码管理、会话处理
│   ├── github_client.py         # GitHub API 客户端（httpx，速率限制感知）
│   ├── utils.py                 # 共享工具
│   ├── services/
│   │   ├── stars.py             # 星标仓库同步服务
│   │   ├── releases.py          # 发布/标签检查服务
│   │   ├── emailer.py           # 旧版 SMTP 封装（委派给 EmailNotifier）
│   │   ├── scheduler.py         # APScheduler 管理（4 个定时任务）
│   │   ├── settings.py          # 设置 CRUD（透明加密/解密）
│   │   ├── logs.py              # 应用日志服务
│   │   ├── notifier_manager.py  # 通知器注册与分发单例
│   │   └── notifiers/
│   │       ├── base.py          # BaseNotifier 抽象基类
│   │       └── email.py         # EmailNotifier（SMTP 实现）
│   └── routers/
│       ├── health.py            # 健康检查端点
│       ├── auth.py              # 登录/登出/改密路由
│       ├── dashboard.py         # 仪表盘统计与历史
│       ├── repos.py             # 仓库管理路由
│       ├── events.py            # 事件查看路由
│       ├── settings_route.py    # 所有设置管理端点
│       └── tasks.py             # 手动触发任务端点
├── frontend/
│   ├── src/                     # Vue 3 + TypeScript SPA（Vuetify 3）
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/          # 可复用组件
│   │   ├── views/               # 页面视图
│   │   ├── router/              # Vue Router 配置
│   │   ├── locales/             # 国际化（中文、英文、日文）
│   │   ├── api/                 # API 客户端
│   │   ├── plugins/             # Vuetify 插件配置
│   │   └── assets/              # 静态资源
│   └── dist/                    # 构建产物（由 FastAPI 托管）
├── tests/
│   ├── test_crypto.py
│   ├── test_github_client.py
│   ├── test_release_detection.py
│   ├── test_settings_encryption.py
│   └── test_settings_validation.py
├── Containerfile                # 多阶段 Podman/Docker 构建
├── compose.yaml                 # Docker Compose 配置
├── .dockerignore
├── pyproject.toml               # Python 项目依赖与配置
├── .github/workflows/ci.yml     # CI 流水线（lint、测试、构建前端）
├── dev.bat                      # Windows 开发启动脚本
├── dev.ps1                      # PowerShell 开发启动脚本
├── AGENTS.md                    # AI 辅助开发代理指南
└── README.md
```

## 许可证

MIT
