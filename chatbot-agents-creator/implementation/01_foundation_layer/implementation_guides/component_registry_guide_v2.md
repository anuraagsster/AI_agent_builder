# Component Registry Implementation Guide

This guide provides detailed instructions for implementing the Component Registry component of the Foundation Layer with a focus on client ownership and serverless architecture.

## Overview

The Component Registry is a central system that manages all components in the application. It allows components to register themselves, discover other components, and manage dependencies between components. In this implementation, we'll focus on supporting client ownership and serverless architecture to align with the project's design principles.

## Design Principles Implementation

### Scalability
- **Lazy Component Initialization**: Components are initialized only when needed
- **Distributed Registry**: Support for distributed component discovery using DynamoDB
- **Efficient Retrieval**: Component caching for fast access

### Modularity
- **Clear Component Boundaries**: Well-defined interfaces between components
- **Dependency Management**: Automatic resolution of component dependencies
- **Plugin Architecture**: Extension system for adding new functionality

### Autonomy
- **Self-Monitoring**: Health checks for components
- **Automatic Recovery**: Retry mechanisms for failed components
- **Graceful Degradation**: Fallback strategies for missing components

### Future-Proofing
- **Component Versioning**: Support for multiple versions of components
- **Compatibility Checking**: Verification of component compatibility
- **Configuration-Driven**: Behavior controlled through configuration

### Client Ownership
- **Ownership Tracking**: Components can be owned by specific clients
- **Exportable Components**: Support for exporting client-owned components
- **Access Control**: Ownership-based access to components

## Implementation Requirements

### Dependencies

```python
import logging
import json
import boto3
import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Set, Callable
import inspect
import importlib
import pkgutil
from dataclasses import dataclass, field
from botocore.exceptions import ClientError
```

### Class Structure

```python
@dataclass
class ComponentMetadata:
    """Metadata for a registered component"""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    owner_id: Optional[str] = None  # Client ownership identifier
    exportable: bool = False  # Whether component can be exported
    health_check: Optional[Callable[[], bool]] = None  # Health check function

class ComponentRegistry:
    """
    Central registry for all system components.
    Handles component registration, discovery, and dependency management.
    """
    
    def __init__(self, config_manager=None):
        self._components: Dict[str, Any] = {}
        self._metadata: Dict[str, ComponentMetadata] = {}
        self._logger = logging.getLogger(__name__)
        self._config_manager = config_manager
        self._ownership_registry: Dict[str, List[str]] = {}  # Maps owner_id to component names
        self._dynamodb_client = None
        self._table_name = None
        
    def register_component(self, component: Any, metadata: ComponentMetadata) -> None:
        """
        Register a component with the registry
        
        Args:
            component: The component instance to register
            metadata: Metadata describing the component
        """
        pass
        
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a component by name
        
        Args:
            name: Name of the component to retrieve
            
        Returns:
            Component instance or None if not found
        """
        pass
        
    def get_components_by_tag(self, tag: str) -> List[Any]:
        """
        Get all components with a specific tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of component instances
        """
        pass
        
    def get_components_by_owner(self, owner_id: str) -> List[Any]:
        """
        Get all components owned by a specific client
        
        Args:
            owner_id: Owner identifier
            
        Returns:
            List of component instances owned by the client
        """
        pass
        
    def get_exportable_components(self) -> List[str]:
        """
        Get all exportable component names
        
        Returns:
            List of exportable component names
        """
        pass
        
    def export_component(self, name: str, format: str = "json") -> Dict[str, Any]:
        """
        Export a component for client deployment
        
        Args:
            name: Name of the component to export
            format: Export format (json, yaml)
            
        Returns:
            Component export data
        """
        pass
        
    def configure_dynamodb(self, table_name: str, region: str = None) -> None:
        """
        Configure DynamoDB for component storage
        
        Args:
            table_name: DynamoDB table name
            region: AWS region
        """
        pass
        
    def save_to_dynamodb(self) -> bool:
        """
        Save component registry to DynamoDB
        
        Returns:
            True if successful, False otherwise
        """
        pass
        
    def load_from_dynamodb(self) -> bool:
        """
        Load component registry from DynamoDB
        
        Returns:
            True if successful, False otherwise
        """
        pass
        
    def initialize_components(self) -> None:
        """
        Initialize all components in dependency order
        """
        pass
        
    def shutdown_components(self) -> None:
        """
        Shutdown all components in reverse dependency order
        """
        pass
        
    def check_component_health(self, name: str) -> bool:
        """
        Check the health of a component
        
        Args:
            name: Name of the component
            
        Returns:
            True if component is healthy, False otherwise
        """
        pass
        
    def _resolve_dependencies(self) -> List[str]:
        """
        Resolve component dependencies and return components in initialization order
        
        Returns:
            List of component names in dependency order
        """
        pass
        
    def _has_circular_dependencies(self) -> bool:
        """
        Check if there are circular dependencies between components
        
        Returns:
            True if circular dependencies exist, False otherwise
        """
        pass
```

