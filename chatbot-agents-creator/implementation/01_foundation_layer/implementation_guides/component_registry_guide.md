# Component Registry Implementation Guide

This guide provides detailed instructions for implementing the Component Registry component of the Foundation Layer. It serves as a reference for junior developers to understand the implementation approach.

## Overview

The Component Registry is a central system that manages all components in the application. It allows components to register themselves, discover other components, and manage dependencies between components. It's a critical part of the system architecture that enables modularity and extensibility.

## Implementation Requirements

### Dependencies

```python
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, cast
import inspect
import importlib
import pkgutil
from dataclasses import dataclass, field
```

### Class Structure

```python
T = TypeVar('T')

@dataclass
class ComponentMetadata:
    """Metadata for a registered component"""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)

class ComponentRegistry:
    """
    Central registry for all system components.
    Handles component registration, discovery, and dependency management.
    """
    
    def __init__(self):
        self._components: Dict[str, Any] = {}
        self._metadata: Dict[str, ComponentMetadata] = {}
        self._logger = logging.getLogger(__name__)
        
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
        
    def get_component_metadata(self, name: str) -> Optional[ComponentMetadata]:
        """
        Get metadata for a component
        
        Args:
            name: Name of the component
            
        Returns:
            ComponentMetadata or None if not found
        """
        pass
        
    def list_components(self) -> List[str]:
        """
        List all registered component names
        
        Returns:
            List of component names
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
        self._extensions: Dict[str, Any] = {}
        self._extension_points: Dict[str, Type] = {}
        self._logger = logging.getLogger(__name__)
        
    def register_extension_point(self, name: str, interface_type: Type) -> None:
        """
        Register an extension point with an interface type
        
        Args:
            name: Name of the extension point
            interface_type: Type that extensions must implement
        """
        pass
        
    def add_extension(self, extension_point: str, name: str, extension: Any) -> None:
        """
        Add an extension to a specific extension point
        
        Args:
            extension_point: Name of the extension point
            name: Name of the extension
            extension: Extension instance
        """
        pass
        
    def remove_extension(self, extension_point: str, name: str) -> None:
        """
        Remove an extension
        
        Args:
            extension_point: Name of the extension point
            name: Name of the extension
        """
        pass
        
    def get_extensions(self, extension_point: str) -> List[Any]:
        """
        Get all extensions for a specific extension point
        
        Args:
            extension_point: Name of the extension point
            
        Returns:
            List of extension instances
        """
        pass
        
    def discover_extensions(self, package_name: str) -> None:
        """
        Discover extensions in a package
        
        Args:
            package_name: Name of the package to scan for extensions
        """
        pass
```

## Implementation Steps

### 1. Implement `register_component` Method

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
        
    self._components[metadata.name] = component
    self._metadata[metadata.name] = metadata
    self._logger.info(f"Registered component: {metadata.name} (v{metadata.version})")
    
    # Validate dependencies
    for dep in metadata.dependencies:
        if dep not in self._components:
            self._logger.warning(f"Component {metadata.name} depends on {dep}, which is not registered")
```

### 2. Implement `get_component` Method

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
```

### 3. Implement Component Listing and Filtering

```python
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
    
def get_component_metadata(self, name: str) -> Optional[ComponentMetadata]:
    """
    Get metadata for a component
    
    Args:
        name: Name of the component
        
    Returns:
        ComponentMetadata or None if not found
    """
    return self._metadata.get(name)
    
def list_components(self) -> List[str]:
    """
    List all registered component names
    
    Returns:
        List of component names
    """
    return list(self._components.keys())
```

### 4. Implement Dependency Resolution

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
            if has_cycle(dep):
                return True
                
        path.remove(node)
        return False
        
    for node in graph:
        if node not in visited:
            if has_cycle(node):
                return True
                
    return False
```

### 5. Implement Component Lifecycle Management

```python
def initialize_components(self) -> None:
    """
    Initialize all components in dependency order
    """
    # Get components in dependency order
    component_order = self._resolve_dependencies()
    
    for name in component_order:
        component = self._components[name]
        self._logger.info(f"Initializing component: {name}")
        
        # Check if component has initialize method
        if hasattr(component, 'initialize') and callable(getattr(component, 'initialize')):
            try:
                component.initialize()
            except Exception as e:
                self._logger.error(f"Error initializing component {name}: {str(e)}")
                raise
                
    self._logger.info("All components initialized successfully")
    
