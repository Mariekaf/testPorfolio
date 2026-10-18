import uuid
import re
from django.db import IntegrityError,transaction
from django.utils.text import slugify
from .models import Portfolio
from .references import default_theme

class PortfolioProblem(Exception):
    def __init__(self,code,message,status=409,fields=None):
        self.code,self.message,self.status,self.fields=code,message,status,fields


def etag(item):
    return f'"portfolio:{item.pk}:{item.version}"'


def slug_conflict():
    return PortfolioProblem('slug_conflict','Ce slug est déjà utilisé dans votre espace.',409,{'slug':['Choisissez un autre slug.']})


def create_portfolio(account,values):
    default_theme()  # Valid descriptor must exist before persisting its reference.
    custom='slug' in values
    generated=re.sub(r'[^a-z0-9]+','-',slugify(values['name'])).strip('-')[:110].rstrip('-')
    base=values.get('slug') or generated or 'portfolio'
    for attempt in range(5):
        slug=base if attempt==0 else base[:100].rstrip('-')+'-'+uuid.uuid4().hex[:8]
        try:
            with transaction.atomic():
                return Portfolio.objects.create(account=account,**(values|{'slug':slug}))
        except IntegrityError as exc:
            if getattr(getattr(exc.__cause__,'diag',None),'constraint_name',None)!='portfolio_account_slug_unique':
                raise
            if custom:raise slug_conflict() from None
    raise slug_conflict()
