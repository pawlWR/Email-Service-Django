from django.urls import path
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Email Service API",
        default_version='v1',
        description="API documentation for Email Service",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('send-email/', SendEmailView.as_view(), name='send_email'),
    path('check-status/', CheckStatusView.as_view(), name='check_status'),
    path('test-connection/', TestConnectionView.as_view(), name='test_connection'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

]
