import os
import re

from xsslint.linters import BaseLinter
from xsslint.reporting import ExpressionRuleViolation, FileResults
from xsslint.rules import Rules
from xsslint.utils import Expression


class UnderscoreTemplateLinter(BaseLinter):
    """
    The linter for Underscore.js template files.
    """
    def __init__(self, skip_dirs=None):
        """
        Init method.
        """
        super(UnderscoreTemplateLinter, self).__init__()
        self._skip_underscore_dirs = skip_dirs or ()

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is an Underscore template file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential underscore file

        Returns:
            The file results containing any violations.

        """
        full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(full_path)

        if not self._is_valid_directory(self._skip_underscore_dirs, directory):
            return results

        if not file_name.lower().endswith('.underscore'):
            return results

        return self._load_and_check_file_is_safe(full_path, self.check_underscore_file_is_safe, results)

    def check_underscore_file_is_safe(self, underscore_template, results):
        """
        Checks for violations in an Underscore.js template.

        Arguments:
            underscore_template: The contents of the Underscore.js template.
            results: A file results objects to which violations will be added.

        """
        self._check_underscore_expressions(underscore_template, results)
        results.prepare_results(underscore_template)

    def _check_underscore_expressions(self, underscore_template, results):
        """
        Searches for Underscore.js expressions that contain violations.

        Arguments:
            underscore_template: The contents of the Underscore.js template.
            results: A list of results into which violations will be added.

        """
        expressions = self._find_unescaped_expressions(underscore_template)
        for expression in expressions:
            if not self._is_safe_unescaped_expression(expression):
                results.violations.append(ExpressionRuleViolation(
                    Rules.underscore_not_escaped, expression
                ))

    def _is_safe_unescaped_expression(self, expression):
        """
        Determines whether an expression is safely escaped, even though it is
        using the expression syntax that doesn't itself escape (i.e. <%= ).

        In some cases it is ok to not use the Underscore.js template escape
        (i.e. <%- ) because the escaping is happening inside the expression.

        Safe examples::

            <%= HtmlUtils.ensureHtml(message) %>
            <%= _.escape(message) %>

        Arguments:
            expression: The Expression being checked.

        Returns:
            True if the Expression has been safely escaped, and False otherwise.

        """
        if expression.expression_inner.startswith('HtmlUtils.'):
            return True
        if expression.expression_inner.startswith('_.escape('):
            return True
        return False

    def _find_unescaped_expressions(self, underscore_template):
        """
        Returns a list of unsafe expressions.

        At this time all expressions that are unescaped are considered unsafe.

        Arguments:
            underscore_template: The contents of the Underscore.js template.

        Returns:
            A list of Expressions.
        """
        unescaped_expression_regex = re.compile("<%=.*?%>", re.DOTALL)

        expressions = []
        for match in unescaped_expression_regex.finditer(underscore_template):
            expression = Expression(
                match.start(), match.end(), template=underscore_template, start_delim="<%=", end_delim="%>"
            )
            expressions.append(expression)
        return expressions


