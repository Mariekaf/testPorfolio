"""Explicit transactional transitions. No implicit read-time conversion."""
import copy
import hashlib
import json
from django.db import transaction, connection
from django.shortcuts import get_object_or_404
from modules.accounts.services import authorized_accounts
from modules.portfolios.models import Portfolio
from modules.portfolios.services import PortfolioProblem, etag
from .models import PortfolioDesign, DesignTransition
from .hero_conversion import convert_v1_to_v2, CONVERTER_VERSION
from .hero_contracts import HeroContractError
from .validation import snapshot_of, validate_document

FIELDS = ('schema_version','composition','content','presentation','customization','experience')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def coherent(design, item):
    snapshot = snapshot_of(design)
    validate_document(snapshot, stored=True)
    if snapshot['composition']['template'] != {'id':item.source_template_id,'version':item.source_template_version}:
        raise PortfolioProblem('design_inconsistent','La provenance nécessite une vérification.')
    return snapshot


def verify_revision(revision, design):
    if (revision.design_id != design.pk or revision.source_digest != design.source_digest
        or revision.converter_version != CONVERTER_VERSION
        or fingerprint(revision.before_snapshot) != revision.before_digest
        or fingerprint(revision.after_snapshot) != revision.after_digest
        or revision.after_version != revision.before_version + 1):
        raise PortfolioProblem('recovery_inconsistent','La révision nécessite une vérification.')
    for snapshot in (revision.before_snapshot, revision.after_snapshot):
        validate_document(snapshot, stored=True)
        if snapshot['composition']['template'] != design.composition['template']:
            raise PortfolioProblem('recovery_inconsistent','La provenance de récupération est incohérente.')


def response_body(revision):
    portfolio_id = revision.design.portfolio_id
    tag = f'"portfolio:{portfolio_id}:{revision.after_version}"'
    return {'portfolio_id':str(portfolio_id), 'version':revision.after_version,
        'etag':tag, 'snapshot':copy.deepcopy(revision.after_snapshot),
        'recovery_revision_id':str(revision.pk)}


def persist(design, item, snapshot):
    for field in FIELDS:
        setattr(design, field, copy.deepcopy(snapshot[field]))
    design.save(update_fields=[*FIELDS, 'updated_at'])
    item.version += 1
    item.save(update_fields=['version','updated_at'])


@transaction.atomic
def transition(user, portfolio_id, action, values, key, original_etag):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL lock_timeout = '2000ms'")
    item = get_object_or_404(Portfolio.objects.select_for_update().filter(
        account_id__in=authorized_accounts(user).values('id'), deleted_at__isnull=True), pk=portfolio_id)
    if original_etag is None:
        raise PortfolioProblem('precondition_required','Actualisez le portfolio avant cette action.',428)
    if item.management_state != 'active':
        raise PortfolioProblem('portfolio_archived','Restaurez le portfolio avant de modifier son design.')
    design = PortfolioDesign.objects.select_for_update().filter(portfolio=item).first()
    if design is None:
        raise PortfolioProblem('design_not_initialized','Ce portfolio est vierge.')
    before = coherent(design, item)
    request_digest = fingerprint({'action':action, 'values':values, 'if_match':original_etag})
    previous = DesignTransition.objects.filter(design=design, user=user, key=key).first()
    if previous is not None:
        if previous.request_digest != request_digest:
            raise PortfolioProblem('idempotency_conflict','Cette intention a déjà été utilisée différemment.')
        verify_revision(previous, design)
        return response_body(previous)
    if original_etag != etag(item):
        raise PortfolioProblem('version_conflict','Ce portfolio a changé. Rechargez avant de réessayer.',412)
    recovery = None
    if action == 'upgrade':
        if before['schema_version'] != 1:
            raise PortfolioProblem('design_already_v2','Le design est déjà en version 2.')
        try:
            after = convert_v1_to_v2(before, values['converter_version'])
        except HeroContractError:
            raise PortfolioProblem('conversion_refused','La conversion explicite nécessite une vérification.') from None
    elif action == 'restore':
        recovery = get_object_or_404(DesignTransition, pk=values['recovery_revision_id'], design=design, action='upgrade')
        verify_revision(recovery, design)
        if before['schema_version'] != 2:
            raise PortfolioProblem('design_already_v1','Le design est déjà en version 1.')
        after = copy.deepcopy(recovery.before_snapshot)
    else:
        raise PortfolioProblem('invalid_request','Action inconnue.',400)
    validate_document(after)
    revision = DesignTransition.objects.create(design=design, user=user, key=key, action=action,
        converter_version=CONVERTER_VERSION, request_digest=request_digest,
        source_digest=design.source_digest, before_snapshot=before, after_snapshot=after,
        before_digest=fingerprint(before), after_digest=fingerprint(after),
        before_version=item.version, after_version=item.version+1, restored_from=recovery)
    # The recovery row is inserted BEFORE any replacement, within this transaction.
    persist(design, item, after)
    return response_body(revision)
