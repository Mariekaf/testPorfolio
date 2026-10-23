import io
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.http import JsonResponse
from .processing import MAX_BODY,MAX_FILE,MAX_FILES
from modules.portfolios.services import PortfolioProblem

class BoundedImageHandler(MemoryFileUploadHandler):
    def handle_raw_input(self,*args,**kwargs):
        self.activated=True
        self.count=0

    def new_file(self,*args,**kwargs):
        self.count+=1
        if self.count>MAX_FILES:raise PortfolioProblem('too_many_files','Importez au maximum 4 images à la fois.',400)
        return super().new_file(*args,**kwargs)

    def receive_data_chunk(self,raw_data,start):
        if start+len(raw_data)>MAX_FILE:raise PortfolioProblem('image_too_large','Chaque image est limitée à 8 Mio.',413)
        return super().receive_data_chunk(raw_data,start)

class MediaUploadLimit:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        if request.method=='POST' and request.path=='/api/v1/media/assets':
            raw=request.read(MAX_BODY+1)
            if len(raw)>MAX_BODY:
                response=JsonResponse({'error':{'code':'payload_too_large','message':'Import limité à 4 images de 8 Mio.'}},status=413)
                response['Cache-Control']='private, no-store';return response
            request._body=raw;request._stream=io.BytesIO(raw)
            request.upload_handlers=[BoundedImageHandler(request)]
        return self.get_response(request)
