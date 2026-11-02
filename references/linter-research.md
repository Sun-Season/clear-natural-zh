# Linter 扩展调研与实现边界

调研日期：2026-11-02。此次实现为 clear-natural-zh v1.1.0。

## 依据

- [Vale：Markup-aware linting](https://vale.sh/features/markup)：先区分正文和标记结构；链接文字与链接地址应分别处理，front matter 不应被当作普通正文误检。本项目借鉴这个边界，尚未采用 Vale 的完整解析和作用域系统。
- [LanguageTool：How to avoid mistakes when writing rules](https://dev.languagetool.org/how-to-avoid-mistakes-when-writing-rules.html)：过度概括会造成误报；例外应配套正确文本测试。本项目增加术语白名单和正反例，不把候选词命中等同于语义错误。
- [CommonMark 0.31.2：Fenced code blocks](https://spec.commonmark.org/0.31.2/#fenced-code-blocks) 与 [Code spans](https://spec.commonmark.org/0.31.2/#code-spans)：围栏类型须匹配，结束围栏不能短于开始围栏；代码片段使用等长反引号配对。本项目为这些行为增加回归测试。

以上是设计参考，不是从这些项目复制实现，也不表示本脚本兼容它们的全部语法。

## 实现选择

保留单文件、Python 标准库和原 JSON 发现格式，先修复已知误报与漏报。自然模式全部提示，严格模式保留原有硬规则；两种模式都不再将术语共现直接判为错误。不提供自动修复，以免改变情态、事实和作者意图。

相比只扩充禁词表，这些改动针对的是已有可复现缺陷。相比引入完整 Markdown 解析器，此方案便于分发，但语法覆盖有限。将来需要复杂 Markdown、编辑器集成或完整语法支持时，应采用成熟解析器及源位置映射，避免继续堆叠正则。

## 参数

| 参数 | 含义 |
|---|---|
| `--profile strict` | 默认模式，按规则原有严重度报告，术语轮换始终为建议 |
| `--profile natural` | 全部发现均为建议，不因发现问题返回 1 |
| `--allow TERM` | 字面术语白名单，可重复，仅豁免该位置的词汇类检查 |
| `--format markdown` | 默认，屏蔽已支持的 Markdown 非正文 |
| `--format text` | 把 Markdown 标记也当作普通输入检查 |
| `--baseline N` | 所有输入合计容忍 N 处硬违规，N 必须非负 |
| `--max-chars N` | 正整数，汉字算一字，连续拉丁字母或数字算一单位 |

保持 `--disable`、`--json`、`--list-rules`、`--selftest` 和多文件输入。行、列以原始文本的 Unicode 字符为单位，从 1 开始，不是 UTF-8 字节偏移。读取失败写 stderr，返回 2。

## 已覆盖与限制

已测试普通围栏、带引用前缀的围栏、较长结束围栏、未闭合围栏、多反引号及跨行片段、链接文字与含括号目标、引用定义、HTML 注释、闭合 YAML front matter、CRLF 行号和转义表格竖线。

这不是完整 CommonMark 解析器。复杂列表容器、引用容器结束后围栏作用域、缩进代码块、HTML 原始块、嵌套链接标签及注释与块语法交错等情形仍可能误报或漏报。句长按物理行检查，跨行段落不会合并计算；摘要长度也是机械计数，不是语言学分词。表格按未转义竖线分段。遇到不支持的语法，可先提取正文，再用 `--format text` 检查。

词汇规则不理解语义。即使使用自然模式或白名单，仍需人工核对。测试通过只证明覆盖用例的行为，不证明整体准确率；本次未做真实语料精确率或召回率评估。
