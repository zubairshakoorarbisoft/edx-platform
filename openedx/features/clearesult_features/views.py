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
    context['favicon'] = '{}{}'.format(base_url, configuration_helpers.get_value('FAVICON'))
    context['logo'] = '{}{}'.format(base_url, configuration_helpers.get_value('LOGO'))
    context['platform_name'] = configuration_helpers.get_value('PLATFORM_NAME')
    trade_ally_urls = configuration_helpers.get_value('TRADE_ALLY_URLS', {})
    context['ta_home'] = trade_ally_urls.get('HOME', '')
    context['ta_contact_us'] = trade_ally_urls.get('CONTACT_US', '')
    context['ta_become'] = trade_ally_urls.get('BECOME_TA', '')
    context['ta_login'] = trade_ally_urls.get('LOGIN', '')
    context['ta_programe_resources'] = trade_ally_urls.get('PROGRAM_RESOURCES', '')
    context['ta_program_announcements'] = trade_ally_urls.get('PROGRAM_ANNOUNCEMENTS', '')
    context['ta_resource'] = trade_ally_urls.get('RESOURCE', '')
    context['ta_events'] = trade_ally_urls.get('EVENTS', '')
    context['ta_news'] = trade_ally_urls.get('NEWS', '')
    context['ta_training'] = trade_ally_urls.get('TRAINING', '')
    context['ta_faqs'] = trade_ally_urls.get('FAQs', '')