### Extension System Class

```python
class ExtensionSystem:
    """
    System for managing extensions to the core functionality.
    Extensions are discovered, loaded, and managed through this system.
    """
    
    def __init__(self, registry: ComponentRegistry):
        self._registry = registry
        self._extensions: Dict[str, Dict[str, Any]] = {}
        self._extension_points: Dict[str, Type] = {}
        self._extension_owners: Dict[str, Dict[str, str]] = {}  # Maps extension_point -> {extension_name -> owner_id}
        self._logger = logging.getLogger(__name__)
        
    def register_extension_point(self, name: str, interface_type: Type) -> None:
        """
        Register an extension point with an interface type
        
        Args:
            name: Name of the extension point
            interface_type: Type that extensions must implement
        """
        pass
        
    def add_extension(self, extension_point: str, name: str, extension: Any, owner_id: Optional[str] = None) -> None:
        """
        Add an extension to a specific extension point
        
        Args:
            extension_point: Name of the extension point
            name: Name of the extension
            extension: Extension instance
            owner_id: Owner identifier (for client-owned extensions)
        """
        pass
        
    def get_extensions_by_owner(self, extension_point: str, owner_id: str) -> List[Any]:
        """
        Get all extensions for a specific extension point owned by a client
        
        Args:
            extension_point: Name of the extension point
            owner_id: Owner identifier
            
        Returns:
            List of extension instances owned by the client
        """
        pass
        
    def export_extensions(self, owner_id: str) -> Dict[str, Any]:
        """
        Export all extensions owned by a client
        
        Args:
            owner_id: Owner identifier
            
        Returns:
            Dictionary of exported extensions
        """
        pass
```

## Implementation Steps

### 1. Implement Component Registration with Ownership Support

```python
def register_component(self, component: Any, metadata: ComponentMetadata) -> None:
    """
    Register a component with the registry
    
    Args:
        component: The component instance to register
        metadata: Metadata describing the component
    """
    if metadata.name in self._components:
        self._logger.warning(f"Component {metadata.name} already registered, replacing")
        
        # If replacing a component, remove it from ownership registry first
        old_metadata = self._metadata.get(metadata.name)
        if old_metadata and old_metadata.owner_id:
            if old_metadata.owner_id in self._ownership_registry:
                if metadata.name in self._ownership_registry[old_metadata.owner_id]:
                    self._ownership_registry[old_metadata.owner_id].remove(metadata.name)
        
    self._components[metadata.name] = component
    self._metadata[metadata.name] = metadata
    self._logger.info(f"Registered component: {metadata.name} (v{metadata.version})")
    
    # Track component ownership
    if metadata.owner_id:
        if metadata.owner_id not in self._ownership_registry:
            self._ownership_registry[metadata.owner_id] = []
        self._ownership_registry[metadata.owner_id].append(metadata.name)
        self._logger.info(f"Component {metadata.name} registered with owner {metadata.owner_id}")
    
    # Validate dependencies
    for dep in metadata.dependencies:
        if dep not in self._components:
            self._logger.warning(f"Component {metadata.name} depends on {dep}, which is not registered")
            
    # Apply configuration if config manager is available
    if self._config_manager:
        component_config = self._config_manager.get_config(f"components.{metadata.name}", {})
        if hasattr(component, 'configure') and callable(getattr(component, 'configure')):
            try:
                component.configure(component_config)
                self._logger.info(f"Applied configuration to component {metadata.name}")
            except Exception as e:
                self._logger.error(f"Error applying configuration to component {metadata.name}: {str(e)}")
```

