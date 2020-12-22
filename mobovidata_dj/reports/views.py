import mimetypes
import os

from django.http import Http404, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from wsgiref.util import FileWrapper

from .models import ReportQuery


@login_required
def export_csv(request, pk):
    try:
        obj = ReportQuery.objects.get(pk=pk)
    except ReportQuery.DoesNotExist:
        raise Http404
    exc = obj.execute(target='download')
    chunk_size = 8192
    StreamingHttpResponse(content_type='text/csv')
    response = StreamingHttpResponse(FileWrapper(open(exc.full_path), chunk_size),
                           content_type=mimetypes.guess_type(exc.full_path)[0])
    response['Content-Length'] = os.path.getsize(exc.full_path)
    response['Content-Disposition'] = 'attachment; filename="%s"'%exc.filename

    return response
