from celery import shared_task
from celery.utils.log import get_task_logger
from mobovidata_dj.reports.models import ReportQuery, ReportExecution

log = get_task_logger(__name__)


@shared_task(ignore_results=True)
def execute_query(pk, *args, **kwargs):
    q = ReportQuery.objects.get(pk=pk)
    q.execute(*args, **kwargs)


@shared_task(ignore_results=True)
def execute_recurring_s3(*args, **kwargs):
    pks = [
            2,
    ]
    for k in pks:
        execute_query(k, target='s3')


@shared_task(ignore_results=True)
def execute_redshift_tables():
    redshift_execs = ReportExecution.objects.filter(target='redshift')
    ids = list(set(e.query_id for e in redshift_execs))
    queries = []
    for i in ids:
        r_filter = ReportQuery.objects.filter(id=i)
        if r_filter.exists():
            r = r_filter[0]
        else:
            print 'pass'
            continue
        if r.query in queries:
            print 'pass'
            continue
        r.execute(target='redshift')
        queries.append(r.query)


@shared_task(ignore_results=True)
def redshift_table_sync():
    exports = {'mvd': [
        'facebook_adstatwindow',
        'facebook_advertisedproduct',
        'facebook_advertisedproduct_ad_objs',
        'facebook_facebookad',
        'facebook_productreport',
        'salesreport_aginginventory',
        'salesreport_productquarantine',
    ]}
    for source, table_names in exports.items():
        for t in table_names:
            rq, _new = ReportQuery.objects.get_or_create(source=source, title=t,
                                                         query='select NOW() as posted_to_redshift_at, %s.* from %s' % (t,
                                                                             t))
            # rq.delay_execute(format='csv', gzip=True, target='redshift')
            try:
                rq.execute(format='csv', gzip=True, target='redshift')
            except Exception as e:
                print e