### 2. Implement Component Retrieval Methods

```python
def get_component(self, name: str) -> Optional[Any]:
    """
    Get a component by name
    
    Args:
        name: Name of the component to retrieve
        
    Returns:
        Component instance or None if not found
    """
    if name not in self._components:
        self._logger.warning(f"Component {name} not found in registry")
        return None
        
    return self._components[name]

def get_components_by_tag(self, tag: str) -> List[Any]:
    """
    Get all components with a specific tag
    
    Args:
        tag: Tag to filter by
        
    Returns:
        List of component instances
    """
    result = []
    for name, metadata in self._metadata.items():
        if tag in metadata.tags:
            result.append(self._components[name])
    return result

def get_components_by_owner(self, owner_id: str) -> List[Any]:
    """
    Get all components owned by a specific client
    
    Args:
        owner_id: Owner identifier
        
    Returns:
        List of component instances owned by the client
    """
    if owner_id not in self._ownership_registry:
        return []
        
    result = []
    for name in self._ownership_registry[owner_id]:
        if name in self._components:
            result.append(self._components[name])
    return result

def get_exportable_components(self) -> List[str]:
    """
    Get all exportable component names
    
    Returns:
        List of exportable component names
    """
    result = []
    for name, metadata in self._metadata.items():
        if metadata.exportable:
            result.append(name)
    return result
```

### 3. Implement Component Health Checking

```python
def check_component_health(self, name: str) -> bool:
    """
    Check the health of a component
    
    Args:
        name: Name of the component
        
    Returns:
        True if component is healthy, False otherwise
    """
    if name not in self._components:
        self._logger.warning(f"Component {name} not found in registry")
        return False
        
    metadata = self._metadata.get(name)
    if not metadata:
        return False
        
    # If component has a health check function, use it
    if metadata.health_check:
        try:
            return metadata.health_check()
        except Exception as e:
            self._logger.error(f"Error checking health of component {name}: {str(e)}")
            return False
            
    # If component has a health_check method, use it
    component = self._components[name]
    if hasattr(component, 'health_check') and callable(getattr(component, 'health_check')):
        try:
            return component.health_check()
        except Exception as e:
            self._logger.error(f"Error checking health of component {name}: {str(e)}")
            return False
            
    # Default to True if no health check is available
    return True
```

### 4. Implement Component Export for Client Deployment

```python
def export_component(self, name: str, format: str = "json") -> Dict[str, Any]:
    """
    Export a component for client deployment
    
    Args:
        name: Name of the component to export
        format: Export format (json, yaml)
        
    Returns:
        Component export data
    """
    if name not in self._components:
        self._logger.warning(f"Component {name} not found in registry")
        return {}
        
    metadata = self._metadata.get(name)
    if not metadata:
        return {}
        
    # Check if component is exportable
    if not metadata.exportable:
        self._logger.warning(f"Component {name} is not exportable")
        return {}
        
    component = self._components[name]
    
    # If component has an export method, use it
    if hasattr(component, 'export') and callable(getattr(component, 'export')):
        try:
            return component.export(format)
        except Exception as e:
            self._logger.error(f"Error exporting component {name}: {str(e)}")
            return {}
            
    # Default export format
    export_data = {
        "name": metadata.name,
        "version": metadata.version,
        "description": metadata.description,
        "dependencies": metadata.dependencies,
        "tags": metadata.tags,
        "owner_id": metadata.owner_id,
        "config_schema": metadata.config_schema
    }
    
    # If component has a get_state method, include state in export
    if hasattr(component, 'get_state') and callable(getattr(component, 'get_state')):
        try:
            export_data["state"] = component.get_state()
        except Exception as e:
            self._logger.error(f"Error getting state for component {name}: {str(e)}")
            
    return export_data
```

### 5. Implement DynamoDB Integration for Serverless Architecture

