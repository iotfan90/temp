import logging
import os
import paramiko
import re
from datetime import datetime

from django.conf import settings


logger = logging.getLogger(__name__)


class ResponsysFtpConnect(object):
    def __init__(self, username=None, url=None, key=None):
        pkey = key or settings.RESPONSYS_FTP['pkey']
        username = username or settings.RESPONSYS_FTP['user']
        url = url or settings.RESPONSYS_FTP['url']
        private_key = paramiko.RSAKey.from_private_key_file(pkey)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(url, username=username, password='', pkey=private_key)
        self.ftp = self.ssh.open_sftp()

    def get_file_path(self, match_pattern, remote_path=None):
        """
        Returns path(s) for files matching the match_pattern. If use_regex is true,
        match_pattern will be compiled and used to search for matches.
        @param str match_pattern: regular expression
        @param str remote_path: destination path on SFTP server
        @return: list
        """
        if not remote_path:
            remote_path = '/home/cli/wirelessemp_scp/archive/'
        files = self.ftp.listdir(remote_path)
        matching_paths = []
        for remote_file in files:
            match_check = re.search(match_pattern, remote_file)
            if match_check:
                matching_paths.append(os.path.join(remote_path, remote_file))
        return matching_paths

    def download_file(self, remote_path, local_path):
        """
        Download specifed file from Responsys
        @param str remote_path: path to file in Responsys
        @param str local_path: desired location to download file
        @return: dict success or failure message
        """
        try:
            self.ftp.get(remote_path, local_path)
        except IOError as e:
            logger.info('Can not download files: %s', e)
            self.ssh.close()
        return True

    def upload_file(self, remote_path, local_path):
        """
        Upload copy of specified file to Responsys
        @param str remote_path: path to store file in Responsys
        @param str local_path: local path to file to be uploaded
        @return: dict success or failure message
        """
        try:
            with open(local_path, 'rb') as f:
                self.ftp.putfo(f, remote_path)
        except IOError as err:
            print 'Error: ', err
            self.ssh.close()

    def check_has_file(self, remote_path):
        """
        Check if specified file exists
        @param str remote_path: path to desired file on server
        @return: bool `True` if file exists, `False` otherwise
        """
        try:
            self.ftp.stat(remote_path)
        except IOError, e:
            if 'No such file' in str(e):
                return False
            raise e
        else:
            return True

    def get_modified_date(self, remote_path):
        """
        Fetch modified date field of specified file
        @param str remote_path: path to desired file on server
        @return: tuple(bool, datetime) `False, None` if file not found, `True, timestamp` otherwise
        """
        if not self.check_has_file(remote_path):
            return False, None
        modified_at = self.ftp.stat(remote_path).st_mtime
        last_modified = datetime.fromtimestamp(modified_at)
        return True, last_modified

    def close_connection(self):
        """
        Close SSH connection
        @return: void
        """
        self.ssh.close()
