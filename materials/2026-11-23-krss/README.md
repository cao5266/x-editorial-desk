# Krss｜给 RSS 订阅自动加星

**v1 · 初稿 · 待人工审核**　[可复制短帖](x-post.txt) · [配图方案](image-brief.md)

事件键：`kue02/krss | 用标题规则挑出 RSS 教程 | v1.2.0`。这是一条具体用法，不宣称标题规则是 v1.2.0 新增的功能。

## 从三路到一条

批次：2026-11-23 15:04:27 北京时间，回看 48 小时。详见[获取、噪声排查与去重记录](../../docs/audit/2026-11-23-editorial-intake.md)。

| 服务 | 获取状态 | 对本稿的贡献 |
| --- | --- | --- |
| Freebie Radar | 部分成功，86 条；8 源中 1 个最新运行失败 | `1075` 来自[小众软件发现频道](https://meta.appinn.net/t/topic/96655)。主题帖发于 11 月 23 日 11:24:49，11:34:44 首次入库（北京时间）。帖子链到 `kue02/Krss`。 |
| Miniflux | 部分成功，237 条；61 个启用订阅中 42 个报错 | 在导出的记录中未找到 Krss，也没有查到专门的 Krss 启用订阅。只说明本批未命中，不代表其他订阅一定没有提过。 |
| changedetection | 部分成功，33 对快照；58 个启用监控中 2 个报错 | 未找到 Krss 专门监控或本批相关快照链接。独立筛查了其他页面差异，不作为 Krss 的证据。 |

## 为什么值得写

栏目：开源工具／自动化工作流。适合已经用 RSS 看 AI 工具、又被未读列表淹没的人。先挑一个公开订阅，用「标题含教程 → 加星」预览；一条规则就能验证是否适合自己，不用迁移整个订阅库。只讲这个用法，短帖足够。插件、MCP、多模型等不是完成这个任务的前置条件，不拿来堆卖点。

## 一手溯源与事实核验

**2026-11-23 15:00–15:10（北京时间），已查作者仓库与对应版本，未安装或运行 Krss。**

| 说法 | 一手证据 | 核对结论 |
| --- | --- | --- |
| 项目可自托管、采用 GPL v2 | [v1.2.0 README](https://github.com/kue02/Krss/tree/v1.2.0) 开头及 [LICENSE](https://github.com/kue02/Krss/blob/v1.2.0/LICENSE) | 作者明确写自托管，仓库有 GPL v2 文本。自托管不是云服务、免费算力或免费模型的承诺。 |
| 版本发布时间 | [v1.2.0 原发布](https://github.com/kue02/Krss/releases/tag/v1.2.0) · [GitHub 发布元数据](https://api.github.com/repos/kue02/Krss/releases/tags/v1.2.0) | 正式发布于 2026-11-23 14:29:33 北京时间，不等于社区帖时间或 Krss 首次发布。此版变更包括规则条件默认改为「或」；正文只举单个条件。 |
| Docker Compose 上手 | [原 README：快速开始](https://github.com/kue02/Krss/tree/v1.2.0#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B) · [Compose 示例](https://github.com/kue02/Krss/blob/v1.2.0/docker-compose.yml) | 需要 Docker 和 Compose；README 给出启动步骤，首次可在 `localhost:8090` 建账号。示例镜像用 `latest`；启动时实际版本以镜像为准。未拉镜像，未验端口或部署结果。只想本机试用时应先按需限制监听；不建议照搬示例到公网。 |
| 订阅 → 标题含关键词 → 加星，可预览 | [原 README 的「自动化规则引擎」](https://github.com/kue02/Krss/tree/v1.2.0) · [v1.2.0 规则编辑器](https://github.com/kue02/Krss/blob/v1.2.0/frontend/src/components/automation/FilterEditor.tsx) | 条件支持标题关键词，代码有标题包含匹配、加星、单源范围和预览。「教程」是自拟关键字，不保证任何订阅都有命中。图和正文不声称已跑通。 |
| AI 摘要和翻译需要自备 Key | [原 README 的「AI 能力（自备 API Key）」](https://github.com/kue02/Krss/tree/v1.2.0) | 规则示例只用普通标题匹配，不依赖模型。启用 AI 摘要／翻译才要配置模型提供方凭据，费用取决于提供方；不宣称这一功能免费或完全本地。 |

## 人工审核与发布台账

| 时间（北京时间） | 版本 | 状态 | 操作／证据 |
| --- | --- | --- | --- |
| 2026-11-23 | v1 | 初稿，待人工审核 | 已整理公开一手证据、可复制正文和配图 brief。产品未实测，配图未制作，不代表批准发稿。 |

正文按 [X 长度规则](https://docs.x.com/fundamentals/counting-characters)本地估算为 243/280；未打开发布编辑器。待审：核对正文口吻和配图方向；若决定配图，出图后逐项校对，发布前在编辑器复核最终文本。没有发布授权，没有渠道操作，没有帖子链接。
