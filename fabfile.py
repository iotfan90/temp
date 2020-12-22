import StringIO

from fabric.api import prefix, sudo
from fabric.context_managers import cd, hide, settings
from fabric.contrib.files import exists, upload_template
from fabric.decorators import task
from fabric.operations import run, put
from fabric.state import env
from fabric.tasks import execute, WrappedCallableTask
from functools import update_wrapper
from hushhush import hush


DEFAULT_TARGET_PARAM = 'target'
DEFAULT_TARGET_BRANCH = 'branch'


CONFIG = {
    # DEFAULT values are available in all configs, but can be override by them
    'DEFAULT': {
        # Not used yet
        'version_file': 'VERSION',
        'timestamp_format': '%Y-%m-%d-%H-%M-%S',
        'service_name': 'mobovidata:',
        'email': 'kenny@mobovida.com'
    },
    'staging': {
        'hosts': ['root@staging.mobovidata.com'],
        'dest': '/usr/local/lib/mobovidata/',
        'env_name': 'staging',
        'requirements': 'production',
        'branch': 'staging',
        'domain': 'staging.mobovidata.com',
        'domain_url': 'http://staging.mobovidata.com',
        'django_debug': True,
        'crate_server': '138.68.10.226:4201',
        's3_sql_backup_bucket': 'mobovidata-sql-backup',
        's3_senddata_backup_bucket': 'mobovidata-senddata-backup',
    },
    'production': {
        'hosts': ['root@mobovidata.com'],  # until we're ready to deploy to
        # prod, don't set this value
        'dest': '/usr/local/lib/mobovidata/',
        'env_name': 'production',
        'requirements': 'production',
        'branch': 'master',
        'domain': 't.mobovidata.com',
        'domain_url': 'http://t.mobovidata.com',
        'django_debug': False,
        'crate_server': '138.68.10.226:4200',
        's3_sql_backup_bucket': 'mobovidata-sql-backup-production',
        's3_senddata_backup_bucket': 'mobovidata-senddata-backup-production',
    },
}

_TASKS_EXECUTED = set()


def config_for_target(target):
    config = CONFIG['DEFAULT']
    config.update(CONFIG[target])
    return config


# TODO: add default target
def configure(func, target_param=DEFAULT_TARGET_PARAM,
              target_branch=DEFAULT_TARGET_BRANCH):
    # TODO: (when making a lib) could be imported from six as well
    def decorator(*args, **kwargs):
        if env.has_key('target_env'):
            execute(func, *args, **kwargs)
        else:
            target = kwargs.pop(target_param)
            branch = kwargs.pop(target_branch)
            config = config_for_target(target)
            if branch:
                config['branch'] = branch
            config['target_env'] = target

            with settings(**config):
                execute(func, *args, **kwargs)

    return WrappedCallableTask(update_wrapper(decorator, func))


def depends(deps):
    def inner(func):
        func.deps = deps

        def decorator(*args, **kwargs):
            for dependency in func.deps:
                if not dependency in _TASKS_EXECUTED:
                    _TASKS_EXECUTED.add(dependency)
                    dependency(*args, **kwargs)
            return func(*args, **kwargs)

        return WrappedCallableTask(update_wrapper(decorator, func))
    return inner


@configure
@task
def set_le_auto_renew():
    # Sets up auto renew for lets encrypt
    context = {
        'DOMAIN': env.domain,
        'EMAIL': env.email
    }
    upload_template('provision/templates/le-renew-webroot.ini',
                    '/usr/local/etc/',
                    context=context)
    put('provision/templates/le-renew-webroot', '/usr/local/sbin/')
    run('chmod u+x /usr/local/sbin/le-renew-webroot')

    def _get_current():
        with settings(hide('warnings', 'stdout'), warn_only=True):
            output = run('crontab -l')
            return output if output.succeeded else ''

    def _crontab_set(content):
        run("echo '%s' | crontab -" % content)

    def _crontab_add(content, market=None):
        old_crontab = _get_current()
        _crontab_set(old_crontab + '\n' + content)

    _crontab_add('30 2 * * 1 /usr/local/sbin/le-renew-webroot >> /var/log/le-renewal.log')
    _crontab_add('@reboot autossh -M 3308 -fNg -L 3307:127.0.0.1:3306 mmg-staging')


@configure
@task
def update_ssl():
    with cd('/root/'):
        sudo('./certbot-auto renew --standalone --pre-hook "service nginx stop" --post-hook "service nginx start"')


