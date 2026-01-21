import networkx as nx
from itertools import combinations
from collections import Counter, defaultdict, deque
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
    def get_critical_path_info(self) -> tuple[int, list]:
        """
        Helper function: Returns (max_length, list_of_heads) for this component.
        Refactored to allow the Manager to compare lengths across components.
        """
        if not self.nodes:
            return 0, []

        memo_height = {}

        def get_height(u):
            if u in memo_height:
                return memo_height[u]
            
            # Base case: No children
            if not self.graph[u]:
                memo_height[u] = 1
                return 1
            
            # Recursive step
            max_child_height = 0
            for v in self.graph[u]:
                h = get_height(v)
                if h > max_child_height:
                    max_child_height = h
            
            memo_height[u] = 1 + max_child_height
            return 1 + max_child_height

        max_len = -1
        critical_heads = []
        
        for head in self._heads:
            length = get_height(head)
            
            if length > max_len:
                max_len = length
                critical_heads = [head]
            elif length == max_len:
                critical_heads.append(head)
                
        return max_len, critical_heads
    def remove_node_safe(self, node) -> bool:
        """
        Removes a node ONLY if it is a Head (first) or a Tail (last).
        Returns True if successful, False if the node is "in the middle".
        """
        if node not in self.nodes:
            return False

        # Check conditions
        # 1. Is it a Head? (No incoming edges / parents)
        is_head = node in self._heads
        
        # 2. Is it a Tail? (No outgoing edges / children)
        is_tail = node not in self.graph or len(self.graph[node]) == 0

        # If it's neither, it's a middle node -> ABORT
        if not is_head and not is_tail:
            return False

        # --- Proceed with Removal ---

        # 1. Handle Outgoing Edges (If it's a Head being removed)
        # Note: If we remove a Head that has children, those children 
        # technically lose their dependency. In your geometric context, 
        # you might want to cascade delete them, but for now, we just 
        # update the graph topology so they become new Heads.
        if node in self.graph:
            for child in self.graph[node]:
                self.reverse_graph[child].remove(node)
                if not self.reverse_graph[child]:
                    self._heads.add(child)
            del self.graph[node]

        # 2. Handle Incoming Edges (If it's a Tail being removed)
        if node in self.reverse_graph:
            for parent in self.reverse_graph[node]:
                self.graph[parent].remove(node)
                # Parent doesn't change head status
            del self.reverse_graph[node]

        # 3. Cleanup Metadata
        self.nodes.remove(node)
        if node in self._heads:
            self._heads.remove(node)
            
        return True
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
    def get_critical_heads(self) -> list[tuple]:
        """
        Returns ONLY the Heads that start the longest possible chains 
        in this component.
        """
        if not self.nodes:
            return []

        # 1. Initialize Memoization Table
        # Maps node -> length of longest chain starting at this node
        memo_height = {}

        # 2. Define DFS helper to calculate height
        def get_height(u):
            if u in memo_height:
                return memo_height[u]
            
            # Base case: No children (Sink)
            if not self.graph[u]:
                memo_height[u] = 1
                return 1
            
            # Recursive step: 1 + max height of children
            max_child_height = 0
            for v in self.graph[u]:
                h = get_height(v)
                if h > max_child_height:
                    max_child_height = h
            
            memo_height[u] = 1 + max_child_height
            return 1 + max_child_height

        # 3. Calculate Height for ALL Heads
        # We only need to start DFS from Heads because all nodes are 
        # reachable from some head.
        max_len = -1
        critical_heads = []
        
        for head in self._heads:
            length = get_height(head)
            
            if length > max_len:
                max_len = length
                critical_heads = [head] # Found a new longest path, reset list
            elif length == max_len:
                critical_heads.append(head) # Tied for longest path
                
        return critical_heads
