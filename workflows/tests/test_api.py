# workflows/tests/test_api.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from workflows.models import Workflow, Node, WorkflowExecution
import json
from unittest.mock import patch

User = get_user_model()

class WorkflowAPITest(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123',
        )
        
        # Create test workflows
        self.workflow1 = Workflow.objects.create(
            name="User1 Workflow",
            user=self.user1,
            config={'continue_on_error': True}
        )
        
        self.workflow2 = Workflow.objects.create(
            name="User2 Workflow",
            user=self.user2,
            config={'continue_on_error': False}
        )
        
        # Create test nodes
        self.node1 = Node.objects.create(
            workflow=self.workflow1,
            type="text_input",
            config={},
            order=1
        )
        
        # URLs
        self.workflows_url = reverse('workflow-list')
        self.workflow1_detail_url = reverse('workflow-detail', kwargs={'pk': self.workflow1.id})
        self.workflow1_execute_url = reverse('workflow-execute', kwargs={'pk': self.workflow1.id})
        self.nodes_url = reverse('node-list')
        
        # API client
        self.client = APIClient()
        
    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
    def authenticate(self, user):
        tokens = self.get_tokens_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    
    def test_get_workflows_list(self):
        """Test that users can only see their own workflows"""
        # Authenticate as user1
        self.authenticate(self.user1)
        
        # Get workflows
        response = self.client.get(self.workflows_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # User1 should see only 1 workflow
        self.assertEqual(response.data[0]['name'], 'User1 Workflow')
        
        # Authenticate as user2
        self.authenticate(self.user2)
        
        # Get workflows
        response = self.client.get(self.workflows_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # User2 should see only 1 workflow
        self.assertEqual(response.data[0]['name'], 'User2 Workflow')
    
    def test_create_workflow(self):
        """Test workflow creation"""
        self.authenticate(self.user1)
        
        data = {
            'name': 'New Workflow',
            'config': {'continue_on_error': True},
            'user': self.user1.id 
        }
        
        response = self.client.post(self.workflows_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workflow.objects.count(), 3)
        
        # Check the workflow was created with correct data
        new_workflow = Workflow.objects.get(name='New Workflow')
        self.assertEqual(new_workflow.user, self.user1)
        self.assertEqual(new_workflow.config, {'continue_on_error': True})
    
    def test_workflow_detail(self):
        """Test that users can access their workflow details but not others'"""
        # Authenticate as user1
        self.authenticate(self.user1)
        
        # Get own workflow
        response = self.client.get(self.workflow1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'User1 Workflow')
        
        # Try to get user2's workflow
        workflow2_detail_url = reverse('workflow-detail', kwargs={'pk': self.workflow2.id})
        response = self.client.get(workflow2_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('workflows.tasks.run_workflow.delay')
    def test_execute_workflow(self, mock_run_workflow):
        """Test workflow execution"""
        self.authenticate(self.user1)
        
        response = self.client.post(self.workflow1_execute_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(WorkflowExecution.objects.count(), 1)
        
        # Check that Celery task was called
        execution = WorkflowExecution.objects.first()
        mock_run_workflow.assert_called_once_with(self.workflow1.id, execution.id)
        
        # Check execution status
        self.assertEqual(execution.status, 'pending')
    
    def test_create_node(self):
        """Test node creation"""
        self.authenticate(self.user1)
        
        data = {
            'workflow': self.workflow1.id,
            'type': 'openai_tts',
            'config': {'voice': 'echo'},
            'order': 2
        }
        
        response = self.client.post(self.nodes_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Node.objects.count(), 2)
        
        # Check the node was created with correct data
        new_node = Node.objects.get(order=2)
        self.assertEqual(new_node.workflow, self.workflow1)
        self.assertEqual(new_node.type, 'openai_tts')
        self.assertEqual(new_node.config, {'voice': 'echo'})
    
    def test_cannot_create_node_for_others_workflow(self):
        """Test users can't create nodes for workflows they don't own"""
        self.authenticate(self.user1)
        
        data = {
            'workflow': self.workflow2.id,  # User2's workflow
            'type': 'text_input',
            'config': {},
            'order': 1
        }
        
        response = self.client.post(self.nodes_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_node_validation(self):
        """Test node type validation"""
        self.authenticate(self.user1)
        
        # Test with invalid node type
        data = {
            'workflow': self.workflow1.id,
            'type': 'invalid_type',
            'config': {},
            'order': 3
        }
        
        response = self.client.post(self.nodes_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with missing required config
        data = {
            'workflow': self.workflow1.id,
            'type': 'openai_tts',
            'config': {},  # Missing 'voice'
            'order': 3
        }
        
        response = self.client.post(self.nodes_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)