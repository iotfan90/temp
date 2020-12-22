from __future__ import print_function

from datetime import datetime


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    return ''


class Command(object):
    pass
