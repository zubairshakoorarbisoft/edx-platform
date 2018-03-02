import os
import re

from xsslint.linters import BaseLinter
from xsslint.reporting import ExpressionRuleViolation, FileResults
from xsslint.rules import Rules
from xsslint.utils import Expression, ParseString, StringLines


class JavaScriptLinter(BaseLinter):
    """
    The linter for JavaScript and CoffeeScript files.
    """

    LINE_COMMENT_DELIM = "//"

    def __init__(self, underscore_linter, javascript_skip_dirs=None, coffeescript_skip_dirs=None):
        """
        Init method.
        """
        super(JavaScriptLinter, self).__init__()
        self.underscore_linter = underscore_linter
        self._skip_javascript_dirs = javascript_skip_dirs or ()
        self._skip_coffeescript_dirs = coffeescript_skip_dirs or ()

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a JavaScript file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential JavaScript file

        Returns:
            The file results containing any violations.

        """
        file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(file_full_path)

        if not results.is_file:
            return results

        if file_name.lower().endswith('.js') and not file_name.lower().endswith('.min.js'):
            skip_dirs = self._skip_javascript_dirs
        elif file_name.lower().endswith('.coffee'):
            skip_dirs = self._skip_coffeescript_dirs
        else:
            return results

        if not self._is_valid_directory(skip_dirs, directory):
            return results

        return self._load_and_check_file_is_safe(file_full_path, self.check_javascript_file_is_safe, results)

    def check_javascript_file_is_safe(self, file_contents, results):
        """
        Checks for violations in a JavaScript file.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        no_caller_check = None
        no_argument_check = None
        self._check_jquery_function(
            file_contents, "append", Rules.javascript_jquery_append, no_caller_check,
            self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "prepend", Rules.javascript_jquery_prepend, no_caller_check,
            self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "unwrap|wrap|wrapAll|wrapInner|after|before|replaceAll|replaceWith",
            Rules.javascript_jquery_insertion, no_caller_check, self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "appendTo|prependTo|insertAfter|insertBefore",
            Rules.javascript_jquery_insert_into_target, self._is_jquery_insert_caller_safe, no_argument_check, results
        )
        self._check_jquery_function(
            file_contents, "html", Rules.javascript_jquery_html, no_caller_check,
            self._is_jquery_html_argument_safe, results
        )
        self._check_javascript_interpolate(file_contents, results)
        self._check_javascript_escape(file_contents, results)
        self._check_concat_with_html(file_contents, Rules.javascript_concat_html, results)
        self.underscore_linter.check_underscore_file_is_safe(file_contents, results)
        results.prepare_results(file_contents, line_comment_delim=self.LINE_COMMENT_DELIM)

    def _get_expression_for_function(self, file_contents, function_start_match):
        """
        Returns an expression that matches the function call opened with
        function_start_match.

        Arguments:
            file_contents: The contents of the JavaScript file.
            function_start_match: A regex match representing the start of the function
                call (e.g. ".escape(").

        Returns:
            An Expression that best matches the function.

        """
        start_index = function_start_match.start()
        inner_start_index = function_start_match.end()
        result = self._find_closing_char_index(
            None, "(", ")", file_contents, start_index=inner_start_index
        )
        if result is not None:
            end_index = result['close_char_index'] + 1
            expression = Expression(
                start_index, end_index, template=file_contents, start_delim=function_start_match.group(), end_delim=")"
            )
        else:
            expression = Expression(start_index)
        return expression

    def _check_javascript_interpolate(self, file_contents, results):
        """
        Checks that interpolate() calls are safe.

        Only use of StringUtils.interpolate() or HtmlUtils.interpolateText()
        are safe.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "StringUtils.", because those are safe
        regex = re.compile(r"(?<!StringUtils).interpolate\(")
        for function_match in regex.finditer(file_contents):
            expression = self._get_expression_for_function(file_contents, function_match)
            results.violations.append(ExpressionRuleViolation(Rules.javascript_interpolate, expression))

    def _check_javascript_escape(self, file_contents, results):
        """
        Checks that only necessary escape() are used.

        Allows for _.escape(), although this shouldn't be the recommendation.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "_.", because those are safe
        regex = regex = re.compile(r"(?<!_).escape\(")
        for function_match in regex.finditer(file_contents):
            expression = self._get_expression_for_function(file_contents, function_match)
            results.violations.append(ExpressionRuleViolation(Rules.javascript_escape, expression))

    def _check_jquery_function(self, file_contents, function_names, rule, is_caller_safe, is_argument_safe, results):
        """
        Checks that the JQuery function_names (e.g. append(), prepend()) calls
        are safe.

        Arguments:
            file_contents: The contents of the JavaScript file.
            function_names: A pipe delimited list of names of the functions
                (e.g. "wrap|after|before").
            rule: The name of the rule to use for validation errors (e.g.
                Rules.javascript_jquery_append).
            is_caller_safe: A function to test if caller of the JQuery function
                is safe.
            is_argument_safe: A function to test if the argument passed to the
                JQuery function is safe.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "HtmlUtils.", because those are safe
        regex = re.compile(r"(?<!HtmlUtils).(?:{})\(".format(function_names))
        for function_match in regex.finditer(file_contents):
            is_violation = True
            expression = self._get_expression_for_function(file_contents, function_match)
            if expression.end_index is not None:
                start_index = expression.start_index
                inner_start_index = function_match.end()
                close_paren_index = expression.end_index - 1
                function_argument = file_contents[inner_start_index:close_paren_index].strip()
                if is_argument_safe is not None and is_caller_safe is None:
                    is_violation = is_argument_safe(function_argument) is False
                elif is_caller_safe is not None and is_argument_safe is None:
                    line_start_index = StringLines(file_contents).index_to_line_start_index(start_index)
                    caller_line_start = file_contents[line_start_index:start_index]
                    is_violation = is_caller_safe(caller_line_start) is False
                else:
                    raise ValueError("Must supply either is_argument_safe, or is_caller_safe, but not both.")
            if is_violation:
                results.violations.append(ExpressionRuleViolation(rule, expression))

    def _is_jquery_argument_safe_html_utils_call(self, argument):
        """
        Checks that the argument sent to a jQuery DOM insertion function is a
        safe call to HtmlUtils.

        A safe argument is of the form:
        - HtmlUtils.xxx(anything).toString()
        - edx.HtmlUtils.xxx(anything).toString()

        Arguments:
            argument: The argument sent to the jQuery function (e.g.
            append(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        # match on HtmlUtils.xxx().toString() or edx.HtmlUtils
        match = re.search(r"(?:edx\.)?HtmlUtils\.[a-zA-Z0-9]+\(.*\)\.toString\(\)", argument)
        return match is not None and match.group() == argument

    def _is_jquery_argument_safe(self, argument):
        """
        Check the argument sent to a jQuery DOM insertion function (e.g.
        append()) to check if it is safe.

        Safe arguments include:
        - the argument can end with ".el", ".$el" (with no concatenation)
        - the argument can be a single variable ending in "El" or starting with
            "$". For example, "testEl" or "$test".
        - the argument can be a single string literal with no HTML tags
        - the argument can be a call to $() with the first argument a string
            literal with a single HTML tag.  For example, ".append($('<br/>'))"
            or ".append($('<br/>'))".
        - the argument can be a call to HtmlUtils.xxx(html).toString()

        Arguments:
            argument: The argument sent to the jQuery function (e.g.
            append(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        match_variable_name = re.search("[_$a-zA-Z]+[_$a-zA-Z0-9]*", argument)
        if match_variable_name is not None and match_variable_name.group() == argument:
            if argument.endswith('El') or argument.startswith('$'):
                return True
        elif argument.startswith('"') or argument.startswith("'"):
            # a single literal string with no HTML is ok
            # 1. it gets rid of false negatives for non-jquery calls (e.g. graph.append("g"))
            # 2. JQuery will treat this as a plain text string and will escape any & if needed.
            string = ParseString(argument, 0, len(argument))
            if string.string == argument and "<" not in argument:
                return True
        elif argument.startswith('$('):
            # match on JQuery calls with single string and single HTML tag
            # Examples:
            #    $("<span>")
            #    $("<div/>")
            #    $("<div/>", {...})
            match = re.search(r"""\$\(\s*['"]<[a-zA-Z0-9]+\s*[/]?>['"]\s*[,)]""", argument)
            if match is not None:
                return True
        elif self._is_jquery_argument_safe_html_utils_call(argument):
            return True
        # check rules that shouldn't use concatenation
        elif "+" not in argument:
            if argument.endswith('.el') or argument.endswith('.$el'):
                return True
        return False

    def _is_jquery_html_argument_safe(self, argument):
        """
        Check the argument sent to the jQuery html() function to check if it is
        safe.

        Safe arguments to html():
        - no argument (i.e. getter rather than setter)
        - empty string is safe
        - the argument can be a call to HtmlUtils.xxx(html).toString()

        Arguments:
            argument: The argument sent to html() in code (i.e. html(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        if argument == "" or argument == "''" or argument == '""':
            return True
        elif self._is_jquery_argument_safe_html_utils_call(argument):
            return True
        return False

    def _is_jquery_insert_caller_safe(self, caller_line_start):
        """
        Check that the caller of a jQuery DOM insertion function that takes a
        target is safe (e.g. thisEl.appendTo(target)).

        If original line was::

            draggableObj.iconEl.appendTo(draggableObj.containerEl);

        Parameter caller_line_start would be:

            draggableObj.iconEl

        Safe callers include:
        - the caller can be ".el", ".$el"
        - the caller can be a single variable ending in "El" or starting with
            "$". For example, "testEl" or "$test".

        Arguments:
            caller_line_start: The line leading up to the jQuery function call.

        Returns:
            True if the caller is safe, and False otherwise.

        """
        # matches end of line for caller, which can't itself be a function
        caller_match = re.search(r"(?:\s*|[.])([_$a-zA-Z]+[_$a-zA-Z0-9])*$", caller_line_start)
        if caller_match is None:
            return False
        caller = caller_match.group(1)
        if caller is None:
            return False
        elif caller.endswith('El') or caller.startswith('$'):
            return True
        elif caller == 'el' or caller == 'parentNode':
            return True
        return False

    def _check_concat_with_html(self, file_contents, rule, results):
        """
        Checks that strings with HTML are not concatenated

        Arguments:
            file_contents: The contents of the JavaScript file.
            rule: The rule that was violated if this fails.
            results: A file results objects to which violations will be added.

        """
        lines = StringLines(file_contents)
        last_expression = None
        # Match quoted strings that starts with '<' or ends with '>'.
        regex_string_with_html = r"""
            {quote}                             # Opening quote.
                (
                   \s*<                         # Starts with '<' (ignoring spaces)
                   ([^{quote}]|[\\]{quote})*    # followed by anything but a closing quote.
                |                               # Or,
                   ([^{quote}]|[\\]{quote})*    # Anything but a closing quote
                   >\s*                         # ending with '>' (ignoring spaces)
                )
            {quote}                             # Closing quote.
        """
        # Match single or double quote.
        regex_string_with_html = "({}|{})".format(
            regex_string_with_html.format(quote="'"),
            regex_string_with_html.format(quote='"'),
        )
        # Match quoted HTML strings next to a '+'.
        regex_concat_with_html = re.compile(
            r"(\+\s*{string_with_html}|{string_with_html}\s*\+)".format(
                string_with_html=regex_string_with_html,
            ),
            re.VERBOSE
        )
        for match in regex_concat_with_html.finditer(file_contents):
            found_new_violation = False
            if last_expression is not None:
                last_line = lines.index_to_line_number(last_expression.start_index)
                # check if violation should be expanded to more of the same line
                if last_line == lines.index_to_line_number(match.start()):
                    last_expression = Expression(
                        last_expression.start_index, match.end(), template=file_contents
                    )
                else:
                    results.violations.append(ExpressionRuleViolation(
                        rule, last_expression
                    ))
                    found_new_violation = True
            else:
                found_new_violation = True
            if found_new_violation:
                last_expression = Expression(
                    match.start(), match.end(), template=file_contents
                )

        # add final expression
        if last_expression is not None:
            results.violations.append(ExpressionRuleViolation(
                rule, last_expression
            ))
