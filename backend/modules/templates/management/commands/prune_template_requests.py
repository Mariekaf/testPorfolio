from django.core.management.base import BaseCommand
from django.utils import timezone
from modules.templates.models import TemplateCreationRequest

class Command(BaseCommand):
    help = 'Count expired template creation records; --execute removes them. Never removes portfolios.'
    def add_arguments(self, parser):parser.add_argument('--execute',action='store_true')
    def handle(self,*args,**options):
        records=TemplateCreationRequest.objects.filter(expires_at__lte=timezone.now())
        count=records.count()
        if options['execute']:records.delete()
        self.stdout.write(f'Expired records: {count}. '+('Removed.' if options['execute'] else 'Dry run; no changes.'))
