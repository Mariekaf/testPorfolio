"""E.02 offline tests: unittest only; no Django setup or database connection."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from modules.templates.hero_contracts import (
    ROOT, HeroCapabilities, HeroContractError, contrast_ratio,
    read_json, schema_validator, validate_schema,
)

CORPUS = json.loads((ROOT/'contracts/fixtures/hero/cases.v1.json').read_text(encoding='utf-8'))


class SharedCases(unittest.TestCase):
    pass


def check_case(case):
    def test(self):
        registry = HeroCapabilities()
        document = case['document']
        before = copy.deepcopy(document)
        def run():
            if case['target'] == 'hero':
                registry.validate_hero(document)
            elif case['target'] == 'design':
                registry.validate_design(document)
            elif case['target'] == 'registry':
                HeroCapabilities(document=document)
            else:
                registry.require_selectable(document)
        if case['valid']:
            run()
        else:
            with self.assertRaises(HeroContractError):
                run()
        self.assertEqual(document, before)
    return test


for case in CORPUS['cases']:
    setattr(SharedCases, 'test_'+case['id'].replace('-', '_'), check_case(case))


class ContractBoundaries(unittest.TestCase):
    def test_every_schema_is_well_formed_and_resolves(self):
        for path in [*ROOT.glob('contracts/schemas/hero/*.json'), *ROOT.glob('contracts/schemas/templates/documents/*.v2.json')]:
            schema_validator(path.relative_to(ROOT/'contracts/schemas'))

    def test_registry_results_are_independent_and_never_selectable(self):
        registry = HeroCapabilities()
        result = registry.document()
        result['layouts'][0]['implemented'] = True
        self.assertFalse(registry.document()['layouts'][0]['implemented'])
        self.assertEqual(registry.selectable_layouts(), [])

    def test_exact_contrast_threshold(self):
        self.assertAlmostEqual(contrast_ratio('#000000', '#FFFFFF'), 21)
        self.assertEqual(contrast_ratio('#222222', '#222222'), 1)
        self.assertGreaterEqual(contrast_ratio('#767676', '#FFFFFF'), 4.5)
        self.assertLess(contrast_ratio('#777777', '#FFFFFF'), 4.5)
        for color in ['red', '#000000\n', 'url(file:///tmp/a)']:
            with self.assertRaises(HeroContractError):
                contrast_ratio(color, '#FFFFFF')

    def test_bounded_size_nan_and_duplicate_json(self):
        with self.assertRaises(HeroContractError):
            validate_schema('hero/hero-config.v1.json', {'schema_version':1, 'value':'a'*262144})
        with self.assertRaises(HeroContractError):
            validate_schema('hero/hero-config.v1.json', {'schema_version':1, 'value':float('nan')})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'fixture.json'
            for value in ['{"schema_version":1,"schema_version":2}', '{"x":NaN}']:
                path.write_text(value, encoding='utf-8')
                with self.assertRaises(HeroContractError):
                    read_json(path)

    def test_schema_path_traversal_rejected(self):
        with self.assertRaises(HeroContractError):
            schema_validator('../../../package.json')

    def test_v1_bundles_still_validate_and_digests_match(self):
        from modules.templates.registry import TemplateRegistry
        self.assertEqual(len(TemplateRegistry().catalogue()), 2)
        manifest = read_json(ROOT/'contracts/templates/manifest.v1.json')
        for entry in manifest['entries']:
            for file in entry['files']:
                self.assertEqual(hashlib.sha256((ROOT/'contracts/templates'/file['path']).read_bytes()).hexdigest(), file['sha256'])

    def test_active_validation_still_rejects_v2(self):
        document = next(c['document'] for c in CORPUS['cases'] if c['id']=='design-matrix')
        with self.assertRaises(HeroContractError):
            validate_schema('templates/documents/snapshot.v1.json', document)

    def test_proposed_openapi_references_and_request_response_matrix(self):
        spec = read_json(ROOT/'docs/tpl001/e02/openapi.v2.proposed.json')
        self.assertEqual(spec['x-activation-status'], 'proposed-not-active')
        active = (ROOT/'contracts/api/openapi.yaml').read_text(encoding='utf-8')
        self.assertNotIn('openapi.v2.proposed', active)
        self.assertNotIn('/upgrade', '\n'.join(spec['paths']))
        for case in CORPUS['cases']:
            if case['id'] != 'design-matrix':
                continue
            design = case['document']
            # External schema targets used by the proposed OpenAPI.
            validate_schema('templates/documents/snapshot.v2.json', design)
            validate_schema('templates/documents/content.v1.json', design['content'])
            validate_schema('templates/documents/customization.v2.json', design['customization'])
        def refs(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    yield value['$ref']
                for child in value.values():
                    yield from refs(child)
            elif isinstance(value, list):
                for child in value:
                    yield from refs(child)
        path = ROOT/'docs/tpl001/e02/openapi.v2.proposed.json'
        for reference in refs(spec):
            if reference.startswith('#/'):
                node = spec
                for part in reference[2:].split('/'):
                    node = node[part]
            else:
                self.assertTrue((path.parent/reference).resolve().is_file())

    def test_proposed_openapi_validates_real_documents_and_closed_updates(self):
        path = ROOT/'docs/tpl001/e02/openapi.v2.proposed.json'
        def retrieve(uri):
            parsed = urlparse(uri)
            self.assertEqual(parsed.scheme, 'file')
            self.assertFalse(parsed.netloc)
            value = unquote(parsed.path)
            if len(value) > 2 and value[0] == '/' and value[2] == ':':
                value = value[1:]
            target = Path(value).resolve()
            self.assertTrue(target.is_relative_to(ROOT/'contracts') or target == path)
            return Resource.from_contents(read_json(target), default_specification=DRAFT202012)
        def validator(name):
            return Draft202012Validator({'$ref':path.as_uri()+'#/components/schemas/'+name},
                registry=Registry(retrieve=retrieve), format_checker=FormatChecker())
        document = next(c['document'] for c in CORPUS['cases'] if c['id']=='design-matrix')
        response = {'portfolio_id':'00000000-0000-4000-8000-000000000001',
                    'version':1, 'etag':'"test-etag"', 'snapshot':document}
        validator('Design').validate(response)
        update = {k:document[k] for k in ['content', 'customization']}
        validator('DesignUpdate').validate(update)
        for change in [dict(update, experience=None), dict(update, customization={'schema_version':3,'sections':[]})]:
            with self.assertRaises(ValidationError):
                validator('DesignUpdate').validate(change)
        validator('Error').validate({'error':{'code':'design_schema_not_acceptable','message':'Version non prise en charge.'}})
        active = read_json(ROOT/'contracts/api/template-instances.v1.json')
        proposed = read_json(path)
        self.assertEqual(active['components']['securitySchemes'], proposed['components']['securitySchemes'])


if __name__ == '__main__':
    unittest.main()
