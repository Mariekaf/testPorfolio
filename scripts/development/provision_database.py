"""Explicit local-only PostgreSQL provisioning, with separate runtime/DDL/test roles.

Native mode prompts for the existing administrator password, never stores it.
Docker mode reads the ignored, generated bootstrap credential. No legacy files.
"""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from config.environment import load_configuration
import psycopg
from psycopg import sql


def provision(admin_user=None):
    config = load_configuration()
    db = config['database']
    if db['host'] not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('Provisioning is restricted to local PostgreSQL.')
    if config['database_mode'] == 'docker':
        user, password = config['bootstrap_user'], config['bootstrap_password']
    else:
        user = admin_user or 'postgres'
        password = getpass.getpass('Existing PostgreSQL administrator password (not saved): ')
    with psycopg.connect(host=db['host'], port=db['port'], dbname='postgres', user=user,
                         password=password, autocommit=True, connect_timeout=3) as connection:
        connection.execute("SET password_encryption = 'scram-sha-256'")
        owner = connection.execute('SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=%s', (db['name'],)).fetchone()
        if owner is not None and owner[0] != db['migration_user']:
            raise ValueError('Existing database has a different owner; no adoption performed.')
        verification_database = db['name'] if owner is not None else 'postgres'
        for kind in ['migration', 'runtime', 'test']:
            name = db[kind+'_user']
            createdb = kind == 'test'
            existing = connection.execute('SELECT rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=%s', (name,)).fetchone()
            if existing is not None:
                if existing != (False, False, createdb, False, False):
                    raise ValueError('Existing role has unexpected privileges; manual review required.')
                # Do not rotate an existing role's password or adopt unrelated credentials.
                with psycopg.connect(host=db['host'], port=db['port'], dbname=verification_database, user=name,
                                     password=db[kind+'_password'], connect_timeout=3):
                    pass
            else:
                connection.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEROLE {} NOREPLICATION NOBYPASSRLS PASSWORD {}').format(
                    sql.Identifier(name), sql.SQL('CREATEDB' if createdb else 'NOCREATEDB'), sql.Literal(db[kind+'_password'])))
        if owner is None:
            connection.execute(sql.SQL("CREATE DATABASE {} OWNER {} ENCODING 'UTF8' TEMPLATE template0").format(sql.Identifier(db['name']),sql.Identifier(db['migration_user'])))
        # Django creates/drops its test DB while connected to postgres. Grant
        # only CONNECT to the test role, never ownership or runtime privileges.
        connection.execute(sql.SQL('GRANT CONNECT ON DATABASE postgres TO {}').format(sql.Identifier(db['test_user'])))
        connection.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(db['name'])))
        for kind in ['runtime', 'migration', 'test']:
            connection.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(db['name']),sql.Identifier(db[kind+'_user'])))
    with psycopg.connect(host=db['host'], port=db['port'], dbname=db['name'], user=db['migration_user'],
                         password=db['migration_password'], autocommit=True, connect_timeout=3) as connection:
        connection.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
        connection.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(db['runtime_user'])))
        connection.execute(sql.SQL('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(db['runtime_user'])))
        connection.execute(sql.SQL('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}').format(sql.Identifier(db['runtime_user'])))
        connection.execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}').format(sql.Identifier(db['runtime_user'])))
        connection.execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {}').format(sql.Identifier(db['runtime_user'])))
    print('Development database and least-privilege roles ready. No credentials logged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admin-user', help='Native PostgreSQL administrator name')
    args = parser.parse_args()
    try:
        provision(args.admin_user)
    except (psycopg.Error, ValueError):
        print('Database provisioning failed. Check the local instance, ownership and private credentials; no secret details are logged.', file=sys.stderr)
        sys.exit(1)
