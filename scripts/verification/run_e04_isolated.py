"""E04-only fresh cluster validation. Never accepts an existing DB or config file.

Requires explicit --execute-isolated-migrations. Docker/Linux or native PostgreSQL
17 (including Windows). All database roles and credentials are synthetic, private,
random and temporary. No service is installed or restarted.
"""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def private_directory(path):
    path.chmod(0o700)
    if os.name == 'nt':
        row=next(csv.reader(io.StringIO(subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True))))
        sid=row[1]
        subprocess.run(['icacls',str(path),'/inheritance:r','/grant:r',f'*{sid}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F'],check=True,stdout=subprocess.DEVNULL)


def validate(options):
    if sys.version_info[:2] != (3,13):
        raise ValueError('Python 3.13 required.')
    if not options.execute_isolated_migrations:
        raise ValueError('Explicit isolated migration approval flag required; no database action performed.')
    output=Path(options.output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Choose a new empty evidence directory; existing files are preserved.')
    output.mkdir(parents=True,exist_ok=True)
    import psycopg
    with tempfile.TemporaryDirectory(prefix='tpl001_e04_') as folder:
        work=Path(folder);private_directory(work)
        container=None;container_created=False;native_data=None
        password=secrets.token_hex(32)
        native_admin='e04_bootstrap'
        try:
            if options.engine=='docker':
                envfile=work/'postgres.env'
                envfile.write_text('POSTGRES_USER=e04_bootstrap\nPOSTGRES_PASSWORD='+password+'\nPOSTGRES_DB=postgres\nPOSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 --auth-local=scram-sha-256\n',encoding='utf-8');envfile.chmod(0o600)
                container='tpl001-e04-'+uuid.uuid4().hex[:12]
                # Image digest verified during Linux validation; no existing container reused.
                subprocess.run(['docker','run','--detach','--name',container,'--label','portfolio.ticket=tpl001_e04',
                    '--env-file',str(envfile),'--mount','type=tmpfs,destination=/var/lib/postgresql/data,tmpfs-mode=0700',
                    '--publish','127.0.0.1::5432',options.image],check=True,stdout=subprocess.DEVNULL)
                container_created=True
                port=int(subprocess.check_output(['docker','port',container,'5432/tcp'],text=True).strip().split(':')[-1])
            else:
                if not options.pg_bin:
                    raise ValueError('--pg-bin is required for native PostgreSQL.')
                suffix='.exe' if os.name=='nt' else ''
                pg_bin=Path(options.pg_bin).resolve()
                initdb=pg_bin/('initdb'+suffix);pg_ctl=pg_bin/('pg_ctl'+suffix)
                version=subprocess.check_output([str(initdb),'--version'],text=True)
                if not version.startswith('initdb (PostgreSQL) 17.'):
                    raise ValueError('Native PostgreSQL 17 required.')
                with socket.socket() as probe:
                    probe.bind(('127.0.0.1',options.port));port=probe.getsockname()[1]
                pwfile=work/'init-password';pwfile.write_text(password+'\n',encoding='utf-8');pwfile.chmod(0o600)
                native_data=work/'pgdata'
                with (work/'cluster.log').open('w',encoding='utf-8') as log:
                    subprocess.run([str(initdb),'-D',str(native_data),'-U',native_admin,'--pwfile',str(pwfile),'--auth-host=scram-sha-256','--auth-local=scram-sha-256','--encoding=UTF8','--locale=C'],check=True,stdout=log,stderr=subprocess.STDOUT)
                with (native_data/'postgresql.conf').open('a',encoding='utf-8') as file:
                    file.write("\nlisten_addresses='127.0.0.1'\nport="+str(port)+"\npassword_encryption='scram-sha-256'\n")
                subprocess.run([str(pg_ctl),'start','-D',str(native_data),'-l',str(work/'cluster.log'),'-w','-t','30'],check=True,stdout=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    with psycopg.connect(host='127.0.0.1',port=port,user=native_admin,password=password,dbname='postgres',connect_timeout=1) as connection:
                        pg_version=connection.execute('SHOW server_version').fetchone()[0]
                        if not pg_version.startswith('17.'):
                            raise ValueError('New cluster is not PostgreSQL 17.')
                    break
                except psycopg.Error:
                    time.sleep(.2)
            else:
                raise ValueError('New isolated cluster did not become ready.')
            prefix='e04_'+uuid.uuid4().hex[:10]
            config={'database_mode':options.engine if options.engine=='docker' else 'native','secret_key':secrets.token_hex(48),
                'bootstrap_user':native_admin,'bootstrap_password':password,'database':{
                    'host':'127.0.0.1','port':port,'name':prefix,'runtime_user':prefix+'_app','migration_user':prefix+'_ddl','test_user':prefix+'_test'}}
            for kind in ('runtime','migration','test'):config['database'][kind+'_password']=secrets.token_hex(32)
            config_path=work/'config.json';config_path.write_text(json.dumps(config),encoding='utf-8');config_path.chmod(0o600)
            child_env=os.environ.copy()
            child_env.update(SAAS_CONFIG_FILE=str(config_path),SAAS_MAILBOX_PATH=str(work/'mailbox'),
                SAAS_HERO_TRANSITIONS_ENABLED='0',SAAS_E04_ISOLATED_MIGRATIONS='1',PYTHONDONTWRITEBYTECODE='1',
                SAAS_HTTPS='0',SAAS_STUDIO_ORIGIN='http://127.0.0.1:3000',
                PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
            for key in ('SAAS_EMAIL_HOST','SAAS_EMAIL_USER','SAAS_EMAIL_PASSWORD','SAAS_EMAIL_PORT'):
                child_env.pop(key,None)
            # Native provisioning prompts are replaced ONLY with this newly generated
            # bootstrap password. The helper does not know any existing admin secret.
            provision_code = "import sys;sys.path.insert(0,'scripts/development');import provision_database;provision_database.provision()"
            if options.engine=='native':
                provision_code = "import sys;sys.path.insert(0,'scripts/development');from config.environment import load_configuration;import provision_database;provision_database.getpass.getpass=lambda _:load_configuration()['bootstrap_password'];provision_database.provision('e04_bootstrap')"
            def run(name,args,cwd=ROOT,extra=None):
                env=child_env.copy();env['PYTHONPATH']=str(ROOT/'backend')
                if extra:env.update(extra)
                with (output/name).open('w',encoding='utf-8') as log:
                    result=subprocess.run([sys.executable,'-B',*args],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
                if result.returncode:
                    raise ValueError('Isolated check failed: '+name+'. Inspect that evidence file; no existing database was used.')
            run('provision.log',['-c',provision_code])
            run('migrations.log',['backend/manage.py','migrate','--settings=config.settings.migration','--noinput'])
            run('schema-check.log',['backend/manage.py','makemigrations','--check','--dry-run','--settings=config.settings.migration'])
            run('runtime-privileges.log',['scripts/verification/verify_core_database.py','--check-test-access'])
            run('django-tests.log',['manage.py','test','tests','--settings=config.settings.test','--noinput','--verbosity','2'],cwd=ROOT/'backend')
            (output/'isolated-environment.json').write_text(json.dumps({'engine':options.engine,'postgresql':pg_version,'cluster':'new-disposable','database_name_prefix':'e04_','test_database_prefix':'test_e04_','existing_database_access':False,'migration_authorization':'explicit-isolated-only','runtime_transition_default':False,'cleanup':'cluster stopped and removed in finally'},indent=2)+'\n',encoding='utf-8')
            print('E04 isolated PostgreSQL, migration, runtime privilege and full Django checks passed. No existing database used.')
        finally:
            if container is not None and container_created:
                # Only the freshly generated container name owned by this invocation.
                subprocess.run(['docker','rm','--force',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
            if native_data is not None and (native_data/'postmaster.pid').exists():
                subprocess.run([str(pg_ctl),'stop','-D',str(native_data),'-m','fast','-w','-t','30'],stdout=subprocess.DEVNULL,check=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=('docker','native'),required=True)
    parser.add_argument('--pg-bin')
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--output',required=True)
    parser.add_argument('--execute-isolated-migrations',action='store_true')
    parser.add_argument('--image',default='postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3')
    args=parser.parse_args()
    try:
        validate(args)
    except (ValueError,subprocess.CalledProcessError,OSError):
        print('E04 validation failed. Preserve evidence; no credentials are logged. Only the new cluster is cleaned up.',file=sys.stderr)
        sys.exit(1)
