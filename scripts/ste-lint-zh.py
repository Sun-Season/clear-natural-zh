#!/usr/bin/env python3
"""受控中文 linter —— ASD-STE100 的中文对应物，只查机械可判的规则。

用法：
    python scripts/ste-lint-zh.py <文件...>          # 检查文件
    python scripts/ste-lint-zh.py < 文本             # 从 stdin 读
    python scripts/ste-lint-zh.py --json <文件...>   # 结构化输出
    python scripts/ste-lint-zh.py --max-chars 25 f   # 程序步骤用 25 字上限
    python scripts/ste-lint-zh.py --baseline 12 f    # 存量文档：容忍 12 处硬违规
    python scripts/ste-lint-zh.py --disable vague-word,synonym-rotation f
    python scripts/ste-lint-zh.py --selftest         # 自检

硬违规（semicolon / long-sentence / nominalization / marketing-adjective /
empty-phrase）超过 --baseline 时退出码 1。
建议类（passive-voice / compound-aspect / vague-word / halfwidth-punct /
dash-join / synonym-rotation）只报告，不导致失败。自然模式下全部规则只作建议。

它**永远不挑情态**（可能 / 也许 / 大概 / 倾向于）：置信度是内容，不是风格。
自检里有一条断言：「请求可能已失败。」必须干净。

仅标准库，Python 3.9+。本分支新增自然模式、术语白名单及 Markdown 屏蔽。
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

HARD = "hard"
ADVISORY = "advisory"

RULE_SEVERITY: Dict[str, str] = {
    "semicolon": HARD,
    "long-sentence": HARD,
    "nominalization": HARD,
    "marketing-adjective": HARD,
    "empty-phrase": HARD,
    "synonym-rotation": ADVISORY,
    "passive-voice": ADVISORY,
    "compound-aspect": ADVISORY,
    "vague-word": ADVISORY,
    "halfwidth-punct": ADVISORY,
    "dash-join": ADVISORY,
}

RULE_ORDER = list(RULE_SEVERITY)

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
SENT_END_RE = re.compile(r"[。！？!?]+")
LIST_MARK_RE = re.compile(r"^(\s*(?:#{1,6}|[-*+]|\d{1,3}[.)]|>)\s+)")

# 营销候选词：命中后仍需结合语境判断，不能自动删除。
MARKETING_WORDS = (
    "无缝", "强大", "赋能", "闭环", "极致", "丝滑", "一站式", "全方位", "颠覆",
    "领先", "顶级", "沉浸式", "智能化", "黑科技", "革命性", "独创", "完美",
    "极速", "超强", "极致体验", "降维打击",
)

# 套话候选：范围限定有实际含义时必须保留。
EMPTY_PHRASES = (
    "需要注意的是", "值得一提的是", "众所周知", "不难看出", "不言而喻",
    "在一定程度上", "某种意义上", "从某种角度", "综上所述", "显而易见",
    "毋庸置疑", "总的来说",
)

# 名词化：虚动词 + 动作名词。改成单个动词。
NOMINALIZATION_RE = re.compile(
    r"(进行|作出|加以|予以|给予|开展)(一[下个次些])?"
    r"[^，。！？；、\s]{0,6}?"
    r"(分析|检查|处理|优化|验证|评估|讨论|说明|调整|改造|升级|计算|统计|测试|"
    r"梳理|比对|排查|确认|审核|复盘|治理|维护|修复|部署|设计|规划|调研|探索|实践|尝试)"
)

PASSIVE_RE = re.compile(r"被[^，。！？；\s]{0,6}")
COMPOUND_ASPECT_RE = re.compile(r"(已经[^，。！？；]{0,10}[了过]|正在[^，。！？；]{0,8}[中着])")
VAGUE_RE = re.compile(r"(相关|有关|若干|一些|适当|酌情|必要时|等等|之类|大致|差不多|一定程度)")
HALFWIDTH_RE = re.compile(r"(?<=[\u4e00-\u9fff])[,;:!?](?=[\u4e00-\u9fff])")
DASH_JOIN_RE = re.compile(r"——")
SEMICOLON_RE = re.compile(r"[；;]")

# 同义轮换：同一篇里出现两个以上成员即视为轮换（同文档范围，跨行统计）。
SYNONYM_GROUPS: Tuple[Tuple[str, ...], ...] = (
    ("用户", "客户", "使用者", "终端用户"),
    ("删除", "移除", "清除", "删掉"),
    ("检查", "校验", "核对", "核查"),
    ("创建", "新建", "建立", "生成"),
    ("错误", "异常", "报错", "故障"),
    ("配置", "设置", "设定"),
    ("显示", "展示", "呈现"),
    ("运行", "执行"),
    ("保存", "存储"),
    ("修改", "更改", "变更"),
)

# 中文没有词边界，命中后要挡掉"看起来像、其实是别的词"的后缀：
# 客户端不是客户，用户名不是用户，检查点不是检查，运行时不是运行……
SYNONYM_BLOCKED_SUFFIX: Dict[str, Tuple[str, ...]] = {
    "用户": ("名",),
    "客户": ("端",),
    "检查": ("点",),
    "创建": ("时间",),
    "生成": ("式",),
    "显示": ("器",),
    "运行": ("时",),
    "错误": ("码",),
}


def member_occurrences(text: str, member: str) -> List[int]:
    """找出 member 在 text 里真正算数的位置，跳过被后缀挡掉的假命中。"""
    blocked = SYNONYM_BLOCKED_SUFFIX.get(member, ())
    positions: List[int] = []
    start = 0
    while True:
        index = text.find(member, start)
        if index < 0:
            break
        tail = text[index + len(member):]
        if not any(tail.startswith(suffix) for suffix in blocked):
            positions.append(index)
        start = index + len(member)
    return positions



@dataclass
class Options:
    max_chars: int = 40
    baseline: int = 0
    disabled: frozenset = frozenset()
    profile: str = "strict"
    allowed: Tuple[str, ...] = ()
    format: str = "markdown"

    def __post_init__(self) -> None:
        if self.max_chars < 1 or self.baseline < 0:
            raise ValueError("max_chars 必须为正数，baseline 不能为负数")
        if self.profile not in ("strict", "natural") or self.format not in ("markdown", "text"):
            raise ValueError("无效的 profile 或 format")
        if self.disabled - RULE_SEVERITY.keys():
            raise ValueError("disabled 中有未知规则")
        if any(not term or "\n" in term or "\r" in term for term in self.allowed):
            raise ValueError("白名单术语必须非空且不能跨行")

    def severity(self, rule: str) -> str:
        return ADVISORY if self.profile == "natural" else RULE_SEVERITY[rule]


@dataclass
class Finding:
    path: str
    line: int
    col: int
    rule: str
    severity: str
    message: str
    match: str

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "col": self.col,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "match": self.match,
        }

    def render(self) -> str:
        return f"{self.path}:{self.line}:{self.col} {self.rule}: {self.message} [{self.match}]"


def count_chars(text: str) -> int:
    """长度口径：一个汉字算 1，一段连续的拉丁字母 / 数字算 1（同上游「按词算」）。"""
    cjk = len(CJK_RE.findall(text))
    latin = len(TOKEN_RE.findall(text))
    return cjk + latin


def blank_span(chars: List[str], start: int, end: int) -> None:
    """用空格遮盖内容，保留换行及原始行列位置。"""
    for index in range(start, end):
        if chars[index] not in "\r\n":
            chars[index] = " "


def mask_line(line: str) -> str:
    """遮盖代码、地址和标签，保留可读的链接文字。也支持跨行代码片段。"""
    chars = list(line)
    # 按出现顺序处理注释和代码，避免代码里的 <!-- 遮盖后面的正文。
    token_re = re.compile(r"<!--|`+")
    position = 0
    while True:
        token = token_re.search(line, position)
        if token is None:
            break
        if token.group() == "<!--":
            close = line.find("-->", token.end())
            end = len(line) if close < 0 else close + 3
            blank_span(chars, token.start(), end)
            position = end
            continue
        # 转义的反引号不作为开头；成对片段内部按原字符处理。
        escapes = token.start() - len(line[:token.start()].rstrip("\\"))
        if escapes % 2:
            position = token.end()
            continue
        paragraph = re.search(r"\r?\n[ \t]*\r?\n", line[token.end():])
        limit = token.end() + paragraph.start() if paragraph else len(line)
        closer = re.compile(r"(?<!`)" + re.escape(token.group()) + r"(?!`)")
        close = closer.search(line, token.end(), limit)
        if close:
            blank_span(chars, token.start(), close.end())
            position = close.end()
        else:
            position = token.end()
    visible = "".join(chars)
    # 链接地址允许括号嵌套；只遮盖目标，保留标签文字。
    for match in re.finditer(r"\]\(", visible):
        start = match.start() + 1
        depth, end = 1, start + 1
        while end < len(visible) and depth:
            if visible[end] == "\\":
                end += 2
                continue
            if visible[end] == "(":
                depth += 1
            elif visible[end] == ")":
                depth -= 1
            end += 1
        if depth == 0:
            blank_span(chars, start, end)
    visible = "".join(chars)
    for match in re.finditer(r"\[[^\]\n]+\](\[[^\]\n]*\])", visible):
        blank_span(chars, match.start(1), match.end(1))
    visible = "".join(chars)
    for pattern in (r"https?://[^\s<>，。！？；]+", r"<[^>\n]+>"):
        for match in re.finditer(pattern, visible):
            blank_span(chars, match.start(), match.end())
    return "".join(chars)


def mask_document(text: str) -> str:
    """屏蔽常见 Markdown 非正文。不是完整的 CommonMark 解析器。"""
    lines = text.splitlines(keepends=True)
    chars = list(text)
    fence = None
    offset = 0
    front_end = -1
    if lines and lines[0].lstrip("\ufeff").strip() == "---":
        front_end = next((i for i in range(1, len(lines))
                          if lines[i].strip() in ("---", "...")), -1)
    for index, raw in enumerate(lines):
        # 支持普通围栏和引用内围栏；复杂列表容器不在此解析器范围内。
        body = re.sub(r"^(?: {0,3}> ?)+", "", raw)
        opener = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", body)
        skip = index <= front_end
        if not skip and fence:
            char, size = fence
            if re.fullmatch(r" {0,3}" + re.escape(char) + "{" + str(size) + r",}[ \t]*[\r\n]*", body):
                fence = None
            skip = True
        elif not skip and opener:
            token, info = opener.groups()
            if token[0] != "`" or "`" not in info:
                fence = (token[0], len(token))
                skip = True
        if re.match(r"^ {0,3}\[[^\]]+\]:\s*\S", body):
            skip = True
        if skip:
            blank_span(chars, offset, offset + len(raw))
        offset += len(raw)
    return mask_line("".join(chars))


def word_matches(text: str, words: Sequence[str]):
    """最长词优先，报告重复出现的位置，避免包含关系造成重复提示。"""
    pattern = "|".join(re.escape(word) for word in sorted(set(words), key=len, reverse=True))
    return re.finditer(pattern, text)


def lexical_text(text: str, opts: Options) -> str:
    chars = list(text)
    for term in opts.allowed:
        for match in re.finditer(re.escape(term), text):
            blank_span(chars, match.start(), match.end())
    return "".join(chars)


def split_cells(line: str) -> List[Tuple[int, str]]:
    """按 markdown 表格竖线切段，保留每段在原行里的起始列。"""
    cells: List[Tuple[int, str]] = []
    start = 0
    for index, char in enumerate(line):
        if char == "|" and (index - len(line[:index].rstrip("\\"))) % 2 == 0:
            cells.append((start, line[start:index]))
            start = index + 1
    cells.append((start, line[start:]))
    return cells


def iter_sentences(text: str, base: int) -> Iterable[Tuple[int, str]]:
    """按句末标点切句；分号留在句内，好让 semicolon 规则看得见它。"""
    start = 0
    for match in SENT_END_RE.finditer(text):
        end = match.end()
        yield base + start, text[start:end]
        start = end
    if text[start:].strip():
        yield base + start, text[start:]


def sentence_findings(
    sentence: str,
    offset: int,
    line_no: int,
    path: str,
    opts: Options,
) -> List[Finding]:
    findings: List[Finding] = []
    stripped = sentence.strip()
    if not stripped:
        return findings

    def add(rule: str, message: str, match_text: str, rel: int) -> None:
        if rule in opts.disabled:
            return
        findings.append(
            Finding(
                path=path,
                line=line_no,
                col=offset + rel + 1,
                rule=rule,
                severity=opts.severity(rule),
                message=message,
                match=match_text,
            )
        )

    for match in SEMICOLON_RE.finditer(sentence):
        add(
            "semicolon",
            "检查分号是否串联独立动作；可在保留条件和关系的前提下拆句。",
            match.group(0),
            match.start(),
        )

    length = count_chars(sentence)
    if length > opts.max_chars:
        add(
            "long-sentence",
            f"句子 {length} 字（上限 {opts.max_chars}）。考虑拆句，保留条件、情态和必要信息。",
            f"{length} 字",
            len(sentence) - len(sentence.lstrip()),
        )

    lexical = lexical_text(sentence, opts)
    for match in NOMINALIZATION_RE.finditer(lexical):
        add(
            "nominalization",
            f"虚动词 + 名词（「{match.group(0)}」）。直接用动词。",
            match.group(0),
            match.start(),
        )

    for match in word_matches(lexical, MARKETING_WORDS):
        add("marketing-adjective", "检查是否为空泛赞美；技术术语和有依据的描述可以保留。",
            match.group(), match.start())
    for match in word_matches(lexical, EMPTY_PHRASES):
        add("empty-phrase", "检查是否有独立信息；保留范围限定和确定程度。",
            match.group(), match.start())

    for match in PASSIVE_RE.finditer(lexical):
        add(
            "passive-voice",
            "被动语态。说清施事并改用主动，除非施事未知或无关。",
            match.group(0),
            match.start(),
        )

    for match in COMPOUND_ASPECT_RE.finditer(lexical):
        add(
            "compound-aspect",
            "复合体貌。简单体貌够用就简化；表达当前状态、历史或情态时保留。",
            match.group(0),
            match.start(),
        )

    for match in VAGUE_RE.finditer(lexical):
        add(
            "vague-word",
            "检查范围是否足够清楚；没有依据时不要补造数量或条件。",
            match.group(0),
            match.start(),
        )

    for match in HALFWIDTH_RE.finditer(sentence):
        add(
            "halfwidth-punct",
            "中文句子里的半角标点。换成全角。",
            match.group(0),
            match.start(),
        )

    for match in DASH_JOIN_RE.finditer(sentence):
        add(
            "dash-join",
            "破折号连接。通常说明这句话该拆。",
            match.group(0),
            match.start(),
        )

    return findings


def analyze(text: str, path: str = "<stdin>", opts: Optional[Options] = None) -> List[Finding]:
    o = opts or Options()
    findings: List[Finding] = []
    # group_index -> member -> [line, col, count]
    rotation_hits: Dict[int, Dict[str, List[int]]] = {}
    prepared = mask_document(text) if o.format == "markdown" else text

    for line_no, raw in enumerate(prepared.splitlines(), 1):
        line = raw
        for cell_offset, cell in split_cells(line):
            mark = LIST_MARK_RE.match(cell)
            skip = mark.end() if mark else len(cell) - len(cell.lstrip())
            body = cell[skip:]
            if not body.strip():
                continue
            base = cell_offset + skip
            # 问号和叹号会被切句，需在切句前检查两侧的汉字。
            if "halfwidth-punct" not in o.disabled:
                for match in re.finditer(r"(?<=[\u4e00-\u9fff])[!?](?=[\u4e00-\u9fff])", body):
                    findings.append(Finding(path, line_no, base + match.start() + 1,
                                            "halfwidth-punct", o.severity("halfwidth-punct"),
                                            "中文句子里的半角标点。换成全角。", match.group()))
            for sent_offset, sentence in iter_sentences(body, base):
                findings.extend(sentence_findings(sentence, sent_offset, line_no, path, o))
                if "synonym-rotation" not in o.disabled:
                    for group_index, group in enumerate(SYNONYM_GROUPS):
                        for member in group:
                            positions = member_occurrences(lexical_text(sentence, o), member)
                            # “终端用户”中的“用户”不是另一次术语选择。
                            positions = [pos for pos in positions if not any(
                                len(other) > len(member) and
                                any(start <= pos and pos + len(member) <= start + len(other)
                                    for start in member_occurrences(sentence, other))
                                for other in group)]
                            if positions:
                                entry = rotation_hits.setdefault(group_index, {}).setdefault(
                                    member, [line_no, sent_offset + positions[0] + 1, 0]
                                )
                                entry[2] += len(positions)

    for group_index, members in sorted(rotation_hits.items()):
        if len(members) < 2:
            continue
        group = SYNONYM_GROUPS[group_index]
        # 保留出现次数最多的那个（并列时取组内顺序靠前的），其余算轮换。
        keeper = max(members.items(), key=lambda item: (item[1][2], -group.index(item[0])))[0]
        found = "、".join(f"{name}×{data[2]}" for name, data in members.items())
        for member, (line_no, col, _count) in sorted(members.items(), key=lambda item: item[1][:2]):
            if member == keeper:
                continue
            findings.append(
                Finding(
                    path=path,
                    line=line_no,
                    col=col,
                    rule="synonym-rotation",
                    severity=o.severity("synonym-rotation"),
                    message=f"术语候选：{found}。仅在指同一概念时统一；不同概念应保留区别。",
                    match=member,
                )
            )

    findings.sort(key=lambda f: (f.line, f.col, RULE_ORDER.index(f.rule)))
    return findings


def summarize(findings: Sequence[Finding], text: str, baseline: int) -> str:
    hard = sum(1 for f in findings if f.severity == HARD)
    total_chars = count_chars(text)
    rate = (len(findings) / total_chars * 100) if total_chars else 0.0
    return (
        f"共 {len(findings)} 处发现（硬违规 {hard}，baseline {baseline}），"
        f"受检文本 {total_chars} 字，每 100 字 {rate:.1f} 处\n"
        "情态（可能 / 也许 / 大概 / 倾向于）永不标记：置信度是内容。"
    )


def run(paths: Sequence[str], opts: Options, as_json: bool, stream) -> int:
    outputs: List[str] = []
    all_findings: List[Finding] = []
    combined: List[str] = []

    if paths:
        sources = []
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    sources.append((path, handle.read()))
            except (OSError, UnicodeError) as error:
                sys.stderr.write(f"{path}: 无法读取 UTF-8 文件：{error}\n")
                return 2
    else:
        sources = [("<stdin>", sys.stdin.read())]

    for path, text in sources:
        combined.append(mask_document(text) if opts.format == "markdown" else text)
        findings = analyze(text, path, opts)
        all_findings.extend(findings)
        for finding in findings:
            outputs.append(finding.render())
        if not as_json:
            hard = sum(1 for f in findings if f.severity == HARD)
            if hard > opts.baseline:
                outputs.append(f"→ {path}: {hard} 处硬违规（baseline 按全部输入合计）")
            else:
                outputs.append(f"→ {path}: 硬违规 {hard} 处（baseline 按全部输入合计）")

    if as_json:
        stream.write(json.dumps([f.as_dict() for f in all_findings], ensure_ascii=False, indent=2))
        stream.write("\n")
    else:
        for line in outputs:
            stream.write(line + "\n")
        stream.write(summarize(all_findings, "\n".join(combined), opts.baseline) + "\n")

    hard_total = sum(1 for f in all_findings if f.severity == HARD)
    return 1 if hard_total > opts.baseline else 0


def selftest() -> int:
    failures: List[str] = []
    clean = Options()

    def rules(text: str, opts: Options = clean, path: str = "<selftest>") -> List[str]:
        return [finding.rule for finding in analyze(text, path, opts)]

    def check(name: str, condition: bool, detail: str = "") -> None:
        if condition:
            print(f"  ok   {name}")
        else:
            failures.append(f"{name} {detail}")
            print(f"  FAIL {name} {detail}")

    print("受控中文 linter 自检：")
    check("干净文本没有发现", rules("打开配置文件。读取第三行。把结果写入日志。") == [])
    check("情态永不标记（可能已失败）", rules("请求可能已失败。") == [])
    check("代码块里的分号不算", rules("```\n先开票；再发货\n```") == [])
    check("行内代码被屏蔽", rules("用 `a；b` 分隔即可。") == [])
    check("分号被判硬违规", "semicolon" in rules("先开票；再发货。"))
    check("名词化被判", "nominalization" in rules("我们需要对日志进行分析。"))
    check("营销形容词被判", rules("这是一款无缝又强大的工具。").count("marketing-adjective") == 2)
    check("套话被判", "empty-phrase" in rules("需要注意的是，缓存会过期。"))
    check("超长句被判", "long-sentence" in rules("把" + "很长的说明" * 9 + "写完了。"))
    check(
        "同义轮换被判",
        "synonym-rotation" in rules("用户登录。用户退出。客户付款。"),
    )
    check("单一用词不报轮换", "synonym-rotation" not in rules("用户登录。用户退出。用户付款。"))
    check(
        "后缀挡住假命中（客户端 ≠ 客户）",
        "synonym-rotation" not in rules("客户端版本过旧。客户端重试。用户登录。"),
    )
    check("含糊词是建议类", "vague-word" in rules("在必要时做适当调整。"))
    check(
        "建议类不影响退出判定",
        all(
            finding.severity == ADVISORY
            for finding in analyze("日志被清空了。", "<selftest>", clean)
        ),
    )
    check("列表标记被剥掉", rules("- 打开文件。\n- 读取第三行。") == [])
    check("表格单元格分别检查", "semicolon" in rules("| 甲 | 先开票；再发货 |"))
    check("--max-chars 收紧后长句被判", "long-sentence" in rules("读取配置并写入日志。", Options(max_chars=5)))
    check(
        "disable 关得掉规则",
        "semicolon" not in rules("先开票；再发货。", Options(disabled=frozenset({"semicolon"}))),
    )
    check(
        "baseline 容忍硬违规",
        run_quiet("先开票；再发货。\n", Options(baseline=1)) == 0,
    )
    check(
        "baseline 不足时退出码 1",
        run_quiet("先开票；再发货。\n", Options(baseline=0)) == 1,
    )

    if failures:
        print(f"selftest FAILED（{len(failures)} 项）")
        return 1
    print("selftest OK")
    return 0


def run_quiet(text: str, opts: Options) -> int:
    original = sys.stdin
    sys.stdin = io.StringIO(text)
    try:
        return run([], opts, False, io.StringIO())
    finally:
        sys.stdin = original


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ste-lint-zh.py",
        description="受控中文 linter：只查机械可判的规则，永不挑情态。",
    )
    parser.add_argument("files", nargs="*", help="要检查的文件；不给则读 stdin")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--max-chars", type=int, default=40, help="句长上限（默认 40；程序步骤建议 25）")
    parser.add_argument("--baseline", type=int, default=0, help="容忍的硬违规数（存量文档接入用）")
    parser.add_argument("--disable", default="", help="要关掉的规则名，逗号分隔")
    parser.add_argument("--profile", choices=("strict", "natural"), default="strict",
                        help="strict 保留硬规则；natural 全部作为建议")
    parser.add_argument("--format", choices=("markdown", "text"), default="markdown",
                        help="输入格式；text 不屏蔽 Markdown 标记")
    parser.add_argument("--allow", action="append", default=[], metavar="TERM",
                        help="术语白名单，可重复；不豁免句长和标点")
    parser.add_argument("--selftest", action="store_true", help="跑内置自检")
    parser.add_argument("--list-rules", action="store_true", help="列出规则与严重度")
    args = parser.parse_args(argv)
    if args.max_chars < 1 or args.baseline < 0:
        parser.error("--max-chars 必须为正数，--baseline 不能为负数")
    if any(not term or "\n" in term or "\r" in term for term in args.allow):
        parser.error("--allow 术语必须非空且不能跨行")
    return args


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if args.selftest:
        return selftest()
    if args.list_rules:
        for rule in RULE_ORDER:
            print(f"{Options(profile=args.profile).severity(rule):9} {rule}")
        return 0

    disabled = frozenset(name.strip() for name in args.disable.split(",") if name.strip())
    unknown = sorted(name for name in disabled if name not in RULE_SEVERITY)
    if unknown:
        print(f"未知规则名：{', '.join(unknown)}（用 --list-rules 看全部）", file=sys.stderr)
        return 2

    opts = Options(max_chars=args.max_chars, baseline=args.baseline, disabled=disabled,
                   profile=args.profile, allowed=tuple(args.allow), format=args.format)
    return run(args.files, opts, args.json, sys.stdout)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
