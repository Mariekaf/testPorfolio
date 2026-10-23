from django.db import IntegrityError,transaction
from django.db.models import Count,Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException,ValidationError,ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.accounts.services import authorized_accounts,ensure_personal_account,AccountInconsistent
from .models import Portfolio
from .serializers import PortfolioInput
from .services import PortfolioProblem,create_portfolio,etag,slug_conflict

class PortfolioSession(SessionAuthentication):
    def authenticate_header(self,request):
        return 'Session'


def serialize(item):
    return {key: str(getattr(item,key)) if key in ['id','account_id'] else getattr(item,key)
            for key in ['id','account_id','name','slug','description','management_state','visibility','version',
                        'source_template_id','source_template_version','initial_theme_id','initial_theme_version']} | {
        'publication_state':item.status,'created_at':item.created_at.isoformat(),'updated_at':item.updated_at.isoformat(),'etag':etag(item)}


def portfolio_response(item,status=200):
    response=Response(serialize(item),status=status)
    response['ETag']=etag(item)
    return response

@method_decorator(never_cache,name='dispatch')
class PortfolioBase(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[PortfolioSession]

    def handle_exception(self,exc):
        if isinstance(exc,AccountInconsistent):
            exc=PortfolioProblem('account_inconsistent','Votre espace nécessite une vérification. Aucune donnée n’a été corrigée.',409)
        if isinstance(exc,PortfolioProblem):
            error={'code':exc.code,'message':exc.message}
            if exc.fields:error['fields']=exc.fields
            return Response({'error':error},status=exc.status)
        if isinstance(exc,Http404):
            return Response({'error':{'code':'not_found','message':'Portfolio introuvable.'}},status=404)
        if isinstance(exc,APIException):
            fields=exc.detail if isinstance(exc,ValidationError) else None
            code='validation_error' if isinstance(exc,(ValidationError,ParseError)) else 'authentication_required' if exc.status_code==401 else 'request_denied'
            message='Vérifiez les informations du formulaire.' if exc.status_code==400 else 'Connexion requise.' if exc.status_code==401 else 'Requête refusée.'
            return Response({'error':{'code':code,'message':message,**({'fields':fields} if fields else {})}},status=exc.status_code)
        return super().handle_exception(exc)

    def owned(self,request,pk,lock=False):
        queryset=Portfolio.objects.filter(account_id__in=authorized_accounts(request.user).values('id'),deleted_at__isnull=True)
        if lock:queryset=queryset.select_for_update()
        return get_object_or_404(queryset,pk=pk)

    def precondition(self,request,item):
        value=request.headers.get('If-Match')
        if value is None:raise PortfolioProblem('precondition_required','Actualisez le portfolio avant cette action.',428)
        if value!=etag(item):raise PortfolioProblem('version_conflict','Ce portfolio a changé. Rechargez avant de réessayer.',412)

class PortfolioList(PortfolioBase):
    def get(self,request):
        if set(request.query_params)-{'state','page'}:
            raise PortfolioProblem('validation_error','Filtre inconnu.',400)
        state=request.query_params.get('state','active')
        try:page=int(request.query_params.get('page','1'))
        except (ValueError,TypeError):page=0
        if state not in ['active','archived'] or page<1:
            raise PortfolioProblem('validation_error','Pagination ou filtre invalide.',400)
        all_items=Portfolio.objects.filter(account_id__in=authorized_accounts(request.user).values('id'),deleted_at__isnull=True)
        counts=all_items.aggregate(active_count=Count('id',filter=Q(management_state='active')),archived_count=Count('id',filter=Q(management_state='archived')))
        items=all_items.filter(management_state=state)
        count=items.count()
        if page>max(1,(count+11)//12):raise Http404()
        return Response({'count':count,**counts,'page':page,'page_size':12,'results':[serialize(p) for p in items[(page-1)*12:page*12]]})

    def post(self,request):
        serializer=PortfolioInput(data=request.data);serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            account=ensure_personal_account(request.user)
            item=create_portfolio(account,serializer.validated_data)
        return portfolio_response(item,201)

class PortfolioDetail(PortfolioBase):
    def get(self,request,pk):
        return portfolio_response(self.owned(request,pk))

    def patch(self,request,pk):
        with transaction.atomic():
            item=self.owned(request,pk,True);self.precondition(request,item)
            if item.management_state!='active':raise PortfolioProblem('archived','Restaurez le portfolio avant de le modifier.')
            serializer=PortfolioInput(data=request.data,partial=True);serializer.is_valid(raise_exception=True)
            for key,value in serializer.validated_data.items():setattr(item,key,value)
            item.version+=1
            try:
                with transaction.atomic():item.save(update_fields=[*serializer.validated_data,'version','updated_at'])
            except IntegrityError as exc:
                if getattr(getattr(exc.__cause__,'diag',None),'constraint_name',None)=='portfolio_account_slug_unique':raise slug_conflict() from None
                raise
        return portfolio_response(item)

    def delete(self,request,pk):
        with transaction.atomic():
            item=self.owned(request,pk,True);self.precondition(request,item)
            if not isinstance(request.data,dict) or set(request.data)!={'confirm'} or request.data['confirm'] is not True:
                raise PortfolioProblem('confirmation_required','Confirmez explicitement la suppression.',400)
            item.deleted_at=timezone.now();item.version+=1
            item.save(update_fields=['deleted_at','version','updated_at'])
        return Response(status=204)

class PortfolioAction(PortfolioBase):
    action=None
    def post(self,request,pk):
        with transaction.atomic():
            item=self.owned(request,pk,True);self.precondition(request,item)
            if request.data!={}:raise PortfolioProblem('validation_error','Cette action attend un objet JSON vide.',400)
            if self.action=='duplicate':
                if item.management_state!='active':raise PortfolioProblem('archived','Restaurez le portfolio avant duplication.')
                values={'name':item.name[:92]+' (copie)','description':item.description,'portfolio_type':item.portfolio_type}
                duplicate=create_portfolio(item.account,values)
                from modules.templates.instance_services import copy_design
                copy_design(item,duplicate)
                return portfolio_response(duplicate,201)
            target='archived' if self.action=='archive' else 'active'
            if item.management_state==target:raise PortfolioProblem('state_conflict','Le portfolio est déjà dans cet état.')
            item.management_state=target;item.version+=1
            item.save(update_fields=['management_state','version','updated_at'])
        return portfolio_response(item)
