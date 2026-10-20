from django.urls import path, include
from config.health import LiveView, ReadyView
from modules.identity import views as auth

urlpatterns = [
    path("health/live", LiveView.as_view(), name="health-live"),
    path("health/ready", ReadyView.as_view(), name="health-ready"),
    path("api/v1/health/live", LiveView.as_view(), name="api-health-live"),
    path("api/v1/health/ready", ReadyView.as_view(), name="api-health-ready"),
]

urlpatterns += [
    path("api/v1/auth/" + route, view.as_view()) for route, view in [
        ("csrf", auth.CsrfView), ("register", auth.RegisterView),
        ("login", auth.LoginView), ("logout", auth.LogoutView), ("me", auth.MeView),
        ("password-reset", auth.PasswordResetView),
        ("password-reset/confirm", auth.PasswordResetConfirmView),
    ]
]

urlpatterns += [path("api/v1/portfolios", include("modules.portfolios.urls"))]

# TPL-001.B: authenticated, read-only catalogue and preview bundles.
urlpatterns += [path("api/v1/templates", include("modules.templates.urls"))]

# E0704 private MVP; does not promote the immutable draft catalogue.
from modules.templates.ready_instances import ReadyTemplates, ReadyCreate, ReadyDetail, ReadyValidate, ReadyRevisions
urlpatterns += [
    path('api/v1/ready-templates', ReadyTemplates.as_view()),
    path('api/v1/ready-portfolios', ReadyCreate.as_view()),
    path('api/v1/ready-portfolios/<uuid:pk>', ReadyDetail.as_view()),
    path('api/v1/ready-portfolios/<uuid:pk>/validate', ReadyValidate.as_view()),
    path('api/v1/ready-portfolios/<uuid:pk>/revisions', ReadyRevisions.as_view()),
]
