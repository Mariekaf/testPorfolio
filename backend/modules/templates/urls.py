from django.urls import path
from .views import TemplateRead

urlpatterns = [
    path('', TemplateRead.as_view()),
    path('/<slug:template_id>/versions/<str:version>', TemplateRead.as_view()),
    path('/<slug:template_id>/versions/<str:version>/preview', TemplateRead.as_view(), {'preview': True}),
]
