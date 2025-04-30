from django.urls import path
from rest_framework.routers import DefaultRouter

from api.versioned.v1.concept.views import ConceptViewSet

router = DefaultRouter()
router.register(r'concepts', ConceptViewSet, basename='concept')

urlpatterns = [
    
] + router.urls