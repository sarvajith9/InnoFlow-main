from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIModelConfigViewSet,
    ModelComparisonViewSet,
    TaskStatusViewSet
)

router = DefaultRouter()
router.register(r'models', AIModelConfigViewSet, basename='aimodelconfig')
router.register(r'comparisons', ModelComparisonViewSet, basename='modelcomparison')
router.register(r'tasks', TaskStatusViewSet, basename='taskstatus')

urlpatterns = [
    path('', include(router.urls)),
]