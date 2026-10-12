# 公共接口与模块交接

信封：`schemas/workflow.schema.json`。所有模块产物使用固定公共字段。JSON Schema验证类型与必填项，业务函数和测试另查ID、范围、确认与原件。

| 模块输出 | data主要内容 | 下一模块 |
|---|---|---|
| source_manifest/project_register | project、sources、来源哈希 | M04/M08 |
| tender_brief | requirements、personnel_rule、coverage | M07/M09 |
| response_matrix/task_plan | responses、template、coverage、excluded_requirements | M09/M13 |
| material_index | persons、assets、reading_boundary | M09/M13 |
| asset_match/confirmed_selection | candidates、selected、selection_digest、confirmation | M13 |
| assembly_result | artifact_status、files、trace、所选ID | M14 |
| review_result | review_status、checks、实际文件哈希、coverage | 显式局部放行/M18 |
| archive_manifest | files、source_files、公开范围 | 回放与后续复用 |

原文证据为 source_id、line定位和quote；来源文件登记哈希。实体ID从项目/标包与稳定来源键生成，修改条款文字不会把历史ID分给另一条款。

候选与确认分开：选择记录包含 project_id、lot_id、source_mode、person_ids、target_digest、confirmed_by、confirmed_at、status。摘要覆盖要求的人员规则与所选人员和证书。这里只接受DEMO输入记录；没有真人来源时不自动补确认人。

`module --from-run` 读取已经生成的上游JSON。输出复制到新目录后只重做指定模块，下游标记STALE且撤销复制的旧放行；要恢复整链用新的完整run。当前没有全自动依赖图重跑，这属于X01任务。

不要临时改状态词、把missing变成空字符串或把业务批准与程序完成混为同一字段。涉及公共接口的任务需列出受影响模块和迁移验证。
