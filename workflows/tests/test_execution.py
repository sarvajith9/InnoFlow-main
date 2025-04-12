from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Workflow, Node, WorkflowExecution
from ..execution import WorkflowExecutor
from ..validators import WorkflowValidator
from ..mock_handlers import HANDLERS
import asyncio
import uuid

User = get_user_model()

class WorkflowExecutionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            user=self.user
        )
        self.execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            execution_id=uuid.uuid4(),
            variables={'input_text': 'test'},
            execution_context={'environment': 'test'},
            started_by=self.user
        )
        self.executor = WorkflowExecutor(self.execution)

    async def async_test(self, coro):
        loop = asyncio.get_event_loop()
        return await loop.create_task(coro)

    def test_execution_initialization(self):
        self.assertEqual(self.executor.execution, self.execution)
        self.assertEqual(self.executor.context, {})
        self.assertEqual(self.executor.results, {})

    async def test_node_execution(self):
        # Create a test node
        node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Test Node',
            order=1,
            config={'text': 'test input'}
        )
        
        # Test node execution
        result = await self.executor.execute_node(node, input_data='test input')
        self.assertIn(node.id, self.executor.results)
        self.assertEqual(self.executor.results[node.id], 'test input')

    async def test_workflow_execution(self):
        # Create test nodes
        node1 = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Input Node',
            order=1,
            config={'text': 'test input'}
        )
        node2 = Node.objects.create(
            workflow=self.workflow,
            type='openai_tts',
            name='Output Node',
            order=2
        )
        
        # Execute workflow
        await self.executor.execute_workflow()
        
        # Check execution status
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.status, 'completed')
        self.assertIsNotNone(self.execution.completed_at)
        self.assertIsNotNone(self.execution.results)

    async def test_execution_error_handling(self):
        # Create a node that will fail
        node = Node.objects.create(
            workflow=self.workflow,
            type='invalid_type',  # This will cause an error
            name='Error Node',
            order=1
        )
        
        # Execute workflow
        with self.assertRaises(ValueError):
            await self.executor.execute_workflow()
        
        # Check execution status
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.status, 'failed')
        self.assertIsNotNone(self.execution.error_logs)

    async def test_node_timeout(self):
        # Create a node with very short timeout
        node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Timeout Node',
            order=1,
            timeout=0.001,  # Very short timeout
            config={'text': 'test input'}
        )
        
        # Test timeout
        with self.assertRaises(TimeoutError):
            await self.executor.execute_node(node, input_data='test')

    async def test_node_retry(self):
        # Create a node with retry configuration
        node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Retry Node',
            order=1,
            retry_count=0,
            max_retries=3,
            config={'text': 'test input'}
        )
        
        # Test retry mechanism
        with self.assertRaises(Exception):
            await self.executor.execute_node(node, input_data='test')
        
        # Check retry count
        node.refresh_from_db()
        self.assertEqual(node.retry_count, 1)

class WorkflowValidatorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            user=self.user
        )
        self.validator = WorkflowValidator()

    def test_empty_workflow_validation(self):
        errors = self.validator.validate_workflow(self.workflow)
        self.assertIn("Workflow has no nodes", errors)

    def test_workflow_with_nodes_validation(self):
        # Create a valid node
        Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Test Node',
            order=1
        )
        
        errors = self.validator.validate_workflow(self.workflow)
        self.assertEqual(len(errors), 0)

    def test_duplicate_orders_validation(self):
        # Create nodes with duplicate orders
        Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Node 1',
            order=1
        )
        Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            name='Node 2',
            order=1
        )
        
        errors = self.validator.validate_workflow(self.workflow)
        self.assertIn("Duplicate node execution orders found", errors)

    def test_execution_validation(self):
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            execution_id=uuid.uuid4(),
            started_by=self.user
        )
        
        errors = self.validator.validate_execution(execution)
        self.assertIn("Execution context is required", errors)

    def test_required_variables_validation(self):
        self.workflow.config = {'required_variables': ['input_text']}
        self.workflow.save()
        
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            execution_id=uuid.uuid4(),
            execution_context={'environment': 'test'},
            started_by=self.user
        )
        
        errors = self.validator.validate_execution(execution)
        self.assertIn("Required variable 'input_text' not provided", errors) 