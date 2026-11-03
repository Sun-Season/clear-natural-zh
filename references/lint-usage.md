# 可选机械检查

仅用户要求检查或长篇技术文本需要辅助时运行。脚本只需 Python 标准库，执行时无需先读取脚本全文。

```bash
python3 <skill-dir>/scripts/ste-lint-zh.py --profile natural <文件>
python3 <skill-dir>/scripts/ste-lint-zh.py --profile strict --json <文件>
python3 <skill-dir>/scripts/ste-lint-zh.py --allow 闭环控制 <文件>
```

将 `<skill-dir>` 替换为技能目录。普通文本用 natural，全部发现为建议；strict 是脚本默认模式，结构及词汇硬规则可能触发非零退出码，术语轮换仍只作建议。`--allow` 按字面豁免词汇检查，可重复使用。

逐项结合上下文复核，不能为了清零删掉事实或正确术语。退出码不代表最终写作判断，零警告不证明原意保留。脚本不判断删除意图或正文边界。

需要完整参数、解析边界或维护脚本时才读 [linter-research](linter-research.md)。
