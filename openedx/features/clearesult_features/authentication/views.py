from django.views.generic.base import View
from django.shortcuts import redirect

from edxmako.shortcuts import render_to_response

from openedx.features.clearesult_features.authentication.forms import SiteSecurityCodeForm
from openedx.features.clearesult_features.authentication.utils import authenticate_site_session
from openedx.features.clearesult_features.authentication.permissions import non_site_authenticated_user_required


class SiteSecurityView(View):
    template_name = 'clearesult/site_security_code.html'

    @non_site_authenticated_user_required
    def get(self, request):
        form = SiteSecurityCodeForm()
        return render_to_response(self.template_name, {'form': form})

    @non_site_authenticated_user_required
    def post(self, request):
        form = SiteSecurityCodeForm(request.POST)

        if form.is_valid():
            authenticate_site_session(request)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('/dashboard')

        return render_to_response(self.template_name, {'form': form})
