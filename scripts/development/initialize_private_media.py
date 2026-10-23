"""Initialize a NEW dedicated media directory only. No database or existing files."""
import argparse
import csv
import io
import os
from pathlib import Path
import subprocess


def initialize(directory):
    root=Path(directory)
    repo=Path(__file__).resolve().parents[2]
    if any(part.lower()=='.local' for part in root.parts) or not root.is_absolute() or root.exists() or root.is_symlink() or root.resolve().is_relative_to(repo):
        raise ValueError('Choose a new absolute directory outside the repository.')
    for parent in root.parents:
        if parent.is_symlink() or (hasattr(parent,'is_junction') and parent.is_junction()):
            raise ValueError('Private storage cannot cross symlinks or junctions.')
    root.mkdir(mode=0o700,parents=False,exist_ok=False)
    if os.name=='nt':
        row=next(csv.reader(io.StringIO(subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True))))
        sid=row[1]
        subprocess.run(['icacls',str(root),'/inheritance:r','/grant:r',f'*{sid}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F'],check=True,stdout=subprocess.DEVNULL)
    marker=root/'.portfolio-media-v1'
    with os.fdopen(os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as file:
        file.write(b'portfolio-media-v1\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',required=True)
    try:
        initialize(parser.parse_args().directory)
        print('New private media directory initialized. No database or existing file modified.')
    except (ValueError,OSError,subprocess.CalledProcessError):
        parser.exit(1,'Private initialization failed; choose a fresh dedicated directory. No existing directory is adopted.\n')
