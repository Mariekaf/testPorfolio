"""Private C+D synthetic DB configuration only; no DB/data migration or copying."""
import json
import secrets
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'))
from config.environment import ROOT,load_configuration


def prepare():
    source=load_configuration()
    target=ROOT/'infra/env/tpl001-cd.validation.local.json'
    if target.exists():
        current=json.loads(target.read_text(encoding='utf-8-sig'))
        if not current['database']['name'].startswith('tpl001_cd_'):
            raise ValueError('Unexpected existing configuration. No overwrite performed.')
        print('Existing private C+D configuration preserved; no database action.')
        return
    suffix=secrets.token_hex(5)
    db={'host':source['database']['host'],'port':source['database']['port'],'name':'tpl001_cd_'+suffix}
    for kind in ['runtime','migration','test']:
        db[kind+'_user']='tplcd_'+kind+'_'+suffix;db[kind+'_password']=secrets.token_urlsafe(32)
    config={'database_mode':source['database_mode'],'database':db,'secret_key':secrets.token_urlsafe(64)}
    if source['database_mode']=='docker':
        config.update(bootstrap_user=source['bootstrap_user'],bootstrap_password=source['bootstrap_password'])
    with target.open('x',encoding='utf-8') as file:
        target.chmod(0o600);json.dump(config,file,indent=2)
    print('Private C+D configuration generated. No credentials logged or database action performed.')

if __name__=='__main__':prepare()
