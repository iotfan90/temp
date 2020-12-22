import json
import logging
import pytz

from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connections
from django.views.generic import TemplateView
from djenga.profiling import start_timer, end_timer
from itertools import chain

from kpi.googleanalytics import GaWrapper
from modjento.models import SalesFlatOrder


logger = logging.getLogger(
    __name__ if not settings.DEBUG
    else '')


__all__ = [
    'HourlySalesTracker',
    'DailySalesTracker',
    'MonthlySalesTracker',
]


PACIFIC = pytz.timezone('US/Pacific')


class KpiReportView(LoginRequiredMixin, TemplateView):
    def __init__(self):
        super(KpiReportView, self).__init__()
        self.net_sales = []
        self.net_sales_ignoring_status = []
        self.total_cost = {}
        self.cursor = connections['magento'].cursor()
        self.end_date = datetime.now(PACIFIC).date()
        if settings.DEBUG:
            self.end_date = (SalesFlatOrder.objects.all().latest('entity_id')
                             .created_at.date())
        self.end_date += timedelta(days=1)
        self.sessions = {}
        self.start_date = None
        self.ga = GaWrapper()

    def calculate_conversion_rates(self, *args):
        for x in chain(*args):
            x['sessions'] = self.sessions.get(x['period'])
            if x['sessions']:
                x['conversion_rate'] = 100.0 * x['total_orders'] / x['sessions']
            else:
                x['conversion_rate'] = 0


class HourlySalesTracker(LoginRequiredMixin, TemplateView):
    template_name = 'hourly_sales_tracker.html'

    def __init__(self):
        super(HourlySalesTracker, self).__init__()
        self.net_sales = []
        self.net_sales_ignoring_status = []
        self.cursor = connections['magento'].cursor()
        self.end_date = datetime.now(PACIFIC).date()
        if settings.DEBUG:
            self.end_date = SalesFlatOrder.objects.all().latest(
                'entity_id'
            ).created_at.astimezone(PACIFIC).date()
        self.end_date += timedelta(days=1)
        self.start_date = self.end_date - timedelta(days=4)
        self.sessions = {}

    def load_sessions(self):
        ga = GaWrapper()
        self.sessions = ga.get_kpi_sessions_by_hour(self.start_date,
                                                    self.end_date)

    def load_hourly_report(self):
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(created_at, '%%Y-%%m-%%d %%H') as period,
                count(entity_id) as total_orders,
                sum(ifnull(base_grand_total, 0))
                as net_sales
            from sales_flat_order
            where created_at >= %s and created_at < %s
                and status in ('processing', 'complete', 'closed')
                and store_id=2
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'), ])
        self.net_sales = [{
            'period': period,
            'total_orders': total_orders,
            'net_sales': float(net_sales),
            'sessions': self.sessions.get(period, 0),
        } for period, total_orders, net_sales in self.cursor.fetchall()]
        self.cursor.execute("set time_zone='UTC';")

    def load_hourly_report_ignoring_status(self):
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(created_at, '%%Y-%%m-%%d %%H') as period,
                count(entity_id) as total_orders,
                sum(ifnull(base_grand_total, 0))
                as net_sales
            from sales_flat_order
            where created_at >= %s and created_at < %s
              and store_id=2
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'), ])
        self.net_sales_ignoring_status = [{
            'period': period,
            'total_orders': total_orders,
            'net_sales': float(net_sales),
            'sessions': self.sessions.get(period, 0),
        } for period, total_orders, net_sales in self.cursor.fetchall()]
        self.cursor.execute("set time_zone='UTC';")

    def extrapolate_sessions(self):
        past_dates = {}
        dt_now = datetime.now()
        for x in xrange(24):
            dt = dt_now - timedelta(hours=x)
            key = '%s' % (dt.strftime('%Y-%m-%d %H'),)
            past_dates[key] = []
            for y in xrange(1, 4):
                dt -= timedelta(days=1)
                past_dates[key].append('%s' % (dt.strftime('%Y-%m-%d %H'),))
        for data in (self.net_sales, self.net_sales_ignoring_status,):
            by_period = {}
            for x in data:
                by_period[x['period']] = x
                x['estimated'] = False
            for x in past_dates.iterkeys():
                mp = by_period.get(x)
                if not mp:
                    continue
                n_sessions = mp['sessions'] or 1
                d_conversion = 1.0 * mp['total_orders'] / n_sessions
                if d_conversion <= 0.10:
                    continue
                mp['estimated'] = True
                n_sessions = 0
                n_count = 0
                for y in past_dates[x]:
                    if y in by_period:
                        n_sessions += by_period[y]['sessions']
                        n_count += 1
                mp['sessions'] = n_sessions / n_count

    def calculate_conversion_rates(self):
        for x in chain(self.net_sales, self.net_sales_ignoring_status,):
            if x['sessions']:
                x['conversion_rate'] = 100.0 * x['total_orders'] / x['sessions']
            else:
                x['conversion_rate'] = 0

    def get_context_data(self, **kwargs):
        data = super(HourlySalesTracker, self).get_context_data(**kwargs)
        self.load_sessions()
        self.load_hourly_report()
        self.load_hourly_report_ignoring_status()
        self.extrapolate_sessions()
        self.calculate_conversion_rates()
        data.update({
            'net_sales': self.net_sales[::-1][:48],
            'net_sales_json': json.dumps(self.net_sales),
            'net_sales_ignoring_status': self.net_sales_ignoring_status[::-1][:48],
            'gross_sales_json': json.dumps(self.net_sales_ignoring_status),
        })
        return data


