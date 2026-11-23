# X 发布流程试走｜Kites 与 Cline + LM Studio

这是手动发布流程的审阅包。先从 Kites 单帖验证文字、图片和链接，再拿 Cline 串帖验证多条排序。**本包不含实测结论：Kites 未试译，Cline 未联调，两张配图都是示意图。**

| 顺序 | 复制哪份文字 | 上传哪张图 |
| --- | --- | --- |
| 1. Kites 单帖 | [Kites 短帖](kites/short-post.txt) | [Kites 配图](kites/cover-illustration.png) |
| 2. Cline 四条串帖 | [Cline 串帖](cline/thread.txt)，按 1/4 至 4/4 分别粘贴 | [Cline 配图](cline/cover-illustration.png)，只放第 1 条 |

在 X 的发帖编辑器检查图片预览、正文换行和链接。试串帖时用「+」逐条添加，发布前确认 1/4 至 4/4 都在同一个串里；不要把整份串帖粘到一条里。**如果只是验证到编排这一步，可以停在编辑器，不必点发布；要确认公开发布成功，需要你自己在 X 点发布，再查看帖子链接和串帖顺序。**

图片替代文字（如需填写）：

- Kites：同一幅雨中小猫漫画，左侧气泡是日文原句，右侧是中文排版示意；非插件实测输出。
- Cline：启动 LM Studio 本地服务，在 Cline 选择 LM Studio，再用测试仓库提问。启用认证才填 Token；官方文档整理，未联调。

原始参考：[Kites 项目仓库](https://github.com/Unheat/Kites) · [Cline 4.1.27 发布说明](https://github.com/cline/cline/releases/tag/v4.1.27) · [LM Studio 下载](https://lmstudio.ai/download)。前一轮准备的漫画样例与测试函数也留在各自子目录，仅供复测，不是发布配图。
