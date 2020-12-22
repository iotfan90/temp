from mobovidata_dj.facebook.tasks import update_last_thirty_days_stats


def run():
    update_last_thirty_days_stats()
    print('OK')