```python
def configure_dynamodb(self, table_name: str, region: str = None) -> None:
    """
    Configure DynamoDB for component storage
    
    Args:
        table_name: DynamoDB table name
        region: AWS region
    """
    self._table_name = table_name
    self._dynamodb_client = boto3.client('dynamodb', region_name=region)
    
    # Check if table exists, create if it doesn't
    try:
        self._dynamodb_client.describe_table(TableName=table_name)
        self._logger.info(f"DynamoDB table {table_name} exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            self._logger.info(f"Creating DynamoDB table {table_name}")
            self._dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'component_name', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'component_name', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            # Wait for table to be created
            waiter = self._dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
        else:
            self._logger.error(f"Error checking DynamoDB table: {str(e)}")

def save_to_dynamodb(self) -> bool:
    """
    Save component registry to DynamoDB
    
    Returns:
        True if successful, False otherwise
    """
    if not self._dynamodb_client or not self._table_name:
        self._logger.error("DynamoDB not configured")
        return False
        
    try:
        # Save metadata for each component
        for name, metadata in self._metadata.items():
            # Convert metadata to DynamoDB format
            item = {
                'component_name': {'S': name},
                'version': {'S': metadata.version},
                'description': {'S': metadata.description},
                'dependencies': {'S': json.dumps(metadata.dependencies)},
                'tags': {'S': json.dumps(metadata.tags)},
                'config_schema': {'S': json.dumps(metadata.config_schema)},
                'exportable': {'BOOL': metadata.exportable}
            }
            
            if metadata.owner_id:
                item['owner_id'] = {'S': metadata.owner_id}
                
            # Save to DynamoDB
            self._dynamodb_client.put_item(
                TableName=self._table_name,
                Item=item
            )
            
        self._logger.info(f"Saved {len(self._metadata)} components to DynamoDB")
        return True
    except Exception as e:
        self._logger.error(f"Error saving to DynamoDB: {str(e)}")
        return False

def load_from_dynamodb(self) -> bool:
    """
    Load component registry from DynamoDB
    
    Returns:
        True if successful, False otherwise
    """
    if not self._dynamodb_client or not self._table_name:
        self._logger.error("DynamoDB not configured")
        return False
        
    try:
        # Scan the table to get all components
        response = self._dynamodb_client.scan(TableName=self._table_name)
        
        # Clear existing metadata
        self._metadata = {}
        self._ownership_registry = {}
        
        # Process each item
        for item in response.get('Items', []):
            name = item['component_name']['S']
            
            # Create metadata
            metadata = ComponentMetadata(
                name=name,
                version=item['version']['S'],
                description=item['description']['S'],
                dependencies=json.loads(item['dependencies']['S']),
                tags=json.loads(item['tags']['S']),
                config_schema=json.loads(item['config_schema']['S']),
                exportable=item.get('exportable', {}).get('BOOL', False)
            )
            
            # Set owner_id if present
            if 'owner_id' in item:
                metadata.owner_id = item['owner_id']['S']
                
                # Update ownership registry
                if metadata.owner_id not in self._ownership_registry:
                    self._ownership_registry[metadata.owner_id] = []
                self._ownership_registry[metadata.owner_id].append(name)
                
            # Store metadata
            self._metadata[name] = metadata
            
        self._logger.info(f"Loaded {len(self._metadata)} components from DynamoDB")
        return True
    except Exception as e:
        self._logger.error(f"Error loading from DynamoDB: {str(e)}")
        return False
```

### 6. Implement Dependency Resolution and Component Lifecycle