class DynamicGraphManager:
    def __init__(self):
        # Maps Node ID -> Component Instance
        self.node_map = {}
        # Keep track of unique component objects
        self.components = set()
    def get_first(self) -> list[tuple]:
        """
        Returns all heads that start the globally longest paths across ALL components.
        Example: 
           Comp1: A->B->C (Len 3)
           Comp2: D->E->F (Len 3)
           Comp3: G->H    (Len 2)
           Returns: [A, D]
        """
        global_max_len = -1
        global_heads = []

        for comp in self.components:
            # Get length and heads for this specific component
            length, heads = comp.get_critical_path_info()
            
            if length > global_max_len:
                # Found a new longest path, discard previous winners
                global_max_len = length
                global_heads = heads[:] 
            elif length == global_max_len:
                # Tie for longest path, add these heads to the list
                global_heads.extend(heads)
                
        return global_heads
    def get_heads(self) -> set[tuple[int, int]]:
        """
        Returns a set of all flips that are currently 'Heads' (no un-executed dependencies)
        across ALL components.
        """
        all_heads = set()
        for comp in self.components:
            all_heads.update(comp.get_heads())
        return all_heads
    def unlink_flip(self, node):
        """
        Attempts to remove a flip. 
        Raises an error or returns False if the flip is in the middle of a chain.
        """
        if node not in self.node_map:
            return False # Node doesn't exist

        comp = self.node_map[node]
        success = comp.remove_node_safe(node)

        if success:
            # Clean up manager reference
            del self.node_map[node]
            # Garbage collect empty components
            if not comp.nodes:
                self.components.remove(comp)
            return True
        else:
            # Depending on your preference, you can print a warning or raise an error
            print(f"Refused to unlink flip {node}: It is a middle dependency.")
            return False
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
    def get_longest_chain_component(self):
        """
        Returns the component with the longest critical path (maximum number of 
        topological layers) and its depth.
        
        Returns:
            (Component, int): The component instance and the number of layers.
        """
        longest_component = None
        max_depth = 0

        for comp in self.components:
            # Calculate the topological layers for this component
            layers = comp.get_layers_topological()
            depth = len(layers)
            
            if depth > max_depth:
                max_depth = depth
                longest_component = comp
                
        return longest_component, max_depth
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
            #if e == (9,30):
                #print(a_working.get_flip_partner(e))

            
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

            #if e == (50, 71):
             #   print(f"    (50, 71) dependent on {relevant_edges}")

            for edge2 in relevant_edges:
                if edge2 in edge_creator_map:
                    creator = edge_creator_map[edge2]
                    
                    if creator != "ORIGINAL":
                        # If edge2 was created by a previous flip, record the dependency
                        AllComponents.add_edge(creator, current_id)
                        
                        #if e == (50, 71):
                        #    print(f"        (50, 71) linked to {creator}")

            
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

def make_component_flip_stages(a:FlippableTriangulation, stages_of_flips: list[list[tuple[int,int]]])-> tuple[list[list[tuple[int,int]]] , int]:
    a_clone2 = a.fork()
    manager = MakeComponents(a, stages_of_flips)
    stages_of_flips_comp = list(list())
    global_layers = []

    for comp in manager.get_all_components():
        comp_layers = comp.get_layers_topological()
        
        for depth, layer in enumerate(comp_layers):
            while len(global_layers) <= depth:
                global_layers.append([])
            
            global_layers[depth].extend(layer)

    print(f"Total parallel stages: {len(global_layers)}")
    dist_comp = len(global_layers)
    for i, layer in enumerate(global_layers):

        stages_of_flips_comp.append(list())
        
        for node_id in layer:
            edge_to_flip = node_id[0]
            
            try:
                a_clone2.add_flip(edge_to_flip)

                stages_of_flips_comp[i].append(edge_to_flip) 
            except ValueError:

                pass
        
        a_clone2.commit()
    return stages_of_flips_comp,dist_comp
def check_if_flips_is_b(a:FlippableTriangulation,b:FlippableTriangulation, stages_of_flips: list[list[tuple[int,int]]])->bool:
    a_clone = a.fork()
    for stage in stages_of_flips:
        for edge in stage:
            a_clone.add_flip(edge)
        a_clone.commit()
    if(a_clone.__eq__(b)):
        return True
    return False
from collections import Counter
import copy

import copy
from helpFuncs import normalize_edge