@configure
@task
def provision_ssl():
    with cd('/root/'):
        run('wget https://dl.eff.org/certbot-auto')
        run('chmod a+x certbot-auto')
        run('./certbot-auto certonly --webroot -w /usr/local/lib/mobovidata/ -d %s' % env.domain)

    def _get_current():
        with settings(hide('warnings', 'stdout'), warn_only=True):
            output = run('crontab -l')
            return output if output.succeeded else ''

    def _crontab_set(content):
        run("echo '%s' | crontab -" % content)

    def _crontab_add(content, market=None):
        old_crontab = _get_current()
        _crontab_set(old_crontab + '\n' + content)

    _crontab_add('30 2 * * 1 /root/certbot-auto renew --standalone --pre-hook "service nginx stop" --post-hook "service nginx start"')


@configure
@task
def provision():
    if exists('/root/certbot-auto'):
        print 'certbot-auto found. Attempting renewal'
        run('./root/certbot-auto renew --standalone --pre-hook "service nginx stop" --post-hook "service nginx start"')
    else:
        print 'LetsEncrypt missing, attempting setup...'
        with cd('/root/'):
            run('wget https://dl.eff.org/certbot-auto')
            run('chmod a+x certbot-auto')
            run('./root/certbot-auto certonly --webroot -w /usr/local/lib/mobovidata/ -d %s' % env.domain)
        with cd('/etc/letsencrypt'):
            run('git clone https://github.com/letsencrypt/letsencrypt')
            with cd("/etc/letsencrypt"):
                run(("./letsencrypt-auto certonly "
                     "-a webroot "
                     "--webroot-path=/usr/local/lib/mobovidata "
                     "--email %s "
                     "-d %s") % (env.email, env.domain))

                def _get_current():
                    with settings(hide('warnings', 'stdout'), warn_only=True):
                        output = run('crontab -l')
                        return output if output.succeeded else ''

                def _crontab_set(content):
                    run("echo '%s' | crontab -" % content)

                def _crontab_add(content, market=None):
                    old_crontab = _get_current()
                    _crontab_set(old_crontab + '\n' + content)

                _crontab_add('30 2 * * 1 /usr/local/sbin/le-renew-webroot >> /var/log/le-renewal.log')
                _crontab_add('35 2 * * 1 /etc/init.d/nginx reload')


    context = {
        'DOMAIN': env.domain,
        'EMAIL': env.email
    }
    upload_template('provision/templates/nginx/sites-available/mobovidata',
                    '/etc/nginx/sites-available/',
                    context=context)

    run('nginx -t')
    run('service nginx restart')

    put('provision/templates/config', '/root/.ssh/config')


def upload_newrelic(file_name, destination, context):
    upload_template(file_name, destination,  context = context, use_jinja=True)


@configure
@task
def update_nginx_config():
    context = {
        'DOMAIN': env.domain,
        'EMAIL': env.email
    }
    upload_template(
        'provision/templates/nginx/sites-available/mobovidata',
        '/etc/nginx/sites-available/',
        context=context)

    run('nginx -t')
    run('service nginx reload')


@configure
@task
def shh():
    put('hushhush/mobovidata_app.key', '/root/.ssh/')
    put('hushhush/mobovidata_app.pub', '/root/.ssh/')
    run('chmod 700 /root/.ssh/mobovidata_app.key')
    if not exists('/usr/local/lib/mobovidata/.ssh/'):
        run('mkdir /usr/local/lib/mobovidata/.ssh/')
    put('hushhush/responsys_key.key', '/usr/local/lib/mobovidata/.ssh/')
    run('chown www-data:www-data /usr/local/lib/mobovidata/.ssh/responsys_key.key')
    run('chmod 0600 /usr/local/lib/mobovidata/.ssh/responsys_key.key')
    run("""
        sudo -H -u www-data bash -c "ssh-keygen -R files.dc2.responsys.net ;
        ssh-keyscan -H files.dc2.responsys.net >> ~/.ssh/known_hosts"
        """)
    sudo('mkdir -p /usr/local/lib/mobovidata/data/send_data')
    sudo('chmod 777 /usr/local/lib/mobovidata/data/send_data')
    run("""
        ssh-keygen -R files.dc2.responsys.net ; ssh-keyscan -H files.dc2.responsys.net >> ~/.ssh/known_hosts
        """)


@configure
@task
def set_permissions():
    sudo('chown www-data:www-data /var/lib/mobovidata/celery')


