from typing import List, Dict
from .models import Workflow, Node, WorkflowExecution

class WorkflowValidator:
    @staticmethod
    def validate_workflow(workflow: Workflow) -> List[str]:
        errors = []
        
        # Validate workflow structure
        if not workflow.nodes.exists():
            errors.append("Workflow has no nodes")
            return errors

        # Validate node connections
        for node in workflow.nodes.all():
            # Check required inputs
            required_inputs = NodePort.objects.filter(
                node=node,
                is_input=True,
                is_required=True
            )
            
            for port in required_inputs:
                if not NodeConnection.objects.filter(
                    target_node=node,
                    target_port=port.name
                ).exists():
                    errors.append(f"Required input '{port.name}' not connected for node {node.name}")

        # Validate execution order
        orders = list(workflow.nodes.values_list('order', flat=True))
        if len(set(orders)) != len(orders):
            errors.append("Duplicate node execution orders found")

        return errors

    @staticmethod
    def validate_execution(execution: WorkflowExecution) -> List[str]:
        errors = []
        
        # Validate execution context
        if not execution.execution_context:
            errors.append("Execution context is required")

        # Validate variables
        required_vars = execution.workflow.config.get('required_variables', [])
        for var in required_vars:
            if var not in execution.variables:
                errors.append(f"Required variable '{var}' not provided")

        return errors