class DailySalesTracker(KpiReportView):
    template_name = 'daily_sales_tracker.html'

    def __init__(self):
        super(DailySalesTracker, self).__init__()
        self.net_sales = []
        self.net_sales_co = []
        self.net_sales_other = []
        self.start_date = self.end_date.replace(day=1)
        if (self.end_date - self.start_date).days < 15:
            self.start_date = self.end_date - timedelta(days=20)

    def load_sessions(self):
        dt_end = self.end_date - timedelta(days=1)
        self.sessions = self.ga.get_kpi_sessions_by_date(self.start_date,
                                                         dt_end)

    def load_daily_report(self):
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(created_at, '%%Y-%%m-%%d') as period,
                count(entity_id) as total_orders,
                sum(ifnull(base_grand_total, 0))
                    - sum(ifnull(base_total_refunded, 0))
                    - sum(ifnull(base_total_canceled, 0))
                    - sum(ifnull(base_tax_amount, 0))
                as net_sales
            from sales_flat_order sfo
            where created_at >= %s and created_at < %s
                and status in ('processing', 'complete', 'closed')
                and store_id <> 5
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'), ])
        self.net_sales = [{
            'period': period,
            'total_orders': total_orders,
            'net_sales': float(net_sales),
        } for period, total_orders, net_sales in self.cursor.fetchall()]
        self.cursor.execute("set time_zone='UTC';")

    def load_daily_report_co(self):
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(created_at, '%%Y-%%m-%%d') as period,
                count(entity_id) as total_orders,
                sum(ifnull(base_grand_total, 0))
                    - sum(ifnull(base_total_refunded, 0))
                    - sum(ifnull(base_total_canceled, 0))
                    - sum(ifnull(base_tax_amount, 0))
                as net_sales
            from sales_flat_order
            where created_at >= %s and created_at < %s
                and status in ('processing', 'complete', 'closed')
                and store_id=2
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'), ])
        self.net_sales_co = [{
            'period': period,
            'total_orders': total_orders,
            'net_sales': float(net_sales),
        } for period, total_orders, net_sales in self.cursor.fetchall()]
        self.cursor.execute("set time_zone='UTC';")

    def load_daily_report_other(self):
        mp_co = { x['period']: x for x in self.net_sales_co }
        self.net_sales_other = [{
            'period': x['period'],
            'total_orders': (x['total_orders'] -
                             mp_co.get(x['period'], {}).get('total_orders', 0)),
            'net_sales': (x['net_sales'] -
                          mp_co.get(x['period'], {}).get('net_sales', 0)),
        } for x in self.net_sales]

    def get_context_data(self, **kwargs):
        start_timer(logger, 'Daily report', True)
        self.load_sessions()
        self.load_daily_report()
        self.load_daily_report_co()
        self.load_daily_report_other()
        self.calculate_conversion_rates(self.net_sales_co)
        end_timer()
        return {
            'net_sales': self.net_sales[::-1],
            'net_sales_co': self.net_sales_co[::-1],
            'net_sales_other': self.net_sales_other[::-1],
        }


