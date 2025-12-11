import networkx as nx
from itertools import combinations
from collections import defaultdict, deque
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from helpFuncs import normalize_edge,new_triangles

class ConnectedDirectedComponent:
    def __init__(self, initial_node=None):
        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
        self.nodes = set()
        self._heads = set()
        
        # Initialize with one node if provided
        if initial_node is not None:
            self.nodes.add(initial_node)
            self._heads.add(initial_node)
    def get_layers_topological(self) -> list[list[tuple]]:
        """
        Returns layers where a node only appears after ALL its dependencies 
        (parents) have been processed. This guarantees valid parallel execution.
        """
        # 1. Calculate In-Degrees for all nodes
        in_degree = {node: 0 for node in self.nodes}
        for u in self.graph:
            for v in self.graph[u]:
                in_degree[v] += 1
        
        # 2. Layer 0 starts with nodes that have NO dependencies (Heads)
        current_layer = [n for n in self.nodes if in_degree[n] == 0]
        layers = []
        
        # 3. Process layer by layer
        while current_layer:
            layers.append(current_layer)
            next_layer = []
            
            for u in current_layer:
                # 'u' is done. Now notify its children.
                for v in self.graph[u]:
                    in_degree[v] -= 1
                    # Only add 'v' if ALL its parents are done
                    if in_degree[v] == 0:
                        next_layer.append(v)
            
            current_layer = next_layer
            
        return layers
    def add_edge_internal(self, u, v):
        """
        Adds edge logic WITHOUT checking for merges. 
        (Used internally by the Manager).
        """
        # 1. Update Sets
        self.graph[u].add(v)
        self.reverse_graph[v].add(u)
        self.nodes.add(u)
        self.nodes.add(v)

        # 2. Update Heads Logic
        # If v is in heads, remove it (it now has a parent)
        if v in self._heads:
            self._heads.remove(v)
        
        # If u is new to this component (and not in reverse_graph), it's a head
        # (Though usually the Manager handles the creation of U/V before calling this)
        if u not in self.reverse_graph:
            self._heads.add(u)

    def merge(self, other: 'ConnectedDirectedComponent'):
        """
        Absorbs 'other' component into 'self'.
        """
        # 1. Merge Nodes
        self.nodes.update(other.nodes)
        
        # 2. Merge Edges (Forward)
        for u, neighbors in other.graph.items():
            self.graph[u].update(neighbors)
            
        # 3. Merge Edges (Backward)
        for v, parents in other.reverse_graph.items():
            self.reverse_graph[v].update(parents)
            
        # 4. Merge Heads
        # (We will fix specific invalid heads when the connecting edge is added later)
        self._heads.update(other._heads)

    def get_heads(self):
        return self._heads
        
    def __repr__(self):
        return f"<Component Nodes: {len(self.nodes)}, Heads: {self._heads}>"
    def get_layers_of_nodes(self) -> list[list[tuple[int, int]]]:
        """
        Returns a list of lists.
        Index 0 contains the Head Flips (Layer 0).
        Index 1 contains flips enabled by Layer 0, etc.
        """
        if not self._heads:
            return []

        layers = []
        
        # Initialize with all heads
        current_layer_nodes = list(self._heads)
        visited_nodes = set(self._heads)
        
        while current_layer_nodes:
            # 1. Add the FLIPS themselves to the result
            layers.append(current_layer_nodes)

            next_layer_nodes = []
            
            for u in current_layer_nodes:
                # Get all dependent flips (children)
                for v in self.graph[u]:
                    if v not in visited_nodes:
                        visited_nodes.add(v)
                        next_layer_nodes.append(v)
            
            # Move to next layer
            current_layer_nodes = next_layer_nodes
            
        return layers
    def get_layers_as_edges(self) -> list[list[tuple]]:
        """
        Returns a list of lists.
        Index 0 contains edges from the Heads (Layer 0 to Layer 1).
        Index 1 contains edges from Layer 1 to Layer 2, etc.
        """
        if not self._heads:
            return []

        layers = []
        
        # Initialize with all heads
        current_layer_nodes = list(self._heads)
        visited_nodes = set(self._heads)
        
        while current_layer_nodes:
            next_layer_nodes = []
            current_layer_edges = []
            
            for u in current_layer_nodes:
                # Get all outgoing neighbors
                for v in self.graph[u]:
                    # We add the edge to the current layer
                    current_layer_edges.append((u, v))
                    
                    # If v hasn't been visited, it will be the start of the next layer
                    if v not in visited_nodes:
                        visited_nodes.add(v)
                        next_layer_nodes.append(v)
            
            # If we found edges in this layer, add them to the result
            if current_layer_edges:
                layers.append(current_layer_edges)
            
            # Move to next layer
            current_layer_nodes = next_layer_nodes
            
        return layers
