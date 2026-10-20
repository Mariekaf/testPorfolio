"""Bounded per-request JSON buffering for design routes only.

Django/DRF may read .body before our parser. Keep AUTH's global 16 KiB limit
unchanged; these two routes explicitly support documents up to 256 KiB.
No global setting is changed, and session/CSRF middleware still run normally.
"""
import io
import re
from django.http import JsonResponse
from django.utils.cache import patch_cache_control
from .registry import LIMIT

class DesignBodyLimit:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        allowed=(request.method=='POST' and request.path=='/api/v1/portfolios/from-template') or (request.method=='PUT' and re.fullmatch(r'/api/v1/portfolios/[0-9a-f-]{36}/design',request.path))
        allowed = allowed or (request.method in ('POST','PUT') and re.fullmatch(r'/api/v1/ready-portfolios(?:/[0-9a-f-]{36}(?:/validate|/media)?)?', request.path))
        if allowed:
            raw=request.read(LIMIT+1)
            if len(raw)>LIMIT:
                response=JsonResponse({'error':{'code':'payload_too_large','message':'Le document dépasse 256 Kio.'}},status=413)
                patch_cache_control(response,no_store=True,private=True)
                return response
            request._body=raw
            request._stream=io.BytesIO(raw)
        return self.get_response(request)
