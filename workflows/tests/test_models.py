# workflows/tests/test_models.py
from django.test import TestCase
from workflows.models import Workflow, Node, WorkflowExecution
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()

class WorkflowModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='workflow_test_user',
            email='workflow@example.com',
            password='workflowpass123'
        )
        
        cls.workflow = Workflow.objects.create(
            name="Test Workflow",
            user=cls.user,
            config={'continue_on_error': True}
        )
        
    def test_workflow_creation(self):
        """Test workflow creation"""
        self.assertEqual(Workflow.objects.count(), 1)
        self.assertEqual(self.workflow.name, "Test Workflow")
        self.assertEqual(self.workflow.user, self.user)
        self.assertEqual(self.workflow.config, {'continue_on_error': True})
        
    def test_workflow_str_method(self):
        """Test workflow string representation"""
        self.assertEqual(str(self.workflow), "Test Workflow")
        
    def test_node_creation(self):
        """Test node creation and relationship to workflow"""
        node = Node.objects.create(
            workflow=self.workflow,
            type="text_input",
            config={"placeholder": "Enter text"},
            order=1
        )
        
        self.assertEqual(Node.objects.count(), 1)
        self.assertEqual(node.type, "text_input")
        self.assertEqual(node.workflow, self.workflow)
        self.assertEqual(node.order, 1)
        
    def test_node_str_method(self):
        """Test node string representation"""
        node = Node.objects.create(
            workflow=self.workflow,
            type="text_input",
            order=2
        )
        
        self.assertEqual(str(node), "text_input (Order: 2)")
        
    def test_workflow_execution_creation(self):
        """Test workflow execution creation"""
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            status='pending'
        )
        
        self.assertEqual(WorkflowExecution.objects.count(), 1)
        self.assertEqual(execution.workflow, self.workflow)
        self.assertEqual(execution.status, 'pending')
        self.assertIsNone(execution.completed_at)
        
    def test_workflow_execution_str_method(self):
        """Test workflow execution string representation"""
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            status='pending'
        )
        
        self.assertEqual(str(execution), f"Execution {execution.id} of Test Workflow")