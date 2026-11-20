# clear-natural-zh

让中文写得清晰、易懂、易读、自然，理顺前后句、前后段与上下文逻辑，避免短句堆砌和 AI 味，同时严格保留事实、条件、不确定性与作者语气。

本技能合并了 Humanizer-zh 的语境判断和 ste-zh v1.0.0 的结构检查，并在 v2.x 中系统强化了清晰度、句式节奏与三层逻辑（句间、段间、上下文）诊断。它可以独立使用，不需要安装原技能。

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
用 clear-natural-zh 润色下面这段话，让它更清晰流畅，去掉短句堆砌感，理顺前后句和段落逻辑。
用严格模式整理这段操作步骤，不要丢掉条件和例外。
检查这段文档的歧义和上下文矛盾，给我前后对照。
```

默认只给成稿。需要修改说明时，可以要求 diff 或前后对照。

若希望每次回答都应用，可在自己的全局或项目指令中加入：

> 每次回答默认应用 clear-natural-zh。普通回答用自然模式，技术步骤用严格模式。保留事实、情态、条件和作者语气，不为满足句长删减信息，也避免短句堆砌。不要重复声明技能使用情况。

安装本身不会修改你的全局指令。

## 两种模式

| 模式 | 适用内容 | 处理方式 |
|---|---|---|
| 自然模式 | 普通回答、文档、README、PR | 清晰易懂、长短句错落流畅、句段与上下文连贯，消除歧义和套话 |
| 严格模式 | 操作步骤、报错、工具描述、agent 指令 | 一句一个动作，术语保持一致，明确条件、例外和顺序 |

创意或文学文本保留节奏与修辞，不套技术句长限制。所有模式都以原意和信息完整为先。

## 示例

原文：

> 需要注意的是，我们正在对导出失败的问题进行排查，目前可能与缓存有关，但原因尚未确认。

改写：

> 我们正在排查导出失败的问题，目前怀疑与缓存有关，但原因尚未确认。

“正在”“可能/怀疑”和“尚未确认”的确定程度都保留，同时保持一句流畅读完，避免硬拆成重复主语的碎句。

## 版本更新

### v2.1.1

省略的前提能从材料确定时才补出，原因和执行者仍有疑问时保留疑问。句子可以在动作或状态改变的地方断开，段间按需要过渡。新增一组陌生材料，用于检验读者能否从成稿判断下一步会发生什么。

### v2.1.0：消除短句堆砌，强化长短句自然节奏

- 在 `SKILL.md` 核心规则中显式增加反短句堆砌（电报体、流水账）约束：同一主语的连续动作或紧密因果、条件、补充优先用逗号、承前省主语和自然复句融合，仅在意思转折、重心切换或句子过载时用句号收束，并明确区分自然模式与严格模式的断句标准。
- 在 [逻辑与连贯诊断指南](references/coherence-and-logic.md) 中新增“破除短句堆砌”正反例与合句/拆句边界，同时更新 `README.md` 示例以身作则。
- 在 [配对回归场景](tests/readability-cases.json) 中新增 `sentence-rhythm` 用例，专门验证短句堆砌消除效果。

### v2.0.0：清晰、易懂、易读与三层逻辑升级

- 重构 `SKILL.md` 核心规则，把“清晰与易懂”“易读与去噪”“前后句逻辑”“前后段逻辑”“上下文逻辑与定稿边界”拆为可逐项核对的独立规则，同时保持入口精简。
- 新增按需参考 [逻辑与连贯诊断指南](references/coherence-and-logic.md)，提供五层排查法、正反改写示例及快速自检清单。
- 在 [配对回归场景](tests/readability-cases.json) 中新增句间逻辑、段间推进与上下文一致性三组评测用例。

### v1.5.0

改案后按最终用途重写受影响的标题和文件名。公开发布等场景按需读取上游 [严格交付流程](references/high-assurance-finalization.md)。运行 `python3 scripts/check_surface.py --terms-file terms.txt --root output output/guide.md`，可检查非敏感词在文本和目录名中的残留。词表每行一项，文件按实际路径列出。同义改写与必要事实仍需结合语境复核。

### v1.4.0

改案后，按最终用途核对正文、文件名、标题和交接说明。兼容要求及用户需要的决策记录应保留。规则改编自 [no-negative-echo](https://github.com/LB623/no-negative-echo)，已并入默认入口。

### v1.3.0：精简加载与偏好回归

默认入口保留核心规则，一般回答和改写不必读取其他文件。严格技术文本、代码注释和 lint 分别按需加载细则；语境难以判断时再查案例。已在上下文中的资料无需反复读取。

此次偏好来自维护者的十题选择：重视自然、直接和连贯，保留有作用的解释与结尾，区分正文和工作汇报；不强制结论先行、短句或列表。它是初步偏好，不代表所有读者。

[偏好回归协议](tests/readability-evaluation.md) 和 [配对场景](tests/readability-cases.json) 用于开发时评测，不进入默认上下文。脚本测试、结构校验和文件长度变化不证明模型更遵循规则；行为效果需独立盲评。

## 可选检查脚本

### v1.2.0 的写作规则更新

- 删除内容后修复衔接，避免用“本版不再涉及……”将话题重新带入正文。
- 区分成稿、修改说明与操作回执，让正文可独立阅读。
- 减少无用辩护与重复限定，保留事实、证据状态和适用条件。
- 检查假对比、重复段落、碎片化列表和多轮修改中的术语漂移。

正反例、必要例外与人工回归标准见 [成稿边界与回归案例](references/final-copy-boundaries.md)。这些检查依赖任务上下文；linter 不能自动判断删除是否符合用户意图。

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