@configure
@task
def tunnel():
    if env.env_name == 'staging':
        run('ssh -fNg -L 3307:127.0.0.1:3306 mmg-staging')
    elif env.env_name == 'production':
        run('ssh -fNg -L 3307:127.0.0.1:3306 mmg-slave')


@configure
@task
def deploy():
    context = {
        'DJANGO_SECRET_KEY': hush.DJANGO_SECRET_KEY,
        'FACEBOOK_APP_ID': hush.FACEBOOK_API['app_id'],
        'FACEBOOK_APP_SECRET': hush.FACEBOOK_API['app_secret'],
        'FACEBOOK_USER_TOKEN': hush.FACEBOOK_API['user_token'],
        'FACEBOOK_ACCOUNT_ID': hush.FACEBOOK_API['account_id'],
        'FACEBOOK_PAGE_ID': hush.FACEBOOK_API['page_id'],
        'INSTAGRAM_ACCOUNT_ID': hush.FACEBOOK_API['instagram_actor_id'],
        'DJANGO_DEBUG': env.django_debug,
        'MAGENTO_DB': hush.MAGENTO_DB[env.env_name]['db'],
        'MAGENTO_PORT': hush.MAGENTO_DB[env.env_name]['port'],
        'MAGENTO_PASSWORD': hush.MAGENTO_DB[env.env_name]['password'],
        'MAGENTO_USER': hush.MAGENTO_DB[env.env_name]['user'],
        'SENTRY_DSN': hush.RAVEN_DSN[env.env_name],
        'GOOGLE_ANALYTICS_PROPERTY_ID': hush.GOOGLE_ANALYTICS[env.env_name],
        'STRANDS_APID': hush.STRANDS_APID,
        'MANDRILL_API_KEY': hush.MANDRILL_API_KEY,
        'HELPSCOUT_API_KEY': hush.HELPSCOUT_API['api_key'],
        'HELPSCOUT_API_ENDPOINT': hush.HELPSCOUT_API['endpoint'],
        'MAILCHIMP_API_KEY': hush.MAILCHIMP_API_KEY,
        'RESPONSYS_PW': hush.RESPONSYS_PW,
        'ENV_TYPE': env.env_name,
        'TESTEFFECTS_FTP_PASS': hush.TESTEFFECTS_FTP_PASS,
        'SHOPIFY_API_KEY': hush.SHOPIFY[env.env_name]['API_KEY'],
        'SHOPIFY_API_PASSWORD': hush.SHOPIFY[env.env_name]['PASSWORD'],
        'SLICKTEXT_ENDPOINT': hush.SLICKTEXT['endpoint'],
        'SLICKTEXT_USER': hush.SLICKTEXT['user'],
        'SLICKTEXT_PW': hush.SLICKTEXT['pw'],
        'CRATE_SERVER': env.crate_server,
        'S3_BACKUP_KEY': hush.S3_BACKUP_KEY,
        'S3_BACKUP_SECRET': hush.S3_BACKUP_SECRET,
        'SES_KEY': hush.SES_KEY,
        'SES_SECRET': hush.SES_SECRET,
        'DOMAIN': env.domain_url,
        'OMNITURE_USER': hush.OMNITURE_CREDENTIALS['username'],
        'OMNITURE_SECRET': hush.OMNITURE_CREDENTIALS['secret'],
        'OMNITURE_REPORT_SUITES': hush.OMNITURE_CREDENTIALS['report_suite_ids'],
        'S3_SQL_BACKUP_BUCKET': env.s3_sql_backup_bucket,
        'S3_SENDDATA_BACKUP_BUCKET': env.s3_senddata_backup_bucket,
        'REDSHIFT_DB': hush.REDSHIFT['db'],
        'REDSHIFT_USER': hush.REDSHIFT['user'],
        'REDSHIFT_PASSWORD': hush.REDSHIFT['password'],
        'REDSHIFT_ENDPOINT': hush.REDSHIFT['endpoint'],
        'MAGENTO_IP': hush.MAGENTO_DB[env.env_name]['ip'],
        'AWS_CONFIG_FILE': hush.AWS_CONFIG_FILE,
        'AWS_SHARED_CREDENTIALS_FILE': hush.AWS_SHARED_CREDENTIALS_FILE,
        'SHOPIFY_WIRELESS_EMPORIUM_URL': hush.SHOPIFY[env.env_name]['WIRELESS_EMPORIUM_URL'],
        'FTP_STONE_EDGE_DOMAIN': hush.FTP_STONE_EDGE_DOMAIN,
        'FTP_STONE_EDGE_PORT': hush.FTP_STONE_EDGE_PORT,
        'FTP_STONE_EDGE_USER': hush.FTP_STONE_EDGE_USER,
        'FTP_STONE_EDGE_PASSWORD': hush.FTP_STONE_EDGE_PASSWORD,
        'FTP_STONE_EDGE_FOLDER_PATH': hush.FTP_STONE_EDGE_FOLDER_PATH
    }
    if not exists('/etc/ssl/private/mad-gentoo.credentials.json',
                  use_sudo=True):
        put('./hushhush/mad-gentoo.credentials.json',
            remote_path='/etc/ssl/private/mad-gentoo.credentials.json',
            use_sudo=True,
            mode=0644)
        sudo('usermod -a -G ssl-cert www-data')
    sudo('service nginx stop')
    sudo('service supervisor stop')
    sudo('kill -9 $(pgrep celery) || true')
    # with settings(warn_only=True):
    #     run('supervisorctl stop %s' % env.service_name)
    print 'Env name: {}'.format(env.env_name)
    print 'Target Mage DB: {}'.format(hush.MAGENTO_DB[env.env_name])
    upload_template('provision/templates/supervisor/mobovidata.conf',
                    '/etc/supervisor/conf.d/',
                    context=context)

    with cd(env.dest):
        upload_newrelic('hushhush/conf/newrelic.ini', 'env/bin/',
                        context={'domain': env.domain})
        upload_newrelic('hushhush/conf/newrelic_celeryworker.ini', 'env/bin/',
                        context={'domain': 'celeryworker.' + env.domain})
        run('git fetch')
        run('git checkout %s' % env.branch)
        run('git pull')
        # NOTE: update might be superfluous
        # run('git update')
        # generate conf/settings/environment.py using value from env.env_name
        env_py = StringIO.StringIO()
        env_py.write("ENVIRONMENT='%s'\n" % env.env_name)

        # NOTE: we may want to check if the below file is NOT in the repository
        # as that could
        #  cause problems with later deployments
        put(env_py, 'config/settings/environment.py')
        with hide('stdout'):
            # NOTE: reusing the same virtualenv may leave old, dangling packages
            # there (e,g, ones not present in the requirements) which may cause
            # problems OR which may cause problems for not being installed when
            # deploying to a new server) HOWEVER, we comment these lines out
            # because of a 'text file is busy' error that we regularly
            # encounter on the production server.
            # run('virtualenv env')
            upload_template('provision/templates/activate', 'env/bin/',
                            context=context)

            # NOTE: use pip-accel to make things faster
            run('env/bin/pip install newrelic')
            run('env/bin/pip install pip-accel')
            run('env/bin/pip-accel install -r requirements/%s.txt' %
                env.requirements)

            # Removing assets to force regeneration of static files & to get rid
            # of danglig files from earlier revisions
            run('rm -rf assets')
            run('mkdir assets')
            # NOTE: can also be run locally

        with prefix('source env/bin/activate'):
            # run('python manage.py makemigrations')
            run('python manage.py migrate')
            run('python manage.py collectstatic -v 0 -l --noinput -c')
            run('chown -R www-data static')

    sudo('service nginx start')
    sudo('service supervisor start')


