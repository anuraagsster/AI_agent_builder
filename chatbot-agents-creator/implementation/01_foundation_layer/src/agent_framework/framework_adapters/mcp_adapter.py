import logging
from typing import Any, Dict, List, Optional, Union
import importlib
from datetime import datetime
import json

class MCPAdapter:
    """
    Adapter for integrating with Model Context Protocol (MCP) SDK.
    This adapter translates between our system's agent interface and MCP's interface.
    
    The Model Context Protocol (MCP) is a standard for communication between AI models
    and external tools/resources. This adapter allows our system to leverage MCP's
    capabilities while maintaining our own abstractions.
    """
    
    def __init__(self, config=None):
        """
        Initialize the MCP adapter
        
        Args:
            config: Configuration dictionary for the adapter
        """
        self.config = config or {}
        self.logger = logging.getLogger("mcp_adapter")
        self._mcp_available = self._check_mcp_available()
        
        # Store references to MCP classes if available
        self.mcp_tool_class = None
        self.mcp_resource_class = None
        self.mcp_server_class = None
        
        if self._mcp_available:
            self._initialize_mcp_classes()
    
    def _check_mcp_available(self) -> bool:
        """
        Check if MCP SDK is available in the environment
        
        Returns:
            True if MCP SDK is available, False otherwise
        """
        try:
            importlib.import_module('mcp_sdk')
            self.logger.info("MCP SDK is available")
            return True
        except ImportError:
            self.logger.warning("MCP SDK is not available. Some functionality will be limited.")
            return False
    
    def _initialize_mcp_classes(self) -> None:
        """
        Initialize references to MCP classes
        """
        try:
            mcp_sdk = importlib.import_module('mcp_sdk')
            self.mcp_tool_class = getattr(mcp_sdk, 'Tool')
            self.mcp_resource_class = getattr(mcp_sdk, 'Resource')
            self.mcp_server_class = getattr(mcp_sdk, 'Server')
            self.logger.info("Successfully initialized MCP classes")
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to initialize MCP classes: {str(e)}")
            self._mcp_available = False
    
    def register_mcp_tool(self, tool_config: Dict[str, Any]) -> Any:
        """
        Register a tool with the MCP system
        
        Args:
            tool_config: Our system's tool configuration
            
        Returns:
            MCP tool registration result or None if MCP SDK is not available
        """
        if not self._mcp_available:
            self.logger.warning("Cannot register MCP tool: MCP SDK is not available")
            return None
        
        try:
            # Extract relevant fields from our tool config
            name = tool_config.get('name', f"Tool-{tool_config.get('tool_id', 'unknown')}")
            description = tool_config.get('description', 'A tool for the MCP system')
            input_schema = tool_config.get('input_schema', {})
            output_schema = tool_config.get('output_schema', {})
            
            # Preserve ownership metadata
            owner_id = tool_config.get('owner_id')
            ownership_type = tool_config.get('ownership_type', 'system')
            exportable = tool_config.get('exportable', False)
            
            # Create the MCP tool
            mcp_tool = self.mcp_tool_class(
                name=name,
                description=description,
                input_schema=json.dumps(input_schema),
                output_schema=json.dumps(output_schema)
            )
            
            # Store original tool_id for reference
            mcp_tool.original_tool_id = tool_config.get('tool_id')
            
            # Store ownership metadata
            mcp_tool.owner_id = owner_id
            mcp_tool.ownership_type = ownership_type
            mcp_tool.exportable = exportable
            
            self.logger.info(f"Registered MCP tool: {name}")
            return mcp_tool
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP tool: {str(e)}")
            return None
    
    def convert_to_mcp_resource(self, resource: Dict[str, Any]) -> Any:
        """
        Convert our resource format to MCP's resource format
        
        Args:
            resource: Our system's resource object
            
        Returns:
            An MCP compatible resource or None if MCP SDK is not available
        """
        if not self._mcp_available:
            self.logger.warning("Cannot convert resource: MCP SDK is not available")
            return None
        
        try:
            # Extract relevant fields from our resource
            uri = resource.get('uri', f"resource://{resource.get('resource_id', 'unknown')}")
            content_type = resource.get('content_type', 'application/json')
            data = resource.get('data', {})
            
            # Preserve ownership metadata
            owner_id = resource.get('owner_id')
            ownership_type = resource.get('ownership_type', 'system')
            
            # Create the MCP resource
            mcp_resource = self.mcp_resource_class(
                uri=uri,
                content_type=content_type,
                data=json.dumps(data) if isinstance(data, (dict, list)) else data
            )
            
            # Store original resource_id for reference
            mcp_resource.original_resource_id = resource.get('resource_id')
            
            # Store ownership metadata
            mcp_resource.owner_id = owner_id
            mcp_resource.ownership_type = ownership_type
            
            self.logger.info(f"Converted resource to MCP format: {uri}")
            return mcp_resource
            
        except Exception as e:
            self.logger.error(f"Failed to convert resource to MCP format: {str(e)}")
            return None
    
    def handle_mcp_request(self, request: Any) -> Dict[str, Any]:
        """
        Handle a request from an MCP client
        
        Args:
            request: Request from MCP
            
        Returns:
            Response in MCP format or error dict if handling fails
        """
        try:
            # Extract request details
            request_type = getattr(request, 'type', 'unknown')
            request_data = getattr(request, 'data', {})
            
            # Convert to our system's format
            our_request = {
                'type': request_type,
                'data': request_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Process the request (this would be implemented by the specific handler)
            # For now, just return a simple response
            response = {
                'status': 'success',
                'result': f"Processed {request_type} request",
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Handled MCP request: {request_type}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to handle MCP request: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def create_mcp_server(self, server_config: Dict[str, Any]) -> Any:
        """
        Create an MCP server based on our configuration
        
        Args:
            server_config: Our system's server configuration
            
        Returns:
            An MCP server instance or None if MCP SDK is not available
        """
        if not self._mcp_available:
            self.logger.warning("Cannot create MCP server: MCP SDK is not available")
            return None
        
        try:
            # Extract relevant fields from our server config
            name = server_config.get('name', f"Server-{server_config.get('server_id', 'unknown')}")
            host = server_config.get('host', 'localhost')
            port = server_config.get('port', 8000)
            tools = server_config.get('tools', [])
            resources = server_config.get('resources', [])
            
            # Convert tools and resources to MCP format if they aren't already
            mcp_tools = []
            for tool in tools:
                if hasattr(tool, 'original_tool_id'):
                    mcp_tools.append(tool)
                else:
                    mcp_tool = self.register_mcp_tool(tool)
                    if mcp_tool:
                        mcp_tools.append(mcp_tool)
            
            mcp_resources = []
            for resource in resources:
                if hasattr(resource, 'original_resource_id'):
                    mcp_resources.append(resource)
                else:
                    mcp_resource = self.convert_to_mcp_resource(resource)
                    if mcp_resource:
                        mcp_resources.append(mcp_resource)
            
            # Create the MCP server
            mcp_server = self.mcp_server_class(
                name=name,
                host=host,
                port=port
            )
            
            # Register tools and resources with the server
            for tool in mcp_tools:
                mcp_server.register_tool(tool)
                
            for resource in mcp_resources:
                mcp_server.register_resource(resource)
            
            # Store original server_id for reference
            mcp_server.original_server_id = server_config.get('server_id')
            
            # Store ownership metadata
            mcp_server.owner_id = server_config.get('owner_id')
            mcp_server.ownership_type = server_config.get('ownership_type', 'system')
            
            self.logger.info(f"Created MCP server: {name} with {len(mcp_tools)} tools and {len(mcp_resources)} resources")
            return mcp_server
            
        except Exception as e:
            self.logger.error(f"Failed to create MCP server: {str(e)}")
            return None
    
    def convert_from_mcp_result(self, mcp_result: Any) -> Dict[str, Any]:
        """
        Convert MCP's result format to our system's result format
        
        Args:
            mcp_result: Result from MCP
            
        Returns:
            Our system's result format
        """
        try:
            # MCP typically returns a structured result
            if hasattr(mcp_result, 'data'):
                data = mcp_result.data
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        pass
                
                return {
                    'status': 'completed',
                    'result': data,
                    'timestamp': datetime.now().isoformat()
                }
            
            # If it's a string, wrap it
            elif isinstance(mcp_result, str):
                return {
                    'status': 'completed',
                    'result': mcp_result,
                    'timestamp': datetime.now().isoformat()
                }
            
            # If it's already a dictionary, ensure it has our required fields
            elif isinstance(mcp_result, dict):
                result = mcp_result.copy()
                if 'status' not in result:
                    result['status'] = 'completed'
                if 'timestamp' not in result:
                    result['timestamp'] = datetime.now().isoformat()
                return result
                
            # For other types, wrap in our format
            else:
                return {
                    'status': 'completed',
                    'result': str(mcp_result),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to process MCP result: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_ownership_compatibility(self, tools: List[Any]) -> None:
        """
        Validate that all tools have compatible ownership
        
        Args:
            tools: List of MCP tools
            
        Raises:
            ValueError: If tools have incompatible ownership
        """
        # Group tools by owner_id
        owners = {}
        for tool in tools:
            owner_id = getattr(tool, 'owner_id', None)
            if owner_id:
                if owner_id not in owners:
                    owners[owner_id] = []
                owners[owner_id].append(tool)
        
        # If we have multiple owners, check if any tools are not exportable
        if len(owners) > 1:
            for owner_id, owner_tools in owners.items():
                for tool in owner_tools:
                    if not getattr(tool, 'exportable', False):
                        raise ValueError(f"Tool {tool.name} is not exportable and cannot be used in a multi-owner context")
    
    def prepare_for_export(self, mcp_tool: Any) -> Dict[str, Any]:
        """
        Prepare an MCP tool for export to a client environment
        
        Args:
            mcp_tool: An MCP tool
            
        Returns:
            Dictionary containing exportable tool configuration
        """
        if not hasattr(mcp_tool, 'exportable') or not mcp_tool.exportable:
            raise ValueError("This tool is not exportable")
            
        # Create a clean export configuration
        export_config = {
            'tool_id': getattr(mcp_tool, 'original_tool_id', None),
            'name': mcp_tool.name,
            'description': mcp_tool.description,
            'input_schema': json.loads(mcp_tool.input_schema) if isinstance(mcp_tool.input_schema, str) else mcp_tool.input_schema,
            'output_schema': json.loads(mcp_tool.output_schema) if isinstance(mcp_tool.output_schema, str) else mcp_tool.output_schema,
            'owner_id': getattr(mcp_tool, 'owner_id', None),
            'ownership_type': getattr(mcp_tool, 'ownership_type', 'client'),
            'exportable': True,
            'exported_at': datetime.now().isoformat(),
            'framework': 'mcp'
        }
        
        return export_config