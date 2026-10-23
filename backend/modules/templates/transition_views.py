import uuid
from django.conf import settings
from django.db import OperationalError
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from modules.portfolios.views import PortfolioBase
from modules.portfolios.services import PortfolioProblem
from .models import PortfolioDesign, DesignTransition
from .instance_views import BoundedJSONParser
from .transitions import transition, verify_revision


class TransitionBase(PortfolioBase):
    parser_classes = [BoundedJSONParser]

    def enabled(self):
        if not settings.SAAS_HERO_TRANSITIONS_ENABLED:
            raise PortfolioProblem('not_found','Ressource introuvable.',404)


class DesignTransitionView(TransitionBase):
    action = None

    def post(self, request, pk):
        self.enabled()
        self.owned(request, pk)  # Authorize before disclosing body/header errors.
        raw_key = request.headers.get('Idempotency-Key', '')
        try:
            key = uuid.UUID(raw_key)
            if str(key) != raw_key:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise PortfolioProblem('invalid_idempotency_key','Clé UUID canonique requise.',400) from None
        values = request.data
        if self.action == 'upgrade':
            if (not isinstance(values, dict) or set(values) != {'target_schema_version','converter_version'}
                or type(values['target_schema_version']) is not int or values['target_schema_version'] != 2
                or values['converter_version'] != '1.0.0'):
                raise PortfolioProblem('invalid_request','Conversion versionnée explicite requise.',400)
        else:
            if not isinstance(values, dict) or set(values) != {'recovery_revision_id'}:
                raise PortfolioProblem('invalid_request','Révision de récupération requise.',400)
            try:
                value = values['recovery_revision_id']
                if str(uuid.UUID(value)) != value:
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                raise PortfolioProblem('invalid_request','Référence UUID invalide.',400) from None
        try:
            body = transition(request.user, pk, self.action, values, key, request.headers.get('If-Match'))
        except OperationalError as exc:
            if getattr(exc.__cause__, 'sqlstate', None) not in ('55P03','57014'):
                raise
            response = Response({'error':{'code':'temporarily_unavailable','message':'Une opération est en cours. Réessayez avec la même clé.'}}, status=503)
            response['Retry-After'] = '2'
            return response
        response = Response(body)
        response['ETag'] = body['etag']
        return response


class DesignRevisions(TransitionBase):
    def get(self, request, pk, revision_id=None):
        self.enabled()
        item = self.owned(request, pk)
        design = get_object_or_404(PortfolioDesign, portfolio=item)
        if revision_id is not None:
            revision = get_object_or_404(DesignTransition, pk=revision_id, design=design)
            verify_revision(revision, design)
            return Response({**self.metadata(revision), 'source_digest':revision.source_digest,
                'before_snapshot':revision.before_snapshot, 'after_snapshot':revision.after_snapshot,
                'before_digest':revision.before_digest, 'after_digest':revision.after_digest})
        query = request.query_params
        page = query.get('page', '1')
        if (set(query)-{'page'} or any(len(query.getlist(k)) != 1 for k in query)
            or not page.isascii() or not page.isdecimal() or len(page) > 7 or not 1 <= int(page) <= 1000000):
            raise PortfolioProblem('invalid_request','Pagination invalide.',400)
        start = (int(page)-1)*20
        rows = DesignTransition.objects.filter(design=design).order_by('-created_at','-id')[start:start+20]
        return Response({'page':int(page),'page_size':20,'results':[self.metadata(row) for row in rows]})

    @staticmethod
    def metadata(revision):
        return {'id':str(revision.pk), 'action':revision.action,
            'converter_version':revision.converter_version, 'before_version':revision.before_version,
            'after_version':revision.after_version, 'created_at':revision.created_at.isoformat(),
            'restored_from':str(revision.restored_from_id) if revision.restored_from_id else None}
