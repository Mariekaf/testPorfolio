import re
import time
from django.db import transaction,connection
from django.core.management.base import BaseCommand,CommandError
from modules.media.models import Asset
from modules.media.storage import PrivateLocalStorage

class Command(BaseCommand):
    help='Report private orphan directories older than 24h; --execute removes only those known-safe directories.'
    def add_arguments(self,parser):parser.add_argument('--execute',action='store_true')
    def handle(self,*args,**options):
        storage=PrivateLocalStorage();count=0
        try:
            for path in storage.root.iterdir():
                if path.is_symlink() or not path.is_dir() or not re.fullmatch(r'[0-9a-f]{64}',path.name) or time.time()-path.stat().st_mtime<86400:continue
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT pg_try_advisory_xact_lock(%s,%s)',[17001,int(path.name[:8],16)&0x7fffffff])
                        if not cursor.fetchone()[0]:continue
                    if Asset.objects.filter(storage_key=path.name).exists():continue
                    count+=1
                    if options['execute']:storage.delete(path.name)
        except OSError:raise CommandError('Orphan cleanup failed; unknown paths are never removed.') from None
        self.stdout.write(f'Orphans older than 24h: {count}. '+('Removed.' if options['execute'] else 'Dry run; no files changed.'))
