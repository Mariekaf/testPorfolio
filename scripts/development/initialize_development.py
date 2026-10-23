"""Create ignored local SaaS settings; never reads or writes legacy .local/."""
import argparse
import json
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def initialize(mode, port):
    config_path = ROOT / 'infra/env/development.local.json'
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding='utf-8-sig'))
        if config['database_mode'] != mode or int(config['database']['port']) != port:
            raise ValueError('Existing configuration differs. Preserve it and edit intentionally; no overwrite performed.')
        print('Existing local configuration preserved.')
    else:
        config = {
            'database_mode': mode, 'secret_key': secrets.token_hex(48),
            'database': {'host': '127.0.0.1', 'port': port, 'name': 'portfolio_core_dev',
                         'runtime_user': 'portfolio_core_app', 'runtime_password': secrets.token_hex(32),
                         'migration_user': 'portfolio_core_migrator', 'migration_password': secrets.token_hex(32),
                         'test_user': 'portfolio_core_test', 'test_password': secrets.token_hex(32)},
        }
        if mode == 'docker':
            config['bootstrap_user'] = 'core001_bootstrap'
            config['bootstrap_password'] = secrets.token_hex(32)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2)+'\n', encoding='utf-8')
        config_path.chmod(0o600)
        print('Private local configuration generated; values omitted.')
    if mode == 'docker':
        env_path = ROOT / 'infra/env/development.local.env'
        expected = ('POSTGRES_USER='+config['bootstrap_user']+'\nPOSTGRES_PASSWORD='+config['bootstrap_password']+
                    '\nPOSTGRES_DB=postgres\nSAAS_POSTGRES_PORT='+str(port)+'\n')
        if env_path.exists() and env_path.read_text(encoding='utf-8') != expected:
            raise ValueError('Existing Docker settings differ; no overwrite performed.')
        if not env_path.exists():
            env_path.write_text(expected, encoding='utf-8')
            env_path.chmod(0o600)
    # Preserve the frozen legacy .gitignore. Generated workspace dependencies
    # are excluded locally, including for clones using the PowerShell wrapper.
    result = subprocess.run(['git', 'rev-parse', '--git-path', 'info/exclude'], cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        path = Path(result.stdout.strip())
        if not path.is_absolute():
            path = ROOT/path
        old = path.read_text(encoding='utf-8') if path.exists() else ''
        if '/node_modules/' not in old.splitlines():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding='utf-8') as file:
                file.write('\n# CORE-001 generated workspace dependencies\n/node_modules/\n')
    print('Mode selected: '+mode+'. No PostgreSQL installation or legacy data action performed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['native', 'docker'], required=True)
    parser.add_argument('--port', type=int, default=5433)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Choose an unprivileged valid port.')
    initialize(args.mode, args.port)
