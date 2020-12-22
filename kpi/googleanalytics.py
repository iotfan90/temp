from __future__ import unicode_literals
import httplib2

from collections import defaultdict
from datetime import date, datetime
from django.conf import settings
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


class GaWrapper(object):
    def __init__(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            settings.GA_KEYFILE,
            scopes='https://www.googleapis.com/auth/analytics.readonly')
        http = credentials.authorize(httplib2.Http(), )
        self.service = build('analytics', 'v3', http=http, )

    def get_sessions(self, dt_start=None, dt_end=None):
        dt_start = dt_start or date.today()
        dt_end = dt_end or dt_start
        data = self.service.data().ga().get(
            ids=settings.GA_PROFILE_ID,
            start_date=dt_start.strftime('%Y-%m-%d'),
            end_date=dt_end.strftime('%Y-%m-%d'),
            metrics='ga:sessions',
            dimensions='ga:date,ga:hour',
        ).execute()
        result = defaultdict(dict)
        if data and 'rows' in data:
            for st_date, st_hour, st_session in data['rows']:
                dt = datetime.strptime(st_date, '%Y%m%d').date()
                n_hour, n_sessions = int(st_hour), int(st_session)
                result[dt][n_hour] = n_sessions
        return result

    def get_kpi_sessions_by_hour(self, dt_start=None, dt_end=None):
        dt_start = dt_start or date.today()
        dt_end = dt_end or dt_start
        data = self.service.data().ga().get(
            ids=settings.GA_PROFILE_ID,
            start_date=dt_start.strftime('%Y-%m-%d'),
            end_date=dt_end.strftime('%Y-%m-%d'),
            metrics='ga:sessions',
            dimensions='ga:date,ga:hour',
        ).execute()
        result = dict()
        if data and 'rows' in data:
            for st_date, st_hour, st_sessions in data['rows']:
                key = '%s-%s-%s %s' % (st_date[:4], st_date[4:6], st_date[6:],
                                       st_hour,)
                result[key] = int(st_sessions)
        return result

    def get_kpi_sessions_by_date(self, dt_start=None, dt_end=None):
        dt_start = dt_start or date.today()
        dt_end = dt_end or dt_start
        data = self.service.data().ga().get(
            ids=settings.GA_PROFILE_ID,
            start_date=dt_start.strftime('%Y-%m-%d'),
            end_date=dt_end.strftime('%Y-%m-%d'),
            metrics='ga:sessions',
            dimensions='ga:date',
        ).execute()
        result = dict()
        if data and 'rows' in data:
            for st_date, st_sessions in data['rows']:
                key = '%s-%s-%s' % (st_date[:4], st_date[4:6], st_date[6:], )
                result[key] = int(st_sessions)
        return result

    def get_kpi_sessions_by_month(self, dt_start=None, dt_end=None):
        dt_end = dt_end or date.today()
        dt_start = dt_start or dt_end.replace(day=1, month=1)
        data = self.service.data().ga().get(
            ids=settings.GA_PROFILE_ID,
            start_date=dt_start.strftime('%Y-%m-%d'),
            end_date=dt_end.strftime('%Y-%m-%d'),
            metrics='ga:sessions',
            dimensions='ga:year,ga:month',
        ).execute()
        import json
        print json.dumps(data, indent=2)
        result = dict()
        if data and 'rows' in data:
            for st_year, st_month, st_sessions in data['rows']:
                key = '%s-%s' % (st_year, st_month, )
                result[key] = int(st_sessions)
        return result

