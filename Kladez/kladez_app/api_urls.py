# kladez_app/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    CompletedWorkViewSet, CarBrandViewSet, 
    CarModelViewSet, RepairTypeViewSet, RepairCategoryViewSet
)

router = DefaultRouter()
router.register(r'completed-works', CompletedWorkViewSet, basename='completed-work')
router.register(r'car-brands', CarBrandViewSet, basename='car-brand')
router.register(r'car-models', CarModelViewSet, basename='car-model')
router.register(r'repair-types', RepairTypeViewSet, basename='repair-type')
router.register(r'repair-categories', RepairCategoryViewSet, basename='repair-category')

urlpatterns = [
    path('', include(router.urls)),
]