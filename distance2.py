import os
from pathlib import Path
import matplotlib.pyplot as plt
import random

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from pyparsing import Dict
k = 8 #depth parameter for blocking_edges function
amount = 0
giga = 0
old_scored_candidates = set()
def distance(a: FlippableTriangulation,
             b: FlippableTriangulation):
    

    #defining variables for first itteration, looks for the edges that differ
    dist =0
    flips_by_layer = list()
    flips_with_partner_by_layer = list()
    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    set_b = set(listb)
    a_working = a.fork()
    setChangedEdges = set(normalize_edge(*e) for e in diff(lista, listb))
    

    #start iterating till we reach b
    while not a_working.__eq__(b):
        giga = 0#for debug
        amount = 0 #for debug
        free = 0 #for debug
        setFlips = set()
        setFlipsWithPartner = set()
        toRemove = set()
        toAdd = set()
        for e in set(setChangedEdges): # try to flip all free edges first
            try:
                if isFree(a_working, set_b, e):
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    toRemove.add(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e,flip_rev))
                    free += 1
            except ValueError:
                continue
        print(f"Free flips this round: {free}")
        
        edges_to_flip = Huristic(a_working, set_b, setChangedEdges, k)
        
        if not edges_to_flip:
            break 

        setFlips = set()
        setFlipsWithPartner = set()
        toRemove = set()
        toAdd = set()
        amount = 0
        
        for e in edges_to_flip:
            try:
                # Double check validity before applying
                if e in a_working.possible_flips():
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    
                    toRemove.add(e)
                    toAdd.add(flip_rev)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e, flip_rev))
                    amount += 1
                    
            except ValueError:
                
                continue
        setChangedEdges -= toRemove
        setChangedEdges |= toAdd
        
        a_working.commit()
        
        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist += 1
        
        #print(f"{amount}")
        #print(setChangedEdges)

    return dist, flips_by_layer, flips_with_partner_by_layer

def Huristic(
    a_working: FlippableTriangulation,
    set_b: set[tuple[int, int]],
    setChangedEdges: set[tuple[int, int]],
    k: int
) -> list[tuple[int, int]]: # Changed return type to list
    
    scored_candidates = []
    

        
    existing_edges = set(e for e, score in scored_candidates)
    
    for e in setChangedEdges:
        if e in existing_edges: 
            continue
            
        try:
            score = blocking_edges(a_working, set_b, {e}, k)
            if score > 0:
                scored_candidates.append((e, score))
        except ValueError:
            continue

    set_scored = set(e for e, score in scored_candidates)
    set_scored = set_scored - old_scored_candidates
    old_scored_candidates.update(set_scored)
    scored_candidates = [pair for pair in scored_candidates if pair[0] in set_scored]

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    return solve_optimal_triangulation(scored_candidates)

