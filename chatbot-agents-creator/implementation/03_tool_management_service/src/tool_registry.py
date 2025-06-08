from typing import Dict, Any, List, Optional, Set
import json
import semver
from .tool_interface import ToolInterface

class ToolMetadata:
    """
    Metadata for a tool in the registry.
    
    This class stores metadata about a tool, including its description,
    version, dependencies, and other information.
    """
    
    def __init__(self, tool: ToolInterface, tags: List[str] = None, 
                 dependencies: Dict[str, str] = None, author: str = None):
        """
        Initialize the tool metadata.
        
        Args:
            tool: The tool interface
            tags: Optional list of tags for categorization
            dependencies: Optional dictionary of dependencies (name -> version constraint)
            author: Optional author information
        """
        self.tool = tool
        self.name = tool.name
        self.description = tool.description
        self.version = tool.version
        self.tags = tags or []
        self.dependencies = dependencies or {}
        self.author = author
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the metadata to a dictionary.
        
        Returns:
            Dictionary representation of the metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'tags': self.tags,
            'dependencies': self.dependencies,
            'author': self.author,
            'parameter_schema': self.tool.get_parameter_schema().to_dict(),
            'result_schema': self.tool.get_result_schema().to_dict()
        }
        
    @staticmethod
    def from_dict(data: Dict[str, Any], tool: ToolInterface) -> 'ToolMetadata':
        """
        Create metadata from a dictionary.
        
        Args:
            data: Dictionary representation of the metadata
            tool: The tool interface
            
        Returns:
            Tool metadata
        """
        return ToolMetadata(
            tool=tool,
            tags=data.get('tags', []),
            dependencies=data.get('dependencies', {}),
            author=data.get('author')
        )


