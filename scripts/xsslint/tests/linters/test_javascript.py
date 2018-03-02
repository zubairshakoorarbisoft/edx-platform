# -*- coding: utf-8 -*-
from ddt import data, ddt

from xsslint.linters.javascript import JavaScriptLinter
from xsslint.linters.underscore import UnderscoreTemplateLinter
from xsslint.reporting import FileResults
from xsslint.rules import Rules
from xsslint.utils import ParseString

from . import TestLinter


def _build_javascript_linter():
    return JavaScriptLinter(
        underscore_linter=UnderscoreTemplateLinter()
    )


@ddt
class TestJavaScriptLinter(TestLinter):
    """
    Test JavaScriptLinter
    """
    @data(
        {'template': 'var m = "Plain text " + message + "plain text"', 'rule': None},
        {'template': 'var m = "檌檒濦 " + message + "plain text"', 'rule': None},
        {
            'template':
                ("""$email_header.append($('<input>', type: "button", name: "copy-email-body-text","""
                 """ value: gettext("Copy Email To Editor"), id: 'copy_email_' + email_id))"""),
            'rule': None
        },
        {'template': 'var m = "<p>" + message + "</p>"', 'rule': Rules.javascript_concat_html},
        {
            'template': r'var m = "<p>\"escaped quote\"" + message + "\"escaped quote\"</p>"',
            'rule': Rules.javascript_concat_html
        },
        {'template': '  // var m = "<p>" + commentedOutMessage + "</p>"', 'rule': None},
        {'template': 'var m = " <p> " + message + " </p> "', 'rule': Rules.javascript_concat_html},
        {'template': 'var m = " <p> " + message + " broken string', 'rule': Rules.javascript_concat_html},
    )
    def test_concat_with_html(self, data):
        """
        Test check_javascript_file_is_safe with concatenating strings and HTML
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)
        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.append( test.render().el )', 'rule': None},
        {'template': 'test.append(test.render().el)', 'rule': None},
        {'template': 'test.append(test.render().$el)', 'rule': None},
        {'template': 'test.append(testEl)', 'rule': None},
        {'template': 'test.append($test)', 'rule': None},
        # plain text is ok because any & will be escaped, and it stops false
        # negatives on some other objects with an append() method
        {'template': 'test.append("plain text")', 'rule': None},
        {'template': 'test.append("<div/>")', 'rule': Rules.javascript_jquery_append},
        {'template': 'graph.svg.append("g")', 'rule': None},
        {'template': 'test.append( $( "<div>" ) )', 'rule': None},
        {'template': 'test.append($("<div>"))', 'rule': None},
        {'template': 'test.append($("<div/>"))', 'rule': None},
        {'template': 'test.append(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'HtmlUtils.append($el, someHtml)', 'rule': None},
        {'template': 'test.append("fail on concat" + test.render().el)', 'rule': Rules.javascript_jquery_append},
        {'template': 'test.append("fail on concat" + testEl)', 'rule': Rules.javascript_jquery_append},
        {'template': 'test.append(message)', 'rule': Rules.javascript_jquery_append},
    )
    def test_jquery_append(self, data):
        """
        Test check_javascript_file_is_safe with JQuery append()
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.prepend( test.render().el )', 'rule': None},
        {'template': 'test.prepend(test.render().el)', 'rule': None},
        {'template': 'test.prepend(test.render().$el)', 'rule': None},
        {'template': 'test.prepend(testEl)', 'rule': None},
        {'template': 'test.prepend($test)', 'rule': None},
        {'template': 'test.prepend("text")', 'rule': None},
        {'template': 'test.prepend( $( "<div>" ) )', 'rule': None},
        {'template': 'test.prepend($("<div>"))', 'rule': None},
        {'template': 'test.prepend($("<div/>"))', 'rule': None},
        {'template': 'test.prepend(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'HtmlUtils.prepend($el, someHtml)', 'rule': None},
        {'template': 'test.prepend("broken string)', 'rule': Rules.javascript_jquery_prepend},
        {'template': 'test.prepend("fail on concat" + test.render().el)', 'rule': Rules.javascript_jquery_prepend},
        {'template': 'test.prepend("fail on concat" + testEl)', 'rule': Rules.javascript_jquery_prepend},
        {'template': 'test.prepend(message)', 'rule': Rules.javascript_jquery_prepend},
    )
    def test_jquery_prepend(self, data):
        """
        Test check_javascript_file_is_safe with JQuery prepend()
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.unwrap(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.wrap(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.wrapAll(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.wrapInner(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.after(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.before(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.replaceAll(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.replaceWith(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.replaceWith(edx.HtmlUtils.HTML(htmlString).toString())', 'rule': None},
        {'template': 'test.unwrap(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.wrap(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.wrapAll(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.wrapInner(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.after(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.before(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.replaceAll(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.replaceWith(anything)', 'rule': Rules.javascript_jquery_insertion},
    )
    def test_jquery_insertion(self, data):
        """
        Test check_javascript_file_is_safe with JQuery insertion functions
        other than append(), prepend() and html() that take content as an
        argument (e.g. before(), after()).
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': '  element.parentNode.appendTo(target);', 'rule': None},
        {'template': '  test.render().el.appendTo(target);', 'rule': None},
        {'template': '  test.render().$el.appendTo(target);', 'rule': None},
        {'template': '  test.$element.appendTo(target);', 'rule': None},
        {'template': '  test.testEl.appendTo(target);', 'rule': None},
        {'template': '$element.appendTo(target);', 'rule': None},
        {'template': 'el.appendTo(target);', 'rule': None},
        {'template': 'testEl.appendTo(target);', 'rule': None},
        {'template': 'testEl.prependTo(target);', 'rule': None},
        {'template': 'testEl.insertAfter(target);', 'rule': None},
        {'template': 'testEl.insertBefore(target);', 'rule': None},
        {'template': 'anycall().appendTo(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.appendTo(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.prependTo(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.insertAfter(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.insertBefore(target)', 'rule': Rules.javascript_jquery_insert_into_target},
    )
    def test_jquery_insert_to_target(self, data):
        """
        Test check_javascript_file_is_safe with JQuery insert to target
        functions that take a target as an argument, like appendTo() and
        prependTo().
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.html()', 'rule': None},
        {'template': 'test.html( )', 'rule': None},
        {'template': "test.html( '' )", 'rule': None},
        {'template': "test.html('')", 'rule': None},
        {'template': 'test.html("")', 'rule': None},
        {'template': 'test.html(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'HtmlUtils.setHtml($el, someHtml)', 'rule': None},
        {'template': 'test.html("any string")', 'rule': Rules.javascript_jquery_html},
        {'template': 'test.html("broken string)', 'rule': Rules.javascript_jquery_html},
        {'template': 'test.html("檌檒濦")', 'rule': Rules.javascript_jquery_html},
        {'template': 'test.html(anything)', 'rule': Rules.javascript_jquery_html},
    )
    def test_jquery_html(self, data):
        """
        Test check_javascript_file_is_safe with JQuery html()
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)
        self._validate_data_rules(data, results)

    @data(
        {'template': 'StringUtils.interpolate()', 'rule': None},
        {'template': 'HtmlUtils.interpolateHtml()', 'rule': None},
        {'template': 'interpolate(anything)', 'rule': Rules.javascript_interpolate},
    )
    def test_javascript_interpolate(self, data):
        """
        Test check_javascript_file_is_safe with interpolate()
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': '_.escape(message)', 'rule': None},
        {'template': 'anything.escape(message)', 'rule': Rules.javascript_escape},
    )
    def test_javascript_interpolate(self, data):
        """
        Test check_javascript_file_is_safe with interpolate()
        """
        linter = _build_javascript_linter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)


