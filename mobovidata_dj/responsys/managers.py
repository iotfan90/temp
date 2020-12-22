import csv
import glob
import hashlib
import logging
import os
import pytz
import subprocess
import utils
import zipfile

from datetime import datetime
from django.db import connections, models
from django.conf import settings

from mobovidata_dj.responsys.connect import ResponsysFtpConnect

logger = logging.getLogger(__name__)


class OptedOutEmailsManager(models.Manager):
    """
    Manager for handling secondary actions that must take place as a result of
    creating/updating customer model
    """
    def add_email_unsub(self, email, riid=None):
        """
        Method to add an unsubscribe record for the given email.  This is a
        temporary measure, as this table is truncated and reloaded nightly, to
        ensure that Criteo email API has no lag between customer opt outs and
        criteo blacklist api calls.
        """
        m = hashlib.md5(email).hexdigest()
        if riid:
            self.update_or_create(
                riid=riid,
                email=email,
                md5=m,
                subscription_status=0
            )
        else:
            self.update_or_create(
                email=email,
                md5=m,
                subscription_status=0
            )

    def add_or_update_email(self, riid, event_type, event_captured, email):
        """
        Get process new OptedOutEmails
        :type riid: str
        :type event_type: str
        :type event_captured: str
        :param email: Optional param for the customer email.  Only required if RIID doesn't exist in the db.
        """
        rg_touched_records = []
        riid = int(riid)
        email_md5 = hashlib.md5(email).hexdigest()
        if event_type == settings.RESPONSYS_CONTACT_EVENT_DATA_MAP['unsubscribe']:
            subscription_status = 0
            record = self.filter(riid=riid)
            if record.exists():
                if record[0].modified_dt < event_captured:
                    rg_touched_records.append(
                        record.update(
                            subscription_status=subscription_status,
                            modified_dt=event_captured
                         ))
                else:
                    rg_touched_records.append(record[0])
            else:
                rg_touched_records.append(
                    self.update_or_create(
                        riid=riid,
                        email=email,
                        md5=email_md5,
                        modified_dt=event_captured,
                        subscription_status=subscription_status
                    )
                )
        elif event_type == settings.RESPONSYS_CONTACT_EVENT_DATA_MAP['subscribe']:
            subscription_status = 1
            record = self.filter(riid=riid)
            if record.exists():
                if record[0].modified_dt < event_captured:
                    rg_touched_records.append(
                        record.update(
                            subscription_status=subscription_status,
                            modified_dt=event_captured
                         ))
                else:
                    rg_touched_records.append(record[0])
            else:
                rg_touched_records.append(
                    self.update_or_create(
                        riid=riid,
                        email=email,
                        md5=email_md5,
                        modified_dt=event_captured,
                        subscription_status=subscription_status
                    )
                )

    def load_contact_list(self, contact_list_file=None):
        """
        Loads the Responsys contact list into the OptedOutEmails model.
        Meant to be used as initial fixture data only.
        Will not work if data already exists in the model.
        :type contact_list_file: str
        """
        if self.filter(riid__gt=0).count() > 0:
            raise RuntimeError(
                'Oops. This function should only be used initially populate the model.'
            )
        if not contact_list_file:
            r = ResponsysFtpConnect()
            # Find the most recent contact list
            lists = r.get_file_path('CONTACT_')
            remote_contact_list = sorted(lists)[-1]
            print 'found and loading contact list %s' % remote_contact_list
            print 'Be patient, this could take up to 45 minutes...'
            # Download the most recent contact list
            e = utils.Extract()
            local_path = e.get_local_path(remote_contact_list)
            r.download_file(remote_contact_list, local_path)
            print 'download finished!'
            contact_list_file = local_path
        fields_map = {
            'RIID_': 'riid',
            'EMAIL_ADDRESS_': 'email',
            'EMAIL_MD5_HASH_': 'md5',
            'EMAIL_PERMISSION_STATUS_': 'subscription_status',
            'MODIFIED_DATE_': 'modified_dt'
        }
        print 'loading records'
        permission_status_map = {'I': 1, 'O': 0}
        with zipfile.ZipFile(contact_list_file, 'r') as archive:
            contact_list_dir = '/'.join(contact_list_file.split('/')[0:-1])
            archive.extractall(contact_list_dir)
        contact_list_file = contact_list_file.replace('.zip', '')
        with open(contact_list_file, 'r') as f:
            readr = csv.DictReader(f)
            for i, row in enumerate(readr):
                # contact_list.append({fields_map[f]: row[f] for f in fields_map.keys()})
                r = {fields_map[f]:row[f] for f in fields_map.keys()}
                try:
                    modified_dt = datetime.datetime.strptime(
                        r['modified_dt'], '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=pytz.UTC)
                    sub_status = permission_status_map.get(r['subscription_status'], -1)
                    if sub_status >= 0:
                        self.create(
                            riid=r['riid'],
                            email=r['email'],
                            md5=hashlib.md5(r['email']).hexdigest(),
                            subscription_status=sub_status,
                            modified_dt=modified_dt
                        )
                except (ValueError, TypeError):
                    continue

        print 'finished loading records'

    def load_optout_list(self):
        """
        Downloads and posts the list of opted out customers
        """
        cmd_data = dict(
            settings.RESPONSYS_SEND_DATA_PATH,
            key=settings.RESPONSYS_FTP['pkey'],
            user=settings.RESPONSYS_FTP['user'],
            url=settings.RESPONSYS_FTP['url'],
        )
        tgt = settings.RESPONSYS_SEND_DATA_PATH['tgt']

        # Find the latest CONTACT_LIST file
        cmd = "eval $(ssh-agent) && ssh-add {key} ; "
        cmd += "ssh {user}@{url} 'ls -lh download/CED_Data/OPT_OUT_MD5*.csv.zip | tail -n1'"
        cmd = cmd.format(**cmd_data)

        get_file = cmd_data['get_file'] = subprocess.check_output(cmd, shell=True).strip().split('/')[-1]
        put_file = cmd_data['put_file'] = os.path.join(tgt, get_file)

        print 'Found contact_list: %s' % get_file

        # Delete old zip files to save space
        for fn in glob.glob(os.path.join(tgt, '*.zip')):
            if fn != put_file:
                os.unlink(fn)

        # Download the file if we don't already have it
        if not os.path.exists(put_file):
            cmd = "eval $(ssh-agent) && ssh-add {key} ; "
            cmd += "rsync -r -a -v -x {user}@{url}:download/CED_Data/{get_file} {put_file}"
            cmd = cmd.format(**cmd_data)

            print subprocess.call(cmd, shell=True)
        else:
            print 'File exists, skipping: %s' % put_file

        # Extract the .zip
        with zipfile.ZipFile(put_file, 'r') as f:
            f.extractall(tgt)

        # truncate table using cursor bc the django ORM times out when truncating large tables

        cursor = connections['default'].cursor()
        cursor.execute(
            '''
            truncate table opted_out_emails;
            '''
        )

        permission_status_map = {'I': 1, 'O': 0}
        with open(put_file.replace('.zip', ''), 'r') as f:
            r = csv.DictReader(f)
            for row in r:
                self.create(
                    riid=row['RIID_'],
                    email=row['EMAIL_ADDRESS_'],
                    md5=row['EMAIL_MD5_HASH_'],
                    subscription_status=permission_status_map.get(row['EMAIL_PERMISSION_STATUS_']),
                )
        os.remove(put_file.replace('.zip', ''))
        os.remove(put_file)
