"""Private v3 instances. No legacy conversion and no media authorization inference."""
import copy
import hashlib
import json
import uuid
from datetime import timedelta
from django.db import transaction, connection, OperationalError
from django.utils import timezone
from rest_framework.response import Response
from modules.accounts.services import ensure_personal_account, authorized_accounts
from modules.portfolios.services import create_portfolio, etag, PortfolioProblem
from modules.portfolios.views import PortfolioBase, serialize
from .instance_views import BoundedJSONParser
from .models import ReadyPortfolioDesign, ReadyDesignRevision, TemplateCreationRequest
from .ready_registry import ReadyRegistry
from .ready_contracts import ReadyContractError


def entry():
    try:
        return ReadyRegistry().get()
    except ReadyContractError:
        raise PortfolioProblem('temporarily_unavailable', 'Le template nécessite une vérification.', 503) from None


def validated(document, stored=False):
    try:
        ReadyRegistry().validator().validate(document)
    except ReadyContractError:
        raise PortfolioProblem('design_inconsistent' if stored else 'invalid_design',
            'Vérifiez les limites des champs, les liens HTTPS, les sections ciblées et les contrastes (4,5:1).', 409 if stored else 400) from None


def design_for(item, lock=False):
    query = ReadyPortfolioDesign.objects.select_for_update() if lock else ReadyPortfolioDesign.objects
    design = query.filter(portfolio=item).first()
    if not design:
        raise PortfolioProblem('not_found', 'Design Creative Editorial introuvable.', 404)
    origin = entry()
    if (design.source_digest != origin['bundle_digest'] or
            design.document.get('composition') != origin['bundle']['snapshot']['composition'] or
            item.source_template_id != 'creative-editorial' or item.source_template_version != '1.0.0'):
        raise PortfolioProblem('design_inconsistent', 'La provenance nécessite une vérification.')
    validated(design.document, stored=True)
    return design


def body(item, document):
    return {'portfolio': serialize(item), 'snapshot': copy.deepcopy(document),
            'version': item.version, 'etag': etag(item), 'media_status': 'unavailable'}


def response(item, document, status=200):
    result = Response(body(item, document), status=status)
    result['ETag'] = etag(item)
    return result


def revision(design, item, user):
    ReadyDesignRevision.objects.create(design=design, user=user, version=item.version, document=copy.deepcopy(design.document))


class ReadyBase(PortfolioBase):
    def handle_exception(self, exc):
        if isinstance(exc, OperationalError) and getattr(exc.__cause__, 'sqlstate', None) in ('55P03','57014','40P01'):
            result = Response({'error': {'code':'temporarily_unavailable', 'message':'Une opération est en cours. Rechargez ou réessayez avec la même intention.'}}, status=503)
            result['Retry-After'] = '2'
            return result
        return super().handle_exception(exc)


class ReadyTemplates(ReadyBase):
    http_method_names = ['get', 'head', 'options']
    def get(self, request):
        if request.query_params:
            raise PortfolioProblem('invalid_request', 'Aucun filtre disponible.', 400)
        b = entry()['bundle']
        return Response({'template': b['descriptor']['template'], 'name': b['descriptor']['name'],
            'status': b['descriptor']['status'], 'private_mvp': True, 'publication_enabled': False,
            'snapshot': b['snapshot'], 'descriptor': b['descriptor'], 'style_policy': b['style-policy']})


class ReadyCreate(ReadyBase):
    parser_classes = [BoundedJSONParser]
    def post(self, request):
        from modules.portfolios.serializers import PortfolioInput
        values = request.data
        if not isinstance(values, dict) or set(values) != {'name'}:
            raise PortfolioProblem('invalid_request', 'Indiquez uniquement le nom du portfolio.', 400)
        fields = PortfolioInput(data=values); fields.is_valid(raise_exception=True)
        raw = request.headers.get('Idempotency-Key', '')
        try:
            key = uuid.UUID(raw)
            if str(key) != raw: raise ValueError()
        except (ValueError, AttributeError):
            raise PortfolioProblem('invalid_idempotency_key', 'Intention de création invalide.', 400) from None
        digest = hashlib.sha256(json.dumps({'kind':'ready-v3', **fields.validated_data}, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
        with transaction.atomic():
            with connection.cursor() as cursor: cursor.execute("SET LOCAL lock_timeout = '2000ms'")
            account = ensure_personal_account(request.user)
            old = TemplateCreationRequest.objects.select_for_update().filter(user=request.user, account=account, key=key).first()
            if old and old.expires_at <= timezone.now():
                old.delete(); old = None
            if old:
                if old.request_digest != digest:
                    raise PortfolioProblem('idempotency_conflict', 'Intention déjà utilisée avec un autre contenu.')
                if not authorized_accounts(request.user).filter(pk=account.pk).exists() or old.portfolio.deleted_at:
                    raise PortfolioProblem('not_found', 'Portfolio introuvable.', 404)
                result = Response(copy.deepcopy(old.response_body), status=201); result['ETag'] = old.response_etag
                return result
            source = entry(); document = source['bundle']['snapshot']
            validated(document)
            item = create_portfolio(account, dict(fields.validated_data))
            item.source_template_id = 'creative-editorial'; item.source_template_version = '1.0.0'
            item.save(update_fields=['source_template_id', 'source_template_version'])
            design = ReadyPortfolioDesign.objects.create(portfolio=item, document=document, source_digest=source['bundle_digest'])
            revision(design, item, request.user)
            result = body(item, document)
            TemplateCreationRequest.objects.create(user=request.user, account=account, key=key, request_digest=digest,
                portfolio=item, response_body=result, response_etag=etag(item), expires_at=timezone.now()+timedelta(hours=24))
            return response(item, document, 201)


class ReadyDetail(ReadyBase):
    parser_classes = [BoundedJSONParser]
    def get(self, request, pk):
        with transaction.atomic():
            item = self.owned(request, pk, True)
            return response(item, design_for(item).document)

    def put(self, request, pk):
        with transaction.atomic():
            item = self.owned(request, pk, True); self.precondition(request, item)
            if item.management_state != 'active':
                raise PortfolioProblem('portfolio_archived', 'Restaurez le portfolio avant modification.')
            design = design_for(item, True)
            document = merged(design.document, request.data)
            design.document = document; design.save(update_fields=['document','updated_at'])
            item.version += 1; item.save(update_fields=['version','updated_at'])
            revision(design, item, request.user)
            return response(item, document)


def merged(original, values):
    if not isinstance(values, dict) or set(values) != {'content','customization'}:
        raise PortfolioProblem('invalid_design', 'Envoyez uniquement contenu et personnalisation.', 400)
    document = copy.deepcopy(original); document.update(values); validated(document)
    return document


class ReadyValidate(ReadyBase):
    parser_classes = [BoundedJSONParser]
    def post(self, request, pk):
        with transaction.atomic():
            item = self.owned(request, pk, True)
            return response(item, merged(design_for(item).document, request.data))


class ReadyRevisions(ReadyBase):
    def get(self, request, pk):
        item = self.owned(request, pk); design = design_for(item)
        return Response({'results':[{'id':str(r.pk),'version':r.version,'created_at':r.created_at.isoformat()}
            for r in design.revisions.order_by('-version')[:50]]})
