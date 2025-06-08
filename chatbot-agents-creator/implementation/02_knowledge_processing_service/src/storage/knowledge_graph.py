from typing import Dict, Any, List, Optional, Set, Tuple
from abc import ABC, abstractmethod

class KnowledgeGraph(ABC):
    """
    Abstract base class for knowledge graph storage backends.
    
    This class defines the interface for storing and retrieving knowledge graph data.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the knowledge graph.
        
        Args:
            config: Configuration dictionary for the knowledge graph
        """
        self.config = config or {}
        
    @abstractmethod
    def add_node(self, id: str, type: str, properties: Dict[str, Any] = None) -> bool:
        """
        Add a node to the graph.
        
        Args:
            id: Unique identifier for the node
            type: Type of the node
            properties: Optional properties to store with the node
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def add_edge(self, source_id: str, target_id: str, type: str, properties: Dict[str, Any] = None) -> bool:
        """
        Add an edge to the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            type: Type of the edge
            properties: Optional properties to store with the edge
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def get_node(self, id: str) -> Dict[str, Any]:
        """
        Get a node from the graph by ID.
        
        Args:
            id: Unique identifier for the node
            
        Returns:
            Node data including type and properties
        """
        pass
        
    @abstractmethod
    def get_edges(self, node_id: str, edge_type: str = None, direction: str = 'outgoing') -> List[Dict[str, Any]]:
        """
        Get edges connected to a node.
        
        Args:
            node_id: ID of the node
            edge_type: Optional type of edges to filter by
            direction: Direction of edges ('outgoing', 'incoming', 'both')
            
        Returns:
            List of edge data including source, target, type, and properties
        """
        pass
        
    @abstractmethod
    def query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a query against the graph.
        
        Args:
            query: Query string (format depends on implementation)
            params: Optional parameters for the query
            
        Returns:
            Query results
        """
        pass
        
    @abstractmethod
    def delete_node(self, id: str) -> bool:
        """
        Delete a node from the graph.
        
        Args:
            id: Unique identifier for the node
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def delete_edge(self, source_id: str, target_id: str, edge_type: str = None) -> bool:
        """
        Delete an edge from the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Optional type of the edge to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass


class InMemoryKnowledgeGraph(KnowledgeGraph):
    """
    In-memory implementation of a knowledge graph.
    
    This is a simple implementation that stores the graph in memory.
    It's suitable for development and testing, but not for production use.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the in-memory knowledge graph.
        """
        super().__init__(config)
        self.nodes = {}  # id -> {type, properties}
        self.outgoing_edges = {}  # source_id -> {target_id -> {type, properties}}
        self.incoming_edges = {}  # target_id -> {source_id -> {type, properties}}
        
    def add_node(self, id: str, type: str, properties: Dict[str, Any] = None) -> bool:
        """
        Add a node to the graph.
        
        Args:
            id: Unique identifier for the node
            type: Type of the node
            properties: Optional properties to store with the node
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.nodes[id] = {
                'type': type,
                'properties': properties or {}
            }
            
            # Initialize edge dictionaries for this node
            if id not in self.outgoing_edges:
                self.outgoing_edges[id] = {}
                
            if id not in self.incoming_edges:
                self.incoming_edges[id] = {}
                
            return True
        except Exception as e:
            print(f"Error adding node: {str(e)}")
            return False
        
    def add_edge(self, source_id: str, target_id: str, type: str, properties: Dict[str, Any] = None) -> bool:
        """
        Add an edge to the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            type: Type of the edge
            properties: Optional properties to store with the edge
            
        Returns:
            True if successful, False otherwise
        """
        # Check if nodes exist
        if source_id not in self.nodes:
            print(f"Source node {source_id} does not exist")
            return False
            
        if target_id not in self.nodes:
            print(f"Target node {target_id} does not exist")
            return False
            
        try:
            # Initialize edge dictionaries if needed
            if source_id not in self.outgoing_edges:
                self.outgoing_edges[source_id] = {}
                
            if target_id not in self.incoming_edges:
                self.incoming_edges[target_id] = {}
                
            # Add the edge
            edge_data = {
                'type': type,
                'properties': properties or {}
            }
            
            if target_id not in self.outgoing_edges[source_id]:
                self.outgoing_edges[source_id][target_id] = []
                
            if source_id not in self.incoming_edges[target_id]:
                self.incoming_edges[target_id][source_id] = []
                
            # Add the edge to both dictionaries
            self.outgoing_edges[source_id][target_id].append(edge_data)
            self.incoming_edges[target_id][source_id].append(edge_data)
            
            return True
        except Exception as e:
            print(f"Error adding edge: {str(e)}")
            return False
        
    def get_node(self, id: str) -> Dict[str, Any]:
        """
        Get a node from the graph by ID.
        
        Args:
            id: Unique identifier for the node
            
        Returns:
            Node data including type and properties
        """
        if id not in self.nodes:
            raise KeyError(f"Node with ID {id} not found")
            
        node_data = self.nodes[id].copy()
        node_data['id'] = id
        
        return node_data
        
    def get_edges(self, node_id: str, edge_type: str = None, direction: str = 'outgoing') -> List[Dict[str, Any]]:
        """
        Get edges connected to a node.
        
        Args:
            node_id: ID of the node
            edge_type: Optional type of edges to filter by
            direction: Direction of edges ('outgoing', 'incoming', 'both')
            
        Returns:
            List of edge data including source, target, type, and properties
        """
        if node_id not in self.nodes:
            raise KeyError(f"Node with ID {node_id} not found")
            
        results = []
        
        # Get outgoing edges
        if direction in ['outgoing', 'both']:
            if node_id in self.outgoing_edges:
                for target_id, edges in self.outgoing_edges[node_id].items():
                    for edge_data in edges:
                        if edge_type is None or edge_data['type'] == edge_type:
                            results.append({
                                'source': node_id,
                                'target': target_id,
                                'type': edge_data['type'],
                                'properties': edge_data['properties']
                            })
                            
        # Get incoming edges
        if direction in ['incoming', 'both']:
            if node_id in self.incoming_edges:
                for source_id, edges in self.incoming_edges[node_id].items():
                    for edge_data in edges:
                        if edge_type is None or edge_data['type'] == edge_type:
                            results.append({
                                'source': source_id,
                                'target': node_id,
                                'type': edge_data['type'],
                                'properties': edge_data['properties']
                            })
                            
        return results
        
    def query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a query against the graph.
        
        This is a very simple implementation that supports only basic queries.
        In a real implementation, this would support a proper query language.
        
        Supported queries:
        - "get_nodes_by_type:<type>" - Get all nodes of a specific type
        - "get_connected_nodes:<node_id>:<edge_type>:<direction>" - Get nodes connected to a node
        
        Args:
            query: Query string
            params: Optional parameters for the query
            
        Returns:
            Query results
        """
        params = params or {}
        
        if query.startswith("get_nodes_by_type:"):
            node_type = query.split(":", 1)[1]
            return self._get_nodes_by_type(node_type)
            
        elif query.startswith("get_connected_nodes:"):
            parts = query.split(":", 3)
            if len(parts) < 4:
                raise ValueError("Invalid query format for get_connected_nodes")
                
            node_id = parts[1]
            edge_type = parts[2] if parts[2] != "null" else None
            direction = parts[3]
            
            return self._get_connected_nodes(node_id, edge_type, direction)
            
        else:
            raise ValueError(f"Unsupported query: {query}")
        
    def delete_node(self, id: str) -> bool:
        """
        Delete a node from the graph.
        
        Args:
            id: Unique identifier for the node
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.nodes:
            return False
            
        try:
            # Delete the node
            del self.nodes[id]
            
            # Delete outgoing edges
            if id in self.outgoing_edges:
                for target_id in list(self.outgoing_edges[id].keys()):
                    if target_id in self.incoming_edges and id in self.incoming_edges[target_id]:
                        del self.incoming_edges[target_id][id]
                del self.outgoing_edges[id]
                
            # Delete incoming edges
            if id in self.incoming_edges:
                for source_id in list(self.incoming_edges[id].keys()):
                    if source_id in self.outgoing_edges and id in self.outgoing_edges[source_id]:
                        del self.outgoing_edges[source_id][id]
                del self.incoming_edges[id]
                
            return True
        except Exception as e:
            print(f"Error deleting node: {str(e)}")
            return False
        
    def delete_edge(self, source_id: str, target_id: str, edge_type: str = None) -> bool:
        """
        Delete an edge from the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Optional type of the edge to delete
            
        Returns:
            True if successful, False otherwise
        """
        if source_id not in self.outgoing_edges or target_id not in self.outgoing_edges[source_id]:
            return False
            
        try:
            # Delete from outgoing edges
            if edge_type is None:
                # Delete all edges between these nodes
                del self.outgoing_edges[source_id][target_id]
                del self.incoming_edges[target_id][source_id]
            else:
                # Delete only edges of the specified type
                self.outgoing_edges[source_id][target_id] = [
                    edge for edge in self.outgoing_edges[source_id][target_id]
                    if edge['type'] != edge_type
                ]
                
                self.incoming_edges[target_id][source_id] = [
                    edge for edge in self.incoming_edges[target_id][source_id]
                    if edge['type'] != edge_type
                ]
                
                # Clean up empty lists
                if not self.outgoing_edges[source_id][target_id]:
                    del self.outgoing_edges[source_id][target_id]
                    
                if not self.incoming_edges[target_id][source_id]:
                    del self.incoming_edges[target_id][source_id]
                    
            return True
        except Exception as e:
            print(f"Error deleting edge: {str(e)}")
            return False
            
    def _get_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """
        Get all nodes of a specific type.
        
        Args:
            node_type: Type of nodes to get
            
        Returns:
            List of node data
        """
        results = []
        
        for node_id, node_data in self.nodes.items():
            if node_data['type'] == node_type:
                result = node_data.copy()
                result['id'] = node_id
                results.append(result)
                
        return results
        
    def _get_connected_nodes(self, node_id: str, edge_type: str, direction: str) -> List[Dict[str, Any]]:
        """
        Get nodes connected to a node.
        
        Args:
            node_id: ID of the node
            edge_type: Type of edges to filter by (or None for all)
            direction: Direction of edges ('outgoing', 'incoming', 'both')
            
        Returns:
            List of node data
        """
        if node_id not in self.nodes:
            raise KeyError(f"Node with ID {node_id} not found")
            
        connected_node_ids = set()
        
        # Get outgoing edges
        if direction in ['outgoing', 'both'] and node_id in self.outgoing_edges:
            for target_id, edges in self.outgoing_edges[node_id].items():
                for edge_data in edges:
                    if edge_type is None or edge_data['type'] == edge_type:
                        connected_node_ids.add(target_id)
                        
        # Get incoming edges
        if direction in ['incoming', 'both'] and node_id in self.incoming_edges:
            for source_id, edges in self.incoming_edges[node_id].items():
                for edge_data in edges:
                    if edge_type is None or edge_data['type'] == edge_type:
                        connected_node_ids.add(source_id)
                        
        # Get node data for connected nodes
        results = []
        for connected_id in connected_node_ids:
            node_data = self.nodes[connected_id].copy()
            node_data['id'] = connected_id
            results.append(node_data)
            
        return results