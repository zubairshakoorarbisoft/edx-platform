""" Journal Tab of Learner Dashboard views """
from edxmako.shortcuts import render_to_response
from openedx.features.journals.api import JournalsApiClient

def journal_listing(request):
    """ View a list of journals which the user has or had access to"""
    #TODO: check assumption, list journals that user HAD access to but no longer does

    journal_client = JournalsApiClient(user=request.user)
    response = journal_client.get_journal_access()

    context = {
        'response': response
    }

    return render_to_response('learner_dashboard/journal_dashboard.html', context)
