"""Verify the actual development PostgreSQL connection and runtime privileges."""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'backend'))
import psycopg
from config.environment import load_configuration
from config.database_checks import check_test_maintenance_access


def main(check_test_access=False):
    db = load_configuration()['database']
    with psycopg.connect(host=db['host'], port=db['port'], dbname=db['name'], user=db['runtime_user'],
                         password=db['runtime_password'], connect_timeout=3) as connection:
        row = connection.execute('SELECT rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()
        if row != (False, False, False, False, False):
            raise ValueError('Runtime role privileges exceed the contract.')
        owner = connection.execute('SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()').fetchone()[0]
        if owner == db['runtime_user']:
            raise ValueError('Runtime role must not own the database.')
        if connection.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE')").fetchone()[0]:
            raise ValueError('Runtime role must not create tables.')
        for privilege in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']:
            if not connection.execute("SELECT has_table_privilege(current_user, 'identity_user', %s)", (privilege,)).fetchone()[0]:
                raise ValueError('Required runtime grant missing.')
        connection.execute('SELECT id FROM identity_user LIMIT 0')
        version = connection.execute('SHOW server_version').fetchone()[0].split(' ')[0]
        encoding = connection.execute('SHOW server_encoding').fetchone()[0]
        if not version.startswith('17.') or encoding != 'UTF8':
            raise ValueError('Expected PostgreSQL 17 and UTF8.')
    if check_test_access:
        check_test_maintenance_access(db)
        print('Test role maintenance connection verified; no runtime privilege added.')
    print('PostgreSQL '+version+' verified: UTF8, initial table accessible, least-privilege runtime role, no DDL/CREATEDB/superuser/BYPASSRLS.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-test-access', action='store_true')
    args = parser.parse_args()
    try:
        main(args.check_test_access)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except psycopg.Error:
        print('PostgreSQL verification failed; inspect the private local configuration. No credentials logged.', file=sys.stderr)
        sys.exit(1)
