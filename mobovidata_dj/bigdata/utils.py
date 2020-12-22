from django.conf import settings


def get_redshift_connection(db_name=None, user=None, pw=None,
                            endpoint=None, port=5439):
    # Not currently in use because pg8000 is easier
    # to install, but could be handy in the future
    # import psycopg2 as dbapi
    import pg8000 as dbapi

    if not db_name:
        db_name = settings.REDSHIFT_DB
    if not user:
        user = settings.REDSHIFT_USER
    if not pw:
        pw = settings.REDSHIFT_PASSWORD
    if not endpoint:
        endpoint = settings.REDSHIFT_ENDPOINT

    # Connect to RedShift
    return dbapi.connect(database=db_name,
                         host=endpoint,
                         port=port,
                         user=user,
                         password=pw,
                         use_ssl=True,
                         socket_timeout=500000)
