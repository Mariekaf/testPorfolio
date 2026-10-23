"""Original synthetic geometric raster fixtures, no personal photographs."""
from io import BytesIO
from PIL import Image,ImageDraw
from django.core.files.uploadedfile import SimpleUploadedFile

def image_upload(name='synthetic.png',format='PNG',size=(600,800),color='#254c43',exif=None):
    image=Image.new('RGB',size,color);draw=ImageDraw.Draw(image)
    draw.ellipse((size[0]*.2,size[1]*.15,size[0]*.8,size[1]*.6),fill='#d9ebaa')
    draw.rectangle((size[0]*.1,size[1]*.7,size[0]*.9,size[1]*.85),fill='#f3ddc8')
    output=BytesIO();image.save(output,format=format,**({'exif':exif} if exif else {}))
    return SimpleUploadedFile(name,output.getvalue(),content_type={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}[format])
