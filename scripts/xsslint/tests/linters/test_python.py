# -*- coding: utf-8 -*-
import textwrap

from ddt import data, ddt

from xsslint.linters.python import PythonLinter
from xsslint.reporting import FileResults
from xsslint.rules import Rules

from . import TestLinter


@ddt
class TestPythonLinter(TestLinter):
    """
    Test PythonLinter
    """
    @data(
        {'template': 'm = "Plain text " + message + "plain text"', 'rule': None},
        {'template': 'm = "檌檒濦 " + message + "plain text"', 'rule': None},
        {'template': '  # m = "<p>" + commentedOutMessage + "</p>"', 'rule': None},
        {'template': 'm = "<p>" + message + "</p>"', 'rule': [Rules.python_concat_html, Rules.python_concat_html]},
        {'template': 'm = " <p> " + message + " </p> "', 'rule': [Rules.python_concat_html, Rules.python_concat_html]},
        {'template': 'm = " <p> " + message + " broken string', 'rule': Rules.python_parse_error},
    )
    def test_concat_with_html(self, data):
        """
        Test check_python_file_is_safe with concatenating strings and HTML
        """
        linter = PythonLinter()
        results = FileResults('')

        linter.check_python_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    def test_check_python_expression_display_name(self):
        """
        Test _check_python_file_is_safe with display_name_with_default_escaped
        fails.
        """
        linter = PythonLinter()
        results = FileResults('')

        python_file = textwrap.dedent("""
            context = {
                'display_name': self.display_name_with_default_escaped,
            }
        """)

        linter.check_python_file_is_safe(python_file, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.python_deprecated_display_name)

    def test_check_custom_escaping(self):
        """
        Test _check_python_file_is_safe fails when custom escapins is used.
        """
        linter = PythonLinter()
        results = FileResults('')

        python_file = textwrap.dedent("""
            msg = mmlans.replace('<', '&lt;')
        """)

        linter.check_python_file_is_safe(python_file, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.python_custom_escape)

    @data(
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {span_start}text{span_end}").format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )
                """),
            'rule': None
        },
        {
            'python':
                textwrap.dedent("""
                    msg = "Mixed {span_start}text{span_end}".format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )
                """),
            'rule': Rules.python_requires_html_or_text
        },
        {
            'python':
                textwrap.dedent("""
                    msg = "Mixed {span_start}{text}{span_end}".format(
                        span_start=HTML("<span>"),
                        text=Text("This should still break."),
                        span_end=HTML("</span>"),
                    )
                """),
            'rule': Rules.python_requires_html_or_text
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {link_start}text{link_end}".format(
                        link_start=HTML("<a href='{}'>").format(url),
                        link_end=HTML("</a>"),
                    ))
                """),
            'rule': [Rules.python_close_before_format, Rules.python_requires_html_or_text]
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {link_start}text{link_end}").format(
                        link_start=HTML("<a href='{}'>".format(url)),
                        link_end=HTML("</a>"),
                    )
                """),
            'rule': Rules.python_close_before_format
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {link_start}text{link_end}".format(
                        link_start=HTML("<a href='{}'>".format(HTML('<b>'))),
                        link_end=HTML("</a>"),
                    ))
                """),
            'rule':
                [
                    Rules.python_close_before_format,
                    Rules.python_requires_html_or_text,
                    Rules.python_close_before_format,
                    Rules.python_requires_html_or_text
                ]
        },
        {
            'python':
                textwrap.dedent("""
                    msg = "Mixed {span_start}text{span_end}".format(
                        span_start="<span>",
                        span_end="</span>",
                    )
                """),
            'rule': [Rules.python_wrap_html, Rules.python_wrap_html]
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text(_("String with multiple lines "
                        "{link_start}unenroll{link_end} "
                        "and final line")).format(
                            link_start=HTML(
                                '<a id="link__over_multiple_lines" '
                                'data-course-id="{course_id}" '
                                'href="#test-modal">'
                            ).format(
                                # Line comment with ' to throw off parser
                                course_id=course_overview.id
                            ),
                            link_end=HTML('</a>'),
                    )
                """),
            'rule': None
        },
        {
            'python': "msg = '<span></span>'",
            'rule': None
        },
        {
            'python': "msg = HTML('<span></span>')",
            'rule': None
        },
        {
            'python': r"""msg = '<a href="{}"'.format(url)""",
            'rule': Rules.python_wrap_html
        },
        {
            'python': r"""msg = '{}</p>'.format(message)""",
            'rule': Rules.python_wrap_html
        },
        {
            'python': r"""r'regex with {} and named group(?P<id>\d+)?$'.format(test)""",
            'rule': None
        },
        {
            'python': r"""msg = '<a href="%s"' % url""",
            'rule': Rules.python_interpolate_html
        },
        {
            'python':
                textwrap.dedent("""
                    def __repr__(self):
                        # Assume repr implementations are safe, and not HTML
                        return '<CCXCon {}>'.format(self.title)
                """),
            'rule': None
        },
        {
            'python': r"""msg = '%s</p>' % message""",
            'rule': Rules.python_interpolate_html
        },
        {
            'python': "msg = HTML('<span></span>'",
            'rule': Rules.python_parse_error
        },
    )
    def test_check_python_with_text_and_html(self, data):
        """
        Test _check_python_file_is_safe tests for proper use of Text() and
        Html().

        """
        linter = PythonLinter()
        results = FileResults('')

        file_content = textwrap.dedent(data['python'])

        linter.check_python_file_is_safe(file_content, results)

        self._validate_data_rules(data, results)

    def test_check_python_with_text_and_html_mixed(self):
        """
        Test _check_python_file_is_safe tests for proper use of Text() and
        Html() for a Python file with a mix of rules.

        """
        linter = PythonLinter()
        results = FileResults('')

        file_content = textwrap.dedent("""
            msg1 = '<a href="{}"'.format(url)
            msg2 = "Mixed {link_start}text{link_end}".format(
                link_start=HTML("<a href='{}'>".format(url)),
                link_end="</a>",
            )
            msg3 = '<a href="%s"' % url
        """)

        linter.check_python_file_is_safe(file_content, results)

        results.violations.sort(key=lambda violation: violation.sort_key())

        self.assertEqual(len(results.violations), 5)
        self.assertEqual(results.violations[0].rule, Rules.python_wrap_html)
        self.assertEqual(results.violations[1].rule, Rules.python_requires_html_or_text)
        self.assertEqual(results.violations[2].rule, Rules.python_close_before_format)
        self.assertEqual(results.violations[3].rule, Rules.python_wrap_html)
        self.assertEqual(results.violations[4].rule, Rules.python_interpolate_html)

    @data(
        {
            'python':
                """
                    response_str = textwrap.dedent('''
                        <div>
                            <h3 class="result">{response}</h3>
                        </div>
                    ''').format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 2,
        },
        {
            'python':
                """
                def function(self):
                    '''
                    Function comment.
                    '''
                    response_str = textwrap.dedent('''
                        <div>
                            <h3 class="result">{response}</h3>
                        </div>
                    ''').format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 6,
        },
        {
            'python':
                """
                def function(self):
                    '''
                    Function comment.
                    '''
                    response_str = '''<h3 class="result">{response}</h3>'''.format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 6,
        },
        {
            'python':
                """
                def function(self):
                    '''
                    Function comment.
                    '''
                    response_str = textwrap.dedent('''
                        <div>
                            \"\"\" Do we care about a nested triple quote? \"\"\"
                            <h3 class="result">{response}</h3>
                        </div>
                    ''').format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 6,
        },
    )
    def test_check_python_with_triple_quotes(self, data):
        """
        Test _check_python_file_is_safe with triple quotes.

        """
        linter = PythonLinter()
        results = FileResults('')

        file_content = textwrap.dedent(data['python'])

        linter.check_python_file_is_safe(file_content, results)

        self._validate_data_rules(data, results)
        self.assertEqual(results.violations[0].start_line, data['start_line'])
