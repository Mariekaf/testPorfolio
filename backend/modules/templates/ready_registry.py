"""Offline only. Separate from the user-facing v1 registry; no runtime activation."""
import copy
import hashlib
import json
from pathlib import Path
from .hero_contracts import ROOT
from .ready_contracts import ReadyValidator, ReadyContractError, require, check_schema, bounded, LIMIT, ROLES


def strict_json(raw):
    try:
        return _strict_json(raw)
    except Exception:
        raise ReadyContractError() from None


def _strict_json(raw):
    require(len(raw) <= LIMIT)
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result)
            result[k] = v
        return result
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                       parse_constant=lambda _: require(False))
    require(bounded(value) <= LIMIT)
    return value


class ReadyRegistry:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else ROOT/'contracts/ready-templates'
        self.entries = {}
        try:
            require(not self.root.is_symlink() and self.root.is_dir())
            manifest = strict_json(self.read('manifest.v2.json'))
            check_schema('manifest.v2.json', manifest)
            seen_paths = set()
            for entry in manifest['entries']:
                identity = entry['template']; key = (identity['id'], identity['version'])
                require(key not in self.entries)
                require(entry['status'] in ('draft','deprecated','retired','quarantined'))
                bundle = {}; roles = set()
                for file in entry['files']:
                    role = file['role']; path = file['path']
                    require(role not in roles and path.lower() not in seen_paths)
                    require(path == f'{key[0]}/{key[1]}/{role}.json')
                    roles.add(role); seen_paths.add(path.lower())
                    raw = self.read(path)
                    require(len(raw) == file['bytes'] and hashlib.sha256(raw).hexdigest() == file['sha256'])
                    bundle[role] = strict_json(raw)
                require(roles == set(ROLES))
                files = [{k:f[k] for k in ('path','bytes','sha256')} for f in sorted(entry['files'],key=lambda f:f['path'])]
                digest = hashlib.sha256(json.dumps(files,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
                require(digest == entry['bundle_digest'])
                validator = ReadyValidator(bundle)
                require(identity == bundle['descriptor']['template'])
                self.entries[key] = {'template':identity,'status':entry['status'],'bundle_digest':digest,'bundle':bundle,'validator':validator}
        except Exception:
            raise ReadyContractError() from None

    def read(self, relative):
        require(isinstance(relative,str) and '\\' not in relative)
        parts = relative.split('/')
        require(all(p and p not in ('.','..') and ':' not in p for p in parts))
        path = self.root
        for part in parts:
            path = path/part
            require(not path.is_symlink())
        require(path.resolve().is_relative_to(self.root.resolve()) and path.is_file())
        require(path.stat().st_size <= LIMIT)
        return path.read_bytes()

    def get(self, identity='creative-editorial', version='1.0.0'):
        entry = self.entries.get((identity,version))
        require(entry is not None)
        return copy.deepcopy({k:v for k,v in entry.items() if k != 'validator'})

    def validator(self, identity='creative-editorial', version='1.0.0'):
        require((identity,version) in self.entries)
        return ReadyValidator(self.get(identity,version)['bundle'])
