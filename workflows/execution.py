from celery import shared_task
from django.utils import timezone
from .models import WorkflowExecution, Node
import asyncio
from typing import Dict, Any

class WorkflowExecutor:
    def __init__(self, execution: WorkflowExecution):
        self.execution = execution
        self.context = {}
        self.results = {}

    async def execute_node(self, node: Node, input_data: Any = None) -> Dict:
        try:
            # Get node handler from registry
            handler = NodeRegistry.get_handler(node.type)
            if not handler:
                raise ValueError(f"No handler found for node type: {node.type}")

            # Execute node with timeout
            async with asyncio.timeout(node.timeout):
                result = await handler.execute(node, input_data, self.context)
                
            # Store result
            self.results[node.id] = result
            return result

        except asyncio.TimeoutError:
            raise TimeoutError(f"Node {node.id} execution timed out")
        except Exception as e:
            if node.retry_count < node.max_retries:
                node.retry_count += 1
                node.save()
                return await self.execute_node(node, input_data)
            raise

    async def execute_workflow(self):
        try:
            self.execution.status = 'running'
            self.execution.started_at = timezone.now()
            self.execution.save()

            # Get nodes in execution order
            nodes = Node.objects.filter(
                workflow=self.execution.workflow,
                is_enabled=True
            ).order_by('order')

            for node in nodes:
                # Get input data from connected nodes
                input_data = await self.get_node_input(node)
                result = await self.execute_node(node, input_data)

            self.execution.status = 'completed'
            self.execution.completed_at = timezone.now()
            self.execution.results = self.results
            self.execution.save()

        except Exception as e:
            self.execution.status = 'failed'
            self.execution.error_logs = str(e)
            self.execution.save()
            raise

    async def get_node_input(self, node: Node) -> Any:
        # Get input from connected nodes
        input_connections = NodeConnection.objects.filter(
            target_node=node,
            target_port='input'
        )
        
        if not input_connections:
            return None

        # Get result from source node
        source_connection = input_connections.first()
        source_result = self.results.get(source_connection.source_node_id)
        
        return source_result
