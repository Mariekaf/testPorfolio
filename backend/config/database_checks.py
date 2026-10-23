"""Preflight checks that never create/drop databases or use Django fallback."""
import psycopg


def check_test_maintenance_access(db):
    try:
        with psycopg.connect(host=db['host'], port=db['port'], dbname='postgres',
                             user=db['test_user'], password=db['test_password'], connect_timeout=3) as connection:
            current = connection.execute('SELECT current_database()').fetchone()[0]
            privileges = connection.execute('SELECT rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()
    except psycopg.Error as error:
        raise ValueError('Test role maintenance connection failed (SQLSTATE '+str(error.sqlstate or 'unknown')+'). Update the branch and re-run Initialize-Database.ps1; no test database action performed.') from None
    if current != 'postgres' or privileges != (False, False, True, False, False):
        raise ValueError('Unexpected test role database or privileges; no test database action performed.')
