"""Generate a separate private config for synthetic PORT-001 validation.

Never provisions a database, copies user data or migrates anything. Uses only
SaaS connection metadata, generates separate database/roles/secret. Native
administrator passwords remain prompted by provision_database.py, never saved.
"""
import json,secrets,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'))
from config.environment import load_configuration,ROOT


def prepare():
    source=load_configuration()
    path=ROOT/'infra/env/port001.validation.local.json'
    if path.exists():
        current=json.loads(path.read_text(encoding='utf-8-sig'))
        if not current['database']['name'].startswith('port001_validation_'):
            raise ValueError('Unexpected validation configuration; no overwrite performed.')
        print('Existing private PORT-001 validation configuration preserved.')
        return
    suffix=secrets.token_hex(4)
    db={'host':source['database']['host'],'port':source['database']['port'],'name':'port001_validation_'+suffix}
    for kind,label in [('runtime','app'),('migration','ddl'),('test','test')]:
        db[kind+'_user']='port001_validation_'+label+'_'+suffix
        db[kind+'_password']=secrets.token_urlsafe(32)
    value={'database_mode':source['database_mode'],'secret_key':secrets.token_urlsafe(64),'database':db}
    if source['database_mode']=='docker':
        value['bootstrap_user']=source['bootstrap_user'];value['bootstrap_password']=source['bootstrap_password']
    with path.open('x',encoding='utf-8') as file:
        path.chmod(0o600);file.write(json.dumps(value,indent=2)+'\n')
    print('Separate private PORT-001 validation configuration generated; values omitted. No database action performed.')

if __name__=='__main__':prepare()
