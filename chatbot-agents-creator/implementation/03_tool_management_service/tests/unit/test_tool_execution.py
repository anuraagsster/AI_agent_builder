import unittest
from unittest.mock import MagicMock, patch
import asyncio
import json
from src.tool_execution import ToolExecutor, ExecutionResult, ExecutionStatus, ToolExecutionError


class TestToolExecutor(unittest.TestCase):
    def setUp(self):
        # Create a mock tool registry
        self.mock_registry = MagicMock()
        
        # Create a mock tool
        self.mock_tool = MagicMock()
        self.mock_tool.name = "test_tool"
        self.mock_tool.description = "A test tool"
        self.mock_tool.get_parameter_schema.return_value = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1"]
        }
        self.mock_tool.execute.return_value = {"result": "test_result"}
        
        # Configure the mock registry to return the mock tool
        self.mock_registry.get_tool.return_value = self.mock_tool
        
        # Create a tool executor
        self.executor = ToolExecutor(self.mock_registry)
        
    def test_execute_tool(self):
        # Execute a tool
        parameters = {"param1": "test", "param2": 42}
        result = self.executor.execute_tool("test_tool", parameters)
        
        # Check if the tool was executed correctly
        self.mock_registry.get_tool.assert_called_once_with("test_tool")
        self.mock_tool.execute.assert_called_once_with(parameters)
        
        # Check the execution result
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.result, {"result": "test_result"})
        self.assertIsNone(result.error)
        
    def test_execute_nonexistent_tool(self):
        # Configure the mock registry to raise KeyError
        self.mock_registry.get_tool.side_effect = KeyError("Tool not found")
        
        # Try to execute a nonexistent tool
        parameters = {"param1": "test"}
        result = self.executor.execute_tool("nonexistent_tool", parameters)
        
        # Check the execution result
        self.assertEqual(result.status, ExecutionStatus.ERROR)
        self.assertIsNone(result.result)
        self.assertIsNotNone(result.error)
        self.assertIn("Tool not found", str(result.error))
        
    def test_execute_tool_with_invalid_parameters(self):
        # Configure the mock tool to raise ValueError for invalid parameters
        self.mock_tool.execute.side_effect = ValueError("Invalid parameters")
        
        # Try to execute a tool with invalid parameters
        parameters = {"param2": "not_an_integer"}
        result = self.executor.execute_tool("test_tool", parameters)
        
        # Check the execution result
        self.assertEqual(result.status, ExecutionStatus.ERROR)
        self.assertIsNone(result.result)
        self.assertIsNotNone(result.error)
        self.assertIn("Invalid parameters", str(result.error))
        
    def test_execute_tool_with_execution_error(self):
        # Configure the mock tool to raise an exception during execution
        self.mock_tool.execute.side_effect = Exception("Execution error")
        
        # Try to execute a tool that raises an exception
        parameters = {"param1": "test"}
        result = self.executor.execute_tool("test_tool", parameters)
        
        # Check the execution result
        self.assertEqual(result.status, ExecutionStatus.ERROR)
        self.assertIsNone(result.result)
        self.assertIsNotNone(result.error)
        self.assertIn("Execution error", str(result.error))
        
    @patch('src.tool_execution.asyncio.create_task')
    def test_execute_tool_async(self, mock_create_task):
        # Mock the create_task function
        mock_task = MagicMock()
        mock_create_task.return_value = mock_task
        
        # Execute a tool asynchronously
        parameters = {"param1": "test"}
        task_id = self.executor.execute_tool_async("test_tool", parameters)
        
        # Check if a task was created
        mock_create_task.assert_called_once()
        self.assertIsNotNone(task_id)
        
        # Check if the task was stored
        self.assertIn(task_id, self.executor.tasks)
        
    def test_get_execution_result(self):
        # Add a mock task to the executor
        task_id = "test_task_id"
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            result={"result": "test_result"},
            error=None
        )
        self.executor.results[task_id] = mock_result
        
        # Get the execution result
        result = self.executor.get_execution_result(task_id)
        
        # Check the result
        self.assertEqual(result, mock_result)
        
    def test_get_nonexistent_execution_result(self):
        # Try to get a nonexistent execution result
        with self.assertRaises(KeyError):
            self.executor.get_execution_result("nonexistent_task_id")
            
    def test_cancel_execution(self):
        # Add a mock task to the executor
        task_id = "test_task_id"
        mock_task = MagicMock()
        self.executor.tasks[task_id] = mock_task
        
        # Cancel the execution
        self.executor.cancel_execution(task_id)
        
        # Check if the task was cancelled
        mock_task.cancel.assert_called_once()
        
    def test_cancel_nonexistent_execution(self):
        # Try to cancel a nonexistent execution
        with self.assertRaises(KeyError):
            self.executor.cancel_execution("nonexistent_task_id")
            
    def test_execution_result_to_dict(self):
        # Create an execution result
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            result={"result": "test_result"},
            error=None
        )
        
        # Convert to dictionary
        result_dict = result.to_dict()
        
        # Check the dictionary
        self.assertEqual(result_dict["status"], "SUCCESS")
        self.assertEqual(result_dict["result"], {"result": "test_result"})
        self.assertIsNone(result_dict["error"])
        
    def test_execution_result_from_dict(self):
        # Create a dictionary
        result_dict = {
            "status": "SUCCESS",
            "result": {"result": "test_result"},
            "error": None
        }
        
        # Create an execution result from the dictionary
        result = ExecutionResult.from_dict(result_dict)
        
        # Check the execution result
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.result, {"result": "test_result"})
        self.assertIsNone(result.error)
        
    def test_execution_result_to_json(self):
        # Create an execution result
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            result={"result": "test_result"},
            error=None
        )
        
        # Convert to JSON
        result_json = result.to_json()
        
        # Parse the JSON
        result_dict = json.loads(result_json)
        
        # Check the dictionary
        self.assertEqual(result_dict["status"], "SUCCESS")
        self.assertEqual(result_dict["result"], {"result": "test_result"})
        self.assertIsNone(result_dict["error"])
        
    def test_tool_execution_error(self):
        # Create a tool execution error
        error = ToolExecutionError("test_tool", "Error message")
        
        # Check the error
        self.assertEqual(error.tool_name, "test_tool")
        self.assertEqual(error.message, "Error message")
        self.assertEqual(str(error), "Error executing tool 'test_tool': Error message")


if __name__ == "__main__":
    unittest.main()