def diff(a: list[tuple[int, int]] , b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    set_a = set(a)
    set_b = set(b)
    symmetric_diff = set_a.symmetric_difference(set_b)
    return list(symmetric_diff)

def isFree(a: FlippableTriangulation, set_b: set[tuple[int, int]],edge:tuple[int,int]) -> bool:
    try:
        flipped_edge = normalize_edge(*a.get_flip_partner(edge))
        if(flipped_edge in set_b):
            return True
    except ValueError:
        return False
    return False

def solve_optimal_triangulation(scored_candidates: list[tuple[tuple[int, int], float]]) -> list[tuple[int, int]]:
    """
    Takes a list of ((u, v), score) tuples and returns the optimal subset of edges
    that form a non-crossing set (triangulation subset) maximizing total score.
    Uses O(N^3) Interval Dynamic Programming.
    """
    if not scored_candidates:
        return []

    edges = [x[0] for x in scored_candidates]
    scores = [x[1] for x in scored_candidates]

    # Map vertices to 0..N-1
    unique_verts = set()
    for u, v in edges:
        unique_verts.add(u)
        unique_verts.add(v)
    
    sorted_verts = sorted(list(unique_verts))
    n = len(sorted_verts)
    
    if n == 0:
        return []

    vert_to_idx = {v: i for i, v in enumerate(sorted_verts)}
    idx_to_vert = {i: v for i, v in enumerate(sorted_verts)}

    # Create Edge Weights Map
    # Use max() to handle duplicate edges if they exist
    edge_weights: dict[tuple[int, int], float] = {}
    for (u, v), s in zip(edges, scores):
        u_idx, v_idx = vert_to_idx[u], vert_to_idx[v]
        if u_idx > v_idx:
            u_idx, v_idx = v_idx, u_idx
        edge_weights[(u_idx, v_idx)] = max(edge_weights.get((u_idx, v_idx), 0), s)

    # DP Tables
    # dp[i][j] = max score for polygon range i..j
    dp = [[0.0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]

    for length in range(2, n):
        for i in range(n - length):
            j = i + length
            
            max_score = -1.0
            best_k = -1
            
            # Score of the chord (i, j) itself (if it exists in candidates)
            current_closing_edge_score = edge_weights.get((i, j), 0.0)
            
            # Try all split points k
            for k in range(i + 1, j):
                # Combined score of left sub-poly + right sub-poly
                val = dp[i][k] + dp[k][j]
                if val > max_score:
                    max_score = val
                    best_k = k
            
            dp[i][j] = max_score + current_closing_edge_score
            split[i][j] = best_k

    # 6. Reconstruct Optimal Set
    selected_edges: list[tuple[int, int]] = []

    def reconstruct(i, j):
        if j <= i + 1:
            return
            
        # If the boundary (i, j) has weight, it means it's a selected edge
        if (i, j) in edge_weights:
            u_orig = idx_to_vert[i]
            v_orig = idx_to_vert[j]
            selected_edges.append((u_orig, v_orig))
            
        k = split[i][j]
        if k != 0:
            reconstruct(i, k)
            reconstruct(k, j)

    reconstruct(0, n - 1)
    
    return selected_edges

def normalize_edge(u, v):
    """Return the edge in a canonical form (smallest vertex first)."""
    return (min(u, v), max(u, v))

def new_triangles(a: FlippableTriangulation, e: tuple[int,int]):
    u, w = e
    v, z = a.get_flip_partner(e)
    
    t1 = [normalize_edge(u,v), normalize_edge(v,z), normalize_edge(z,u)]
    t2 = [normalize_edge(v,w), normalize_edge(w,z), normalize_edge(z,v)]
    
    return t1, t2
def blocking_edges(a: FlippableTriangulation, 
                   set_b: set[tuple[int, int]],
                   edges: set[tuple[int,int]], 
                   k: int,
                   visited: set[tuple[int, int]] = None) -> int:
    """
    Calculates how many 'free' edges can be reached recursively starting from a set of edges.
    """
    if k == 0 or not edges:
        return 0
    
    # Initialize visited set if this is the top-level call
    if visited is None:
        visited = set()
    
    # Create a local copy/update for this branch to prevent cycles
    # We add the current candidate edges to visited so we don't try to flip them again
    # deeper in the recursion (though they are removed from the triangulation anyway).
    current_visited = visited.copy()
    current_visited.update(edges)
    
    a_temp = a.fork()
    
    edge_to_partner = {}
    successful_flips = []
    
    # Try to schedule all flips in the current 'edges' set

    valid_flips_set = a_temp.possible_flips()
    
    for edge in edges:
        try:
            if edge in valid_flips_set:
                partner = normalize_edge(*a_temp.get_flip_partner(edge))
                edge_to_partner[edge] = partner
                a_temp.add_flip(edge)
                successful_flips.append(edge)
        except ValueError:
            continue
    
    if not successful_flips:
        return 0
    

    try:
        a_temp.commit()
    except ValueError:
        return 0
        

    for new_e in edge_to_partner.values():
        current_visited.add(new_e)
    
    newly_free_edges = set()
    candidates_for_next_layer = set()
    

    current_valid_flips = a_temp.possible_flips()
    

    for old_edge in successful_flips:
        new_edge = edge_to_partner[old_edge]

        neighbors = get_quad_boundaries(old_edge, new_edge)
        
        for neighbor in neighbors:
            norm_neighbor = normalize_edge(*neighbor)

            if norm_neighbor in current_visited:
                continue

            if norm_neighbor in current_valid_flips:
                
                if isFree(a_temp, set_b, norm_neighbor):
                    newly_free_edges.add(norm_neighbor)
                    current_visited.add(norm_neighbor)
                else:
                    candidates_for_next_layer.add(norm_neighbor)

    # Score
    score = len(newly_free_edges)
    
    next_batch = newly_free_edges | candidates_for_next_layer
    

    next_batch = {e for e in next_batch if e not in current_visited}
    
    if next_batch:
        #print(f"Depth {k}: Next batch size: {len(next_batch)}")
        recursive_score = blocking_edges(a_temp, set_b, next_batch, k - 1, current_visited)
        score += recursive_score

    return score


def get_quad_boundaries(old_edge: tuple[int, int], new_edge: tuple[int, int]) -> list[tuple[int, int]]:
    """
    Returns the 4 boundary edges of the quadrilateral defined by the diagonal flip.
    Old edge: (u, w)
    New edge: (v, z)
    The boundary edges are (u,v), (v,w), (w,z), (z,u).
    """
    u, w = old_edge
    v, z = new_edge
    
    # The edges of the quad are the connections between the endpoints
    # of the old diagonal and the new diagonal.
    boundaries = [
        normalize_edge(u, v),
        normalize_edge(v, w),
        normalize_edge(w, z),
        normalize_edge(z, u)
    ]
    
    return boundaries
