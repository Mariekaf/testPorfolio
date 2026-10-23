from django.urls import path
from .views import AssetList,AssetDetail,AssetFile
urlpatterns=[path('/assets',AssetList.as_view()),path('/assets/<uuid:pk>',AssetDetail.as_view()),
    path('/assets/<uuid:pk>/file',AssetFile.as_view()),
    path('/assets/<uuid:pk>/thumbnail',AssetFile.as_view(),{'variant':'thumbnail'})]
