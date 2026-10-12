# 基座验证记录

日期：2026-10-13。数据全部为公开合成资料。

## 本地程序与文件

- Python业务与协作回归测试28项通过：原文/稳定ID、未确认、过期、缺图、换人、输入上下文、未知ID、路径约束、模板哈希、实际Word四类错误、失效放行、归档回放，以及认领/协作/求助/转交。
- 正常与换人运行直接读取原始Markdown、说明文件、图片和模板，生成实际JSON与可编辑DOCX；没有读取期望答案作为产物。
- 四个核心Skill的名称、描述与元数据通过skill-creator的结构检查。
- 正常与换人文档各4页，用内置LibreOffice渲染并逐页检查；中文字体、表格、证书图与断页通过。模板嵌入OFL许可字体，解决无中文字体环境的显示问题。
- 视觉检查是本次基座的人工检查记录，M14程序本身仍明确输出visual_review=NOT_PERFORMED_BY_PROGRAM。

## 复现命令

```bash
python -m unittest discover -s tests -v
python -m fdex_tender run --input samples/e2e/core-normal --output outputs/normal
python -m fdex_tender run --input samples/e2e/replacement --output outputs/replacement
```

## 不在这份通过记录内

图片OCR、真实证书核验、任意模板、完整标书、真实签章/递交、企业部署和学员WorkBuddy客户端实机运行。GitHub协作工作流的上线实测与审查执行入口在automation-status中单独记录。