def optimize_best_triangulation(triangs_stages_flips: list[list[list[tuple[int,int]]]], opt, triangs: list[FlippableTriangulation]) -> tuple:
    """
    Optimizes the center triangulation using a simple greedy loop approach.
    """
    """
    for i in range(len(triangs_stages_flips)):
        if check_if_flips_is_b(opt, triangs[i], triangs_stages_flips[i]) == False:
            print(f"Warning: One of the flip sequences does not lead to the target triangulation. {i}")
        else:
            print(f"Flip sequence {i} verified to lead to target triangulation.")
    """
    current_center = opt.fork()
    
    # Deep copy to protect the original data during the process
    current_stages_list = copy.deepcopy(triangs_stages_flips)
    n = len(triangs_stages_flips)
    last_improvement_iteration = 0
    iteration = 0
    max_length = max(len(stages) for stages in current_stages_list)
    # Track the edges created by the last move to prevent immediate undo loops
    last_created_edges = set()

    while last_improvement_iteration < max_length*n: #need ot iterate until no improvement in all triangs
        print("--- Optimization Round ---")
        
        total_dist_before = 0
        total_dist_after = 0
        current = MakeComponents(current_center, current_stages_list[iteration%n]) # need to choose one
        heads = current.get_first() # instead of these need to take first layer nodes of longest chains

        #create a new center with the flips of the first layer applied
        print(f"Trying flips: {heads}")
        if (len(heads) == 0):
            print("No heads to flip, skipping iteration.")
            iteration += 1
            last_improvement_iteration += 1
            continue
            
        center_try = current_center.fork()
        for ((u,v),(ut,vt),i) in heads:
            center_try.add_flip((u,v))
        center_try.commit()

        new_stages_list = []
        #loops and checkes new distance
        for stages in current_stages_list:
            tree = MakeComponents(current_center.fork(), stages)
            _, depth = tree.get_longest_chain_component()
            total_dist_before += depth
            stagescopy = copy.deepcopy(stages)
            headscurrent = tree.get_heads()

            active_head_edges = { node[0] for node in headscurrent }
            #delete or add the flips or oppisites
            for full_node_id in heads:
                ((u, v), _, _) = full_node_id

                # Check if this edge is wanted by the current target
                if (u, v) in active_head_edges:

                    
                    found_and_removed = False
                    
                    # We search layers in order (0, 1, 2...)
                    for idx, layer in enumerate(stagescopy):
                        if (u, v) in layer:
                            # 1. Remove the flip
                            layer.remove((u, v))
                            
                            # 2. Cleanup: If the layer is now empty, remove the list itself
                            if not layer:
                                stagescopy.pop(idx)
                            
                            # 3. CRITICAL: Stop searching! We only delete the first one.
                            found_and_removed = True
                            break 
                    
                    if not found_and_removed:
                        print(f"Warning: Flip {(u,v)} expected but not found in stages.")

                else:
                    partner = current_center.get_flip_partner((u, v))
                    stagescopy.insert(0, [partner])

            treeafter = MakeComponents(center_try, stagescopy)
            _, depth = treeafter.get_longest_chain_component()
            l = make_component_flip_stages(center_try, stagescopy)[0]
            new_stages_list.append(l)
            total_dist_after += depth
        
        # Determine strictness of improvement
        is_strict_improvement = total_dist_after < total_dist_before
        is_sideways_move = total_dist_after == total_dist_before
        
        # Extract the edges we just proposed to flip (to check against history)
        proposed_edges = { h[0][0] for h in heads }
        
        # Check if we are simply reversing the previous step (Cycle Detection)
        # If the edges we want to flip now are exactly the edges we created in the last step, it's a loop.
        is_reversal = (proposed_edges == last_created_edges)

        iteration += 1
        
        # We allow commit if Strict Improvement OR (Sideways Move AND Not a Reversal)
        if is_strict_improvement or (is_sideways_move and not is_reversal):
            
            if is_strict_improvement:
                print(f"Improved total distance: {total_dist_before} -> {total_dist_after}")
                last_improvement_iteration = 0 # Reset termination counter only on strict gains
            else:
                print(f"Sideways move (exploring plateau): {total_dist_before} -> {total_dist_after}")
                # We do NOT reset last_improvement_iteration here. 
                # This ensures we don't get stuck in a plateau forever.
                last_improvement_iteration += 1
                iteration -=1

            current_center = center_try
            current_stages_list = new_stages_list
            
            # Update the history for cycle detection
            # We store the *result* of the flips (the new diagonals), which correspond to h[0][1] in your tuple structure
            last_created_edges = { h[0][1] for h in heads }
            
        else:
            print(f"No improvement (or cycle detected): {total_dist_before} -> {total_dist_after}")
            last_improvement_iteration += 1
            
    return current_center, current_stages_list