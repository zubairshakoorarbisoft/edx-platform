""" Journal Tab of Learner Dashboard views """
from django.http import Http404
from django.template.loader import render_to_string

from web_fragments.fragment import Fragment

from edxmako.shortcuts import render_to_response
from openedx.features.journals.api import JournalsApiClient, journals_enabled
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


def journal_listing(request):
    """ View a list of journals which the user has or had access to"""
    #TODO: check assumption, list journals that user HAD access to but no longer does

    # import pdb; pdb.set_trace()
    journals_fragment = JournalsFragmentsView().render_to_fragment(request)

    context = {
        'journals_fragment': journals_fragment,
    }

    return render_to_response('learner_dashboard/journal_dashboard.html', context)


class JournalsFragmentsView(EdxFragmentView):
    """
    A fragment to journal listing.
    """
    def render_to_fragment(self, request, **kwargs):
        """
        Render the journal listing fragment.
        """
        user = request.user

        if not journals_enabled() or not user.is_authenticated():
            raise Http404

        journal_client = JournalsApiClient(user=user)
        journals = journal_client.get_journal_access()

        context = {
            'journals': journals
        }
        html = render_to_string('dashboard/journals_fragment.html', context)
        journals_fragment = Fragment(html)
        self.add_fragment_resource_urls(journals_fragment)

        return journals_fragment
