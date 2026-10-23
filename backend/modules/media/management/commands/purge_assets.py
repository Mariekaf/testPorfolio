from django.core.management.base import BaseCommand,CommandError
from modules.media.models import Asset
from modules.media.services import purge_asset

class Command(BaseCommand):
    help='Dry-run by default. Purge only unreferenced assets deleted at least seven days ago.'
    def add_arguments(self,parser):parser.add_argument('--execute',action='store_true')
    def handle(self,*args,**options):
        count=0
        try:
            for identity in Asset.objects.filter(status='deleted').values_list('pk',flat=True).iterator():
                if purge_asset(identity,execute=options['execute']):count+=1
        except OSError:raise CommandError('Private storage cleanup failed; retained metadata is preserved.') from None
        self.stdout.write(f'Eligible assets: {count}. '+('Purged.' if options['execute'] else 'Dry run; no files changed.'))