def shutdown_components(self) -> None:
    """
    Shutdown all components in reverse dependency order
    """
    # Get components in dependency order and reverse it
    component_order = self._resolve_dependencies()
    component_order.reverse()
    
    for name in component_order:
        component = self._components[name]
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

### 6. Implement Extension System Methods

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
    self._logger.info(f"Registered extension point: {name}")
    
def add_extension(self, extension_point: str, name: str, extension: Any) -> None:
    """
    Add an extension to a specific extension point
    
    Args:
        extension_point: Name of the extension point
        name: Name of the extension
        extension: Extension instance
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
    self._logger.info(f"Added extension: {name} to {extension_point}")
    
def remove_extension(self, extension_point: str, name: str) -> None:
    """
    Remove an extension
    
    Args:
        extension_point: Name of the extension point
        name: Name of the extension
    """
    if extension_point not in self._extension_points:
        raise ValueError(f"Extension point {extension_point} not registered")
        
    if name not in self._extensions[extension_point]:
        self._logger.warning(f"Extension {name} not found in {extension_point}")
        return
        
    del self._extensions[extension_point][name]
    self._logger.info(f"Removed extension: {name} from {extension_point}")
    
def get_extensions(self, extension_point: str) -> List[Any]:
    """
    Get all extensions for a specific extension point
    
    Args:
        extension_point: Name of the extension point
        
    Returns:
        List of extension instances
    """
    if extension_point not in self._extension_points:
        raise ValueError(f"Extension point {extension_point} not registered")
        
    return list(self._extensions[extension_point].values())
    
def discover_extensions(self, package_name: str) -> None:
    """
    Discover extensions in a package
    
    Args:
        package_name: Name of the package to scan for extensions
    """
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        self._logger.error(f"Could not import package {package_name}")
        return
        
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        try:
            module = importlib.import_module(name)
            
            # Look for classes with extension_point attribute
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and hasattr(attr, 'extension_point'):
                    extension_point = getattr(attr, 'extension_point')
                    extension_name = getattr(attr, 'extension_name', attr_name)
                    
                    if extension_point in self._extension_points:
                        try:
                            extension = attr()
                            self.add_extension(extension_point, extension_name, extension)
                        except Exception as e:
                            self._logger.error(f"Error creating extension {extension_name}: {str(e)}")
                            
        except ImportError:
            self._logger.error(f"Could not import module {name}")
```

## Usage Example

```python
# Create component registry
registry = ComponentRegistry()

# Register components
db_component = DatabaseComponent()
registry.register_component(db_component, ComponentMetadata(
    name="database",
    version="1.0.0",
    description="Database access component",
    tags=["storage", "persistence"]
))

cache_component = CacheComponent()
registry.register_component(cache_component, ComponentMetadata(
    name="cache",
    version="1.0.0",
    description="Cache component",
    dependencies=["database"],
    tags=["storage", "performance"]
))

# Initialize all components (in dependency order)
registry.initialize_components()

# Get a component
db = registry.get_component("database")

# Get components by tag
storage_components = registry.get_components_by_tag("storage")

# Create extension system
extension_system = ExtensionSystem(registry)

# Register extension point
extension_system.register_extension_point("data_processor", DataProcessorInterface)

# Add extension
csv_processor = CSVProcessor()
extension_system.add_extension("data_processor", "csv", csv_processor)

# Discover extensions in a package
extension_system.discover_extensions("my_package.extensions")

# Get all extensions for a point
processors = extension_system.get_extensions("data_processor")

# Shutdown all components (in reverse dependency order)
registry.shutdown_components()
```

## Testing

Create unit tests to verify:

1. Component registration and retrieval
2. Component dependency resolution
3. Component initialization and shutdown order
4. Extension point registration
5. Extension discovery and management
6. Circular dependency detection

## Integration with Other Components

The Component Registry will be used by:

1. Application bootstrap code to initialize all components
2. Config Manager for component configuration
3. All other components to discover and use other components
4. Extension System for plugin management

## Next Steps

After implementing the Component Registry:

1. Create a decorator for easy component registration
2. Implement automatic dependency injection
3. Add component versioning and compatibility checking
4. Create a component health monitoring system
5. Implement component hot-reloading for development