# 来源与合并差异

本技能是合并改编版，版本 1.4.0。

- Humanizer-zh：采用 Humanizer-zh 的本地修订规则（修订日期：2026-09-23）。其来源包括 [blader/humanizer v3.0.0](https://github.com/blader/humanizer/blob/v3.0.0/SKILL.md)、[Humanizer-zh PR 39](https://github.com/op7418/Humanizer-zh/pull/39) 与 [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)。本地 Humanizer-zh 随附的 MIT 许可与版权声明保存在 [LICENSE-humanizer-zh](../LICENSE-humanizer-zh)。这些参考链接不表示本项目重新授权其全部内容。
- ste-zh v1.0.0：来自 [lemonhall/asd-ste100-skill-zh](https://github.com/lemonhall/asd-ste100-skill-zh)。随附 linter 基于此版本扩展，MIT 许可与版权声明保存在 `../LICENSE-ste-zh`。原始版权声明保留。扩展增加了模式、术语白名单、Markdown 屏蔽与回归测试。其规则分类参考 danyuchn/asd-ste100-skill；不包含 ASD-STE100 标准正文或受控词表。

合并保留 Humanizer-zh 的信息保护、作者声音、语境判断与格式保护，并吸收 ste-zh 的动作拆分、术语一致、严格模式和机械检查。

冲突处理：句长改为受语义约束的目标；普通文本不强制术语式用词；档位与规则分析默认不展示；linter 命中只作待复核提示。合并版运行不依赖两个原技能。原技能后续更新不会自动同步到合并版。

v1.2.0 根据用户的删除残余案例及公开写作讨论，补充成稿边界、必要限定、段落信息推进和多轮修改检查。规则与示例为本项目归纳编写；外部材料作为研究参考，未安装或复制其技能实现。来源及覆盖范围见 [成稿边界与回归案例](final-copy-boundaries.md#调研依据)。

v1.3.0 根据维护者十题选择与确认的偏好精简入口，并拆分条件性参考资料。增加开发阶段的配对行为用例和评测协议；未修改 linter 检测逻辑，未将偏好选择当作模型评测结果。

v1.4.0 将 [LB623/no-negative-echo 的成稿规则](https://github.com/LB623/no-negative-echo/blob/eba9f1d2b4c19e699786a49427189988ad6d8d65/no-negative-echo/SKILL.md) 融入交付规则，扩展到文件名、元数据、提交与交接。见 [MIT 许可](../LICENSE-no-negative-echo)。
