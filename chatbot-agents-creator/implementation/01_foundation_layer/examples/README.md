# Foundation Layer Implementation Examples

This directory contains example implementations of Foundation Layer components. These examples are provided to help junior developers understand how to implement the components according to the requirements in the implementation guides.

## Purpose of Examples

The examples in this directory serve several purposes:

1. **Reference Implementation**: They provide a concrete implementation of the concepts described in the implementation guides.
2. **Best Practices**: They demonstrate best practices for code organization, documentation, and testing.
3. **Design Principles**: They show how to apply the core design principles (Scalability, Modularity, Autonomy, Future-Proofing, Client Ownership).
4. **Learning Resource**: They help junior developers understand the expected implementation approach.

## How to Use These Examples

These examples are meant to be **learning resources**, not code to be copied directly. Here's how to use them effectively:

1. **Read the Implementation Guide First**: Always start with the corresponding implementation guide to understand the requirements and design principles.
2. **Study the Example**: Review the example implementation to understand how the requirements are translated into code.
3. **Implement Your Own Version**: Create your own implementation based on the guide, using the example as a reference when needed.
4. **Compare and Refine**: After implementing your solution, compare it with the example to identify areas for improvement.

## Available Examples

### Config Manager Example

[`config_manager_example.py`](./config_manager_example.py) - Example implementation of the Config Manager component.

This example demonstrates:
- Implementation of the `ConfigSource` base class
- Implementation of the `FileConfigSource` class for file-based configuration
- Implementation of the `ConfigManager` class with support for:
  - Multiple configuration sources
  - Hierarchical configuration
  - Environment-specific configuration
  - Client-specific configuration
  - Environment variable overrides
  - Configuration validation
  - Configuration export/import

### Sample Unit Tests

[`test_config_manager_sample.py`](../tests/unit/test_config_manager_sample.py) - Example unit tests for the Config Manager component.

This example demonstrates:
- Comprehensive test coverage for all functionality
- Test fixtures setup and teardown
- Testing with temporary files
- Testing different file formats (JSON, YAML)
- Testing edge cases and error conditions
- Testing client ownership features

## Key Implementation Patterns

These examples demonstrate several important implementation patterns:

### 1. Abstract Base Classes

Using abstract base classes (ABC) to define interfaces that concrete implementations must follow:

```python
class ConfigSource(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def save(self, config: Dict[str, Any]) -> bool:
        pass
```

### 2. Dependency Injection

Passing dependencies as constructor parameters rather than creating them internally:

```python
def __init__(self, 
             config_sources: List[ConfigSource] = None,
             schema_file: Optional[str] = None,
             owner_id: Optional[str] = None,
             environment: str = "development"):
    self.config_sources = config_sources or []
    # ...
```

### 3. Composition Over Inheritance

Building functionality by composing objects rather than through inheritance:

```python
# ConfigManager uses ConfigSource objects through composition
config_manager = ConfigManager(
    config_sources=[file_source, parameter_store_source]
)
```

### 4. Separation of Concerns

Each class has a single responsibility:
- `ConfigSource`: Interface for loading/saving configuration
- `FileConfigSource`: Handles file-based configuration
- `ConfigManager`: Manages configuration from multiple sources

### 5. Client Ownership Support

Supporting client ownership through metadata and isolation:

```python
# Client-specific configuration
client_config = config_manager.get_client_config("client123")
```

## Extending the Examples

As you implement more components, consider how they interact with these examples:

- How does the Component Registry use the Config Manager?
- How do agents get their configuration?
- How is client ownership propagated through the system?

## Next Steps

After studying these examples:

1. Implement your assigned component following the implementation guide
2. Write comprehensive unit tests for your implementation
3. Ensure your implementation follows the design principles
4. Submit your implementation for review

Remember that your implementation doesn't need to match the example exactly, but it should fulfill all the requirements in the implementation guide and follow the core design principles.