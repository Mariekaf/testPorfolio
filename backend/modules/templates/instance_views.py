import uuid
from django.conf import settings
from django.db import transaction, OperationalError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from modules.portfolios.serializers import PortfolioInput
from modules.portfolios.views import PortfolioBase, serialize
from modules.portfolios.services import PortfolioProblem, etag
from .models import PortfolioDesign
from .instance_services import create_from_template
from .registry import strict_json, LIMIT
from .validation import snapshot_of, validate_document

class BoundedJSONParser(JSONParser):
    def parse(self,stream,media_type=None,parser_context=None):
        raw=stream.read(LIMIT+1)
        if len(raw)>LIMIT:raise PortfolioProblem('payload_too_large','Le document dépasse 256 Kio.',413)
        try:return strict_json(raw)
        except (ValueError,RecursionError):raise PortfolioProblem('invalid_request','Document JSON invalide.',400) from None

class TemplateInput(PortfolioInput):
    template_id=serializers.RegexField(r'^[a-z][a-z0-9-]{0,99}$')
    template_version=serializers.RegexField(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$',max_length=30)

class TemplateCreate(PortfolioBase):
    parser_classes=[BoundedJSONParser]
    def post(self,request):
        raw=request.headers.get('Idempotency-Key','')
        try:
            key=uuid.UUID(raw)
            if str(key)!=raw:raise ValueError()
        except (ValueError,AttributeError):raise PortfolioProblem('invalid_idempotency_key','Actualisez l’intention de création.',400) from None
        data=TemplateInput(data=request.data);data.is_valid(raise_exception=True)
        try:body,tag=create_from_template(request.user,dict(data.validated_data),key,serialize)
        except OperationalError as exc:
            if getattr(exc.__cause__,'sqlstate',None) not in ['55P03','57014']:raise
            response=Response({'error':{'code':'temporarily_unavailable','message':'Une création est en cours. Réessayez avec la même intention.'}},status=503)
            response['Retry-After']='2';return response
        response=Response(body,status=201);response['ETag']=tag;return response

class DesignDetail(PortfolioBase):
    parser_classes=[BoundedJSONParser]

    def read_design(self,item,lock=False):
        query=PortfolioDesign.objects
        if lock:query=query.select_for_update()
        design=query.filter(portfolio=item).first()
        if not design:raise PortfolioProblem('design_not_initialized','Ce portfolio est vierge. Ses informations restent modifiables.')
        snapshot=snapshot_of(design);validate_document(snapshot,stored=True)
        if snapshot['composition']['template']!={'id':item.source_template_id,'version':item.source_template_version}:
            raise PortfolioProblem('design_inconsistent','La provenance nécessite une vérification.')
        return design,snapshot

    def response(self,item,snapshot):
        tag=etag(item);response=Response({'portfolio_id':str(item.pk),'version':item.version,'etag':tag,'snapshot':snapshot});response['ETag']=tag;return response

    def negotiate(self, request, snapshot):
        accepted = request.headers.get('Accept-Design-Schema', '1')
        if accepted not in ('1','2','1,2','2,1'):
            raise PortfolioProblem('invalid_request','Versions de design invalides.',400)
        if str(snapshot['schema_version']) not in accepted.split(','):
            raise PortfolioProblem('design_schema_not_acceptable','Ce client ne prend pas en charge la version du design.',406)

    def get(self,request,pk):
        with transaction.atomic():
            item=self.owned(request,pk,True)
            _,snapshot=self.read_design(item)
            self.negotiate(request, snapshot)
            return self.response(item,snapshot)

    def put(self,request,pk):
        with transaction.atomic():
            item=self.owned(request,pk,True);self.precondition(request,item)
            if item.management_state!='active':raise PortfolioProblem('portfolio_archived','Restaurez le portfolio avant de modifier son design.')
            design,snapshot=self.read_design(item,True)
            self.negotiate(request, snapshot)
            if snapshot['schema_version'] == 2 and not settings.SAAS_HERO_TRANSITIONS_ENABLED:
                raise PortfolioProblem('hero_transitions_disabled','Les écritures de design v2 sont désactivées.')
            values=request.data
            if not isinstance(values,dict) or set(values)!={'content','customization'}:
                raise PortfolioProblem('invalid_design','Envoyez uniquement le contenu et la personnalisation.',400)
            snapshot.update(values);validate_document(snapshot)
            design.content=values['content'];design.customization=values['customization']
            design.save(update_fields=['content','customization','updated_at'])
            item.version+=1;item.save(update_fields=['version','updated_at'])
            return self.response(item,snapshot)
