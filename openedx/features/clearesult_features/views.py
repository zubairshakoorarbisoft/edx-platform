from django.contrib.auth.decorators import login_required

from edxmako.shortcuts import render_to_response
from openedx.features.clearesult_features.authentication.permissions import local_admin_required


@login_required
def render_continuing_education(request):
    return render_to_response('clearesult/continuing_education.html', {'uses_bootstrap': True})


@login_required
@local_admin_required
def render_reports(request):
    return render_to_response('clearesult/reports.html', {'uses_bootstrap': True})


@login_required
@local_admin_required
def render_catalogs_manager(request):
    return render_to_response(
        'clearesult/catalogs_manager.html',
        {
            'uses_bootstrap': True,
            'is_superuser': 1 if request.user.is_superuser else 0,
        }
    )


@login_required
@local_admin_required
def render_groups_manager(request):
    return render_to_response('clearesult/groups_manager.html', {'uses_bootstrap': True})


@login_required
@local_admin_required
def render_group_catalogs_manager(request):
    return render_to_response('clearesult/group_catalogs_manager.html', {'uses_bootstrap': True})


@login_required
@local_admin_required
def render_admin_configurations(request):
    return render_to_response('clearesult/admin_configurations.html', {'uses_bootstrap': True})
