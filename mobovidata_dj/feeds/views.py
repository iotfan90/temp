from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from .tasks import make_feeds


@login_required()
def generate_feeds(request):
    """
    Generates product feeds at the click of a button
    :param request: http request
    :return: http response of credentials
    """
    if request.method == 'POST':
        make_feeds.delay()
        return render_to_response(
            'feeds.html',
            context_instance=RequestContext(request)
        )
    else:
        return render_to_response(
            'feeds.html',
            context_instance=RequestContext(request)
        )
