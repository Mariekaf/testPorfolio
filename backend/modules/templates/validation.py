"""Validate saved instance documents independently of catalogue availability."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource
from .registry import ROOT, LIMIT, RegistryInvalid, validate_snapshot, LAYOUT_VARIANTS
from modules.portfolios.services import PortfolioProblem


def validator():
    def retrieve(uri):
        path = Path.from_uri(uri).resolve()
        if not path.is_relative_to((ROOT/'contracts/schemas').resolve()):
            raise RegistryInvalid('Invalid schema reference.')
        return Resource.from_contents(json.loads(path.read_text(encoding='utf-8')))
    return Draft202012Validator({'$ref':(ROOT/'contracts/schemas/templates/documents/snapshot.v1.json').as_uri()}, registry=Registry(retrieve=retrieve), format_checker=FormatChecker())


def validate_document(snapshot, stored=False):
    try:
        if isinstance(snapshot, dict) and snapshot.get('schema_version') == 2:
            from .hero_resolution import resolve_heroes
            resolve_heroes(snapshot)
            return
        if len(json.dumps(snapshot,ensure_ascii=False).encode('utf-8')) > LIMIT:
            raise RegistryInvalid('Document too large.')
        validator().validate(snapshot)
        validate_snapshot(snapshot)
        if any(s['variant'] not in LAYOUT_VARIANTS[snapshot['composition']['layout']] for s in snapshot['composition']['sections']):
            raise RegistryInvalid('Unsupported variant.')
    except (ValidationError, RegistryInvalid, ValueError, TypeError, KeyError, RecursionError):
        raise PortfolioProblem('design_inconsistent' if stored else 'invalid_design',
            'Le design nécessite une vérification.' if stored else 'Vérifiez les contenus, les liens HTTPS et les réglages autorisés.',409 if stored else 400) from None
    except Exception:
        raise PortfolioProblem('temporarily_unavailable','Les contrats de design sont temporairement indisponibles.',503) from None


def snapshot_of(design):
    return {'schema_version':design.schema_version, **{k:getattr(design,k) for k in ['composition','content','presentation','customization','experience']}}
