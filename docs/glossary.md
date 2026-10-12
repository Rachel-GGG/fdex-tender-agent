# 学员术语与状态

- Issue：一个有范围、负责人和验收条件的工程任务。
- PR：提出一组变更供审查；不是直接改主干。
- 主干 main：团队共用的当前工程基座。
- Skill：可复用的任务说明及必要工具。使用者在WorkBuddy调用，开发者在Codex构建和测试。
- 模块：业务能力边界；不必每个模块都独立开一个Agent。
- Schema：机器检查的字段与类型约定。校验通过不等于业务结论正确。
- source_id：来源原件的稳定编号；hash证明对应字节，不能单独证明材料真实性。
- project_id / lot_id：项目和采购包，防止不同文件误混。
- run_id：一次运行；新目录保存新运行，旧结果可追溯。
- SOURCE_FACT：材料写了什么；PROPOSED：建议；HUMAN_CONFIRMED：有明确确认记录的内容。
- COMPLETE / REVIEW / BLOCKED：处理状态，分别为声明范围完成、需复核、相关范围不能继续。
- UNCONFIRMED / CONFIRMED / STALE：具体对象的确认状态；变更后旧确认可能失效。
- PARTIAL_DRAFT：局部草稿；与整本标书完成不同。
- RELEASED：某个哈希和范围的显式放行；本基座只支持DEMO人员章节。
