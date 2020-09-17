import datetime

from django.views.generic.base import TemplateView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class LoginView(TemplateView):

    template_name = 'b2c_login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_url = self.request.build_absolute_uri().split('/clearesult')[0]
        _get_context_data(base_url, context)
        return context


class ResetPasswordView(TemplateView):

    template_name = 'b2c_reset_password.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_url = self.request.build_absolute_uri().split('/clearesult')[0]
        _get_context_data(base_url, context)
        return context


def _get_context_data(base_url, context):
    trade_ally_urls = configuration_helpers.get_value('TRADE_ALLY_URLS', {})
    context.update({
        'favicon': '{}{}'.format(base_url, configuration_helpers.get_value('FAVICON')),
        'logo': '{}{}'.format(base_url, configuration_helpers.get_value('LOGO')),
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME'),
        'style_sheet_path': '{}{}'.format(base_url, configuration_helpers.get_value('STYLE_SHEET_PATH')),
        'ta_home': trade_ally_urls.get('HOME', ''),
        'ta_contact_us': trade_ally_urls.get('CONTACT_US', ''),
        'ta_become_ally': trade_ally_urls.get('BECOME_TA', ''),
        'ta_login': trade_ally_urls.get('LOGIN', ''),
        'ta_programe_resources': trade_ally_urls.get('PROGRAM_RESOURCES', ''),
        'ta_program_announcements': trade_ally_urls.get('PROGRAM_ANNOUNCEMENTS', ''),
        'ta_resource': trade_ally_urls.get('RESOURCE', ''),
        'ta_events': trade_ally_urls.get('EVENTS', ''),
        'ta_news': trade_ally_urls.get('NEWS', ''),
        'ta_training': trade_ally_urls.get('TRAINING', ''),
        'ta_faqs': trade_ally_urls.get('FAQs', ''),
        'banner_image': trade_ally_urls.get('BANNER_IMAGE', ''),
        'copyrights_year': datetime.datetime.now().year
    })
