# integration_tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from workflows.models import Workflow, Node, WorkflowExecution
from unittest.mock import patch
import json

User = get_user_model()

class UserWorkflowIntegrationTest(APITestCase):
    def setUp(self):
        # Create clients
        self.client = APIClient()
        
        # URLs
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        self.workflows_url = reverse('workflow-list')
        self.nodes_url = reverse('node-list')

        self.user = get_user_model().objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
        )
        
    def test_complete_user_workflow_flow(self):
        """Test a complete flow from user registration to workflow execution"""
        
        # 1. Register a new user
        register_data = {
            'username': 'integration_user',
            'email': 'integration@example.com',
            'password': 'integration123',
            'password2': 'integration123',
            'first_name': 'Integration',
            'last_name': 'Test'
        }
        
        response = self.client.post(self.register_url, register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2. Login and get token
        login_data = {
            'username': 'integration_user',
            'password': 'integration123'
        }
        
        response = self.client.post(self.token_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        
        # 3. Create a workflow
        workflow_data = {
            'name': 'Integration Workflow',
            'config': {'continue_on_error': True},
            'user': self.user.id,
        }
        
        response = self.client.post(self.workflows_url, workflow_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Integration Workflow')
        workflow_id = response.data['id']
        
        # 4. Create nodes for the workflow
        node1_data = {
            'workflow': workflow_id,
            'type': 'text_input',
            'config': {},
            'order': 1
        }
        
        response = self.client.post(self.nodes_url, node1_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        node2_data = {
            'workflow': workflow_id,
            'type': 'openai_tts',
            'config': {'voice': 'alloy'},
            'order': 2
        }
        
        response = self.client.post(self.nodes_url, node2_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Execute the workflow
        with patch('workflows.tasks.run_workflow.delay') as mock_run_workflow:
            workflow_execute_url = reverse('workflow-execute', kwargs={'pk': workflow_id})
            response = self.client.post(workflow_execute_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('execution_id', response.data)
            
            # Verify Celery task was called
            execution_id = response.data['execution_id']
            mock_run_workflow.assert_called_once_with(workflow_id, execution_id)

        # 6. Check workflow execution status
        workflow_executions_url = reverse('workflowexecution-list')
        response = self.client.get(workflow_executions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'pending')
        
    def test_multi_user_isolation(self):
        """Test that workflows are isolated between users"""
        
        # 1. Create two users
        user1_data = {
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'user1pass123',
            'password2': 'user1pass123',
            'first_name': 'User',
            'last_name': 'One'
        }
        
        user2_data = {
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'user2pass123',
            'password2': 'user2pass123',
            'first_name': 'User',
            'last_name': 'Two'
        }
        
        self.client.post(self.register_url, user1_data, format='json')
        self.client.post(self.register_url, user2_data, format='json')
        
        # 2. Login as user1 and create a workflow
        login_response = self.client.post(self.token_url, 
                                         {'username': 'user1', 'password': 'user1pass123'}, 
                                         format='json')
        token1 = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        
        workflow_data = {
            'name': 'User1 Workflow',
            'config': {'continue_on_error': True},
            'user': get_user_model().objects.get(username='user1').id
        }
        
        response = self.client.post(self.workflows_url, workflow_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        workflow1_id = response.data['id']
        
        # 3. Login as user2 and create a workflow
        login_response = self.client.post(self.token_url, 
                                         {'username': 'user2', 'password': 'user2pass123'}, 
                                         format='json')
        token2 = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        workflow_data = {
            'name': 'User2 Workflow',
            'config': {'continue_on_error': False},
            'user': get_user_model().objects.get(username='user2').id
        }
        
        response = self.client.post(self.workflows_url, workflow_data, format='json')
        workflow2_id = response.data['id']
        
        # 4. Verify user1 can only see their workflow
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        
        response = self.client.get(self.workflows_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'User1 Workflow')
        
        # 5. Verify user2 can only see their workflow
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        response = self.client.get(self.workflows_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'User2 Workflow')
        
        # 6. Verify user2 cannot access user1's workflow
        workflow1_url = reverse('workflow-detail', kwargs={'pk': workflow1_id})
        response = self.client.get(workflow1_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 7. Verify user2 cannot add nodes to user1's workflow
        node_data = {
            'workflow': workflow1_id,
            'type': 'text_input',
            'config': {},
            'order': 1
        }
        
        response = self.client.post(self.nodes_url, node_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)