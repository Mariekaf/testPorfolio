import copy
import hashlib
import json
import uuid
from datetime import timedelta
from django.db import transaction, connection
from django.utils import timezone
from modules.accounts.services import ensure_personal_account, authorized_accounts
from modules.portfolios.models import Portfolio
from modules.portfolios.services import PortfolioProblem, create_portfolio, etag
from .models import PortfolioDesign, TemplateCreationRequest
from .registry import TemplateRegistry, RegistryInvalid
from .validation import snapshot_of, validate_document


def initial_content(snapshot, name):
    """Instances start editable and neutral; sample identities are preview-only."""
    for section in snapshot['content']['sections']:
        defaults = {
            'hero': {'title':name,'subtitle':'','cta_label':'Découvrir mes projets'},
            'about': {'heading':'À propos','body':''},
            'projects': {'heading':'Mes projets','items':[]},
            'skills': {'heading':'Mes compétences','items':[]},
            'contact': {'heading':'Parlons de votre projet','body':'','email':None},
        }
        section['data'] = copy.deepcopy(defaults[section['type']])


def design_record(portfolio, snapshot, digest):
    return PortfolioDesign.objects.create(portfolio=portfolio, source_digest=digest,
        **{k:snapshot[k] for k in ['schema_version','composition','content','presentation','customization','experience']})


@transaction.atomic
def create_from_template(user, values, key, serialize):
    # Same-user creation/provisioning lock serializes idempotency reservations.
    with connection.cursor() as cursor:cursor.execute("SET LOCAL lock_timeout = '2000ms'")
    account = ensure_personal_account(user)
    canonical = {'description':'', **values}
    digest = hashlib.sha256(json.dumps(canonical,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
    previous = TemplateCreationRequest.objects.select_for_update().filter(user=user,account=account,key=key).first()
    if previous and previous.expires_at <= timezone.now():
        previous.delete();previous=None
    if previous:
        if previous.request_digest != digest:
            raise PortfolioProblem('idempotency_conflict','Cette intention de création a déjà été utilisée avec un autre contenu.')
        if not Portfolio.objects.filter(pk=previous.portfolio_id,account_id__in=authorized_accounts(user).values('id'),deleted_at__isnull=True).exists():
            raise PortfolioProblem('not_found','Portfolio introuvable.',404)
        return previous.response_body, previous.response_etag
    try:entry = TemplateRegistry().get(values['template_id'], values['template_version'])
    except RegistryInvalid:raise PortfolioProblem('temporarily_unavailable','Bibliothèque temporairement indisponible.',503) from None
    if entry is None:raise PortfolioProblem('not_found','Template introuvable.',404)
    if entry['descriptor']['availability']!='available':raise PortfolioProblem('template_unavailable','Ce template n’est plus disponible.')
    snapshot = entry['snapshot']
    initial_content(snapshot,values['name']);validate_document(snapshot)
    item = create_portfolio(account,{k:v for k,v in canonical.items() if k not in ['template_id','template_version']})
    item.source_template_id=values['template_id'];item.source_template_version=values['template_version']
    item.save(update_fields=['source_template_id','source_template_version'])
    design_record(item,snapshot,entry['source_digest'])
    body=serialize(item);tag=etag(item)
    TemplateCreationRequest.objects.create(user=user,account=account,key=key,request_digest=digest,portfolio=item,
        response_body=body,response_etag=tag,expires_at=timezone.now()+timedelta(hours=24))
    return body,tag


def copy_design(source, duplicate):
    design=PortfolioDesign.objects.select_for_update().filter(portfolio=source).first()
    if design is None:
        if source.source_template_id:raise PortfolioProblem('design_inconsistent','La source nécessite une vérification.')
        return
    document=copy.deepcopy(snapshot_of(design));validate_document(document,stored=True)
    if document['composition']['template'] != {'id':source.source_template_id,'version':source.source_template_version}:
        raise PortfolioProblem('design_inconsistent','La provenance nécessite une vérification.')
    for section in document['content']['sections']:
        if section['type']=='projects':
            for item in section['data']['items']:item['id']=str(uuid.uuid4())
    duplicate.source_template_id=source.source_template_id;duplicate.source_template_version=source.source_template_version
    duplicate.save(update_fields=['source_template_id','source_template_version'])
    design_record(duplicate,document,design.source_digest)