```python
def _resolve_dependencies(self) -> List[str]:
    """
    Resolve component dependencies and return components in initialization order
    
    Returns:
        List of component names in dependency order
    """
    # Check for circular dependencies
    if self._has_circular_dependencies():
        raise ValueError("Circular dependencies detected between components")
        
    # Build dependency graph
    graph: Dict[str, List[str]] = {}
    for name, metadata in self._metadata.items():
        graph[name] = metadata.dependencies
        
    # Perform topological sort
    result = []
    visited = set()
    temp_visited = set()
    
    def visit(node: str) -> None:
        if node in temp_visited:
            raise ValueError(f"Circular dependency detected involving {node}")
        if node not in visited:
            temp_visited.add(node)
            for dep in graph.get(node, []):
                if dep in graph:  # Only visit nodes that exist in the graph
                    visit(dep)
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
            
    for node in graph:
        if node not in visited:
            visit(node)
            
    return result
    
def _has_circular_dependencies(self) -> bool:
    """
    Check if there are circular dependencies between components
    
    Returns:
        True if circular dependencies exist, False otherwise
    """
    # Build dependency graph
    graph: Dict[str, List[str]] = {}
    for name, metadata in self._metadata.items():
        graph[name] = metadata.dependencies
        
    # Check for cycles using DFS
    visited = set()
    path = set()
    
    def has_cycle(node: str) -> bool:
        if node in path:
            return True
        if node in visited:
            return False
            
        visited.add(node)
        path.add(node)
        
        for dep in graph.get(node, []):
            if dep in graph and has_cycle(dep):  # Only check nodes that exist in the graph
                return True
                
        path.remove(node)
        return False
        
    for node in graph:
        if node not in visited:
            if has_cycle(node):
                return True
                
    return False

def initialize_components(self) -> None:
    """
    Initialize all components in dependency order
    """
    # Get components in dependency order
    try:
        component_order = self._resolve_dependencies()
    except ValueError as e:
        self._logger.error(f"Error resolving dependencies: {str(e)}")
        return
    
    for name in component_order:
        component = self._components.get(name)
        if not component:
            self._logger.warning(f"Component {name} not found, skipping initialization")
            continue
            
        self._logger.info(f"Initializing component: {name}")
        
        # Check if component has initialize method
        if hasattr(component, 'initialize') and callable(getattr(component, 'initialize')):
            try:
                component.initialize()
            except Exception as e:
                self._logger.error(f"Error initializing component {name}: {str(e)}")
                # Continue with other components
                
    self._logger.info("Component initialization complete")
    
def shutdown_components(self) -> None:
    """
    Shutdown all components in reverse dependency order
    """
    # Get components in dependency order and reverse it
    try:
        component_order = self._resolve_dependencies()
        component_order.reverse()
    except ValueError as e:
        self._logger.error(f"Error resolving dependencies: {str(e)}")
        return
    
    for name in component_order:
        component = self._components.get(name)
        if not component:
            continue
            
        self._logger.info(f"Shutting down component: {name}")
        
        # Check if component has terminate method
        if hasattr(component, 'terminate') and callable(getattr(component, 'terminate')):
            try:
                component.terminate()
            except Exception as e:
                self._logger.error(f"Error shutting down component {name}: {str(e)}")
                # Continue shutting down other components
                
    self._logger.info("All components shut down")
```

### 7. Implement Extension System with Ownership Support

```python
def register_extension_point(self, name: str, interface_type: Type) -> None:
    """
    Register an extension point with an interface type
    
    Args:
        name: Name of the extension point
        interface_type: Type that extensions must implement
    """
    if name in self._extension_points:
        self._logger.warning(f"Extension point {name} already registered, replacing")
        
    self._extension_points[name] = interface_type
    self._extensions[name] = {}
    self._extension_owners[name] = {}
    self._logger.info(f"Registered extension point: {name}")
    
def add_extension(self, extension_point: str, name: str, extension: Any, owner_id: Optional[str] = None) -> None:
    """
    Add an extension to a specific extension point
    
    Args:
        extension_point: Name of the extension point
        name: Name of the extension
        extension: Extension instance
        owner_id: Owner identifier (for client-owned extensions)
    """
    if extension_point not in self._extension_points:
        raise ValueError(f"Extension point {extension_point} not registered")
        
    # Check if extension implements the required interface
    interface_type = self._extension_points[extension_point]
    if not isinstance(extension, interface_type):
        raise TypeError(f"Extension {name} does not implement {interface_type.__name__}")
        
    if name in self._extensions[extension_point]:
        self._logger.warning(f"Extension {name} already registered for {extension_point}, replacing")
        
    self._extensions[extension_point][name] = extension
    
    # Track extension ownership
    if owner_id:
        self._extension_owners[extension_point][name] = owner_id
        self._logger.info(f"Extension {name} registered with owner {owner_id}")
        
    self._logger.info(f"Added extension: {name} to {extension_point}")
    
def get_extensions_by_owner(self, extension_point: str, owner_id: str) -> List[Any]:
    """
    Get all extensions for a specific extension point owned by a client
    
    Args:
        extension_point: Name of the extension point
        owner_id: Owner identifier
        
    Returns:
        List of extension instances owned by the client
    """
    if extension_point not in self._extension_points:
        raise ValueError(f"Extension point {extension_point} not registered")
        
    result = []
    for name, ext_owner_id in self._extension_owners.get(extension_point, {}).items():
        if ext_owner_id == owner_id and name in self._extensions[extension_point]:
            result.append(self._extensions[extension_point][name])
            
    return result
    
def export_extensions(self, owner_id: str) -> Dict[str, Any]:
    """
    Export all extensions owned by a client
    
    Args:
        owner_id: Owner identifier
        
    Returns:
        Dictionary of exported extensions
    """
    result = {}
    
    for extension_point, owners in self._extension_owners.items():
        for name, ext_owner_id in owners.items():
            if ext_owner_id == owner_id:
                extension = self._extensions[extension_point].get(name)
                if extension:
                    # If extension has an export method, use it
                    if hasattr(extension, 'export') and callable(getattr(extension, 'export')):
                        try:
                            export_data = extension.export()
                        except Exception as e:
                            self._logger.error(f"Error exporting extension {name}: {str(e)}")
                            export_data = {"name": name}
                    else:
                        # Default export format
                        export_data = {"name": name}
                        
                    # Add to result
                    if extension_point not in result:
                        result[extension_point] = {}
                    result[extension_point][name] = export_data
                    
    return result
```

