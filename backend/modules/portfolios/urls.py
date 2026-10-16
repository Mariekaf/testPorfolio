from django.urls import path
from .views import PortfolioList, PortfolioDetail, PortfolioDuplicate
urlpatterns = [
    path("",PortfolioList.as_view()),
    path("<uuid:pk>/",PortfolioDetail.as_view()),
    path("<uuid:pk>/duplicate/",PortfolioDuplicate.as_view()),
]
