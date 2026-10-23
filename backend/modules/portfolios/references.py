"""Versioned descriptors only. No template catalogue or theme rendering engine."""
import json
from functools import lru_cache
from pathlib import Path
from jsonschema import Draft202012Validator

DEFAULT_THEME_ID='studio-neutral'
DEFAULT_THEME_VERSION='1.0.0'

@lru_cache(maxsize=1)
def default_theme():
    root=Path(__file__).resolve().parents[3]
    schema=json.loads((root/'contracts/schemas/themes/theme.v1.json').read_text(encoding='utf-8'))
    descriptor=json.loads((root/'contracts/themes/studio-neutral.v1.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(descriptor)
    if (descriptor['id'],descriptor['version'])!=(DEFAULT_THEME_ID,DEFAULT_THEME_VERSION):
        raise ValueError('Default theme reference mismatch; no content logged.')
    return descriptor
