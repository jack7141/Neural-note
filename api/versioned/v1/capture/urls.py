from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CaptureViewSet, StatusViewSet

router = DefaultRouter()
router.register(r'capture', CaptureViewSet, basename='capture')

urlpatterns = [
    path('', StatusViewSet.as_view({'get': 'get'}))
] + router.urls