from django.contrib import admin
from django.urls import path, include
from apps.common.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check
    path('api/v1/health/', HealthCheckView.as_view(), name='api-health'),

    # API v1 routes
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/faqs/', include('apps.faqs.urls')),
    path('api/v1/chat/', include('apps.chatbot.urls')),
    path('api/v1/conversations/', include('apps.conversations.urls')),
    path('api/v1/knowledge/', include('apps.knowledge_base.urls')),
]
