"""
Fragments for rendering Journals.
"""
import logging
from urlparse import urljoin
from django.http import Http404
from django.template.loader import render_to_string
from django.utils.translation import get_language_bidi
from django.conf import settings

from web_fragments.fragment import Fragment
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.journals.api import JournalsApiClient, journals_enabled

logger = logging.getLogger(__name__)


class JournalsFragmentView(EdxFragmentView):
    """
    A fragment to program listing.
    """
    def render_to_fragment(self, request, **kwargs):
        """
        Render the journal listing fragment.
        """
        journals = self.get_journals(request)

        context = {
            'journals': journals,
        }

        print('\n\nBF - found journals=', journals)
        html = render_to_string('learner_dashboard/journals_fragment.html', context)
        journals_fragment = Fragment(html)
        self.add_fragment_resource_urls(journals_fragment)

        return journals_fragment

    def css_dependencies(self):
        """
        Returns list of CSS files that this view depends on.

        The helper function that it uses to obtain the list of CSS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        if get_language_bidi():
            return self.get_css_dependencies('style-learner-dashboard-rtl')
        else:
            return self.get_css_dependencies('style-learner-dashboard')

    def get_journals(self, request):
        """ View a list of journals which the user has or had access to"""
        #TODO: check assumption, list journals that user HAD access to but no longer does

        # import pdb; pdb.set_trace()
        user = request.user

        if not journals_enabled() or not user.is_authenticated():
            raise Http404

        journal_client = JournalsApiClient()
        journals = journal_client.get_journal_access(user)

        for journal in journals:
            journal['url'] = self.get_journal_about_page_url(slug=journal['journal']['journalaboutpage']['slug'])

        return journals

    def get_journal_about_page_url(self, slug=''):
        """
        Returns the url of a journal about page for the given journal slug.
        """
        return urljoin(settings.JOURNALS_ROOT_URL, slug)
