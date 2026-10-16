import logging
from django.db import DatabaseError, connection
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("foundations.health")


@method_decorator(never_cache, name="dispatch")
class LiveView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "portfolio-api", "schema_version": 1})


class ReadyView(LiveView):
    def get(self, request):
        try:
            if connection.vendor != "postgresql":
                raise DatabaseError
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                # A live DB without initial migrations is not a ready application.
                cursor.execute('SELECT 1 FROM "identity_user" LIMIT 0')
        except DatabaseError:
            logger.warning("PostgreSQL readiness check failed; connection details omitted.")
            return Response({"status": "unavailable", "service": "portfolio-api", "schema_version": 1}, status=503)
        return Response({"status": "ok", "service": "portfolio-api", "schema_version": 1})
