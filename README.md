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

## 可选检查脚本

仅使用 Python 标准库，无需 API 密钥或联网服务。已验证 Python 3.9 环境。

```bash
python3 scripts/ste-lint-zh.py document.md
python3 scripts/ste-lint-zh.py --json document.md
python3 scripts/ste-lint-zh.py --max-chars 25 steps.md
python3 scripts/ste-lint-zh.py --selftest
```

脚本来自 ste-zh v1.0.0，保持原实现。它会机械标记部分词语、句长和同义词，可能误报。检查结果需要结合语义复核，不能为了消除警告而删掉事实或正确术语。零警告不证明原意保留。

## 来源与许可

本项目采用 MIT 许可。新增内容见 [LICENSE](LICENSE)，第三方版权声明见 [LICENSE-humanizer-zh](LICENSE-humanizer-zh) 和 [LICENSE-ste-zh](LICENSE-ste-zh)。

感谢 [Humanizer-zh](https://github.com/op7418/Humanizer-zh)、[blader/humanizer](https://github.com/blader/humanizer) 和 [lemonhall/asd-ste100-skill-zh](https://github.com/lemonhall/asd-ste100-skill-zh)。具体来源及合并差异见 [references/provenance.md](references/provenance.md)。

本项目是独立合并改编版。上游更新不会自动同步。不包含 ASD-STE100 标准正文或词表，也不提供官方合规认证或 AI 检测通过保证。
