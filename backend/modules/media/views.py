from django.db import transaction,OperationalError
from django.http import FileResponse,Http404
from django.shortcuts import get_object_or_404
from django.utils.cache import patch_vary_headers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from modules.accounts.services import authorized_accounts
from modules.portfolios.views import PortfolioBase
from modules.portfolios.services import PortfolioProblem
from modules.templates.instance_views import BoundedJSONParser
from .models import Asset
from .services import import_images,metadata,tag,delete_asset,MAX_ACCOUNT_BYTES,MAX_ASSETS
from .storage import get_storage

class MediaBase(PortfolioBase):
    def finalize_response(self,request,response,*args,**kwargs):
        response=super().finalize_response(request,response,*args,**kwargs)
        response['Cache-Control']='private, no-store';response['X-Content-Type-Options']='nosniff'
        response['Cross-Origin-Resource-Policy']='same-origin';patch_vary_headers(response,['Cookie'])
        return response

    def handle_exception(self,exc):
        if isinstance(exc,OSError) or isinstance(exc,OperationalError):
            exc=PortfolioProblem('media_unavailable','Le service d’images est temporairement indisponible. Vos contenus sont conservés.',503)
        return super().handle_exception(exc)

    def asset(self,request,pk):
        return get_object_or_404(Asset,pk=pk,status='ready',account_id__in=authorized_accounts(request.user).values('id'))

class AssetList(MediaBase):
    parser_classes=[MultiPartParser]
    def get(self,request):
        query=request.query_params
        if set(query)-{'page'} or any(len(query.getlist(k))!=1 for k in query):
            raise PortfolioProblem('invalid_request','Pagination invalide.',400)
        page=query.get('page','1')
        if not page.isascii() or not page.isdecimal() or len(page)>6 or int(page)<1:
            raise PortfolioProblem('invalid_request','Pagination invalide.',400)
        page=int(page);items=Asset.objects.filter(account_id__in=authorized_accounts(request.user).values('id'),status='ready')
        count=items.count()
        if page>max(1,(count+11)//12):raise Http404()
        return Response({'count':count,'page':page,'page_size':12,'max_files':4,'max_file_bytes':8*1024*1024,
            'max_account_bytes':MAX_ACCOUNT_BYTES,'max_assets':MAX_ASSETS,'results':[metadata(a) for a in items[(page-1)*12:page*12]]})

    def post(self,request):
        if set(request.data)-{'files','rights'} or set(request.FILES)!={'files'} or request.data.get('rights')!='true' or len(request.data.getlist('rights'))!=1:
            raise PortfolioProblem('invalid_upload','Choisissez vos images et confirmez que vous disposez des droits nécessaires.',400)
        assets=import_images(request.user,request.FILES.getlist('files'))
        return Response({'results':[metadata(a) for a in assets]},status=201)

class AssetDetail(MediaBase):
    parser_classes=[BoundedJSONParser]
    def get(self,request,pk):
        asset=self.asset(request,pk);response=Response(metadata(asset));response['ETag']=tag(asset);return response
    def delete(self,request,pk):
        if request.data!={'confirm':True}:raise PortfolioProblem('confirmation_required','Confirmez la suppression de cette image.',400)
        delete_asset(request.user,pk,request.headers.get('If-Match'))
        return Response(status=204)

class AssetFile(MediaBase):
    http_method_names=['get','head','options']
    def get(self,request,pk,variant='full'):
        asset=self.asset(request,pk)
        if variant not in ('full','thumbnail'):raise Http404()
        digest=asset.digest if variant=='full' else asset.thumbnail_digest
        size=asset.size if variant=='full' else asset.thumbnail_size
        try:file=get_storage().open(asset.storage_key,variant,digest,size)
        except OSError:raise Http404() from None
        response=FileResponse(file,content_type='image/webp')
        response['Content-Disposition']='inline; filename="image.webp"'
        response['Content-Security-Policy']="default-src 'none'; sandbox"
        return response