class ToolRegistry:
    """
    Registry for MCP-compliant tools.
    
    This class manages the registration, discovery, and retrieval of tools.
    """
    
    def __init__(self):
        """
        Initialize the tool registry.
        """
        self.tools = {}  # name -> {version -> (tool, metadata)}
        self.tags = {}   # tag -> set of (name, version)
        
    def register_tool(self, tool: ToolInterface, metadata: ToolMetadata = None) -> bool:
        """
        Register a tool in the registry.
        
        Args:
            tool: The tool to register
            metadata: Optional metadata for the tool
            
        Returns:
            True if registration was successful, False otherwise
        """
        name = tool.name
        version = tool.version
        
        # Create metadata if not provided
        if metadata is None:
            metadata = ToolMetadata(tool)
            
        # Check if tool with same name and version already exists
        if name in self.tools and version in self.tools[name]:
            return False
            
        # Initialize tool entry if needed
        if name not in self.tools:
            self.tools[name] = {}
            
        # Register the tool
        self.tools[name][version] = (tool, metadata)
        
        # Update tag index
        for tag in metadata.tags:
            if tag not in self.tags:
                self.tags[tag] = set()
            self.tags[tag].add((name, version))
            
        return True
        
    def get_tool(self, name: str, version: str = None) -> Optional[ToolInterface]:
        """
        Get a tool from the registry.
        
        Args:
            name: Name of the tool
            version: Optional version of the tool (latest if not specified)
            
        Returns:
            The tool interface, or None if not found
        """
        if name not in self.tools:
            return None
            
        if version is not None:
            # Get specific version
            if version in self.tools[name]:
                return self.tools[name][version][0]
            return None
            
        # Get latest version
        latest_version = self._get_latest_version(name)
        if latest_version:
            return self.tools[name][latest_version][0]
            
        return None
        
    def get_metadata(self, name: str, version: str = None) -> Optional[ToolMetadata]:
        """
        Get metadata for a tool.
        
        Args:
            name: Name of the tool
            version: Optional version of the tool (latest if not specified)
            
        Returns:
            The tool metadata, or None if not found
        """
        if name not in self.tools:
            return None
            
        if version is not None:
            # Get specific version
            if version in self.tools[name]:
                return self.tools[name][version][1]
            return None
            
        # Get latest version
        latest_version = self._get_latest_version(name)
        if latest_version:
            return self.tools[name][latest_version][1]
            
        return None
        
    def list_tools(self, tag: str = None) -> List[Dict[str, Any]]:
        """
        List all tools in the registry.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of tool information dictionaries
        """
        result = []
        
        if tag:
            # Filter by tag
            if tag in self.tags:
                for name, version in self.tags[tag]:
                    tool, metadata = self.tools[name][version]
                    result.append({
                        'name': name,
                        'version': version,
                        'description': tool.description,
                        'tags': metadata.tags
                    })
        else:
            # List all tools (latest versions)
            for name in self.tools:
                latest_version = self._get_latest_version(name)
                if latest_version:
                    tool, metadata = self.tools[name][latest_version]
                    result.append({
                        'name': name,
                        'version': latest_version,
                        'description': tool.description,
                        'tags': metadata.tags
                    })
                    
        return result
        
    def list_versions(self, name: str) -> List[str]:
        """
        List all versions of a tool.
        
        Args:
            name: Name of the tool
            
        Returns:
            List of versions, sorted newest to oldest
        """
        if name not in self.tools:
            return []
            
        # Sort versions using semver
        versions = list(self.tools[name].keys())
        versions.sort(key=lambda v: semver.VersionInfo.parse(v), reverse=True)
        
        return versions
        
    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tools by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tool information dictionaries
        """
        query = query.lower()
        result = []
        
        for name in self.tools:
            latest_version = self._get_latest_version(name)
            if latest_version:
                tool, metadata = self.tools[name][latest_version]
                
                # Check if query matches name or description
                if query in name.lower() or query in tool.description.lower():
                    result.append({
                        'name': name,
                        'version': latest_version,
                        'description': tool.description,
                        'tags': metadata.tags
                    })
                    
        return result
        
    def remove_tool(self, name: str, version: str = None) -> bool:
        """
        Remove a tool from the registry.
        
        Args:
            name: Name of the tool
            version: Optional version of the tool (all versions if not specified)
            
        Returns:
            True if removal was successful, False otherwise
        """
        if name not in self.tools:
            return False
            
        if version is not None:
            # Remove specific version
            if version not in self.tools[name]:
                return False
                
            # Remove from tag index
            metadata = self.tools[name][version][1]
            for tag in metadata.tags:
                if tag in self.tags:
                    self.tags[tag].discard((name, version))
                    
            # Remove the version
            del self.tools[name][version]
            
            # Remove the tool entry if no versions left
            if not self.tools[name]:
                del self.tools[name]
                
            return True
            
        # Remove all versions
        for version in list(self.tools[name].keys()):
            self.remove_tool(name, version)
            
        return True
        
    def check_dependencies(self, name: str, version: str) -> Dict[str, List[str]]:
        """
        Check if all dependencies of a tool are satisfied.
        
        Args:
            name: Name of the tool
            version: Version of the tool
            
        Returns:
            Dictionary of unsatisfied dependencies (name -> list of issues)
        """
        if name not in self.tools or version not in self.tools[name]:
            return {'error': ['Tool not found']}
            
        metadata = self.tools[name][version][1]
        unsatisfied = {}
        
        for dep_name, dep_version_constraint in metadata.dependencies.items():
            # Check if dependency exists
            if dep_name not in self.tools:
                unsatisfied[dep_name] = [f'Dependency {dep_name} not found']
                continue
                
            # Check if any version satisfies the constraint
            satisfied = False
            for dep_version in self.tools[dep_name]:
                try:
                    if semver.match(dep_version, dep_version_constraint):
                        satisfied = True
                        break
                except ValueError:
                    # Invalid version constraint
                    pass
                    
            if not satisfied:
                unsatisfied[dep_name] = [
                    f'No version of {dep_name} satisfies constraint {dep_version_constraint}'
                ]
                
        return unsatisfied
        
    def _get_latest_version(self, name: str) -> Optional[str]:
        """
        Get the latest version of a tool.
        
        Args:
            name: Name of the tool
            
        Returns:
            Latest version, or None if no versions exist
        """
        if name not in self.tools or not self.tools[name]:
            return None
            
        # Sort versions using semver
        versions = list(self.tools[name].keys())
        versions.sort(key=lambda v: semver.VersionInfo.parse(v), reverse=True)
        
        return versions[0] if versions else None