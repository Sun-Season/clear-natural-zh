# 来源与合并差异

本技能是合并改编版，版本 1.0.0。

- Humanizer-zh：采用 Humanizer-zh 的本地修订规则（修订日期：2026-09-23）。其来源包括 [blader/humanizer v3.0.0](https://github.com/blader/humanizer/blob/v3.0.0/SKILL.md)、[Humanizer-zh PR 39](https://github.com/op7418/Humanizer-zh/pull/39) 与 [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)。本地 Humanizer-zh 随附的 MIT 许可与版权声明保存在 [LICENSE-humanizer-zh](../LICENSE-humanizer-zh)。这些参考链接不表示本项目重新授权其全部内容。
- ste-zh v1.0.0：来自 [lemonhall/asd-ste100-skill-zh](https://github.com/lemonhall/asd-ste100-skill-zh)。随附 linter 原样复制，MIT 许可与版权声明保存在 `../LICENSE-ste-zh`。其规则分类参考 danyuchn/asd-ste100-skill；不包含 ASD-STE100 标准正文或受控词表。

合并保留 Humanizer-zh 的信息保护、作者声音、语境判断与格式保护，并吸收 ste-zh 的动作拆分、术语一致、严格模式和机械检查。

冲突处理：句长改为受语义约束的目标；普通文本不强制术语式用词；档位与规则分析默认不展示；linter 命中只作待复核提示。合并版运行不依赖两个原技能。原技能后续更新不会自动同步到合并版。