class DynamicGraphManager:
    def __init__(self):
        # Maps Node ID -> Component Instance
        self.node_map = {}
        # Keep track of unique component objects
        self.components = set()
    def get_all_components(self) -> list['ConnectedDirectedComponent']:
            """Returns a list of all active connected components."""
            return list(self.components)
    def add_node(self, node):
        """
        Adds a single isolated node (flip) to the graph.
        If the node already exists, it does nothing.
        """
        if node not in self.node_map:
            # Create a new component containing ONLY this one flip
            new_comp = ConnectedDirectedComponent(node)
            self.components.add(new_comp)
            self.node_map[node] = new_comp
    def add_edge(self, u, v):
        # Case 1: Both nodes are new
        if u not in self.node_map and v not in self.node_map:
            new_comp = ConnectedDirectedComponent(u)
            # v will be added by add_edge_internal
            self.components.add(new_comp)
            self.node_map[u] = new_comp
            self.node_map[v] = new_comp
            new_comp.add_edge_internal(u, v)

        # Case 2: u is old, v is new
        elif u in self.node_map and v not in self.node_map:
            comp = self.node_map[u]
            self.node_map[v] = comp
            comp.add_edge_internal(u, v)

        # Case 3: u is new, v is old
        elif u not in self.node_map and v in self.node_map:
            comp = self.node_map[v]
            self.node_map[u] = comp
            comp.add_edge_internal(u, v)

        # Case 4: Both exist (The Merge Scenario)
        else:
            comp_u = self.node_map[u]
            comp_v = self.node_map[v]

            if comp_u is not comp_v:
                # MERGE DETECTED!
                # We merge v into u (arbitrary choice)
                #print(f"Merging component of {v} into component of {u}...")
                
                # 1. Perform the data merge
                comp_u.merge(comp_v)
                
                # 2. Update the pointer map for all nodes in the old component
                for node in comp_v.nodes:
                    self.node_map[node] = comp_u
                
                # 3. Remove the old component object
                self.components.remove(comp_v)
                
                # 4. Finally add the connecting edge
                comp_u.add_edge_internal(u, v)
            else:
                # They are already in the same component, just add edge
                comp_u.add_edge_internal(u, v)
        
    def get_component(self, node):
        return self.node_map.get(node)
def MakeComponents(a: FlippableTriangulation,
                   stages_of_flips: list[list[tuple[int, int]]]):
    
    AllComponents = DynamicGraphManager()
    
    # We maintain ONE working triangulation that moves forward in time.
    # This guarantees we never get "ValueError: Edge not flippable".
    a_working = a.fork()
    
    # MEMORY: Maps an active edge on the board -> The Node ID that created it.
    # This replaces the need to re-simulate components to find dependencies.
    edge_creator_map = {}
    
    # Initialize creator map with "ORIGINAL" for initial edges
    for edge in a.get_edges():
        norm_edge = normalize_edge(*edge)
        edge_creator_map[norm_edge] = "ORIGINAL"

    # Global counter to enforce uniqueness for every single flip operation (handles cycles)
    global_flip_id = 0

    for FlipList in stages_of_flips:
        for e in FlipList:
            
            e = normalize_edge(*e)
            if e == (9,30):
                print(a_working.get_flip_partner(e))

            
            # We calculate the partner edge to use in the ID
            partner = normalize_edge(*a_working.get_flip_partner(e))
            
            # format: (Edge_Before, Edge_After, Unique_Index)
            current_id = (e, partner, global_flip_id)
            global_flip_id += 1
            
            
            AllComponents.add_node(current_id)

            
            if e in edge_creator_map:
                creator = edge_creator_map[e]
                if creator != "ORIGINAL":
                    AllComponents.add_edge(creator, current_id)
            
            
            t1, t2 = new_triangles(a_working, e)
            raw_affecting = set(t1 + t2)
            affecting_edges = {normalize_edge(*edge) for edge in raw_affecting}
            
            # only the ones who affect the possiblity of it to flip
            relevant_edges = affecting_edges - {partner}

            if e == (50, 71):
                print(f"    (50, 71) dependent on {relevant_edges}")

            for edge2 in relevant_edges:
                if edge2 in edge_creator_map:
                    creator = edge_creator_map[edge2]
                    
                    if creator != "ORIGINAL":
                        # If edge2 was created by a previous flip, record the dependency
                        AllComponents.add_edge(creator, current_id)
                        
                        if e == (50, 71):
                            print(f"        (50, 71) linked to {creator}")

            
            try:
                
                a_working.add_flip(e)
                
                
                # The new edge (partner) is created by THIS specific node
                edge_creator_map[partner] = current_id
                
                # The old edge (e) is gone, remove it to keep map clean
                if e in edge_creator_map:
                    del edge_creator_map[e]

            except ValueError:
                print(f"    failed flip {e}")
                pass
        
        a_working.commit()
                
    return AllComponents
def FlipInThisTriangulation(a: FlippableTriangulation, e_before: tuple,e_after: tuple): #check if flip is now
    """ Checks if flipping e_before in triangulation a results in e_after."""
    
    try:
        if normalize_edge(*a.get_flip_partner(e_before)) == normalize_edge(*e_after):

            return True

    except ValueError:
        pass

    return False