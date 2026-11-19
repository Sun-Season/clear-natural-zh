# clear-natural-zh

让中文写得清楚、自然，同时保留事实、条件、不确定性与作者语气。

本技能合并了 Humanizer-zh 的语境判断和 ste-zh v1.0.0 的结构检查：先消歧义，再润色，最后核对原意。它可以独立使用，不需要安装两个原技能。

## 安装

### Codex

把仓库克隆到个人技能目录。目标目录应尚不存在：

```bash
git clone https://github.com/Sun-Season/clear-natural-zh.git ~/.codex/skills/clear-natural-zh
```

如果设置了自定义 `CODEX_HOME`，请把目标改为其下的 `skills/clear-natural-zh`。安装后，在客户端刷新技能列表或新开会话。

也可以直接把仓库链接发给 Codex，并说：“帮我安装这个 skill。”

### 其他支持 SKILL.md 的客户端

把仓库放入该客户端的技能目录，按客户端要求加载 `SKILL.md`。

## 使用

```text
用 clear-natural-zh 润色下面这段话，保留事实和语气。
用严格模式整理这段操作步骤，不要丢掉条件和例外。
检查这段 README 的歧义，给我前后对照。
```

默认只给成稿。需要修改说明时，可以要求 diff 或前后对照。

若希望每次回答都应用，可在自己的全局或项目指令中加入：

> 每次回答默认应用 clear-natural-zh。普通回答用自然模式，技术步骤用严格模式。保留事实、情态、条件和作者语气，不为满足句长删减信息。不要重复声明技能使用情况。

安装本身不会修改你的全局指令。

## 两种模式

| 模式 | 适用内容 | 处理方式 |
|---|---|---|
| 自然模式 | 普通回答、文档、README、PR | 消除歧义和套话，保留文体及必要长句 |
| 严格模式 | 操作步骤、报错、工具描述、agent 指令 | 一句一个动作，术语保持一致，明确条件和顺序 |

创意或文学文本保留节奏与修辞，不套技术句长限制。所有模式都以原意和信息完整为先。

## 示例

原文：

> 需要注意的是，我们正在对导出失败的问题进行排查，目前可能与缓存有关，但原因尚未确认。

改写：

> 我们正在排查导出失败的问题。问题可能与缓存有关，但原因尚未确认。

“正在”“可能”和“尚未确认”都保留，避免把调查中的判断改成事实。

## v1.4.0

改案后，按最终用途核对正文、文件名、标题和交接说明。兼容要求及用户需要的决策记录应保留。规则改编自 [no-negative-echo](https://github.com/LB623/no-negative-echo)，已并入默认入口。

## v1.3.0：精简加载与偏好回归

默认入口保留六项核心规则，一般回答和改写不必读取其他文件。严格技术文本、代码注释和 lint 分别按需加载细则；语境难以判断时再查案例。已在上下文中的资料无需反复读取。

此次偏好来自维护者的十题选择：重视自然、直接和连贯，保留有作用的解释与结尾，区分正文和工作汇报；不强制结论先行、短句或列表。它是初步偏好，不代表所有读者。

[偏好回归协议](tests/readability-evaluation.md) 和 [配对场景](tests/readability-cases.json) 用于开发时评测，不进入默认上下文。脚本测试、结构校验和文件长度变化不证明模型更遵循规则；行为效果需独立盲评。

## 可选检查脚本

### v1.2.0 的写作规则更新

- 删除内容后修复衔接，避免用“本版不再涉及……”将话题重新带入正文。
- 区分成稿、修改说明与操作回执，让正文可独立阅读。
- 减少无用辩护与重复限定，保留事实、证据状态和适用条件。
- 检查假对比、重复段落、碎片化列表和多轮修改中的术语漂移。

正反例、必要例外与人工回归标准见 [成稿边界与回归案例](references/final-copy-boundaries.md)。这些检查依赖任务上下文；本次未增加 linter 检测规则，脚本不能自动判断删除是否符合用户意图。

### 脚本使用

仅使用 Python 标准库，无需 API 密钥或联网服务。已验证 Python 3.9 环境。

```bash
python3 scripts/ste-lint-zh.py document.md
python3 scripts/ste-lint-zh.py --json document.md
python3 scripts/ste-lint-zh.py --profile natural --allow 闭环控制 document.md
python3 scripts/ste-lint-zh.py --format text notes.txt
python3 scripts/ste-lint-zh.py --max-chars 25 steps.md
python3 scripts/ste-lint-zh.py --selftest
```

脚本基于 ste-zh v1.0.0 扩展。它会机械标记部分词语、句长和同义词，可能误报。检查结果需要结合语义复核，不能为了消除警告而删掉事实或正确术语。零警告不证明原意保留。

### v1.1.0 的改进

- 自然模式将全部发现作为建议；严格模式仍是默认值。术语轮换在两种模式下都只作建议。
- `--allow TERM` 可重复指定术语，不影响句长和标点检查。
- 改善代码围栏、跨行代码片段、链接、引用式链接、HTML 注释及 YAML front matter 的处理。链接文字参与检查，地址不参与。
- 修正嵌套术语重复计数、重复词漏报及重叠词重复报告，保留原始行列坐标。
- 验证参数和 UTF-8 输入；`--baseline` 按全部输入的硬违规合计计算，摘要计数排除屏蔽内容。

旧 CLI 参数和 JSON 发现字段保持不变。注意：同义词轮换从硬违规降为建议，可能改变退出码。自然模式有发现也返回 0；严格模式硬违规超过 baseline 返回 1；输入或参数错误返回 2。JSON 模式读取文件失败时，错误写到 stderr，stdout 留空。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/ste-lint-zh.py --selftest
```

调研依据、解析边界与后续方向见 [linter-research.md](references/linter-research.md)。

## 来源与许可

本项目采用 MIT 许可。新增内容见 [LICENSE](LICENSE)，第三方版权声明见 [LICENSE-humanizer-zh](LICENSE-humanizer-zh) 和 [LICENSE-ste-zh](LICENSE-ste-zh)。

感谢 [Humanizer-zh](https://github.com/op7418/Humanizer-zh)、[blader/humanizer](https://github.com/blader/humanizer) 和 [lemonhall/asd-ste100-skill-zh](https://github.com/lemonhall/asd-ste100-skill-zh)。具体来源及合并差异见 [references/provenance.md](references/provenance.md)。

本项目是独立合并改编版。上游更新不会自动同步。不包含 ASD-STE100 标准正文或词表，也不提供官方合规认证或 AI 检测通过保证。