@configure
@task
def put_aws_configs():
    with cd(env.dest):
        run('mkdir .aws')
        put('hushhush/aws_config', '.aws/aws_config')
        put('hushhush/aws_credentials', '.aws/aws_credentials')


@configure
@task
def place_activate_script():
    put('provision/templates/activate', '/usr/local/lib/mobovidata/env/bin/')


@configure
@task
def test():
    with cd(env.dest):
        with prefix('source env/bin/activate'):
            run('python manage.py test tests')


@configure
@task
def stop_celery():
    run('supervisorctl stop mobovidata:celery_worker')
    run('supervisorctl stop mobovidata:celerybeat')


@configure
@task
def start_celery():
    run('supervisorctl start mobovidata:celery_worker')
    run('supervisorctl start mobovidata:celery_beat')


@configure
@task
def migrate_crate():
    # Use this after making substantial changes to the crate model
    with cd(env.dest):
        with prefix('source env/bin/activate'):
            run('python manage.py migrate bigdata --database=crate')


@configure
@task
def deploy_crate():
    # Deploys docker containers to a crate server
    pass


@configure
@task
def install_pillow_reqs():
    sudo('apt-get install libjpeg-dev')
    sudo('apt-get install libjpeg8-dev')
    sudo('apt-get install libfreetype6-dev')
