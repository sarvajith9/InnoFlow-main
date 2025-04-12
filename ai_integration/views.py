from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AIModelConfig, ModelComparison, ModelResponse
from .serializers import (
    AIModelConfigSerializer,
    ModelComparisonSerializer,
    CompareModelsSerializer
)
from .tasks import run_ai_model_task
from celery.result import AsyncResult
from django.shortcuts import get_object_or_404

class AIModelConfigViewSet(viewsets.ModelViewSet):
    queryset = AIModelConfig.objects.filter(is_active=True)
    serializer_class = AIModelConfigSerializer

class ModelComparisonViewSet(viewsets.ModelViewSet):
    queryset = ModelComparison.objects.all()
    serializer_class = ModelComparisonSerializer
    
    @action(detail=False, methods=['post'])
    def compare_models(self, request):
        serializer = CompareModelsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        prompt = serializer.validated_data['prompt']
        model_ids = serializer.validated_data['model_ids']
        
        # Create comparison record
        comparison = ModelComparison.objects.create(prompt=prompt)
        
        # Start tasks for each model
        task_ids = []
        for model_id in model_ids:
            model_config = get_object_or_404(AIModelConfig, id=model_id, is_active=True)
            task = run_ai_model_task.delay(model_config.id, prompt, comparison.id)
            task_ids.append(task.id)
        
        return Response({
            "comparison_id": comparison.id,
            "task_ids": task_ids
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        comparison = self.get_object()
        serializer = self.get_serializer(comparison)
        return Response(serializer.data)

class TaskStatusViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        task = AsyncResult(pk)
        return Response({
            'task_id': pk,
            'status': task.status,
            'result': task.result if task.ready() else None
        })