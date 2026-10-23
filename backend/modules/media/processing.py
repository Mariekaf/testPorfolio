"""Bounded, static raster decoding. No original bytes or metadata survive encoding."""
import hashlib
from io import BytesIO
from pathlib import PurePath
import unicodedata
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from modules.portfolios.services import PortfolioProblem

MAX_FILE = 8*1024*1024
MAX_FILES = 4
MAX_BODY = MAX_FILES*MAX_FILE + 65536
MAX_PIXELS = 20_000_000
MAX_SIDE = 8192
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
FORMATS = {'JPEG':({'.jpg','.jpeg'},'image/jpeg'), 'PNG':({'.png'},'image/png'), 'WEBP':({'.webp'},'image/webp')}


def process_image(upload):
    name = unicodedata.normalize('NFC',upload.name)
    if (not 1 <= len(name) <= 180 or any(c in name for c in '/\\:') or
            any(unicodedata.category(c).startswith('C') for c in name)):
        raise PortfolioProblem('invalid_image','Nom de fichier invalide.',400)
    if upload.size > MAX_FILE:
        raise PortfolioProblem('image_too_large','Chaque image est limitée à 8 Mio.',413)
    raw = upload.read(MAX_FILE+1)
    if not raw or len(raw)>MAX_FILE:
        raise PortfolioProblem('image_too_large','Image vide ou supérieure à 8 Mio.',413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as probe:
                if probe.format not in FORMATS: raise ValueError()
                extensions,mime=FORMATS[probe.format]
                if PurePath(name).suffix.lower() not in extensions or upload.content_type not in (mime,'application/octet-stream'):
                    raise ValueError()
                if (getattr(probe,'n_frames',1)!=1 or min(probe.size)<1 or max(probe.size)>MAX_SIDE or probe.width*probe.height>MAX_PIXELS):
                    raise ValueError()
                probe.verify()
            with Image.open(BytesIO(raw)) as decoded:
                decoded.load()
                oriented=ImageOps.exif_transpose(decoded)
                # Copy pixels only, never decoder.info, exif, ICC or arbitrary text chunks.
                mode='RGBA' if 'A' in oriented.getbands() or 'transparency' in oriented.info else 'RGB'
                pixels=oriented.convert(mode)
                image=Image.new(mode,pixels.size);image.paste(pixels)
                image.thumbnail((2560,2560),Image.Resampling.LANCZOS)
                main=BytesIO();image.save(main,format='WEBP',quality=85,method=4)
                thumb=image.copy();thumb.thumbnail((400,400),Image.Resampling.LANCZOS)
                small=BytesIO();thumb.save(small,format='WEBP',quality=75,method=4)
        full,thumbnail=main.getvalue(),small.getvalue()
        if max(len(full),len(thumbnail))>MAX_FILE:raise ValueError()
        return {'original_name':name,'width':image.width,'height':image.height,
            'thumbnail_width':thumb.width,'thumbnail_height':thumb.height,
            'size':len(full),'thumbnail_size':len(thumbnail),
            'digest':hashlib.sha256(full).hexdigest(),'thumbnail_digest':hashlib.sha256(thumbnail).hexdigest(),
            'full':full,'thumbnail':thumbnail}
    except (ValueError,OSError,UnidentifiedImageError,SyntaxError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise PortfolioProblem('invalid_image','Image refusée : utilisez un JPEG, PNG ou WebP statique valide (20 Mpx, 8 192 px par côté maximum).',400) from None
