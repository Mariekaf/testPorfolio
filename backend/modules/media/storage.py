"""Private binary adapter. No storage path or key is a public API value."""
from abc import ABC, abstractmethod
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
from functools import lru_cache
from .windows_acl import inspect_private_acl
from django.conf import settings
from modules.portfolios.services import PortfolioProblem

@lru_cache(maxsize=8)
def verify_windows_acl(root):
    try:
        inspect_private_acl(root)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise PortfolioProblem('media_unavailable','Les permissions Windows du stockage doivent être privées.',503) from exc



class BinaryStorage(ABC):
    @abstractmethod
    def write(self,key,full,thumbnail): ...
    @abstractmethod
    def open(self,key,variant,digest,size): ...
    @abstractmethod
    def delete(self,key): ...


class PrivateLocalStorage(BinaryStorage):
    def __init__(self):
        configured=os.environ.get('SAAS_MEDIA_ROOT')
        if not configured:
            raise PortfolioProblem('media_unavailable','Le stockage privé des images n’est pas configuré.',503)
        root=Path(configured)
        repo=Path(settings.BASE_DIR).parent.resolve()
        if any(part.lower()=='.local' for part in root.parts) or not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise PortfolioProblem('media_unavailable','Le stockage privé est indisponible.',503)
        for parent in [root,*root.parents]:
            if parent.is_symlink() or (hasattr(parent,'is_junction') and parent.is_junction()):raise PortfolioProblem('media_unavailable','Le stockage privé est indisponible.',503)
        if root.resolve().is_relative_to(repo) or root==Path(root.anchor):
            raise PortfolioProblem('media_unavailable','Le stockage doit être dédié et hors du dépôt.',503)
        if os.name!='nt' and root.stat().st_mode & 0o077:
            raise PortfolioProblem('media_unavailable','Les permissions du stockage privé doivent être restreintes.',503)
        marker=root/'.portfolio-media-v1'
        if marker.is_symlink() or not marker.is_file() or marker.stat().st_size!=19 or marker.read_bytes()!=b'portfolio-media-v1\n':
            raise PortfolioProblem('media_unavailable','Le répertoire doit être initialisé et dédié aux médias.',503)
        if os.name=='nt':verify_windows_acl(str(root.resolve()))
        self.root=root.resolve()

    def directory(self,key):
        if not isinstance(key,str) or re.fullmatch(r'[0-9a-f]{64}',key) is None:raise OSError('Invalid private key')
        path=self.root/key
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()) or not path.resolve().is_relative_to(self.root):raise OSError('Unsafe private path')
        return path

    def write(self,key,full,thumbnail):
        path=self.directory(key)
        if shutil.disk_usage(self.root).free < len(full)+len(thumbnail)+64*1024*1024:
            raise OSError('Private disk capacity')
        path.mkdir(mode=0o700,exist_ok=False)
        try:
            for name,data in [('full.webp',full),('thumbnail.webp',thumbnail)]:
                flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0)
                fd=os.open(path/name,flags,0o600)
                with os.fdopen(fd,'wb') as file:
                    file.write(data);file.flush();os.fsync(file.fileno())
        except BaseException:
            self.delete(key)
            raise

    def open(self,key,variant,digest,size):
        if variant not in ('full','thumbnail'):raise OSError('Unknown private variant')
        path=self.directory(key)/(variant+'.webp')
        if path.is_symlink() or not path.is_file():raise FileNotFoundError()
        fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
        file=os.fdopen(fd,'rb')
        try:
            if os.fstat(fd).st_size != size:raise FileNotFoundError()
            actual=hashlib.file_digest(file,'sha256').hexdigest()
            if actual!=digest:raise FileNotFoundError()
            file.seek(0);return file
        except BaseException:
            file.close();raise

    def delete(self,key):
        directory=self.directory(key)
        if not directory.exists():return
        for name in ('full.webp','thumbnail.webp'):
            path=directory/name
            if path.is_symlink():raise OSError('Unsafe private file')
            path.unlink(missing_ok=True)
        directory.rmdir()  # Unknown files are preserved; never recursively delete.


def get_storage() -> BinaryStorage:
    """Single adapter factory. A future object adapter must keep private streaming semantics."""
    return PrivateLocalStorage()
