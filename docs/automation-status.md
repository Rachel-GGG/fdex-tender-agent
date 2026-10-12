# 协作自动化接入状态

本文件区分仓库工作流、模型审查执行与业务审批。最后核查日期：2026-10-13。

| 能力 | 基座提供的入口 | 状态与依赖 |
|---|---|---|
| 任务发布 | 19份模块/底座任务，publish_tasks.py幂等发布 | 随建仓发布，实际Issues为准 |
| 认领和唯一负责人 | issue_comment工作流、共享串行队列、状态评论 | 发布后实测；不需要额外API key |
| 进展/求助/协作/释放 | /progress /help /assist /approve-assist /release | 同一协调流程，保留交接 |
| 停滞回收 | 每6小时检查，48小时提醒、提醒后24小时释放 | 有PR或blocked暂停；调度有GitHub延迟 |
| CI | pull_request只读环境、公开合成测试 | GitHub runner执行；首次外部fork可能需平台审批 |
| PR任务校验 | 只执行main的可信代码、检查认领和绑定 | contribution状态检查 |
| 审查请求 | PR更新自动加入needs-maintainer-review | 这是排队请求，不等于模型已执行 |
| 当前提交批准后合并 | PR coordinator重新读SHA、审查与CI，再按分支保护合并 | 常规学员PR；作者不能批准自己 |
| Codex自动审查 | 当前本机任务的仓库监控作为先行入口 | 依赖本机Codex/联网在线，按实际监控配置运行 |
| GitHub托管的模型审查 | 后续可接Codex Action或独立webhook worker | 新仓库尚无OPENAI_API_KEY；未冒充已运行 |
| 业务确认/正式部署 | 原始记录、哈希与具名责任人 | 不从工程合并自动产生 |

## 为什么没有等待新密钥

GitHub内置token足够完成任务协调、CI、状态更新与合并门禁。模型审查可以先由已登录的Codex维护入口承担；将来需要全天托管、按事件即时执行时，再接入指定服务。现阶段本机监控的延迟和在线条件要明确。

托管Codex Action按官方说明需要API密钥：[官方文档](https://learn.chatgpt.com/docs/github-action)。不要把个人ChatGPT登录凭据复制到公开仓库或Actions日志。使用已有GitHub身份只授予此项目所需操作。

## 合并条件

main为目标；任务负责人/协作者绑定正确；test成功；当前提交得到iurp或已授权独立审查者批准；没有当前阻塞意见；可以与最新main整合。核心文件由CODEOWNERS请求审查。

CI成功只是工程证据。正常样例、Word实际查看、WorkBuddy实机运行和业务确认分别记录。高风险权限、真实交易、目标变化或超范围功能不自动推进。
