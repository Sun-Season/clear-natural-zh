"""验证误报边界、原文位置与命令行行为。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'ste-lint-zh.py'
spec = importlib.util.spec_from_file_location('ste_lint', SCRIPT)
lint = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lint
spec.loader.exec_module(lint)


class LinterTests(unittest.TestCase):
    def findings(self, text, **options):
        return lint.analyze(text, opts=lint.Options(**options))

    def rules(self, text, **options):
        return [f.rule for f in self.findings(text, **options)]

    def cli(self, *args, text=''):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=text,
                              text=True, capture_output=True)

    def test_comment_marker_in_inline_code(self):
        self.assertEqual(self.rules('用 `<!--` 标记。强大。'), ['marketing-adjective'])

    def test_comment_across_blank_lines(self):
        self.assertEqual(self.rules('<!--\n\n强大；\n-->'), [])

    def test_crlf_offsets(self):
        f = self.findings('```\r\n强大；\r\n```\r\n强大。')
        self.assertEqual([(x.line,x.col) for x in f],[(4,1)])

    def test_escaped_backtick(self):
        self.assertIn('marketing-adjective',self.rules(r'\`强大`'))

    def test_question_punctuation(self):
        self.assertIn('halfwidth-punct',self.rules('完成了吗?尚未完成。'))

    def test_code_not_in_summary_denominator(self):
        result = self.cli(text='```\n强大；\n```\n甲。')
        self.assertIn('受检文本 1 字',result.stdout)

    def test_fence_type(self):
        self.assertEqual(self.rules('```\n~~~\n强大；\n```'), [])

    def test_fence_length(self):
        self.assertEqual(self.rules('````\n```\n强大；\n````'), [])

    def test_longer_closer(self):
        self.assertEqual(self.rules('```\n强大；\n````\n强大。'), ['marketing-adjective'])

    def test_unclosed_fence(self):
        self.assertEqual(self.rules('~~~\n强大；'), [])

    def test_closer_cannot_have_text(self):
        self.assertEqual(self.rules('```\n```text\n强大；\n```'), [])

    def test_quote_fence(self):
        self.assertEqual(self.rules('> ```\n> 强大；\n> ```'), [])

    def test_front_matter(self):
        self.assertEqual(self.rules('---\ntitle: 强大；\n---\n打开文件。'), [])

    def test_unclosed_front_matter_not_hidden(self):
        self.assertIn('marketing-adjective', self.rules('---\n强大。'))

    def test_multiline_comment(self):
        self.assertEqual(self.rules('<!--\n强大；\n-->\n打开文件。'), [])

    def test_multibacktick_span(self):
        self.assertEqual(self.rules('用 ``a ` 强大； b`` 分隔。'), [])

    def test_multiline_span(self):
        self.assertEqual(self.rules('用 `a\n强大；` 分隔。'), [])

    def test_unmatched_backtick(self):
        self.assertIn('marketing-adjective', self.rules('用 ` 强大。'))

    def test_link_label_and_column(self):
        text = '查看 [强大工具](https://example.com/a(b);c)。'
        f = self.findings(text)
        self.assertEqual([(x.rule, x.col) for x in f], [('marketing-adjective', text.index('强大')+1)])

    def test_link_after_code(self):
        text = '`强大；` [强大](https://example.com)'
        self.assertEqual([f.col for f in self.findings(text)], [text.rindex('强大')+1])

    def test_reference_definition(self):
        self.assertEqual(self.rules('[id]: https://example.com/强大;'), [])

    def test_reference_label(self):
        self.assertEqual(self.rules('[打开文件][强大]。'), [])

    def test_url_followed_by_chinese(self):
        self.assertEqual(self.rules('https://example.com。强大。'), ['marketing-adjective'])

    def test_nested_terms(self):
        self.assertNotIn('synonym-rotation', self.rules('终端用户登录。'))

    def test_distinct_terms_advisory(self):
        findings = self.findings('用户登录。客户付款。')
        self.assertTrue(findings)
        self.assertTrue(all(f.severity == lint.ADVISORY for f in findings))
        self.assertNotIn('建议「', findings[0].message)

    def test_repeated_words(self):
        self.assertEqual([f.col for f in self.findings('强大又强大。')], [1,4])

    def test_overlapping_words(self):
        self.assertEqual([f.match for f in self.findings('极致体验。')], ['极致体验'])

    def test_allowlist(self):
        self.assertEqual(self.rules('采用闭环控制。', allowed=('闭环控制',)), [])
        self.assertEqual(self.rules('采用闭环控制，提供闭环服务。', allowed=('闭环控制',)), ['marketing-adjective'])

    def test_allowlist_does_not_hide_punctuation_or_length(self):
        self.assertIn('semicolon', self.rules('甲；乙', allowed=('甲；乙',)))
        self.assertIn('long-sentence', self.rules('闭环控制', allowed=('闭环控制',), max_chars=2))

    def test_natural_mode(self):
        f = self.findings('强大；用户和客户。', profile='natural')
        self.assertTrue(f)
        self.assertTrue(all(x.severity == lint.ADVISORY for x in f))
        self.assertEqual(self.cli('--profile','natural',text='强大；').returncode,0)

    def test_text_mode(self):
        self.assertIn('semicolon', self.rules('`甲；乙`', format='text'))

    def test_invalid_arguments(self):
        for args in [('--max-chars','0'),('--max-chars','-1'),('--baseline','-1'),
                     ('--allow',''),('--disable','typo')]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode,2)
                self.assertNotIn('Traceback',result.stderr)

    def test_json_schema_and_position(self):
        result = self.cli('--json',text='```\n强大；\n```\n  强大。')
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode,1)
        self.assertEqual((data[0]['line'],data[0]['col']),(4,3))
        self.assertEqual(set(data[0]),{'path','line','col','rule','severity','message','match'})

    def test_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'bad.md'; p.write_bytes(b'\xff')
            result = self.cli('--json',str(p))
        self.assertEqual(result.returncode,2)
        self.assertEqual(result.stdout,'')
        self.assertNotIn('Traceback',result.stderr)

    def test_missing_file(self):
        result = self.cli('--json','/nonexistent/ste-fixture.md')
        self.assertEqual(result.returncode,2)
        self.assertEqual(result.stdout,'')

    def test_baseline_is_global(self):
        with tempfile.TemporaryDirectory() as directory:
            files = [Path(directory)/f'{i}.md' for i in range(2)]
            for p in files: p.write_text('甲；乙。',encoding='utf-8')
            result = self.cli('--baseline','1', *map(str,files))
        self.assertEqual(result.returncode,1)
        self.assertNotIn('未超过',result.stdout)

    def test_modal_preservation(self):
        for text in ['请求可能已失败。','也许会失败。','有时会失败。','倾向于保留原样。']:
            self.assertEqual(self.findings(text),[])

    def test_escaped_table_pipe(self):
        self.assertEqual(lint.split_cells(r'甲\|乙|丙'),[(0,r'甲\|乙'),(5,'丙')])

    def test_source_offsets(self):
        text = '---\ntitle: x\n---\n[链接](https://example.com) 强大。\n`代码；` 需要注意的是，继续。'
        for f in self.findings(text):
            line=text.splitlines()[f.line-1]
            self.assertEqual(line[f.col-1:f.col-1+len(f.match)],f.match)


if __name__ == '__main__':
    unittest.main()
