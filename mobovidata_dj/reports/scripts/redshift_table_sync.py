def run():
    from mobovidata_dj.reports.tasks import redshift_table_sync
    redshift_table_sync()
    print('DONE')
