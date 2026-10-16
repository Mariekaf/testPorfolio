from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import Portfolio
from .serializers import PortfolioSerializer

class PortfolioBase(APIView):
    permission_classes = [IsAuthenticated]
    def owned(self, request, pk):
        return get_object_or_404(Portfolio, pk=pk, owner=request.user, deleted_at__isnull=True)
    def invalid(self, error):
        return Response({"error":{"code":"validation_error","fields":error.errors,"message":"Vérifiez les informations du portfolio."}},status=400)

class PortfolioList(PortfolioBase):
    def get(self, request):
        paginator = PageNumberPagination()
        paginator.page_size = 12
        paginator.max_page_size = 12
        queryset = Portfolio.objects.filter(owner=request.user, deleted_at__isnull=True)
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(PortfolioSerializer(page,many=True).data)
    def post(self, request):
        serializer=PortfolioSerializer(data=request.data)
        if not serializer.is_valid(): return self.invalid(serializer)
        try:
            with transaction.atomic():
                instance=serializer.save(owner=request.user)
        except IntegrityError:
            return Response({"error":{"code":"slug_conflict","message":"Ce slug est déjà utilisé."}},status=409)
        return Response(PortfolioSerializer(instance).data,status=201)

class PortfolioDetail(PortfolioBase):
    def get(self, request, pk):
        return Response(PortfolioSerializer(self.owned(request,pk)).data)
    def patch(self, request, pk):
        instance=self.owned(request,pk)
        serializer=PortfolioSerializer(instance,data=request.data,partial=True)
        if not serializer.is_valid(): return self.invalid(serializer)
        try:
            with transaction.atomic(): instance=serializer.save()
        except IntegrityError:
            return Response({"error":{"code":"slug_conflict","message":"Ce slug est déjà utilisé."}},status=409)
        return Response(PortfolioSerializer(instance).data)
    def delete(self, request, pk):
        instance=self.owned(request,pk)
        instance.deleted_at=timezone.now()
        instance.save(update_fields=["deleted_at","updated_at"])
        return Response(status=204)

class PortfolioDuplicate(PortfolioBase):
    def post(self, request, pk):
        original=self.owned(request,pk)
        # UUID-based suffix prevents concurrent duplicate collisions; source remains unchanged.
        from uuid import uuid4
        slug=(original.slug[:95].rstrip("-")+"-"+uuid4().hex[:12])
        with transaction.atomic():
            duplicate=Portfolio.objects.create(owner=request.user,name=original.name+" (copie)" if len(original.name)<=92 else original.name[:92]+" (copie)",slug=slug,description=original.description,portfolio_type=original.portfolio_type)
        return Response(PortfolioSerializer(duplicate).data,status=201)
