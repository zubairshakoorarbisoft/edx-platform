"""
A utility to translate file path to the actual paver command you want to use
"""
import re
from paver.easy import sh, path, task, cmdopts, needs, consume_args, call_task, no_help

BOKCHOY_PATTERN = "common/test/acceptance/tests/"
COMMON_LIB_PATTERN = "common/lib/"
COMMON_UNIT_TEST_PATTERN = "common/"
LETTUCE_LMS_PATTERN = "lms/djangoapps/courseware/features/"
LETTUCE_CMS_PATTERN = "cms/contentstore/features/"

CMS_DIR = "cms/"
LMS_DIR = "lms/"

@task
@consume_args
def tellme(args):

    if len(args) > 1:
        print "I see two arguments. Sorry but I can only look at one file. Exiting..."
        return
    if len(args) == 0:
        print "I don't see any arguments. Please give me the path to a test file."
        return
    testpath = args[0]

    if re.match(r".test.", testpath) or re.match(r"spec", testpath):
        print "It doesn't look like you're giving me a test file. Sorry; can't help you."

    if not (testpath.endswith('.py') or testpath.endswith('.js') or testpath.endswith('.feature')):
        print "I need a path that ends with .py, .js, or .feature"
        return

    if testpath.startswith(BOKCHOY_PATTERN):
        whatyouwant = re.split(BOKCHOY_PATTERN, testpath)[1]
        print "You may want bokchoy. Say something like\n\tpaver test_bokchoy -t " + whatyouwant
        return

    if testpath.startswith(COMMON_LIB_PATTERN):
        print "You probably want\n\tpaver test_lib " + testpath
        return

    if testpath.startswith(COMMON_UNIT_TEST_PATTERN):
        print "Looks like you're running a django-dependent test in common. You really want to use something like:\n\tpaver test_system -s lms -t " + testpath
        return

    if testpath.startswith(LETTUCE_LMS_PATTERN):
        print "Looks like lettuce. You want to run something like:\n\tpaver test_acceptance -s lms --extra_args=\"" + testpath + "\""
        return

    if testpath.startswith(LETTUCE_CMS_PATTERN):
        print "Looks like lettuce. You want to run something like:\n\tpaver test_acceptance -s cms --extra_args=\"" + testpath + "\""
        return

    if testpath.startswith(CMS_DIR) or testpath.startswith(LMS_DIR):
        if testpath.endswith(".js"):
            print "I see js tests. You will want something like: \n\tpaver test_js_dev -s " + testpath[0:3]
            return
        else:
            print "You want something like:\n\tpaver test_system -s " + testpath[0:3] + " -t " + testpath

