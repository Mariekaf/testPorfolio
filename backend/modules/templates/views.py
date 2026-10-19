"""B exposes authenticated reads only; no portfolio creation/design write API."""
from rest_framework.response import Response
from modules.portfolios.views import PortfolioBase
from .registry import CATEGORIES, RegistryInvalid, TemplateRegistry

class TemplateRead(PortfolioBase):
    http_method_names = ['get', 'head', 'options']

    def get(self, request, template_id=None, version=None, preview=False):
        try:
            registry = TemplateRegistry()
        except RegistryInvalid:
            return Response({'error': {'code': 'temporarily_unavailable', 'message': 'Bibliothèque temporairement indisponible.'}}, status=503)
        if template_id is not None:
            if request.query_params:
                return self.invalid()
            item = registry.get(template_id, version)
            if item is None:
                return Response({'error': {'code': 'not_found', 'message': 'Template introuvable.'}}, status=404)
            if preview and item['descriptor']['availability'] != 'available':
                return Response({'error': {'code': 'template_unavailable', 'message': 'Cet aperçu est indisponible.'}}, status=409)
            return Response(item['snapshot'] if preview else item['descriptor'])
        query = request.query_params
        if set(query) - {'category', 'availability', 'page'} or any(len(query.getlist(k)) != 1 for k in query):
            return self.invalid()
        category, availability = query.get('category'), query.get('availability', 'available')
        page = query.get('page', '1')
        if (category is not None and category not in CATEGORIES) or availability not in ['available', 'unavailable', 'retired'] or not page.isascii() or not page.isdecimal() or len(page) > 6 or int(page) < 1:
            return self.invalid()
        items = registry.catalogue(category, availability)
        start = (int(page) - 1) * 12
        return Response({'count': len(items), 'page': int(page), 'page_size': 12, 'results': items[start:start+12]})

    @staticmethod
    def invalid():
        return Response({'error': {'code': 'invalid_request', 'message': 'Paramètres de bibliothèque invalides.'}}, status=400)
