import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from dataclasses import dataclass, field

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
    owner_id: Optional[str] = None  # Client ownership identifier
    exportable: bool = False  # Whether component can be exported

class ComponentRegistry:
    """
    Central registry for all system components.
    Handles component registration, discovery, and dependency management.
    """
    
    def __init__(self):
        """Initialize the component registry"""
        self._components: Dict[str, Any] = {}
        self._metadata: Dict[str, ComponentMetadata] = {}
        self._logger = logging.getLogger(__name__)
        
    def register(self, component_id: str, component: Any, metadata: Optional[ComponentMetadata] = None) -> None:
        """
        Register a component with the registry
        
        Args:
            component_id: Unique identifier for the component
            component: The component instance to register
            metadata: Optional metadata describing the component
        """
        if component_id in self._components:
            self._logger.warning(f"Component {component_id} already registered, replacing")
            
        self._components[component_id] = component
        
        # Create default metadata if none provided
        if metadata is None:
            metadata = ComponentMetadata(
                name=component_id,
                version="1.0.0",
                description=f"Component: {component_id}"
            )
        
        self._metadata[component_id] = metadata
        self._logger.info(f"Registered component: {component_id} (v{metadata.version})")
        
        # Validate dependencies
        for dep in metadata.dependencies:
            if dep not in self._components:
                self._logger.warning(f"Component {component_id} depends on {dep}, which is not registered")
    
    def get(self, component_id: str) -> Optional[Any]:
        """
        Get a component by ID
        
        Args:
            component_id: ID of the component to retrieve
            
        Returns:
            Component instance or None if not found
        """
        if component_id not in self._components:
            self._logger.warning(f"Component {component_id} not found in registry")
            return None
            
        return self._components[component_id]
    
    def list_components(self) -> List[str]:
        """
        List all registered component IDs
        
        Returns:
            List of component IDs
        """
        return list(self._components.keys())
        
    def get_components_by_owner(self, owner_id: str) -> List[Any]:
        """
        Get all components owned by a specific client
        
        Args:
            owner_id: Client ownership identifier
            
        Returns:
            List of component instances owned by the client
        """
        result = []
        for component_id, metadata in self._metadata.items():
            if hasattr(metadata, 'owner_id') and metadata.owner_id == owner_id:
                result.append(self._components[component_id])
        return result
    
    def get_metadata(self, component_id: str) -> Optional[ComponentMetadata]:
        """
        Get metadata for a component
        
        Args:
            component_id: ID of the component
            
        Returns:
            ComponentMetadata or None if not found
        """
        return self._metadata.get(component_id)
    
    def remove(self, component_id: str) -> bool:
        """
        Remove a component from the registry
        
        Args:
            component_id: ID of the component to remove
            
        Returns:
            True if component was removed, False if not found
        """
        if component_id not in self._components:
            self._logger.warning(f"Cannot remove: Component {component_id} not found in registry")
            return False
            
        del self._components[component_id]
        if component_id in self._metadata:
            del self._metadata[component_id]
            
        self._logger.info(f"Removed component: {component_id}")
        return True
    
    def get_components_by_tag(self, tag: str) -> List[Any]:
        """
        Get all components with a specific tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of component instances
        """
        result = []
        for component_id, metadata in self._metadata.items():
            if tag in metadata.tags:
                result.append(self._components[component_id])
        return result
        
    def export_component(self, component_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Export a component for client deployment
        
        Args:
            component_id: ID of the component to export
            format: Export format (json, yaml)
            
        Returns:
            Dictionary with component export data
        """
        if component_id not in self._components:
            self._logger.warning(f"Component {component_id} not found in registry")
            return {}
            
        metadata = self._metadata[component_id]
        if not hasattr(metadata, 'exportable') or not metadata.exportable:
            self._logger.warning(f"Component {component_id} is not exportable")
            return {}
            
        component = self._components[component_id]
        
        # Check if component has export method
        if hasattr(component, 'prepare_for_export') and callable(getattr(component, 'prepare_for_export')):
            try:
                return component.prepare_for_export()
            except Exception as e:
                self._logger.error(f"Error exporting component {component_id}: {str(e)}")
                return {}
        
        # Default export format if component doesn't have export method
        export_data = {
            "component_id": component_id,
            "metadata": {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "owner_id": metadata.owner_id,
                "exported_at": "2025-08-06T15:30:00Z",  # In a real implementation, use actual timestamp
            },
            "configuration": {}  # Would include safe configuration values
        }
        
        return export_data
        
    def access_component(self, component_id: str, requester_id: str) -> Optional[Any]:
        """
        Access a component with ownership validation
        
        Args:
            component_id: ID of the component to access
            requester_id: ID of the requester
            
        Returns:
            Component instance or None if access denied
        """
        if component_id not in self._components:
            self._logger.warning(f"Component {component_id} not found in registry")
            return None
            
        metadata = self._metadata[component_id]
        
        # System components can be accessed by anyone
        if not hasattr(metadata, 'owner_id') or metadata.owner_id is None:
            return self._components[component_id]
            
        # Client components can only be accessed by their owner
        if metadata.owner_id == requester_id:
            return self._components[component_id]
            
        # Access denied
        self._logger.warning(f"Access denied: {requester_id} cannot access {component_id}")
        return None
    
    def _resolve_dependencies(self) -> List[str]:
        """
        Resolve component dependencies and return components in initialization order
        
        Returns:
            List of component IDs in dependency order
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


class ExtensionSystem:
    """
    System for managing extensions to the core functionality.
    Extensions are discovered, loaded, and managed through this system.
    """
    
    def __init__(self, registry: Optional[ComponentRegistry] = None):
        """
        Initialize the extension system
        
        Args:
            registry: Optional component registry to use
        """
        self._registry = registry
        self._extension_points: Dict[str, Type] = {}
        self._extensions: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(__name__)
        
    def register_extension_point(self, name: str, interface: Type) -> None:
        """
        Register an extension point with an interface type
        
        Args:
            name: Name of the extension point
            interface: Type that extensions must implement
        """
        if name in self._extension_points:
            self._logger.warning(f"Extension point {name} already registered, replacing")
            
        self._extension_points[name] = interface
        self._extensions[name] = {}
        self._logger.info(f"Registered extension point: {name}")
        
    def register_extension(self, point_name: str, extension: Any, name: Optional[str] = None, owner_id: Optional[str] = None) -> None:
        """
        Register an extension to a specific extension point
        
        Args:
            point_name: Name of the extension point
            extension: Extension instance
            name: Optional name for the extension (defaults to class name)
            owner_id: Optional client ownership identifier
        """
        if point_name not in self._extension_points:
            raise ValueError(f"Extension point {point_name} not registered")
            
        # Check if extension implements the required interface
        interface_type = self._extension_points[point_name]
        if not isinstance(extension, interface_type):
            raise TypeError(f"Extension does not implement {interface_type.__name__}")
            
        # Use class name if no name provided
        if name is None:
            name = extension.__class__.__name__
            
        if name in self._extensions[point_name]:
            self._logger.warning(f"Extension {name} already registered for {point_name}, replacing")
            
        self._extensions[point_name][name] = extension
        self._logger.info(f"Added extension: {name} to {point_name}")
        
        # Register with component registry if available
        if self._registry:
            self._registry.register(
                f"extension.{point_name}.{name}",
                extension,
                ComponentMetadata(
                    name=f"extension.{point_name}.{name}",
                    version="1.0.0",
                    description=f"Extension {name} for {point_name}",
                    owner_id=owner_id,
                    exportable=(owner_id is not None)
                )
            )
    
    def get_extensions(self, point_name: str) -> List[Any]:
        """
        Get all extensions for a specific extension point
        
        Args:
            point_name: Name of the extension point
            
        Returns:
            List of extension instances
        """
        if point_name not in self._extension_points:
            raise ValueError(f"Extension point {point_name} not registered")
            
        return list(self._extensions[point_name].values())
        
    def get_extensions_by_owner(self, point_name: str, owner_id: str) -> List[Any]:
        """
        Get extensions owned by a specific client
        
        Args:
            point_name: Name of the extension point
            owner_id: Client ownership identifier
            
        Returns:
            List of extension instances owned by the client
        """
        if point_name not in self._extension_points:
            raise ValueError(f"Extension point {point_name} not registered")
            
        result = []
        for name, extension in self._extensions[point_name].items():
            # Check if extension is registered in component registry
            if self._registry:
                extension_id = f"extension.{point_name}.{name}"
                metadata = self._registry.get_metadata(extension_id)
                if metadata and hasattr(metadata, 'owner_id') and metadata.owner_id == owner_id:
                    result.append(extension)
        
        return result
        
    def export_extensions(self, owner_id: str) -> Dict[str, Any]:
        """
        Export extensions owned by a client
        
        Args:
            owner_id: Client ownership identifier
            
        Returns:
            Dictionary with extension export data
        """
        result = {}
        
        # Check if we have a component registry
        if not self._registry:
            return result
            
        # Find all extensions owned by the client
        for point_name in self._extension_points:
            point_extensions = {}
            for name, extension in self._extensions[point_name].items():
                extension_id = f"extension.{point_name}.{name}"
                metadata = self._registry.get_metadata(extension_id)
                
                if metadata and hasattr(metadata, 'owner_id') and metadata.owner_id == owner_id:
                    # Export the extension
                    export_data = self._registry.export_component(extension_id)
                    if export_data:
                        point_extensions[name] = export_data
            
            if point_extensions:
                result[point_name] = point_extensions
                
        return result
    
    def remove_extension(self, point_name: str, name: str) -> bool:
        """
        Remove an extension
        
        Args:
            point_name: Name of the extension point
            name: Name of the extension
            
        Returns:
            True if extension was removed, False if not found
        """
        if point_name not in self._extension_points:
            raise ValueError(f"Extension point {point_name} not registered")
            
        if name not in self._extensions[point_name]:
            self._logger.warning(f"Extension {name} not found in {point_name}")
            return False
            
        del self._extensions[point_name][name]
        self._logger.info(f"Removed extension: {name} from {point_name}")
        
        # Remove from component registry if available
        if self._registry:
            self._registry.remove(f"extension.{point_name}.{name}")
            
        return True