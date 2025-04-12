from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from ..models import Workflow, Node, WorkflowExecution
import uuid

User = get_user_model()

class WorkflowViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            user=self.user
        )
        self.url = reverse('workflow-list')

    def test_create_workflow(self):
        data = {
            'name': 'New Workflow',
            'description': 'Test Description',
            'tags': ['test'],
            'metadata': {'category': 'test'}
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workflow.objects.count(), 2)
        self.assertEqual(Workflow.objects.get(name='New Workflow').user, self.user)

    def test_list_workflows(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_validate_workflow(self):
        url = reverse('workflow-validate', kwargs={'pk': self.workflow.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_valid', response.data)
        self.assertIn('errors', response.data)

    def test_execute_workflow(self):
        # Create a valid node first
        Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Test Node',
            order=1
        )
        
        url = reverse('workflow-execute', kwargs={'pk': self.workflow.pk})
        data = {
            'variables': {'input_text': 'test'},
            'context': {'environment': 'test'}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('execution_id', response.data)
        self.assertEqual(response.data['status'], 'started')

class NodeViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            user=self.user
        )
        self.node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Test Node',
            order=1
        )
        self.url = reverse('node-list')

    def test_create_node(self):
        data = {
            'workflow': self.workflow.id,
            'type': 'text_input',
            'name': 'New Node',
            'order': 2,
            'position_x': 100,
            'position_y': 200
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Node.objects.count(), 2)

    def test_create_node_unauthorized(self):
        # Create another user's workflow
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        other_workflow = Workflow.objects.create(
            name='Other Workflow',
            user=other_user
        )
        
        data = {
            'workflow': other_workflow.id,
            'type': 'text_input',
            'name': 'New Node',
            'order': 1
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_nodes(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class WorkflowExecutionViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            user=self.user
        )
        self.execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            execution_id=uuid.uuid4(),
            started_by=self.user
        )
        self.url = reverse('workflowexecution-list')

    def test_list_executions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_execution(self):
        url = reverse('workflowexecution-detail', kwargs={'pk': self.execution.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.execution.id)

    def test_list_executions_unauthorized(self):
        # Create another user's execution
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        other_workflow = Workflow.objects.create(
            name='Other Workflow',
            user=other_user
        )
        WorkflowExecution.objects.create(
            workflow=other_workflow,
            execution_id=uuid.uuid4(),
            started_by=other_user
        )
        
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)  # Should only see own executions 