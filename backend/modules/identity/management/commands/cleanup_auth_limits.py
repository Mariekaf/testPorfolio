"""Bound retention without logging IP addresses or email addresses."""
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from modules.identity.models import AuthenticationLimit

class Command(BaseCommand):
    help = 'Delete expired authentication limit buckets (no active limits removed).'
    def handle(self,*args,**options):
        retention=max(86400,max(window for _,window in settings.AUTH_RATE_LIMITS.values()))
        count,_=AuthenticationLimit.objects.filter(window_start__lt=timezone.now()-timedelta(seconds=retention)).delete()
        self.stdout.write(f'{count} expired authentication limit buckets removed.')
