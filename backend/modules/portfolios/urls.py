from django.urls import path
from modules.templates.instance_views import TemplateCreate,DesignDetail
from modules.templates.transition_views import DesignTransitionView,DesignRevisions
from .views import PortfolioList,PortfolioDetail,PortfolioAction
urlpatterns=[path('/from-template',TemplateCreate.as_view()),path('/<uuid:pk>/design',DesignDetail.as_view()),path('',PortfolioList.as_view()),path('/<uuid:pk>',PortfolioDetail.as_view())]
for action in ['upgrade','restore']:
    urlpatterns.append(path('/<uuid:pk>/design/'+action, DesignTransitionView.as_view(action=action)))
urlpatterns += [path('/<uuid:pk>/design/revisions', DesignRevisions.as_view()), path('/<uuid:pk>/design/revisions/<uuid:revision_id>', DesignRevisions.as_view())]
for action in ['duplicate','archive','restore']:
    urlpatterns.append(path('/<uuid:pk>/'+action,PortfolioAction.as_view(action=action)))