## Usage Examples

### Basic Usage with Client Ownership

```python
# Create component registry
registry = ComponentRegistry()

# Register components with ownership
db_component = DatabaseComponent()
registry.register_component(db_component, ComponentMetadata(
    name="database",
    version="1.0.0",
    description="Database access component",
    tags=["storage", "persistence"],
    owner_id="system"  # System-owned component
))

client_component = ClientComponent()
registry.register_component(client_component, ComponentMetadata(
    name="client_processor",
    version="1.0.0",
    description="Client-specific data processor",
    dependencies=["database"],
    tags=["processing"],
    owner_id="client123",  # Client-owned component
    exportable=True  # Can be exported for client deployment
))

# Get components by owner
client_components = registry.get_components_by_owner("client123")
print(f"Client components: {[c.__class__.__name__ for c in client_components]}")

# Get exportable components
exportable = registry.get_exportable_components()
print(f"Exportable components: {exportable}")

# Export a component for client deployment
export_data = registry.export_component("client_processor")
print(f"Export data: {export_data}")
```

### Serverless Implementation with DynamoDB

```python
# Create component registry with DynamoDB support
registry = ComponentRegistry()
registry.configure_dynamodb("component-registry", "us-west-2")

# Register components
registry.register_component(component1, metadata1)
registry.register_component(component2, metadata2)

# Save registry to DynamoDB
registry.save_to_dynamodb()

# In another Lambda function or instance
new_registry = ComponentRegistry()
new_registry.configure_dynamodb("component-registry", "us-west-2")
new_registry.load_from_dynamodb()

# Components are now available by metadata, but instances need to be recreated
for name in new_registry.list_components():
    metadata = new_registry._metadata[name]
    print(f"Component: {name}, Version: {metadata.version}, Owner: {metadata.owner_id}")
```

### Extension System with Client Ownership

```python
# Create component registry and extension system
registry = ComponentRegistry()
extension_system = ExtensionSystem(registry)

# Register extension point
extension_system.register_extension_point("data_processor", DataProcessorInterface)

# Add system extension
csv_processor = CSVProcessor()
extension_system.add_extension("data_processor", "csv", csv_processor)

# Add client-owned extension
client_processor = ClientProcessor()
extension_system.add_extension(
    "data_processor", 
    "client_custom", 
    client_processor, 
    owner_id="client123"
)

# Get client-owned extensions
client_extensions = extension_system.get_extensions_by_owner("data_processor", "client123")
print(f"Client extensions: {[e.__class__.__name__ for e in client_extensions]}")

# Export client extensions
export_data = extension_system.export_extensions("client123")
print(f"Export data: {export_data}")
```

## Testing

Create unit tests to verify:

1. Component registration and retrieval with ownership
2. Component dependency resolution
3. Component initialization and shutdown order
4. Extension point registration and ownership tracking
5. Component export functionality
6. DynamoDB integration

Example test for client ownership:

```python
import unittest
from unittest.mock import MagicMock, patch
from component_registry import ComponentRegistry, ComponentMetadata

class TestComponentRegistry