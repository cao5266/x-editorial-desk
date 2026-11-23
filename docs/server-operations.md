# 采集服务器：连接与服务说明

最近核验：2026-11-23（北京时间）。本文记连接方式和服务位置，不记录密钥正文、登录口令或 API Token。

## SSH 连接

- 公网地址：`101.34.76.198`；用户名：`ubuntu`；SSH 端口：`22`；系统：Ubuntu 24.04.4 LTS。
- 本机项目内的 SSH 私钥：`.local-secrets/kakacodex.pem`。这是本地文件，Git 忽略该目录；克隆仓库不会拿到密钥。新机器应使用经授权分发的密钥或登记自己的公钥，不能从 Git 获取私钥。
- 历史上用过 `100.104.134.84`（Tailscale）。当前运维以已核实的公网方式为准，不依赖这个历史地址。

在项目根目录的 PowerShell 中执行：

```powershell
ssh.exe -i '..local-secretskakacodex.pem' -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes ubuntu@101.34.76.198
```

新电脑若还没有这台服务器的主机记录，先通过可信渠道核对服务器的 SSH 主机密钥指纹，再录入 `known_hosts`。不要关闭主机校验，也不要把私钥内容粘到聊天、工单或仓库里。

## 当前服务

| 服务 | 用来做什么 | 访问入口 | 部署与数据 |
| --- | --- | --- | --- |
| Freebie Radar | 汇总 AI 与工具线索，做候选初筛。核验时有 8 个启用来源，每源 10 分钟一次。 | [公网 HTTPS](https://101.34.76.198/)；Nginx 对外提供入口，应用在服务器的 `127.0.0.1:8789`。 | Compose：`/opt/freebie-radar-test`；数据：`/opt/freebie-radar-test/data/radar.db`（SQLite）。 |
| Miniflux 2.3.5 | 订阅官方博客、GitHub Releases 等 RSS；适合发现开源项目更新。 | 服务器 `127.0.0.1:8080`，使用 SSH 隧道或在服务端本地访问。 | Compose：`/opt/ai-source-monitoring`；条目和订阅保存在 PostgreSQL。 |
| changedetection.io 0.70.4 | 监控无 RSS 的官网、更新日志和权益页面；对比快照，区分有效变更和页面噪声。 | 服务器 `127.0.0.1:5000`，使用 SSH 隧道或在服务端本地访问。 | 与 Miniflux 同一 Compose 目录；快照保存在 `ai-monitor_changedetection_data` Docker 卷。 |
| PostgreSQL 17.6 | 给 Miniflux 存储订阅、条目与应用数据；不是独立的采集服务。 | Docker 网络内 `5432`，未发布到宿主机端口。 | 数据卷：`ai-monitor_miniflux_pg_data`。 |
| Nginx | Freebie Radar 的公网入口。 | 公网监听 `80/443`；已验证 HTTPS 首页可访问。 | 宿主机系统服务；不是单独的采集进程。 |

核验时三个应用容器和一个数据库容器均在运行，三个应用的本地 HTTP 入口以及 Freebie Radar 的公网 HTTPS 首页返回了 `200`。这不等于每个采集源都成功抓取，也不证明各服务已经接入统一选题池。采集不会自动发 X；发稿范围见 [选题、核验与审稿手册](editorial-workflow.md)。

## 从本机打开需要隧道的页面

在项目根目录执行，保持窗口打开：

```powershell
ssh.exe -NT -i '..local-secretskakacodex.pem' -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -L 127.0.0.1:15000:127.0.0.1:5000 -L 127.0.0.1:18080:127.0.0.1:8080 ubuntu@101.34.76.198
```

- changedetection.io：[本机 15000](http://127.0.0.1:15000/)
- Miniflux：[本机 18080](http://127.0.0.1:18080/)

若本机端口冲突，只改每个 `-L` 参数最左边 `127.0.0.1:` 后的端口（15000 或 18080），不用改服务器端口。Freebie Radar 直接用 HTTPS，无需隧道。

## 提交到私有仓库前

- 提交文档、审阅稿和可共享的素材；不提交 SSH 私钥、服务端 `.env`、数据库、数据卷、应用密码和 API Key。私有仓库也不要提交这些文件。
- 初始化后，用 `git check-ignore -v .local-secrets/kakacodex.pem` 确认忽略规则生效，再用 `git diff --cached --name-only` 检查准备提交的文件。不要用 `git add -f` 绕过忽略。
- `materials/kites-cline-lmstudio/cline/test-repo/shipping.js` 是普通的测试样例文件。若需要独立 Git 仓库做联调，把样例复制到项目外再初始化，避免在素材目录里嵌套 Git 仓库。
