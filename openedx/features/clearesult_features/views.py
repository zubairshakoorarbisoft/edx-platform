from django.views.generic.base import TemplateView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class AuthenticationView(TemplateView):

    template_name = "authentication.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_url = self.request.build_absolute_uri().split('/clearesult')[0]
        context['favicon'] = '{}{}'.format(base_url, configuration_helpers.get_value('FAVICON'))
        context['logo'] = '{}{}'.format(base_url, configuration_helpers.get_value('LOGO'))
        context['platform_name'] = configuration_helpers.get_value('PLATFORM_NAME')
        return context