class MonthlySalesTracker(KpiReportView):
    template_name = 'monthly_sales_tracker.html'

    def __init__(self):
        super(MonthlySalesTracker, self).__init__()
        self.net_sales = []
        self.net_other_sales = []

    def load_cost(self):
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(sfo.created_at, '%%Y-%%m') as period,
                sum(sfo_item.base_cost * (sfo_item.qty_ordered - sfo_item.qty_canceled - sfo_item.qty_refunded))
                    as total_cost
            from sales_flat_order_item sfo_item
                 inner join sales_flat_order sfo
                 on sfo.entity_id=sfo_item.order_id
            where sfo.created_at >= %s and sfo.created_at < %s
                and sfo.status in ('processing', 'complete', 'closed')
                and sfo_item.parent_item_id is null
                and sfo.store_id <> 5
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'), ])
        self.total_cost = {
            period: float(total_cost)
            for period, total_cost in self.cursor.fetchall()
        }
        self.total_cost['Total'] = sum(self.total_cost.itervalues())
        self.cursor.execute("set time_zone='UTC';")

    def load_monthly_report(self):
        self.end_date = datetime.now(PACIFIC).date()
        # if settings.DEBUG:
        #     dt_end = datetime(2016, 6, 1).date()
        self.start_date = self.end_date.replace(month=1, day=1)
        if (self.end_date - self.start_date).days < 120:
            self.start_date = self.end_date - timedelta(days=120)
            self.start_date = self.start_date.replace(day=1)
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(created_at, '%%Y-%%m') as period,
                count(entity_id) as total_orders,
                sum(ifnull(base_grand_total, 0))
                    - sum(ifnull(base_total_refunded, 0))
                    - sum(ifnull(base_total_canceled, 0))
                    - sum(ifnull(base_tax_amount, 0))
                as net_sales,
                sum(ifnull(base_shipping_amount, 0)) as total_shipping
            from sales_flat_order
            where created_at >= %s
                and status in ('processing', 'complete', 'closed')
                and store_id <> 5
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
            ])
        n_total_orders, n_total_sales, n_total_shipping = 0, Decimal(0), Decimal(0)
        for period, total_orders, net_sales, total_shipping in self.cursor.fetchall():
            n_total_orders += total_orders
            n_total_sales += net_sales
            n_total_shipping += total_shipping
            self.net_sales.append({
                'period': period,
                'total_orders': total_orders,
                'total_shipping': float(total_shipping),
                'net_sales': float(net_sales),
            })
        self.net_sales.append({
            'period': 'Total',
            'total_orders': n_total_orders,
            'total_shipping': float(n_total_shipping),
            'net_sales': float(n_total_sales),
        })
        self.cursor.execute("set time_zone='UTC';")

    def load_other_monthly_report(self):
        self.cursor.execute("set time_zone='US/Pacific';")
        self.cursor.execute(
            '''
            select
                date_format(created_at, '%%Y-%%m') as period,
                count(entity_id) as total_orders,
                sum(ifnull(base_grand_total, 0))
                    - sum(ifnull(base_total_refunded, 0))
                    - sum(ifnull(base_total_canceled, 0))
                    - sum(ifnull(base_tax_amount, 0))
                as net_sales
            from sales_flat_order
            where created_at >= %s
                and status in ('processing', 'complete', 'closed')
                and store_id not in (2, 5)
            group by period;
            ''', [
                self.start_date.strftime('%Y-%m-%d'),
            ])
        n_total_orders, n_total_sales = 0, Decimal(0)
        for period, total_orders, net_sales in self.cursor.fetchall():
            n_total_orders += total_orders
            n_total_sales += net_sales
            self.net_other_sales.append({
                'period': period,
                'total_orders': total_orders,
                'net_sales': float(net_sales),
            })
        self.net_other_sales.append({
            'period': 'Total',
            'total_orders': n_total_orders,
            'net_sales': float(n_total_sales),
        })
        self.cursor.execute("set time_zone='UTC';")

    def add_other(self):
        data = { x['period']: x for x in self.net_sales }
        for x in self.net_other_sales:
            period = x['period']
            data[period]['other_net_sales'] = x['net_sales']
            data[period]['other_total_orders'] = x['total_orders']

    def calculate_gm(self, *args):
        for x in chain(*args):
            x['total_cost'] = self.total_cost.get(x['period'])
            if x['total_cost']:
                # x['total_cost'] += x['total_shipping']
                x['gross_margin'] = 100.0 * x['total_cost'] / x['net_sales']
                x['gross_margin'] = 100.0 - x['gross_margin']
            else:
                x['gross_margin'] = 0

    def get_context_data(self, **kwargs):
        # start_timer(logger, 'Monthly Report')
        self.load_monthly_report()
        self.load_cost()
        self.load_other_monthly_report()
        self.calculate_gm(self.net_sales)
        self.add_other()
        # end_timer()
        self.net_sales = self.net_sales[::-1]
        return {
            'net_sales': self.net_sales,
            'net_sales_json': json.dumps(self.net_sales),
        }
