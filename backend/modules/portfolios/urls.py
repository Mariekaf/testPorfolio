from django.urls import path
from .views import PortfolioList,PortfolioDetail,PortfolioAction
urlpatterns=[path('',PortfolioList.as_view()),path('/<uuid:pk>',PortfolioDetail.as_view())]
for action in ['duplicate','archive','restore']:
    urlpatterns.append(path('/<uuid:pk>/'+action,PortfolioAction.as_view(action=action)))
