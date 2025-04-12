from rest_framework import serializers
from .models import AIModelConfig, ModelComparison, ModelResponse

class AIModelConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModelConfig
        fields = ['id', 'name', 'provider', 'model_name', 'is_active']

class ModelResponseSerializer(serializers.ModelSerializer):
    model_config = AIModelConfigSerializer()
    
    class Meta:
        model = ModelResponse
        fields = ['id', 'model_config', 'response', 'latency', 'created_at']

class ModelComparisonSerializer(serializers.ModelSerializer):
    responses = ModelResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = ModelComparison
        fields = ['id', 'prompt', 'created_at', 'responses']

class CompareModelsSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    model_ids = serializers.ListField(child=serializers.IntegerField())