import boto
import json
import os
import time

from boto.s3.key import Key
from celery.task.control import inspect
from django.conf import settings
from django.core.cache import cache


def upload_to_s3(aws_access_key_id, aws_secret_access_key, f_handle,
                 bucket_name, key, callback=None, md5=None,
                 reduced_redundancy=False, content_type=None):
    """
    Uploads the given file to the AWS S3
    bucket and key specified.

    callback is a function of the form:

    def callback(complete, total)

    The callback should accept two integer parameters,
    the first representing the number of bytes that
    have been successfully transmitted to S3 and the
    second representing the size of the to be transmitted
    object.

    Returns boolean indicating success/failure of upload.
    """
    try:
        size = os.fstat(f_handle.fileno()).st_size
    except:
        # Not all file objects implement fileno(),
        # so we fall back on this
        f_handle.seek(0, os.SEEK_END)
        size = f_handle.tell()

    bucket = s3_bucket(aws_access_key_id, aws_secret_access_key, bucket_name)
    k = Key(bucket)
    k.key = key

    if content_type:
        k.set_metadata('Content-Type', content_type)
    sent = k.set_contents_from_file(f_handle, cb=callback, md5=md5,
                                    reduced_redundancy=reduced_redundancy,
                                    rewind=True)

    # Rewind for later use
    f_handle.seek(0)

    if sent == size:
        return key
    return False


def s3_bucket(aws_access_key_id, aws_secret_access_key, bucket_name):
    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    return conn.get_bucket(bucket_name, validate=True)


def s3_backup_connection():
    return boto.connect_s3(settings.S3_BACKUP_KEY, settings.S3_BACKUP_SECRET)


def upload_s3_backup(fn, bucket_name, target_fn=None, callback=None):
    if not target_fn:
        target_fn = fn
    with open(fn, 'r') as f_handle:
        return upload_to_s3(settings.S3_BACKUP_KEY, settings.S3_BACKUP_SECRET,
                            f_handle, bucket_name, target_fn, callback=callback)


def upload_s3_sql_backup(fn, target_fn=None):
    return upload_s3_backup(fn, settings.S3_SQL_BACKUP_BUCKET, target_fn)


def upload_s3_senddata_backup(fn, target_fn=None):
    return upload_s3_backup(fn, settings.S3_SENDDATA_BACKUP_BUCKET, target_fn)


def download_from_s3(f_handle,
                     dest_file,
                     bucket_name='mobovidata-reports',
                     aws_access_key_id=settings.S3_BACKUP_KEY,
                     aws_secret_access_key=settings.S3_BACKUP_SECRET):
    """
    :param aws_access_key_id: AWS access key credential
    :param aws_secret_access_key: AWS secret access key credential
    :param f_handle: Name of the file on S3
    :param dest_file: path and name of the file to download to
    :param bucket_name: Name of the S3 bucket. Default = looker-exports.
    :return: Nothing
    """
    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(bucket_name)
    # Get the Key object of the given key, in the bucket
    k = Key(bucket, f_handle)
    # Get the contents of the key into a file
    k.get_contents_to_filename(dest_file)


def get_files_list_from_s3(bucket_name='mobovidata-reports',
                           aws_access_key_id=settings.S3_BACKUP_KEY,
                           aws_secret_access_key=settings.S3_BACKUP_SECRET):
    """
    Returns a list of files from the designated bucket
    :param bucket_name:
    :param aws_access_key_id:
    :param aws_secret_access_key:
    :return: list of file names existing in the designated s3 bucket
    """
    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(bucket_name)
    return [obj.key for obj in bucket.get_all_keys()]


def get_active():
    active = {}
    inspected = inspect().active() or {}
    for worker, tasks in inspected.items():
        for task in tasks:
            active[task['id']] = worker
    return active


def get_active_cached():
    # get_active takes non-trivial time, and we want to use it in the admin
    EXPIRY = 5
    CACHE_KEY = '__celery_inspect_active'
    try:
        data = json.loads(cache.get(CACHE_KEY))
        dt = float(data['timestamp'])
        if time.time() - dt < EXPIRY:
            return data['active']
    except:
        pass
    data = {'timestamp': time.time(), 'active': get_active()}
    cache.set(CACHE_KEY, json.dumps(data))
    return data['active']


def get_scheduled():
    scheduled = {}
    inspected = inspect().scheduled() or {}
    for worker, tasks in inspected.items():
        for task in tasks:
            scheduled[task['id']] = worker
    return scheduled


def get_scheduled_cached():
    # get_scheduled takes non-trivial time, and we want to use it in the admin
    EXPIRY = 5
    CACHE_KEY = '__celery_inspect_scheduled'
    try:
        data = json.loads(cache.get(CACHE_KEY))
        dt = float(data['timestamp'])
        if time.time() - dt < EXPIRY:
            return data['scheduled']
    except:
        pass
    data = {'timestamp': time.time(), 'scheduled': get_scheduled()}
    cache.set(CACHE_KEY, json.dumps(data))
    return data['scheduled']


def get_reserved():
    reserved = {}
    inspected = inspect().reserved() or {}
    for worker, tasks in inspected.items():
        for task in tasks:
            reserved[task['id']] = worker
    return reserved


def get_reserved_cached():
    # get_reserved takes non-trivial time, and we want to use it in the admin
    EXPIRY = 5
    CACHE_KEY = '__celery_inspect_reserved'
    try:
        data = json.loads(cache.get(CACHE_KEY))
        dt = float(data['timestamp'])
        if time.time() - dt < EXPIRY:
            return data['reserved']
    except:
        pass
    data = {'timestamp': time.time(), 'reserved': get_reserved()}
    cache.set(CACHE_KEY, json.dumps(data))
    return data['reserved']


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
