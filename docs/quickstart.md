# 开发与复现

安装、跨平台命令和贡献步骤见根README。这里补充独立排查入口。

## 输入在哪里

samples/e2e/core-normal/context.json 决定项目/标包/分析时间；sources.json 列出原件；tender/tender.md 是实际读取的招标节选；materials/ 包含4个说明和4张公开虚构证书；template-manifest.json 声明模板；selection.json 是显式模拟确认输入。

不用根据文件名猜测身份，也不从另一个对话恢复资料。输出的input_refs、requirements.evidence_refs、assets.field_refs可以回到原件。

## 查看整链

每个输出JSON都有同名中文摘要。run_record记录本次模块状态，archive_manifest记录字节哈希。解压archive.zip后，可再次用inputs目录执行run，重新生成自己的结果。

## DOCX视觉检查

实际用Word/WPS打开，看中文、表格、三张对应证书与断页。模板嵌入OFL许可的Noto中文字体，生成文件也保留它，以减少不同电脑缺字体造成的缺字；文件因此较大。原字体与许可在assets/fonts。程序检查不会自动声称视觉通过。

测试构造四种实际文档错误：缺图片、错项目、旧人员、残留占位符，并验证实际审查器能定位。生产模板、报价、完整标书另行验收。

## 修改样例注意

请复制到自己的新DEMO输入目录再修改。换人或材料内容变化需要新的selection摘要和输入确认，不能只改状态为CONFIRMED。保留旧样例用于回归。

现有样例制作工具用于维护基座资源，不建议学员每次运行都重建它；重建会改变图片/模板字节，需要维护manifest。正常运行只使用已经提供的文件。
