# tests.py (continued)
class IntegrationTests(APITestCase):
    @patch('ai_integration.tasks.run_ai_model_task.delay')
    def test_full_workflow(self, mock_task):
        mock_task.return_value.id = 'mock-task-id'
        
        # Create test models
        config1 = AIModelConfig.objects.create(
            name="Integration Model 1",
            provider="OPENAI",
            model_name="gpt-4",
            api_key="key1"
        )
        config2 = AIModelConfig.objects.create(
            name="Integration Model 2",
            provider="ANTHROPIC",
            model_name="claude-2",
            api_key="key2"
        )
        
        # Start comparison
        data = {
            "prompt": "Integration test prompt",
            "model_ids": [config1.id, config2.id]
        }
        response = self.client.post('/comparisons/compare_models/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check comparison was created
        comparison_id = response.data['comparison_id']
        comparison = ModelComparison.objects.get(id=comparison_id)
        self.assertEqual(comparison.prompt, "Integration test prompt")
        
        # Check tasks were created
        self.assertEqual(len(response.data['task_ids']), 2)
        
        # Simulate task completion
        ModelResponse.objects.create(
            comparison=comparison,
            model_config=config1,
            response="Response 1",
            latency=1.0
        )
        ModelResponse.objects.create(
            comparison=comparison,
            model_config=config2,
            response="Response 2",
            latency=2.0
        )
        
        # Check results
        response = self.client.get(f'/comparisons/{comparison_id}/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['responses']), 2)
        self.assertEqual(response.data['responses'][0]['latency'], 1.0)
        self.assertEqual(response.data['responses'][1]['latency'], 2.0)