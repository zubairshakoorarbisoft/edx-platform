"""
A utility to translate file path to the actual paver command you want to use
"""
import re
from paver.easy import sh, path, task, cmdopts, needs, consume_args, call_task, no_help

BOKCHOY_PATTERN = "common/test/acceptance/tests"
COMMON_UNIT_TEST_PATTERN = "common/"


@task
@consume_args
def tellme(args):

    if len(args) > 1:
        print "I see two arguments. Sorry but I can only look at one path. Exiting..."
        return
    if len(args) == 0:
        print "I don't see any arguments. Please give me the path to a test file."
        return
    testpath = args[0]

    if testpath.startswith("common/test/acceptance/tests"):
        whatyouwant = testpath.strip("common/test/acceptance/tests")
        print "You want bokchoy. Say something like\n\tpaver test_bokchoy -t " + whatyouwant


    print args[0]
    print args